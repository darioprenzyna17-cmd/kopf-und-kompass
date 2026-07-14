"""Plant ein fertiges Footage-Reel in die Posting-Queue ein (fuer die Reel-Tage Mo/Mi/Sa
der Wochen-Routine). Nimmt assets/video_reels/<name>.mp4 + <name>.caption.txt und haengt
einen queue.jsonl-Eintrag (format=reel) an. Das Reel wird zur geplanten Zeit vom
GitHub-Actions-Poster (scheduler.py --live) veroeffentlicht.

WICHTIG: Die mp4 muss ins Repo committet + gepusht sein, damit die Cloud den Clip
oeffentlich hochladen und posten kann.

Aufruf:
    python3 queue_reel.py <name> <YYYY-MM-DD> [HH:MM:SS]
Beispiel:
    python3 queue_reel.py dachdecker 2026-07-20 12:00:00
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
QUEUE = HERE / "queue.jsonl"
VDIR = HERE / "assets" / "video_reels"


def main():
    if len(sys.argv) < 3:
        print("Aufruf: python3 queue_reel.py <name> <YYYY-MM-DD> [HH:MM:SS]")
        sys.exit(1)
    name, day = sys.argv[1], sys.argv[2]
    tm = sys.argv[3] if len(sys.argv) > 3 else "12:00:00"
    vid = VDIR / f"{name}.mp4"
    capf = VDIR / f"{name}.caption.txt"
    if not vid.exists():
        print(f"FEHLER: {vid} fehlt. Zuerst mit build_video_reel.py bauen.")
        sys.exit(1)
    caption = capf.read_text(encoding="utf-8") if capf.exists() else ""
    entry = {
        "id": f"reel-{name}-{day}",
        "datetime": f"{day}T{tm}",
        "theme": name,
        "format": "reel",
        "video_url": f"assets/video_reels/{name}.mp4",
        "caption": caption,
        "status": "pending",
    }
    # Dublette vermeiden (gleiche id schon in der Queue?)
    if QUEUE.exists():
        for line in QUEUE.read_text().splitlines():
            line = line.strip()
            if line and json.loads(line).get("id") == entry["id"]:
                print(f"Bereits eingeplant: {entry['id']} (nichts getan)")
                return
    with QUEUE.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Eingeplant: {name} am {day} {tm} -> {vid.name}")
    print("Nicht vergessen: die mp4 + queue.jsonl committen und pushen, damit die Cloud posten kann.")


if __name__ == "__main__":
    main()
