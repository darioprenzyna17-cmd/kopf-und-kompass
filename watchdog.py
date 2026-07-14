"""
DC-Autopilot Waechter. Laeuft einmal taeglich abends (GitHub-Actions-Cron).

Prueft, ob HEUTE (Europe/Zurich) schon ein Post auf dem Konto rausging.
Wenn ja: nichts tun. Wenn nein: automatisch ein zeitloses Evergreen-Motiv posten,
damit der Account nie stumm bleibt. Rotiert durch den Evergreen-Pool (evergreen.json),
Fortschritt in evergreen_state.json.

Sicherheit: postet nur, wenn wirklich kein Post des Tages existiert.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Zurich")
except Exception:
    TZ = None

from lib_meta import _creds, get_json, GRAPH, post_single_image, ensure_public_url, find_live_by_caption

HERE = Path(__file__).parent
POOL = json.loads((HERE / "evergreen.json").read_text())
STATE = HERE / "evergreen_state.json"


def today():
    return (datetime.now(TZ) if TZ else datetime.now()).date()


def posted_today():
    """True, wenn der neueste Post auf dem Konto von heute ist."""
    ig, tok = _creds()
    d = get_json(f"{GRAPH}/{ig}/media?fields=timestamp&limit=1&access_token={tok}")
    items = d.get("data") or []
    if not items:
        return False
    ts = items[0].get("timestamp")
    if not ts:
        return False
    when = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")
    local = when.astimezone(TZ) if TZ else when
    return local.date() == today()


def main():
    if posted_today():
        print("Heute wurde bereits gepostet -> kein Ersatz noetig.")
        return 0
    st = json.loads(STATE.read_text()) if STATE.exists() else {"i": 0}
    item = POOL[st["i"] % len(POOL)]
    st["i"] += 1
    print("Kein Post heute -> Evergreen-Ersatz:", (item["caption"].splitlines() or [""])[0])
    try:
        mid, link = post_single_image(ensure_public_url(item["image"]), item["caption"])
    except Exception as ex:
        # 400-aber-live abfangen (wie beim Poster)
        mid, link = find_live_by_caption(item["caption"])
        if not mid:
            raise
        print("(API-Fehler, aber Post ging live)", ex)
    print("Evergreen live:", link)
    STATE.write_text(json.dumps(st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
