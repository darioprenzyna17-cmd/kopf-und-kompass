"""Autonomer Cloud-Lauf: baut das naechste approved-Konzept im Archivkino-Look und
postet es direkt nach @kopfundkompass. Aktualisiert reel_pipeline.json + used_reels.json.
Zugang aus Umgebung (GitHub-Secrets IG_USER_ID, IG_ACCESS_TOKEN, KIE_API_KEY).
Aufruf in reel.yml. Committen/Pushen der Ledger macht der Workflow."""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_video_reel as bvr   # noqa: E402
import kk_resilienz as res       # noqa: E402
import lib_meta as meta          # noqa: E402
import zeitplan                  # noqa: E402


def pick(approved):
    """Waehlt das naechste Konzept.

    Auftrag 3.1: gesperrte Konzepte fallen raus.
    Auftrag 6.2: rund 70 Prozent Gewinner-Muster, rund 30 Prozent bewusst neues Terrain.
    Die alte Fassung nahm IMMER das erste Gewinner-Thema. Damit hat sich der Account auf
    ein Thema festgefahren, die Bestands-Audience gesaettigt und nichts Neues mehr gelernt.
    """
    frei = [c for c in approved if not res.ist_gesperrt(c.get("name", ""))]
    if not frei:
        print("Alle Konzepte in Quarantaene, nichts baubar.")
        return None
    gesperrt = len(approved) - len(frei)
    if gesperrt:
        print(f"{gesperrt} Konzept(e) in Quarantaene uebersprungen.")

    winners = []
    lp = HERE / "learnings.json"
    if lp.exists():
        try:
            winners = json.loads(lp.read_text()).get("gewinner_themen", []) or []
        except Exception:
            winners = []

    bewaehrt = [c for c in frei if c.get("theme") in winners]
    neuland = [c for c in frei if c.get("theme") not in winners]

    # Deterministisch ueber den Tag gestreut statt zufaellig, damit der Anteil ueber die
    # Woche wirklich bei 70/30 landet und nicht am Zufall haengt.
    erkunden = (date.today().toordinal() % 10) >= 7
    if erkunden and neuland:
        c = neuland[0]
        print(f"Erkundung (30-Prozent-Anteil): Thema '{c.get('theme')}' ausserhalb der Gewinner.")
        return c
    if bewaehrt:
        c = bewaehrt[0]
        print(f"Lern-Loop: waehle Gewinner-Thema '{c.get('theme')}'")
        return c
    print(f"Kein Gewinner-Thema verfuegbar, nehme '{frei[0].get('theme')}'.")
    return frei[0]


