"""Kopf & Kompass — Wachstums-Messung.

Erfasst eine datierte Momentaufnahme (Follower, Reichweite-%, Sends/Reel, Saves/Reel)
und haengt sie an growth_log.json an. So wird die Wachstumskurve belegbar und steuerbar.
Nordstern: Reichweite-% (Ziel weg von ~1% Richtung 8-10%) + Sends pro Reel + Follower.

Zugang aus Umgebung (IG_USER_ID, IG_ACCESS_TOKEN). Aufruf: python3 growth_report.py
"""
import datetime
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from learn_and_adapt import env, media_index, insights, GRAPH  # noqa: E402


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    ig, token = env("IG_USER_ID"), env("IG_ACCESS_TOKEN")
    prof = _get(f"{GRAPH}/{ig}?fields=followers_count,media_count&access_token={token}")
    followers = prof.get("followers_count")

    data = json.loads((HERE / "reel_pipeline.json").read_text())
    built = data.get("built", [])[-8:]   # die letzten bis zu 8 Reels
    idx = media_index(ig, token)
    reels = []
    for b in built:
        mid = idx.get((b.get("permalink") or "").rstrip("/"))
        if not mid:
            continue
        ins = insights(mid, token)
        reels.append({"name": b.get("name"), "theme": b.get("theme"),
                      "reach": ins.get("reach", 0), "shares": ins.get("shares", 0),
                      "saved": ins.get("saved", 0)})
    n = len(reels) or 1
    avg_reach = round(sum(r["reach"] for r in reels) / n, 1)
    avg_shares = round(sum(r["shares"] for r in reels) / n, 2)
    avg_saved = round(sum(r["saved"] for r in reels) / n, 2)
    reach_pct = round(100 * avg_reach / followers, 2) if followers else None

    snap = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "followers": followers,
        "reels_gemessen": len(reels),
        "avg_reach": avg_reach,
        "reach_pct": reach_pct,
        "avg_shares": avg_shares,
        "avg_saved": avg_saved,
    }

    logp = HERE / "growth_log.json"
    if logp.exists():
        log = json.loads(logp.read_text())
    else:
        log = {"_hinweis": "Woechentliche Wachstums-Baseline. Nordstern: Reichweite-% (Ziel 8-10%), Sends/Reel, Follower.",
               "snapshots": []}
    prev = log["snapshots"][-1] if log["snapshots"] else None
    log["snapshots"].append(snap)
    logp.write_text(json.dumps(log, ensure_ascii=False, indent=2))

    print("SNAPSHOT:", json.dumps(snap, ensure_ascii=False))
    if prev:
        df = (followers or 0) - (prev.get("followers") or 0)
        dp = round((reach_pct or 0) - (prev.get("reach_pct") or 0), 2)
        ds = round((avg_shares or 0) - (prev.get("avg_shares") or 0), 2)
        print(f"DELTA seit {prev['date']}: Follower {df:+d}, Reichweite-% {dp:+}, Sends/Reel {ds:+}")
    else:
        print("BASELINE gesetzt (erste Messung).")


if __name__ == "__main__":
    main()
