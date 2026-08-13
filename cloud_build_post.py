"""Autonomer Cloud-Lauf: baut das naechste approved-Konzept im Archivkino-Look und
postet es direkt nach @kopfundkompass. Aktualisiert reel_pipeline.json + used_reels.json.
Zugang aus Umgebung (GitHub-Secrets IG_USER_ID, IG_ACCESS_TOKEN, KIE_API_KEY).
Aufruf in reel.yml. Committen/Pushen der Ledger macht der Workflow."""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_video_reel as bvr   # noqa: E402
import kk_budget as budget      # noqa: E402
import kk_konzept as konzept     # noqa: E402
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

    # Solange das neue Lernsystem noch keine belegte Regel hat, haben Konzepte Vorrang,
    # die nach dem aktuellen Standard gebaut sind (mit Ausloeser, Adressat, Hypothese).
    # Die 'gewinner_themen' in learnings.json stammen aus dem alten 21-Sekunden-Format
    # und aus Kennzahlen, die nicht mehr der Nordstern sind. Sie duerfen die Auswahl
    # nicht laenger steuern, sonst baut der Account im neuen Format alten Text.
    regeln = HERE / "regeln.md"
    ohne_belege = not (regeln.exists() and regeln.read_text().count("- ") > 0)
    if ohne_belege:
        nach_standard = [c for c in frei if c.get("ausloeser") and c.get("hypothese")]
        if nach_standard:
            c = nach_standard[0]
            print(f"STANDARD-VORRANG: '{c['name']}' ({c.get('theme')}), gebaut nach dem "
                  f"aktuellen Auftrag. Alte Gewinner-Themen zaehlen erst wieder, wenn "
                  f"regeln.md eigene Belege hat.")
            return c

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
    # ignoriere_slot (FORCE_BUILD=1) heisst: von Hand angestossen, Slot UND Tagessperre
    # werden uebergangen. Ohne das laeuft ein Force-Lauf ins Leere, sobald an dem Tag
    # schon gepostet wurde, und genau dann braucht man ihn.
    schon = zeitplan.schon_gepostet() and not ignoriere_slot
    slot_da = ignoriere_slot or zeitplan.ist_mein_slot()
    gepostet = None
    # Den Status dieses Laufs sofort setzen, sonst bleibt die Meldung des letzten
    # geglueckten Posts stehen und der Lauf schmueckt sich mit fremden Federn.
    res.status_schreiben(True, grund="Lauf gestartet, noch nichts gepostet")
    if schon:
        print("Heute wurde bereits gepostet, kein zweiter Post.", flush=True)
        res.status_schreiben(True, grund="Heute wurde bereits gepostet.")
    elif not slot_da:
        print("Slot noch nicht erreicht, kein Post.", flush=True)
        res.status_schreiben(True, grund="Slot noch nicht erreicht, kein Post faellig.")
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


VORRATSORDNER = HERE / "assets" / "vorrat"


def _in_vorratsordner(name, mp4):
    """Legt das fertige Video dorthin, wo der naechste Lauf es wiederfindet.

    assets/video_reels/ ist in .gitignore, dort landen die Rohclips und Zwischenstufen.
    Der Poster laeuft aber als EIGENER Lauf auf einem frischen Checkout: was nicht im
    Repo liegt, existiert fuer ihn nicht. Darum wandert nur das fertige Reel nach
    assets/vorrat/ und wird mitgesichert. Genau dieses Muster laesst den DC-Autopiloten
    seit Wochen stabil posten.
    """
    VORRATSORDNER.mkdir(parents=True, exist_ok=True)
    ziel = VORRATSORDNER / f"{name}.mp4"
    shutil.copyfile(mp4, ziel)
    return str(ziel.relative_to(HERE))


