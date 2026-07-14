"""
Lern-Report: liest die echten Account-Zahlen (Instagram Insights) der letzten Posts,
findet je Wochentag die beste Uhrzeit (nach Reichweite/Interaktionen) und schreibt sie
in posting_times.json. Wird vor der woechentlichen Generierung ausgefuehrt.

Voraussetzung: Token mit Berechtigung 'instagram_manage_insights'.
Bis genug Daten pro Wochentag da sind, bleiben die Recherche-Startwerte stehen.
"""
import json
import os
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).parent
PT_FILE = HERE / "posting_times.json"
GRAPH = "https://graph.facebook.com/v21.0"
MIN_SAMPLES = 2  # ab so vielen Posts pro Wochentag wird die Zeit angepasst


def env(name):
    v = os.environ.get(name)
    if not v and (HERE / ".env").exists():
        for l in (HERE / ".env").read_text().splitlines():
            if l.startswith(name + "="):
                v = l.split("=", 1)[1].strip()
    if not v:
        raise RuntimeError(name)
    return v


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def score(media_id, token):
    try:
        d = get(f"{GRAPH}/{media_id}/insights?metric=reach,total_interactions&access_token={token}")
        vals = {m["name"]: (m.get("values") or [{}])[0].get("value", 0) for m in d.get("data", [])}
        return vals.get("reach", 0) + 3 * vals.get("total_interactions", 0)
    except Exception:
        try:
            d = get(f"{GRAPH}/{media_id}/insights?metric=reach&access_token={token}")
            return (d["data"][0]["values"][0]["value"]) if d.get("data") else 0
        except Exception:
            return 0


def main():
    ig, token = env("IG_USER_ID"), env("IG_ACCESS_TOKEN")
    feed = get(f"{GRAPH}/{ig}/media?fields=id,timestamp,media_type&limit=60&access_token={token}")
    # je Wochentag: Liste (hour, score)
    by_day = defaultdict(list)
    for m in feed.get("data", []):
        ts = m.get("timestamp", "")
        try:
            # in lokale Zeit (Europe/Zurich ~ UTC+2 Sommer); grob +2h
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=2)))
        except Exception:
            continue
        by_day[t.weekday()].append((t.hour, score(m["id"], token)))

    pt = json.loads(PT_FILE.read_text())
    changed = []
    for wd, arr in by_day.items():
        if len(arr) < MIN_SAMPLES:
            continue
        # beste Stunde = hoechster Durchschnitts-Score
        hours = defaultdict(list)
        for h, s in arr:
            hours[h].append(s)
        best_h = max(hours, key=lambda h: sum(hours[h]) / len(hours[h]))
        newt = f"{best_h:02d}:00:00"
        if pt.get(str(wd)) != newt:
            pt[str(wd)] = newt
            changed.append((wd, newt, len(arr)))

    PT_FILE.write_text(json.dumps(pt, ensure_ascii=False, indent=2))
    if changed:
        for wd, t, n in changed:
            print(f"Wochentag {wd}: beste Zeit -> {t} (aus {n} Posts)")
    else:
        print("Noch nicht genug Daten pro Wochentag, Startwerte bleiben.")


if __name__ == "__main__":
    main()
