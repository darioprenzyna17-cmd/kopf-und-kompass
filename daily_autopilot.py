"""Kopf & Kompass — Tages-Autopilot (laeuft taeglich via launchd, ganz ohne Nutzer).
1) baut + postet den naechsten klaren Reel (cloud_build_post: lernt vorher aus den Zahlen)
2) postet 2 Stories: Teaser auf den neuen Reel + einen eigenstaendigen Gedanken
Zugang aus .env (lokal). Robust: eine fehlgeschlagene Story blockiert den Reel nicht.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
for line in (HERE / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
sys.path.insert(0, str(HERE))


def main():
    import cloud_build_post
    concept = None
    try:
        concept = cloud_build_post.main()   # baut + postet Reel, gibt Konzept zurueck
    except Exception as e:
        print("REEL-FEHLER:", repr(e)[:300], flush=True)

    # Stories nur, wenn ein Reel gepostet wurde
    if not concept:
        print("Kein Reel heute (Pipeline leer oder Fehler), keine Stories.", flush=True)
        return
    try:
        import build_story as st
        import lib_meta as meta
        thoughts = concept.get("thoughts", [])
        hook = thoughts[0] if thoughts else ""
        killer = thoughts[-1] if thoughts else ""
        # Story 1: Teaser auf den neuen Reel
        p1 = st.story_teaser(hook, HERE / "assets" / "stories" / "daily_teaser.png",
                             label="Neu im Feed", foot="Ganzer Gedanke im Feed")
        meta.post_story(meta.ensure_public_url(str(p1)), is_video=False)
        print("STORY teaser gepostet", flush=True)
        # Story 2: eigenstaendiger Gedanke (Killer-Zeile des heutigen Reels)
        p2 = st.story_gedanke(killer, HERE / "assets" / "stories" / "daily_gedanke.png",
                              foot="Antworte mit einem Wort.")
        meta.post_story(meta.ensure_public_url(str(p2)), is_video=False)
        print("STORY gedanke gepostet", flush=True)
    except Exception as e:
        print("STORY-FEHLER:", repr(e)[:300], flush=True)


if __name__ == "__main__":
    main()
