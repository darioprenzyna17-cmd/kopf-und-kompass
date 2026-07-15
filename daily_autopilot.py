"""Kopf & Kompass — Tages-Autopilot (laeuft taeglich via launchd, ganz ohne Nutzer).
Postzeit VARIIERT taeglich: launchd feuert zu mehreren Slots, gepostet wird nur zum
Slot des Tages (rotierend), und nie zweimal am selben Tag (Marker).
1) baut + postet den naechsten klaren Reel (cloud_build_post: lernt vorher aus den Zahlen)
2) postet 2 Stories: Teaser auf den neuen Reel + einen eigenstaendigen Gedanken
Zugang aus .env (lokal). Robust: eine fehlgeschlagene Story blockiert den Reel nicht.
"""
import os
import sys
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).parent
for line in (HERE / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
sys.path.insert(0, str(HERE))

# Variierende Postzeiten: launchd feuert zu allen Slots, gepostet wird zum Slot des Tages.
SLOTS = ["08:10", "12:35", "17:05", "19:40"]


def should_post_now():
    marker = HERE / "last_post.txt"
    today = date.today().isoformat()
    if marker.exists() and marker.read_text().strip() == today:
        print("Heute schon gepostet, ueberspringe.", flush=True)
        return False
    chosen = SLOTS[date.today().timetuple().tm_yday % len(SLOTS)]
    now = datetime.now().strftime("%H:%M")
    if now < chosen:
        print(f"Heutiger Slot ist {chosen}, jetzt {now}. Warte auf spaeteren Lauf.", flush=True)
        return False
    print(f"Heutiger Slot {chosen} erreicht (jetzt {now}). Poste.", flush=True)
    return True


def main():
    if not should_post_now():
        return
    import cloud_build_post
    concept = None
    try:
        concept = cloud_build_post.main()   # baut + postet Reel, gibt Konzept zurueck
    except Exception as e:
        print("REEL-FEHLER:", repr(e)[:300], flush=True)
    if not concept:
        print("Kein Reel (Pipeline leer oder Fehler), keine Stories, kein Marker.", flush=True)
        return
    # Marker erst NACH erfolgreichem Reel setzen (sonst Retry beim naechsten Slot)
    (HERE / "last_post.txt").write_text(date.today().isoformat())
    try:
        import build_story as st
        import lib_meta as meta
        thoughts = concept.get("thoughts", [])
        hook = thoughts[0] if thoughts else ""
        killer = thoughts[-1] if thoughts else ""
        p1 = st.story_teaser(hook, HERE / "assets" / "stories" / "daily_teaser.png",
                             label="Neu im Feed", foot="Ganzer Gedanke im Feed")
        meta.post_story(meta.ensure_public_url(str(p1)), is_video=False)
        print("STORY teaser gepostet", flush=True)
        p2 = st.story_gedanke(killer, HERE / "assets" / "stories" / "daily_gedanke.png",
                              foot="Antworte mit einem Wort.")
        meta.post_story(meta.ensure_public_url(str(p2)), is_video=False)
        print("STORY gedanke gepostet", flush=True)
    except Exception as e:
        print("STORY-FEHLER:", repr(e)[:300], flush=True)


if __name__ == "__main__":
    main()