def main(ignoriere_slot: bool = False):
    # 0) Zeit-Experiment: postet nur zum heutigen Slot, und nie zweimal am Tag
    if not ignoriere_slot:
        if zeitplan.schon_gepostet():
            return
        if not zeitplan.ist_mein_slot():
            return
    # 1) Erst lernen: echte Zahlen auswerten, learnings.json aktualisieren
    try:
        import learn_and_adapt
        learn_and_adapt.main()
    except Exception as e:
        print("Lern-Schritt uebersprungen:", e)
    pf = HERE / "reel_pipeline.json"
    data = json.loads(pf.read_text())
    approved = data.get("approved", [])
    if not approved:
        print("Pipeline leer, nichts zu tun.")
        return
    c = pick(approved)
    if c is None:
        res.status_schreiben(False, grund="Alle Konzepte in Quarantaene.")
        return
    name = c["name"]

    # Auftrag 4: erst das Geld pruefen, dann bauen.
    ok, grund = res.budget_ok()
    if not ok:
        print("STOPP:", grund, flush=True)
        res.status_schreiben(False, name=name, grund=grund)
        return

    try:
        print(f"=== BUILD {name} ===", flush=True)
        mp4 = bvr.produce(name, c)
        print(f"=== POST {name} ===", flush=True)
        mid, link = meta.post_reel(meta.ensure_public_url(str(mp4)), c["caption"])
    except Exception as e:
        # Auftrag 3.1 + 1.2: Fehlschlag zaehlen, ehrlich hinterlegen, sauber abbrechen.
        eintrag = res.fehler_vermerken(name, repr(e)[:300])
        res.status_schreiben(False, name=name, grund=f"{type(e).__name__}: {str(e)[:200]}")
        print(f"=== FEHLGESCHLAGEN {name} ({eintrag['fehler']}. Mal): {repr(e)[:300]} ===", flush=True)
        raise

    # Auftrag 1.1: nicht dem eigenen Exit-Code glauben, sondern Instagram fragen.
    online, nachweis = res.wirklich_online(mid)
    if not online:
        res.status_schreiben(False, name=name, grund=f"Kein Nachweis bei Instagram: {nachweis}")
        raise RuntimeError(f"Post gemeldet, aber bei Instagram nicht auffindbar: {nachweis}")
    print(f"=== LIVE UND BESTAETIGT {name}: {mid} {link} ===", flush=True)
    res.erfolg_vermerken(name)
    res.status_schreiben(True, name=name, permalink=link)
    zeitplan.eintragen(mid, link, c.get("theme"))
    # Pipeline + Ledger (das GEWAEHLTE Konzept entfernen, nicht zwingend approved[0])
    data["approved"] = [x for x in approved if x.get("name") != name]
    data.setdefault("built", []).append({"name": name, "theme": c.get("theme"), "permalink": link})
    pf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ur = HERE / "used_reels.json"
    u = json.loads(ur.read_text())
    u.setdefault("used_topics", []).append(c.get("theme"))
    u.setdefault("used_hooks", []).append(c["thoughts"][0])
    ur.write_text(json.dumps(u, ensure_ascii=False, indent=2))
    print(f"OK, {len(data['approved'])} Konzepte verbleiben.", flush=True)
    # Stories laufen jetzt AUSSCHLIESSLICH ueber den eigenen Story-Cron (run_story.py /
    # story.yml) = deterministisch genau 2/Tag. Kein zusaetzliches Story-Posten beim Reel,
    # damit es an Reel-Tagen nicht auf 3-4 hochlaeuft (Dario-Vorgabe 2026-07-19).
    # post_stories(c)  # bewusst deaktiviert
    return c


def post_stories(c):
    """2 Stories: Teaser auf den neuen Reel + ein eigenstaendiger Gedanke.
    Laeuft nach dem Reel; ein Story-Fehler darf den bereits live gegangenen Reel
    nicht nachtraeglich kippen, darum alles in einem try."""
    # Deaktiviert: Stories kommen ausschliesslich vom Story-Cron (genau 2/Tag).
    print("post_stories deaktiviert (Story-Cron uebernimmt, 2/Tag).", flush=True)
    return
    try:
        import build_story as st
        thoughts = c.get("thoughts", [])
        if not thoughts:
            print("Keine Gedanken im Konzept, keine Stories.", flush=True)
            return
        sdir = HERE / "assets" / "stories"
        sdir.mkdir(parents=True, exist_ok=True)
        p1 = st.story_teaser(thoughts[0], sdir / "daily_teaser.png",
                             label="Neu im Feed", foot="Ganzer Gedanke im Feed")
        meta.post_story(meta.ensure_public_url(str(p1)), is_video=False)
        print("STORY teaser gepostet", flush=True)
        p2 = st.story_gedanke(thoughts[-1], sdir / "daily_gedanke.png",
                              foot="Antworte mit einem Wort.")
        meta.post_story(meta.ensure_public_url(str(p2)), is_video=False)
        print("STORY gedanke gepostet", flush=True)
    except Exception as e:
        print("STORY-FEHLER (Reel bleibt live):", repr(e)[:300], flush=True)


if __name__ == "__main__":
    import os
    main(ignoriere_slot=os.environ.get("FORCE_BUILD") == "1")
