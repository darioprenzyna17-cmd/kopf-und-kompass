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
import kk_budget as budget      # noqa: E402
import kk_lernen as lernen       # noqa: E402
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
    gebraucht = {t for t in (json.loads((HERE / "used_reels.json").read_text())
                             .get("used_topics", []) or [])}

    # Testverteilung 70/20/10 aus dem Content-Agent-Auftrag, deterministisch ueber den
    # Tag gestreut. Ohne die 10 Prozent Wagnis findet der Account nie ein neues Muster,
    # ohne die 70 Prozent Basis faellt die Leistung ab.
    klasse = lernen.testklasse()
    if klasse == "wagnis":
        fremd = [c for c in neuland if c.get("theme") not in gebraucht] or neuland
        if fremd:
            c = fremd[0]
            print(f"WAGNIS (10 Prozent): Thema '{c.get('theme')}', noch nie gepostet.")
            return c
    if klasse == "variation" and neuland:
        c = neuland[0]
        print(f"VARIATION (20 Prozent): Thema '{c.get('theme')}' ausserhalb der Gewinner.")
        return c
    if bewaehrt:
        c = bewaehrt[0]
        print(f"BASIS (70 Prozent): Gewinner-Thema '{c.get('theme')}'")
        return c
    print(f"Kein Gewinner-Thema verfuegbar, nehme '{frei[0].get('theme')}'.")
    return frei[0]


def main(ignoriere_slot: bool = False):
    """Zwei getrennte Aufgaben in fester Reihenfolge:
       POSTEN  aus dem Vorrat, kostet nichts, hat Vorrang.
       BAUEN   hoechstens ein Video pro Tag, nur wenn der Vorrat Platz hat.
    Frueher war beides verschraenkt. Darum hat jeder Postversuch eine komplette
    Produktion ausgeloest, und acht Fehlversuche am 01.08.2026 haben acht Produktionen
    bezahlt, ohne dass ein Video online ging."""
    try:
        import learn_and_adapt
        learn_and_adapt.main()
    except Exception as e:
        print("Lern-Schritt uebersprungen:", e)
    pf = HERE / "reel_pipeline.json"
    data = json.loads(pf.read_text())
    print(budget.bericht(), flush=True)

    # --- POSTEN ---
    schon = zeitplan.schon_gepostet()
    slot_da = ignoriere_slot or zeitplan.ist_mein_slot()
    gepostet = None
    if schon:
        print("Heute wurde bereits gepostet, kein zweiter Post.", flush=True)
    elif not slot_da:
        print("Slot noch nicht erreicht, kein Post.", flush=True)
    else:
        fertig = budget.vorrat_entnehmen()
        if fertig is None:
            print("Vorrat leer, es wird einmalig fuer heute gebaut.", flush=True)
            fertig = _bauen(data, data.get("approved", []))
            data = json.loads(pf.read_text())
        if fertig is not None:
            gepostet = _posten(fertig, data)

    # --- BAUEN (Puffer), unabhaengig davon ob heute gepostet wurde ---
    data = json.loads(pf.read_text())
    darf, grund = budget.darf_bauen()
    if darf:
        print(f"Vorrat auffuellen: {grund}", flush=True)
        _bauen(data, data.get("approved", []))
    else:
        print(f"Kein Bau: {grund}", flush=True)
    print(budget.bericht(), flush=True)
    return gepostet


def _laenge(mp4):
    try:
        import subprocess
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(mp4)], capture_output=True, text=True,
                             timeout=60).stdout.strip()
        return round(float(out), 1)
    except Exception:
        return None


def _hypothese(klasse, c):
    """Erwartung, die sich nach 48 Stunden widerlegen laesst. Kein Wunschsatz.
    Die Testverteilung 70/20/10 steckt in lernen.testklasse()."""
    thema = c.get("theme", "?")
    if klasse == "basis":
        return ("Das bewaehrte Kurzformat (rund 10s, Spannung zuerst, Frage am Schluss) haelt "
                "den Watchtime-Anteil ueber dem Kontodurchschnitt.", "bewaehrtes Kurzformat")
    if klasse == "variation":
        return (f"Thema '{thema}' ausserhalb der bisherigen Gewinner erreicht einen "
                "gleich hohen oder hoeheren Anteil an Nicht-Follower-Views.",
                f"Thema {thema} statt Gewinner-Thema")
    return (f"Ein Wagnis ausserhalb des Musters ('{thema}') findet ein neues Publikum und "
            "hebt Sends pro Reichweite ueber den Schnitt.", f"Wagnis {thema}")