def _aufraeumen(pfad):
    """Nach bestaetigtem Post wird die Datei geloescht. Das Repo soll nicht zuwachsen."""
    try:
        p = HERE / pfad
        if p.is_file() and VORRATSORDNER in p.parents:
            p.unlink()
            print(f"Vorratsdatei entfernt: {pfad}", flush=True)
    except Exception as e:
        print("Aufraeumen uebersprungen:", e, flush=True)


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
        # Der Satz muss beschreiben, was WIRKLICH gebaut wurde, sonst lernt die Auswertung
        # gegen ein Format, das gar nicht online ging. Bis 13.08.2026 stand hier fest
        # "Kurzformat, rund 10s", obwohl seit dem 09.08. wieder das Langformat laeuft.
        if bvr.KURZ:
            return ("Das Kurzformat (rund 10s, Spannung zuerst, Frage am Schluss) haelt "
                    "den Watchtime-Anteil ueber dem Kontodurchschnitt.", "Kurzformat")
        return ("Das bewaehrte Langformat (rund 20s, drei Clips, Aussage zuerst) haelt "
                "den Watchtime-Anteil ueber dem Kontodurchschnitt.", "bewaehrtes Langformat")
    if klasse == "variation":
        return (f"Thema '{thema}' ausserhalb der bisherigen Gewinner erreicht einen "
                "gleich hohen oder hoeheren Anteil an Nicht-Follower-Views.",
                f"Thema {thema} statt Gewinner-Thema")
    return (f"Ein Wagnis ausserhalb des Musters ('{thema}') findet ein neues Publikum und "
            "hebt Sends pro Reichweite ueber den Schnitt.", f"Wagnis {thema}")


# Gemessene Preise auf kie.ai, Stand 13.08.2026: ein Bau mit 2 Veo-Clips und einem
# Musikstueck kostete 142 Credits (653 auf 511). Daraus rund 60 pro Clip und 25 fuer die
# Musik. Bewusst grosszuegig gerundet, lieber einmal zu frueh stoppen als ein halbes
# Video bezahlen.
CREDITS_CLIP = 65
CREDITS_MUSIK = 30


def _guthaben():
    """Kontostand bei kie.ai, oder None wenn die Abfrage nicht klappt. Ein Netzfehler
    darf den Bau nicht blockieren, ein leeres Konto schon."""
    try:
        import kk_credits
        return kk_credits.guthaben()
    except Exception as e:
        print("Guthaben nicht abfragbar, Pruefung uebersprungen:", repr(e)[:150], flush=True)
        return None


