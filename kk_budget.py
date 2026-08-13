"""Harte Ausgabenbremse und Vorrats-Logik fuer @kopfundkompass.

Dario-Vorgabe 2026-08-02, verschaerft am 05.08.2026: Es wird HOECHSTENS EIN Video pro Tag
produziert, und es liegt hoechstens EIN fertiges Video auf Halde. Niemals mehr. Just in
time statt Vorrat: so ist nie viel vorausbezahlt, und eine Aenderung an Bau oder Look
greift sofort beim naechsten Reel. Am 01.08.2026 hat eine
Fehlerschleife acht Baulaeufe gestartet und dabei zwei bis drei bezahlte Veo-Clips
pro Lauf verbrannt, ohne dass ein einziges Video online ging.

Der entscheidende Punkt: Gezaehlt wird VOR jedem bezahlten Aufruf, nicht danach und
nicht auf der Ebene "Bauversuch". Ein Bauversuch, der zur Haelfte durchlaeuft, kostet
trotzdem Geld. Nur ein Zaehler direkt am Aufruf kann das begrenzen.

Ablauf neu:
  bauen  -> Video wird erzeugt und im Repo abgelegt, der PFAD landet im Vorrat
  posten -> nimmt den aeltesten Eintrag, laedt ihn erst jetzt hoch, kostet nichts
Damit haengt das taegliche Posten nicht mehr davon ab, ob heute eine Produktion klappt.
"""
import json
import os
import tempfile
import threading
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
# Ein Schloss fuer alle Zaehler. Video und Musik werden parallel erzeugt, ohne das
# gingen Buchungen verloren.
_SCHLOSS = threading.RLock()

BUDGET = HERE / "budget.json"
VORRAT = HERE / "vorrat.json"

# --- Die Grenzen. Aenderungen hier sind Geldentscheidungen, nicht Technik. ---
MAX_VEO_PRO_TAG = 4        # Langformat braucht 3 Clips, einer bleibt als Reserve fuer EINEN Ersatzversuch
# Stand 13.08.2026 von 2 auf 4 erhoben. Die 2 stammten vom Kurzformat (1 Clip pro Reel).
# Am 09.08.2026 wurde das Kurzformat zurueckgenommen, seither braucht ein Reel 3 Clips,
# die Grenze blieb aber bei 2. Folge: der Bau bezahlte jede Nacht Clip 1 und 2 samt Musik
# und brach bei Clip 3 an der eigenen Bremse ab. Vier Tage lang kein Reel online und rund
# 550 Credits fuer nichts. Wer das Kurzformat wieder einschaltet (KK_KURZFORMAT=1),
# setzt hier auf 2 zurueck.
MAX_MUSIK_PRO_TAG = 2      # ein Musikstueck pro Reel, eines in Reserve
MAX_BAUTEN_PRO_TAG = 1     # hoechstens EIN Video pro Tag, Dario-Vorgabe
MAX_VORRAT = 1             # genau EIN fertiges Video auf Halde, Dario-Vorgabe 05.08.2026
# Vorher 3. Dario hat auf 1 heruntergesetzt: just in time produzieren, nichts liegt lange
# herum. Weniger vorausbezahlte Videos, und eine Aenderung an Bau oder Look greift sofort
# beim naechsten Reel statt erst, wenn der alte Vorrat abgearbeitet ist.

GRENZEN = {"veo": MAX_VEO_PRO_TAG, "musik": MAX_MUSIK_PRO_TAG,
           "bau": MAX_BAUTEN_PRO_TAG, "post": 1}


class BudgetErschoepft(RuntimeError):
    """Harte Bremse. Wird bewusst NICHT abgefangen und ersetzt, sondern beendet den Lauf."""