def _bauen(data, approved):
    """Erzeugt HOECHSTENS ein Video und legt es in den Vorrat. Gibt den Vorratseintrag
    zurueck oder None. Kostet Geld, darum sitzen hier alle Bremsen."""
    darf, grund = budget.darf_bauen()
    if not darf:
        print(f"BAU GESPERRT: {grund}", flush=True)
        res.status_schreiben(False, grund=f"Bau gesperrt: {grund}")
        return None
    ok, ggrund = res.budget_ok()
    if not ok:
        print("STOPP:", ggrund, flush=True)
        res.status_schreiben(False, grund=ggrund)
        return None
    c = pick(approved)
    if c is None:
        res.status_schreiben(False, grund="Alle Konzepte in Quarantaene.")
        return None
    name = c["name"]
    budget.buchen("bau")          # der Tag ist damit verbraucht, auch wenn es scheitert
    try:
        print(f"=== BUILD {name} ===", flush=True)
        mp4 = bvr.produce(name, c)
        url = meta.ensure_public_url(str(mp4))   # dauerhafte URL, Video muss nie neu gebaut werden
    except Exception as e:
        eintrag = res.fehler_vermerken(name, repr(e)[:300])
        res.status_schreiben(False, name=name, grund=f"{type(e).__name__}: {str(e)[:200]}")
        print(f"=== BAU FEHLGESCHLAGEN {name} ({eintrag['fehler']}. Mal): {repr(e)[:300]} ===", flush=True)
        print("Heute wird nichts mehr erzeugt. Der Vorrat traegt den Account.", flush=True)
        return None
    res.erfolg_vermerken(name)
    # Jedes Posting ist ein Experiment mit einer Erwartung (Auftrag Abschnitt 5 und 7:
    # kein Posting ohne Hypothese). Klasse und Hypothese werden beim BAU festgelegt und
    # wandern mit dem Video durch den Vorrat bis zum Posten.
    klasse = lernen.testklasse()
    hyp, variable = _hypothese(klasse, c)
    budget.vorrat_zufuegen(
        name, url, c["caption"], c.get("theme"),
        laenge_sek=_laenge(mp4), testklasse=klasse, hypothese=hyp, variable=variable,
        hook_typ="Spannung zuerst, Aufloesung zum Schluss" if bvr.KURZ else "Aussage zuerst")
    # Konzept ist verbraucht, sobald es gebaut ist, nicht erst beim Posten.
    data["approved"] = [x for x in approved if x.get("name") != name]
    (HERE / "reel_pipeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return budget.vorrat()[-1]


def _posten(eintrag, data):
    """Postet einen fertigen Vorratseintrag. Kostet nichts und kann nicht am Bau scheitern."""
    name = eintrag["name"]
    print(f"=== POST {name} (aus Vorrat, gebaut {eintrag.get('gebaut')}) ===", flush=True)
    try:
        mid, link = meta.post_reel(eintrag["url"], eintrag["caption"])
    except Exception as e:
        # Nicht verloren geben: zurueck in den Vorrat, damit der naechste Lauf es erneut
        # versucht, ohne dass ein einziger Franken neu ausgegeben wird.
        budget.vorrat_zufuegen(name, eintrag["url"], eintrag["caption"], eintrag.get("theme"))
        res.status_schreiben(False, name=name, grund=f"Posten fehlgeschlagen: {str(e)[:200]}")
        print(f"POSTEN FEHLGESCHLAGEN, Video bleibt im Vorrat: {repr(e)[:200]}", flush=True)
        raise
    online, nachweis = res.wirklich_online(mid)
    if not online:
        res.status_schreiben(False, name=name, grund=f"Kein Nachweis bei Instagram: {nachweis}")
        raise RuntimeError(f"Post gemeldet, aber bei Instagram nicht auffindbar: {nachweis}")
    print(f"=== LIVE UND BESTAETIGT {name}: {mid} {link} ===", flush=True)
    try:
        budget.buchen("post")     # nur Buchhaltung, darf einen erfolgten Post nie kippen
    except budget.BudgetErschoepft as e:
        print("Hinweis:", e, flush=True)
    res.status_schreiben(True, name=name, permalink=link)
    try:
        lernen.protokollieren({
            "name": name, "media_id": mid, "permalink": link,
            "thema": eintrag.get("theme"), "format": "Reel",
            "laenge_sek": eintrag.get("laenge_sek"),
            "hook_typ": eintrag.get("hook_typ"),
            "testklasse": eintrag.get("testklasse"),
            "variable": eintrag.get("variable"),
            "hypothese": eintrag.get("hypothese") or "Kein Vermerk beim Bau, nachtraeglich offen.",
            "postingzeit": zeitplan.jetzt_zh().strftime("%a %H:%M"),
        })
    except Exception as e:
        print("Lern-Protokoll fehlgeschlagen (Post bleibt live):", repr(e)[:200], flush=True)
    zeitplan.eintragen(mid, link, eintrag.get("theme"))
    data.setdefault("built", []).append(
        {"name": name, "theme": eintrag.get("theme"), "permalink": link})
    (HERE / "reel_pipeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ur = HERE / "used_reels.json"
    u = json.loads(ur.read_text())
    u.setdefault("used_topics", []).append(eintrag.get("theme"))
    ur.write_text(json.dumps(u, ensure_ascii=False, indent=2))
    # Stories laufen ausschliesslich ueber den eigenen Story-Cron (run_story.py /
    # story.yml), deterministisch genau 2/Tag (Dario-Vorgabe 2026-07-19).
    return eintrag


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
