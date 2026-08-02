"""Torwaechter fuer Reel-Konzepte (@kopfundkompass).

Die harten Verbote aus CONTENT_AGENT.md stehen sonst nur in einem Textdokument, das
niemand liest, wenn es schnell gehen muss. Hier werden sie geprueft, bevor gebaut wird.
Ein Konzept, das durchfaellt, kostet null, ein gebautes Video kostet rund 70 Credits.

Aufruf: python3 kk_konzept.py            prueft die ganze Pipeline
        python3 kk_konzept.py --streng   Konzepte ohne Viral-Felder zaehlen als Fehler
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PIPELINE = HERE / "reel_pipeline.json"
USED = HERE / "used_reels.json"

AUSLOESER = {"Erkennen", "Widerspruch", "Statuswert", "Nutzwert",
             "Spannungsluecke", "Spannungslücke", "Emotion mit Adressat"}

# Geschlossene Fragen taugen nicht als Handlungsaufruf: sie laden zum Nicken ein,
# nicht zum Antworten. Genau daran sind 14 Reels mit null Kommentaren gescheitert.
GESCHLOSSEN = re.compile(r"^\s*(was meint ihr|wie seht ihr das|stimmt ihr zu|kennst du das|"
                         r"seht ihr das auch so|geht es euch auch so)\b", re.I)
OFFEN_START = re.compile(r"^\s*(wo|wer|was|wann|wie|welche[rsn]?|wofür|wofuer|wovor|wessen|woran|worauf)\b", re.I)

PHRASEN = ["du bist einzigartig", "du schaffst das", "glaub an dich",
           "alles wird gut", "sei du selbst", "das leben ist schön"]


def _felder(c):
    fehlt = [f for f in ("name", "theme", "thoughts", "cta", "clips", "music", "caption")
             if not c.get(f)]
    return fehlt


def _normal(s):
    return re.sub(r"[^a-zäöüß ]", "", (s or "").replace("|", " ").lower()).strip()


def pruefe(c, used_topics=(), used_hooks=(), streng=False):
    """Gibt (fehler, warnungen) zurueck. Fehler blockieren den Bau, Warnungen nicht.

    Die Trennung ist wichtig: Ein Torwaechter, der bei 26 von 26 Konzepten anschlaegt,
    wird ignoriert und schuetzt dann gar nichts mehr."""
    m, w = [], []
    fehlt = _felder(c)
    if fehlt:
        m.append(f"Pflichtfelder fehlen: {', '.join(fehlt)}")
        return m, w

    # Geprueft wird, was WIRKLICH ins Video kommt. Im Kurzformat sind das zwei von vier
    # Beats. Alles andere zu beanstanden erzeugt Laerm ueber Text, den niemand sieht.
    try:
        import build_video_reel as bvr
        c = bvr.kurzfassung(c) if bvr.KURZ else c
    except Exception:
        pass

    th = c["thoughts"]
    if len(th) < 2:
        m.append(f"Nur {len(th)} Beat(s), es braucht mindestens zwei.")

    # Sprache: die Regeln gelten fuer alles, was auf dem Bildschirm oder in der Caption steht.
    text = " ".join(list(th) + [c.get("cta", ""), c.get("caption", ""), c.get("kicker", "")])
    if "—" in text or "–" in text:
        m.append("Langer Gedankenstrich im Text (verboten).")
    if re.search(r",\s+und\b", text):
        m.append("Komma vor 'und' im Text (verboten).")
    for p in PHRASEN:
        if p in text.lower():
            m.append(f"Leerformel im Text: '{p}'.")

    # Zeilen muessen lesbar bleiben. render_card faellt ab 30 Zeichen auf die kleinste
    # Schrift. Bei einer Zielgruppe von 45 bis 64 auf dem Handy ist das die Grenze,
    # ab 42 Zeichen wird es unzumutbar.
    for t in th:
        for zeile in t.split("|"):
            n = len(zeile.strip())
            if n > 42:
                m.append(f"Zeile zu lang ({n} Zeichen): '{zeile.strip()[:40]}...'")
            elif n > 34:
                w.append(f"Zeile grenzwertig ({n} Zeichen, kleinste Schrift): '{zeile.strip()[:40]}...'")

    # Handlungsaufruf
    cta = c.get("cta", "").strip()
    if GESCHLOSSEN.match(cta):
        m.append(f"Geschlossene Frage als Handlungsaufruf: '{cta}'.")
    elif cta.endswith("?") and not OFFEN_START.match(cta):
        m.append(f"Frage ohne Fragewort, wirkt geschlossen: '{cta}'.")

    # Bildmaterial
    for k in c.get("clips", []):
        low = k.lower()
        if "no on-screen text" not in low and "no text" not in low:
            m.append("Clip-Prompt verbietet Text im Bild nicht.")
        if "9:16" not in low:
            m.append("Clip-Prompt nennt das Format 9:16 nicht.")

    # Wiederholung. Ein Thema doppelt ist bei 19 Inhaltssaeulen normal und kein Fehler,
    # der GEDANKE doppelt ist einer. Geprueft wird darum gegen die bereits benutzten
    # Hooks, nicht gegen die Themenliste.
    hooks_norm = {_normal(h) for h in used_hooks}
    for t in th:
        if _normal(t) and _normal(t) in hooks_norm:
            m.append(f"Gedanke lief schon wortgleich: '{t[:50]}'")
    if c.get("theme") in used_topics and not c.get("neuer_winkel"):
        w.append(f"Thema '{c.get('theme')}' lief schon, Winkel muss neu sein.")

    # Viral-Felder. Nur im strengen Modus ein Fehler, damit die 26 Altkonzepte nicht
    # pauschal gesperrt werden. Neue Konzepte muessen sie tragen.
    ziel = m if streng else w
    if c.get("ausloeser") not in AUSLOESER:
        ziel.append(f"Kein gueltiger Viral-Ausloeser (hat: {c.get('ausloeser')!r}).")
    if not c.get("wer_schickt_wem"):
        ziel.append("Feld 'wer_schickt_wem' fehlt.")
    if not c.get("hypothese"):
        ziel.append("Feld 'hypothese' fehlt.")
    return m, w


def pruefe_pipeline(streng=False, leise=False):
    data = json.loads(PIPELINE.read_text())
    u = json.loads(USED.read_text()) if USED.exists() else {}
    topics = set(u.get("used_topics", []) or [])
    hooks = list(u.get("used_hooks", []) or [])
    schlecht, gewarnt = 0, 0
    for c in data.get("approved", []):
        m, w = pruefe(c, topics, hooks, streng=streng)
        if m:
            schlecht += 1
            print(f"FAIL {c.get('name')}")
            for x in m:
                print(f"     - {x}")
        elif w and not leise:
            gewarnt += 1
            print(f"warn {c.get('name')}: {w[0]}")
    n = len(data.get("approved", []))
    print(f"\n{n - schlecht} von {n} Konzepten bestanden, {gewarnt} mit Hinweis"
          f"{' (streng)' if streng else ''}.")
    return schlecht


if __name__ == "__main__":
    raise SystemExit(1 if pruefe_pipeline("--streng" in sys.argv) else 0)
