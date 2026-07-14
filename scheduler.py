"""
DC-Autopilot Laeufer. Wird regelmaessig (GitHub-Actions-Cron) aufgerufen.

Liest queue.jsonl, postet alle faelligen Eintraege (Zeitpunkt erreicht, Status
pending) je nach Format (image / carousel / reel), markiert sie als posted und
schreibt die Queue zurueck. Idempotent ueber den Status.

Sicherheit: Standard ist Trockenlauf. Echt gepostet wird nur mit --live.

Queue-Eintrag (eine JSON-Zeile pro Post):
  {
    "id": "2026-08-05-0730",
    "datetime": "2026-08-05T07:30:00",     # Europe/Zurich, lokale Zeit
    "theme": "Fachkraeftemangel",
    "format": "carousel",                    # image | carousel | reel
    "image_urls": ["https://.../1.jpg", ...],# bei image genau 1, bei carousel 2-10
    "video_url": "https://.../reel.mp4",     # nur bei reel
    "caption": "…",
    "status": "pending"
  }
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

from lib_meta import publish_entry, find_live_by_caption

QUEUE = Path(__file__).parent / "queue.jsonl"


def load_queue():
    if not QUEUE.exists():
        return []
    return [json.loads(l) for l in QUEUE.read_text().splitlines() if l.strip()]


def save_queue(entries):
    QUEUE.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n"
    )


def now():
    return datetime.now(TZ) if TZ else datetime.now()


def due(entries, now_dt):
    out = []
    for e in entries:
        if e.get("status", "pending") != "pending":
            continue
        try:
            when = datetime.fromisoformat(e["datetime"])
            if TZ and when.tzinfo is None:
                when = when.replace(tzinfo=TZ)
        except Exception:
            print(f"WARN ungueltiges datetime bei {e.get('id')}", file=sys.stderr)
            continue
        if when <= now_dt:
            out.append(e)
    return out


def main(live):
    entries = load_queue()
    now_dt = now()
    todo = due(entries, now_dt)
    print(f"=== DC-Autopilot {now_dt.isoformat(timespec='seconds')} | Modus: {'LIVE' if live else 'DRY-RUN'} ===")
    if not todo:
        print("Keine faelligen Posts.")
        return 0

    rc = 0
    for e in todo:
        label = f"{e.get('id')} [{e.get('format','image')}] {e.get('theme','')}"
        if not live:
            print(f"DRY-RUN wuerde posten: {label}")
            continue
        # Idempotenz-Vorpruefung: ist dieser Post (gleicher Hook) schon live? Dann nicht doppelt posten.
        dup_id, dup_link = find_live_by_caption(e.get("caption", ""))
        if dup_id:
            e["status"] = "posted"
            e["media_id"] = dup_id
            e["permalink"] = dup_link
            e["posted_at"] = now_dt.isoformat(timespec="seconds")
            e["note"] = "bereits live gefunden, kein Doppel-Post"
            print(f"SKIP {label}: bereits live {dup_link}")
            save_queue(entries)
            continue
        try:
            media_id, link = publish_entry(e)
            e["status"] = "posted"
            e["media_id"] = media_id
            e["permalink"] = link
            e["posted_at"] = now_dt.isoformat(timespec="seconds")
            print(f"LIVE {label}: {link}")
        except Exception as ex:
            # Nach Fehler pruefen, ob der Post trotzdem live ging (haeufig 400 bei Carousel).
            dup_id, dup_link = find_live_by_caption(e.get("caption", ""))
            if dup_id:
                e["status"] = "posted"
                e["media_id"] = dup_id
                e["permalink"] = dup_link
                e["posted_at"] = now_dt.isoformat(timespec="seconds")
                e["error"] = str(ex)
                e["note"] = "API-Fehler, aber Post ging live"
                print(f"RECOVER {label}: live trotz Fehler ({ex}) -> {dup_link}")
            else:
                e["status"] = "failed"
                e["error"] = str(ex)
                rc = 1
                print(f"FEHLER {label}: {ex}", file=sys.stderr)
        save_queue(entries)
    return rc


if __name__ == "__main__":
    sys.exit(main(live="--live" in sys.argv))