def _reicht_es_fuer_den_ganzen_reel(c):
    """Prueft VOR dem ersten bezahlten Aufruf, ob Tagesbudget UND Kontoguthaben fuer den
    kompletten Reel reichen. Gibt die Gruende zurueck, warum nicht, sonst eine leere Liste.

    Warum es das gibt: vom 10. bis 13.08.2026 startete der Bau jede Nacht, bezahlte Clip 1
    und 2 samt Musik und lief bei Clip 3 in die eigene Tagesgrenze. Rund 550 Credits fuer
    vier Naechte ohne ein einziges Video. Ein halb bezahlter Reel ist wertlos, also wird
    entweder alles gebaut oder gar nichts.
    """
    n_clips = 1 if bvr.KURZ else len(c.get("clips") or [])
    fehlt = []
    if budget.rest("veo") < n_clips:
        fehlt.append(f"Tagesbudget Veo reicht nicht ({budget.rest('veo')} frei, "
                     f"{n_clips} noetig)")
    if budget.rest("musik") < 1:
        fehlt.append("Tagesbudget Musik ist aufgebraucht")
    noetig = n_clips * CREDITS_CLIP + CREDITS_MUSIK
    haben = _guthaben()
    if haben is not None and haben < noetig:
        fehlt.append(f"kie.ai-Guthaben reicht nicht ({haben:.0f} Credits da, "
                     f"rund {noetig} noetig)")
        try:
            from kk_waechter import push
            push("Kopf & Kompass: Guthaben reicht nicht fuer ein Reel",
                 f"Nur noch {haben:.0f} Credits, ein Reel braucht rund {noetig}. "
                 f"Es wird nichts mehr gebaut, bis du auflaedst. Bereits gebaute Videos "
                 f"im Vorrat werden weiter gepostet.")
        except Exception:
            pass
    return fehlt


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
    # Torwaechter VOR dem Bau: ein durchgefallenes Konzept kostet null, ein gebautes
    # Video rund 70 Credits. Faellt eines durch, wird es gesperrt und das naechste geholt.
    u = json.loads((HERE / "used_reels.json").read_text())
    c = None
    for _ in range(5):
        kandidat = pick(approved)
        if kandidat is None:
            res.status_schreiben(False, grund="Alle Konzepte in Quarantaene.")
            return None
        fehler, warnungen = konzept.pruefe(kandidat, set(u.get("used_topics", []) or []),
                                           u.get("used_hooks", []) or [])
        if not fehler:
            for x in warnungen[:2]:
                print(f"  Hinweis zu '{kandidat['name']}': {x}", flush=True)
            c = kandidat
            break
        print(f"KONZEPT DURCHGEFALLEN '{kandidat['name']}':", flush=True)
        for x in fehler:
            print(f"     - {x}", flush=True)
        # kostet=False: hier ist kein Geld geflossen, das Tagesbudget bleibt unangetastet.
        res.fehler_vermerken(kandidat["name"], "Konzeptpruefung: " + "; ".join(fehler)[:200],
                             kostet=False, sofort_sperren=True)
        approved = [x for x in approved if x.get("name") != kandidat["name"]]
    if c is None:
        res.status_schreiben(False, grund="Kein Konzept hat die Pruefung bestanden.")
        return None
    name = c["name"]
    fehlt = _reicht_es_fuer_den_ganzen_reel(c)
    if fehlt:
        grund = ("Bau gar nicht erst begonnen, sonst waere Geld fuer ein halbes Video "
                 "geflossen: " + "; ".join(fehlt))
        print("STOPP:", grund, flush=True)
        res.status_schreiben(False, name=name, grund=grund[:300])
        return None
    budget.buchen("bau")          # der Tag ist damit verbraucht, auch wenn es scheitert
    try:
        print(f"=== BUILD {name} ===", flush=True)
        mp4 = bvr.produce(name, c)
        # Im Vorrat steht der Pfad im Repo, NICHT eine kie.ai-URL. Die kie.ai-Links
        # sterben nach rund drei Tagen. Vorher lag genau so ein toter Link im Vorrat,
        # Instagram konnte das Video nicht laden und meldete nur "container ERROR" -
        # deshalb ging seit dem 02.08.2026 kein Reel mehr online. Die oeffentliche URL
        # wird jetzt erst beim Posten frisch erzeugt, genau wie beim DC-Autopiloten.
        url = _in_vorratsordner(name, mp4)
    except budget.BudgetErschoepft as e:
        # Die Tagesbremse sagt nichts ueber das Konzept aus. Frueher zaehlte sie als
        # Fehlschlag, und nach zwei Naechten lag ein voellig intaktes Konzept in
        # Quarantaene (siehe was_frueher_schwer_war, 13.08.2026). Nicht vermerken.
        res.status_schreiben(False, name=name, grund=f"Tagesbudget: {str(e)[:200]}")
        print(f"=== BAU ABGEBROCHEN {name}, Tagesbremse: {str(e)[:200]} ===", flush=True)
        print("Das Konzept bleibt frei und wird beim naechsten Lauf erneut gezogen.", flush=True)
        return None
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
        # ensure_public_url laedt den Repo-Pfad JETZT frisch in den kie.ai-Speicher hoch.
        # Ein bereits fertiges http-Feld (Altbestand) wird unveraendert durchgereicht.
        mid, link = meta.post_reel(meta.ensure_public_url(eintrag["url"]), eintrag["caption"])
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
    _aufraeumen(eintrag["url"])
    try:
        budget.buchen("post")     # nur Buchhaltung, darf einen erfolgten Post nie kippen
    except budget.BudgetErschoepft as e:
        print("Hinweis:", e, flush=True)
    res.status_schreiben(True, name=name, permalink=link, gepostet=True)
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