def _atomar_schreiben(pfad, daten):
    """Erst in eine Nachbardatei schreiben, dann umbenennen. Ein abgebrochener Lauf
    hinterlaesst so nie eine halbe Zaehlerdatei."""
    fd, tmp = tempfile.mkstemp(dir=str(pfad.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)
        os.replace(tmp, pfad)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _laden(pfad, leer):
    if pfad.exists():
        try:
            return json.loads(pfad.read_text())
        except Exception:
            pass
    return leer


def _budget():
    return _laden(BUDGET, {"_hinweis": "Taegliche Zaehler bezahlter Aufrufe. "
                                       "Grenzen stehen in kk_budget.py.", "tage": {}})


def _heute_key():
    return date.today().isoformat()


def stand(tag=None):
    d = _budget()["tage"].get(tag or _heute_key(), {})
    return {k: d.get(k, 0) for k in GRENZEN}


def buchen(art, menge=1):
    """Bucht einen bezahlten Aufruf. Wirft BudgetErschoepft, BEVOR Geld fliesst.

    Lesen, Aendern und Schreiben laufen unter einem Schloss und atomar. Ohne das gehen
    Buchungen verloren: build_video_reel erzeugt Video und Musik in einem
    ThreadPoolExecutor, beide Threads lasen dieselbe Datei und der letzte Schreiber
    ueberschrieb den anderen. Am 02.08.2026 sind dabei der Veo-Zaehler und eine
    Bau-Buchung verschwunden, und es liefen zwei bezahlte Bauten an einem Tag statt
    einem. Genau das soll die Bremse verhindern.
    """
    if art not in GRENZEN:
        raise ValueError(f"Unbekannte Budget-Art: {art}")
    with _SCHLOSS:
        d = _budget()                      # innerhalb des Schlosses frisch lesen
        tag = _heute_key()
        t = d["tage"].setdefault(tag, {})
        ist = t.get(art, 0)
        if ist + menge > GRENZEN[art]:
            raise BudgetErschoepft(
                f"Tagesgrenze '{art}' erreicht: {ist}/{GRENZEN[art]}. "
                f"Heute wird nichts mehr erzeugt.")
        t[art] = ist + menge
        # Nur die letzten 30 Tage behalten, die Datei soll nicht wachsen.
        d["tage"] = dict(sorted(d["tage"].items())[-30:])
        _atomar_schreiben(BUDGET, d)
        neu = t[art]
    print(f"  [Budget] {art}: {neu}/{GRENZEN[art]} heute", flush=True)
    return neu


def rest(art):
    return GRENZEN[art] - stand().get(art, 0)


# ------------------------------------------------------------------- Vorrat

def vorrat():
    return _laden(VORRAT, {"_hinweis": "Fertige, noch nicht gepostete Videos. "
                                       f"Hoechstens {MAX_VORRAT} (Dario-Vorgabe).", "videos": []})["videos"]


def _vorrat_sichern(videos):
    _atomar_schreiben(VORRAT, {"_hinweis": "Fertige, noch nicht gepostete Videos. "
                                           f"Hoechstens {MAX_VORRAT} (Dario-Vorgabe).", "videos": videos})


def vorrat_zufuegen(name, url, caption, theme, **extra):
    with _SCHLOSS:
        v = vorrat()
        v.append({"name": name, "url": url, "caption": caption, "theme": theme,
                  "gebaut": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **extra})
        _vorrat_sichern(v)
        print(f"  [Vorrat] '{name}' abgelegt, Vorrat jetzt {len(v)}/{MAX_VORRAT}.", flush=True)
        return v


def vorrat_entnehmen():
    """Aeltester Eintrag zuerst, damit nichts liegen bleibt."""
    with _SCHLOSS:
        v = vorrat()
        if not v:
            return None
        e = v.pop(0)
        _vorrat_sichern(v)
        return e


def darf_bauen():
    """Auftrag 4 plus Dario-Vorgabe: 1 Bau pro Tag, hoechstens MAX_VORRAT auf Halde."""
    s = stand()
    if s["bau"] >= MAX_BAUTEN_PRO_TAG:
        return False, f"Heute wurde bereits {s['bau']}x gebaut (Grenze {MAX_BAUTEN_PRO_TAG})."
    n = len(vorrat())
    if n >= MAX_VORRAT:
        return False, f"Vorrat voll: {n}/{MAX_VORRAT} fertige Videos liegen bereit."
    return True, f"Vorrat {n}/{MAX_VORRAT}, heute noch kein Bau."


def bericht():
    s = stand()
    return (f"Budget heute: Veo {s['veo']}/{MAX_VEO_PRO_TAG}, Musik {s['musik']}/{MAX_MUSIK_PRO_TAG}, "
            f"Bauten {s['bau']}/{MAX_BAUTEN_PRO_TAG}, Posts {s['post']}/1. "
            f"Vorrat: {len(vorrat())}/{MAX_VORRAT}.")


if __name__ == "__main__":
    print(bericht())
    print("darf_bauen:", darf_bauen())
