"""
Kopf & Kompass — Reel-Engine im Look "Archivkino".
Warmes Filmschwarz, EIN kuehler Petrol-Akzent (nur Haarlinien/Tick), Serifenschrift
Fraunces, weiche Cross-Dissolves (1,2s), ruhiger Text mit langer Standzeit (immer gut
leserlich), Filmgrade + Korn + Vignette, Schlusskarte ohne Kompass, saubere Musik (loudnorm).
Kein Hardcut, kein Shake, kein Blitz, kein Slow-Mo-Kitsch. Sog statt Reiz.

Baut EIN Reel:  python3 build_video_reel.py <name>   |   --pipeline
Spec: strategie/DESIGN.md (Archivkino), Zahlen in §0.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
FONTS = HERE / "fonts"
OUT = HERE / "assets" / "video_reels"
OUT.mkdir(parents=True, exist_ok=True)
CHROME = os.environ.get("CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
GEN = "https://api.kie.ai/api/v1/veo/generate"
REC = "https://api.kie.ai/api/v1/veo/record-info"

# --- Archivkino-Palette (DESIGN.md §1) ---
FILMBLACK = "#1A1712"; FB_RGB = "26,23,18"
SHADOW = "#241C15"
PAPER = "#F2E9D8"          # Kernaussagen
LIGHT = "#E4D5BC"
META = "#C9B79A"           # Kicker / Untertext
PETROL = "#3B6E6A"         # einziger Akzent, nur Haarlinie/Tick
PETROL_HI = "#5C9089"

# --- Timing (DESIGN.md §0) ---
DISSOLVE = 1.2             # Cross-Dissolve zwischen Clips
END_LEN = 3.5             # Schlusskarten-Standzeit
END_XF = 1.0             # Dissolve in die Schlusskarte
FADE_IN = 0.9; FADE_OUT = 0.7; HOOK_IN = 0.5
OVERLAP = 0.25            # Karten-Ueberlappung (weich)
HEADROOM = 1.5           # Montage-Puffer nach der Textphase (fuer sauberen End-Dissolve)
ST_MIN = 3.5; ST_MAX = 5.0


# --- Kurzformat (Dario-Freigabe 2026-08-02) ---------------------------------
# Gemessen ueber 14 Reels: Watchtime 3,8 bis 5,7 Sekunden bei rund 21 Sekunden Laenge,
# also etwa 23 Prozent Completion. Instagram verteilt danach nicht weiter. Das lange
# Format zeigt Gedanke drei und vier an Menschen, die laengst weg sind.
# Neu: ZWEI Beats, EIN Bild, rund 10 Sekunden. Spannung zuerst, Aufloesung zum Schluss,
# Frage auf der Schlusskarte. Nebeneffekt: ein Veo-Clip statt drei, also ein Drittel
# der Produktionskosten.
# Kurzformat ZURUECKGENOMMEN am 09.08.2026, weil die Zahlen dagegen sprechen.
#
# Eingefuehrt am 02.08. mit der Begruendung: Watchtime 3,8 bis 5,7s bei 21s Laenge,
# also 23 Prozent Completion, deshalb auf 10s kuerzen. Die Hypothese war plausibel,
# sie ist aber widerlegt.
#
#   langes Format (8 Reels, 25.07 bis 02.08):   Median 826 Views
#   Kurzformat ohne Trial Reels (5 Reels):      Median 341 Views
#
# Das sind 59 Prozent weniger. Der Trial-Reel-Effekt ist herausgerechnet: der eine
# Ausreisser mit 111 Views lief zusaetzlich als Trial Reel und ist separat betrachtet.
# Offenbar zaehlt fuer die Verteilung die absolute Sehdauer mehr als der Anteil: vier
# Sekunden von zehn bringen weniger Sehzeit als vier Sekunden von einundzwanzig.
#
# Wieder einschaltbar ueber KK_KURZFORMAT=1, aber nur mit besseren Zahlen als diesen.
KURZ = os.environ.get("KK_KURZFORMAT", "0") == "1"
KURZ_ST_MIN, KURZ_ST_MAX = 2.9, 3.8
KURZ_CLIP_MAX = 7.9        # Veo liefert 8 Sekunden, mehr geht mit einem Clip nicht

# --- Sparmodus (Dario-Vorgabe 13.08.2026: ein Reel soll unter 100 Credits kosten) ---
# Gemessen kostete ein Reel im Langformat 210 bis 240 Credits: drei bezahlte Veo-Clips
# zu je 57 bis 75 plus Musik zu 17 bis 22. Uploads sind gratis, daran lag es nicht.
# Unter 100 geht nur ueber die Struktur, nicht ueber Details:
#   1. EIN Kauf statt drei. Der eine gekaufte Clip enthaelt selbst drei Szenen mit
#      harten Schnitten (Zeitmarken im Prompt, siehe szenen_prompt). Spart rund 130.
#      Dario 14.08.2026: "ein video das 3 szenen hat", nicht drei Videos aneinander
#      und auch nicht ein Motiv in drei Bildausschnitten.
#   2. Musik aus assets/musik statt jedes Mal neu von Suno. Spart rund 20.
# Bleibt rund 60 bis 75 pro Reel.
# Preis dafuer: Veo liefert hoechstens 8 Sekunden pro Generierung (erlaubt sind 4, 6
# oder 8, eine Verlaengerung gibt es nicht). Die Textphase braucht rund 15, also laeuft
# das Material mit Faktor 2,1 langsamer, mit echten Zwischenbildern statt verdoppelter
# Bilder. Gemessenes Ergebnis: 18,8 Sekunden Reel, damit ueber der Warnschwelle von 18
# und weit ueber dem Kurzformat vom 02.08. (9,9s), das wegen zu kurzer Sehdauer
# zurueckgenommen wurde.
SPARMODUS = os.environ.get("KK_SPARMODUS", "1") == "1"
# 8s mal 2.0 sind 16s Material, damit kommt der Reel auf rund 18 Sekunden und bleibt
# ueber der internen Warnschwelle. Ohne Zwischenbilder waere Faktor 2 sichtbares
# Ruckeln, mit ihnen bleibt die Bewegung fluessig (siehe _dehnen).
DEHNUNG_MAX = float(os.environ.get("KK_DEHNUNG_MAX", "2.1"))
ZWISCHENBILDER = os.environ.get("KK_ZWISCHENBILDER", "1") == "1"
MUSIK_NEU = os.environ.get("KK_MUSIK_NEU", "0") == "1"   # 1 = doch ein neues Stueck kaufen
MUSIKLAGER = HERE / "assets" / "musik"

# Ein echter Gesprächsanlass auf der Schlusskarte. Ueber 14 Reels kamen null
# Kommentare, weil nie jemand gefragt wurde.
FRAGEN = {
    "Grenzen": "Wo fällt dir ein Nein bis heute schwer?",
    "Nein ohne Erklärung": "Wem sagst du zu oft Ja?",
    "Falsches Ja": "Wem sagst du zu oft Ja?",
    "Geduld": "Worauf wartest du gerade?",
    "Fortschritt": "Woran arbeitest du gerade leise?",
    "Unsichtbares Wachstum": "Woran arbeitest du gerade leise?",
    "Eigenes Tempo": "Wer gibt dir gerade dein Tempo vor?",
    "Zeitgrenzen": "Wofür hast du zuletzt keine Zeit gehabt?",
    "Selbstwert": "Wofür machst du dich zu klein?",
    "Sich klein machen": "Wofür machst du dich zu klein?",
    "Selbstrespekt": "Wofür machst du dich zu klein?",
    "Selbstmitgefühl": "Wie redest du mit dir, wenn niemand zuhört?",
    "Disziplin": "Was tust du auch ohne Lust?",
    "Charakter": "Wessen Wort hält bei dir immer?",
    "Loslassen": "Was trägst du länger mit als nötig?",
    "Erwartungen": "Wessen Erwartung trägst du gerade?",
    "Klarheit": "Welche Entscheidung schiebst du vor dir her?",
    "Präsenz": "Wann warst du zuletzt wirklich da?",
    "Achtsamkeit": "Woran bist du heute vorbeigegangen?",
    "Eigene Bedürfnisse": "Wann hast du zuletzt etwas nur für dich gemacht?",
    "Gesehen werden": "Wer fragt dich, wie es dir geht?",
    "Mut": "Wovor drückst du dich gerade?",
}
FRAGE_FALLBACK = "Was davon kennst du?"


def kurzfassung(r):
    """Macht aus einem Vier-Beat-Konzept ein Zwei-Beat-Reel.

    thoughts[0] ist die fertige Kernaussage. Genau die vorwegzunehmen war der Fehler:
    wer die Aufloesung in Sekunde eins liest, hat keinen Grund zu bleiben. Deshalb
    faengt es jetzt mit dem Aufbau an (thoughts[1]) und endet mit der Pointe
    (thoughts[-1]).
    """
    th = r.get("thoughts") or []
    if len(th) >= 4:
        beats = [th[1], th[3]]
    elif len(th) == 3:
        beats = [th[1], th[2]]
    elif len(th) == 2:
        beats = list(th)
    else:
        beats = list(th)
    k = dict(r)
    k["thoughts"] = beats
    k["clips"] = (r.get("clips") or [])[:1]
    k["endcard_term"] = r.get("kicker", "") or r.get("endcard_term", "")
    k["cta"] = FRAGEN.get(r.get("theme", ""), FRAGE_FALLBACK)
    return k


def standzeit(text, kurz=False):
    w = len(text.replace("|", " ").split())
    lo, hi = (KURZ_ST_MIN, KURZ_ST_MAX) if kurz else (ST_MIN, ST_MAX)
    return max(lo, min(hi, w * 0.42 + 1.6))


def kie_key():
    v = os.environ.get("KIE_API_KEY")
    if not v and (HERE / ".env").exists():
        for l in (HERE / ".env").read_text().splitlines():
            if l.startswith("KIE_API_KEY="):
                v = l.split("=", 1)[1].strip()
    return v


KEY = kie_key()
KH = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def _b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode("ascii")


def _fonts_css():
    return (f"@font-face{{font-family:'Fraunces';font-weight:400 700;font-style:normal;"
            f"src:url(data:font/ttf;base64,{_b64(FONTS/'Fraunces.ttf')}) format('truetype');}}"
            f"@font-face{{font-family:'Fraunces';font-weight:400 700;font-style:italic;"
            f"src:url(data:font/ttf;base64,{_b64(FONTS/'Fraunces-Italic.ttf')}) format('truetype');}}")


def _shoot(html, out_png, transparent):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html); hp = f.name
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
            "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920",
            f"--screenshot={out_png}", f"file://{hp}"]
    if transparent:
        args.insert(-1, "--default-background-color=00000000")
    subprocess.run(args, check=True, capture_output=True)


def _hero_size(text):
    longest = max((len(l) for l in text.split("|")), default=0)
    return 92 if longest <= 16 else 84 if longest <= 22 else 74 if longest <= 30 else 64


def render_card(kicker, text, out_png, hook=False):
    """Text im Band 40-65%, linksbuendig, Fraunces. Petrol-Haarlinie + optional Kicker."""
    hs = _hero_size(text)
    lines = "".join(f"<div>{l.strip()}</div>" for l in text.split("|"))
    kick = ""
    if kicker:
        kick = (f'<div class="kick"><span class="tick"></span>{kicker}</div>')
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Fraunces',serif;}}
.scrim{{position:absolute;inset:0;background:
  radial-gradient(120% 52% at 20% 58%,rgba({FB_RGB},.66),transparent 68%),
  linear-gradient(to top,rgba({FB_RGB},.82) 6%,rgba({FB_RGB},0) 42%);}}
.block{{position:absolute;left:108px;right:108px;bottom:712px;}}
.rule{{width:64px;height:2px;background:{PETROL};margin-bottom:30px;}}
.kick{{font-weight:600;font-size:30px;letter-spacing:.30em;text-transform:uppercase;
  color:{META};margin-bottom:26px;display:flex;align-items:center;}}
.tick{{display:inline-block;width:26px;height:2px;background:{PETROL};margin-right:16px;}}
.hero div{{font-weight:460;font-size:{hs}px;line-height:1.26;letter-spacing:.01em;color:{PAPER};
  text-shadow:0 2px 24px rgba(0,0,0,.55);text-wrap:balance;}}
</style></head><body>
<div class="scrim"></div>
<div class="block"><div class="rule"></div>{kick}<div class="hero">{lines}</div></div>
</body></html>"""
    _shoot(html, out_png, transparent=True)


def render_endcard(term, cta, out_png):
    term_html = (f'<div class="term"><span class="tick"></span>{term}</div>' if term else "")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Fraunces',serif;
  background:radial-gradient(90% 60% at 50% 46%,{SHADOW},{FILMBLACK} 72%);overflow:hidden;}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 120px;}}
.term{{font-weight:600;font-size:32px;letter-spacing:.30em;text-transform:uppercase;color:{META};
  margin-bottom:42px;}}
.term .tick{{display:inline-block;width:24px;height:2px;background:{PETROL};vertical-align:middle;margin-right:16px;margin-bottom:6px;}}
.mark{{font-weight:600;font-size:66px;letter-spacing:.14em;color:{PAPER};margin-bottom:40px;}}
.cta{{font-style:italic;font-weight:440;font-size:40px;line-height:1.35;color:{META};}}
.hair{{width:180px;height:2px;background:{PETROL};margin:52px auto 0;}}
.handle{{position:absolute;left:0;right:0;bottom:150px;text-align:center;font-weight:500;
  font-size:30px;letter-spacing:.10em;color:#8A7C66;}}
</style></head><body>
<div class="mid">
  {term_html}
  <div class="mark">Kopf &amp; Kompass</div>
  <div class="cta">{cta}</div>
  <div class="hair"></div>
</div>
<div class="handle">@kopfundkompass</div>
</body></html>"""
    _shoot(html, out_png, transparent=False)


class VeoAusfall(RuntimeError):
    """Ein Clip liess sich nicht erzeugen. Kein Grund, den ganzen Reel zu kippen."""


def _veo_einmal(prompt, out_mp4, model, res, duration, poll_sek):
    """Ein Anlauf. poll_sek MUSS groesser sein als das Zeitlimit des Anbieters,
    sonst meldet man den eigenen Abbruch statt seines Fehlers (Auftrag 2.3).
    kie.ai meldet 'video generation timed out' erst nach rund 640 Sekunden."""
    body = json.dumps({"prompt": prompt, "model": model, "aspect_ratio": "9:16",
                       "resolution": res, "duration": duration}).encode()
    tid = None
    for attempt in range(5):
        try:
            resp = json.loads(urllib.request.urlopen(urllib.request.Request(
                GEN, data=body, headers=KH, method="POST"), timeout=60).read().decode())
        except Exception as e:
            resp = {"err": str(e)}
        tid = (resp.get("data") or {}).get("taskId")
        if tid:
            break
        print(f"  Veo-Start ohne taskId ({resp.get('msg') or resp.get('message') or resp.get('err') or resp}), Retry {attempt+1}/5 ...", flush=True)
        time.sleep(10 * (attempt + 1))
    if not tid:
        raise VeoAusfall("Veo: kein taskId nach 5 Versuchen (API ueberlastet?)")
    print(f"  Veo-Task {tid} laeuft ...", flush=True)
    for _ in range(int(poll_sek / 4)):
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{REC}?taskId={urllib.parse.quote(tid)}", headers=KH), timeout=60).read().decode()).get("data") or {}
        flag = d.get("successFlag")
        if flag == 1:
            resp = d.get("response") or {}
            urls = resp.get("resultUrls") or resp.get("originUrls") or d.get("resultUrls")
            if isinstance(urls, str):
                urls = json.loads(urls)
            url = urls[0] if isinstance(urls, list) and urls else (urls if isinstance(urls, str) else None)
            if not url:
                raise VeoAusfall(f"Veo: keine Video-URL: {d}")
            Path(out_mp4).write_bytes(urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
            return
        if flag in (2, 3):
            raise VeoAusfall(f"Veo abgelehnt: {d.get('errorMessage') or d}")
        time.sleep(4)
    raise VeoAusfall(f"Veo: kein Ergebnis nach {poll_sek}s (Anbieter haengt)")


def _prompt_entschaerfen(prompt):
    """Zweiter Anlauf mit ruhigerem, kuerzerem Prompt. Lange, verschachtelte
    Szenenbeschreibungen sind es, an denen Veo haengen bleibt."""
    kern = prompt.split(".")[0].strip()
    return (f"{kern}. Ruhige, cineastische Aufnahme, 9:16, warmes gedaempftes Licht, "
            f"langsame Kamerabewegung, keine Schrift im Bild.")


def veo_generate(prompt, out_mp4, model="veo3_fast", res="1080p", duration=8):
    """Auftrag 2.2: Zeitlimit, begrenzte Wiederholungen, definierter Ersatzweg.
    Anlauf 1 mit dem Originalprompt und weitem Fenster, Anlauf 2 entschaerft.

    Jeder Anlauf wird VOR dem Aufruf gebucht. Ist die Tagesgrenze erreicht, fliegt
    BudgetErschoepft und wird bewusst nicht als 'Clip-Ausfall' behandelt, sondern
    beendet den Lauf. Genau hier ist am 01.08.2026 das Geld verbrannt."""
    import kk_budget as budget
    anlaeufe = [(prompt, 900), (_prompt_entschaerfen(prompt), 600)]
    letzter = None
    for i, (p, fenster) in enumerate(anlaeufe, 1):
        budget.buchen("veo")          # wirft, bevor etwas kostet
        try:
            _veo_einmal(p, out_mp4, model, res, duration, fenster)
            if i > 1:
                print(f"  Clip erst im {i}. Anlauf erzeugt (entschaerfter Prompt).", flush=True)
            return
        except VeoAusfall as e:
            letzter = e
            print(f"  Veo-Anlauf {i}/{len(anlaeufe)} gescheitert: {str(e)[:160]}", flush=True)
    raise VeoAusfall(str(letzter))


def _motiv(clip_prompt):
    """Zieht das reine Motiv aus einem fertigen Clip-Prompt heraus.

    Die Prompts sind aufgebaut als "<Vorspann>, <MOTIV>, filmed on a modern ...".
    Fuer den Ein-Kauf-Prompt wird nur das Motiv gebraucht, der Look-Teil steht dort
    einmal fuer alle drei Szenen.
    """
    t = clip_prompt
    for vorspann in ("filling the entire frame edge to edge, ", "9:16 footage, "):
        if vorspann in t:
            t = t.split(vorspann, 1)[1]
            break
    for ende in (", filmed on a modern", ", shot on warm faded film", ", no on-screen text"):
        if ende in t:
            t = t.split(ende, 1)[0]
            break
    return t.strip().rstrip(".")


def szenen_prompt(r):
    """Baut aus den drei Motiven EINEN Prompt mit drei Szenen und harten Schnitten.

    Dario-Vorgabe 14.08.2026: "er soll ja ein video kaufen und nicht 3 und sie zusammen
    tun, sondern ein video das 3 szenen hat". Veo 3.1 kann das ueber Zeitmarken im
    Prompt, es schneidet dann innerhalb der einen Generierung. Ein Kauf, drei echte
    Motive, rund 60 Credits statt 180.

    Die 8 Sekunden sind die harte Grenze von Veo (erlaubt sind 4, 6 oder 8), laenger
    geht pro Generierung nicht. Die drei Szenen teilen sich diese 8 Sekunden.
    """
    m = [_motiv(c) for c in (r.get("clips") or [])][:3]
    while len(m) < 3:
        m.append(m[-1] if m else "a quiet natural scene in soft daylight")
    return (
        "Realistic documentary-style vertical 9:16 video made of three different shots "
        "with a hard cut between them, consistent look and light mood across all three, "
        "filmed on a modern full-frame camera with a 35mm lens, natural true-to-life "
        "colours, realistic daylight, natural contrast, no colour grading, no film look. "
        f"[00:00-00:03] {m[0]}. "
        f"[00:03-00:05] {m[1]}. "
        f"[00:05-00:08] {m[2]}. "
        "Slow contemplative camera motion in every shot, no on-screen text, no people, "
        "no faces, no letterbox, no vignette frame, no film strip border, 24fps"
    )


def _dehnen(quelle, ziel, ziel_len):
    """Zieht die gekauften 8 Sekunden auf die Laenge der Textphase.

    Veo liefert hoechstens 8 Sekunden pro Kauf, die Textphase braucht rund 14. Statt
    einen zweiten Clip zu kaufen laeuft das Material langsamer.

    Wichtig ist das WIE: setpts allein verdoppelt nur vorhandene Bilder, bei Faktor 2
    steht jedes Bild doppelt so lange und die Bewegung ruckelt sichtbar. minterpolate
    rechnet echte Zwischenbilder aus der Bewegung, damit bleibt der Schwenk fluessig.
    Kostet rund eine Minute Rechenzeit pro Clip, aber kein Geld. Faellt es aus, wird
    einfach gedehnt, lieber ein leichtes Ruckeln als kein Video.
    """
    quell_len = _laenge_sek(quelle)
    faktor = min(DEHNUNG_MAX, max(1.0, ziel_len / max(quell_len, 0.1)))
    basis = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(quelle)]
    ende = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
            "-pix_fmt", "yuv420p", str(ziel)]
    glatt = (f"minterpolate=fps={int(round(24 * faktor))}:mi_mode=mci:mc_mode=aobmc:"
             f"vsbmc=1,setpts={faktor:.4f}*PTS,fps=24")
    einfach = f"setpts={faktor:.4f}*PTS,fps=24"
    if ZWISCHENBILDER and faktor > 1.15:
        try:
            subprocess.run(basis + ["-vf", glatt] + ende, check=True, timeout=900)
            print(f"  TEMPO: {quell_len:.1f}s auf {quell_len * faktor:.1f}s gedehnt "
                  f"(Faktor {faktor:.2f}, mit Zwischenbildern).", flush=True)
            return quell_len * faktor
        except Exception as e:
            print(f"  Zwischenbilder fehlgeschlagen ({repr(e)[:120]}), dehne einfach.",
                  flush=True)
    subprocess.run(basis + ["-vf", einfach] + ende, check=True, timeout=600)
    print(f"  TEMPO: {quell_len:.1f}s auf {quell_len * faktor:.1f}s gedehnt "
          f"(Faktor {faktor:.2f}).", flush=True)
    return quell_len * faktor


def _laenge_sek(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 8.0


def musik_aus_lager(ziel, name=""):
    """Nimmt ein bereits erzeugtes Stueck aus assets/musik statt Suno neu zu bezahlen.

    Musik kostet 17 bis 22 Credits pro Reel und ist das Einzige, was sich ohne jeden
    sichtbaren Verlust wiederverwenden laesst: instrumentales Ambient, 21 Sekunden lang
    benutzt, danach nie wieder gehoert. Die Auswahl haengt am Konzeptnamen, damit nicht
    immer dasselbe Stueck laeuft, aber derselbe Reel beim Neubau gleich klingt.
    """
    lager = sorted(MUSIKLAGER.glob("*.mp3")) if MUSIKLAGER.exists() else []
    lager = [p for p in lager if p.stat().st_size >= 10000]
    if not lager:
        return False
    import hashlib
    i = int(hashlib.sha1(name.encode()).hexdigest(), 16) % len(lager)
    shutil.copyfile(lager[i], ziel)
    print(f"  MUSIK aus dem Lager: {lager[i].name} ({len(lager)} Stuecke, 0 Credits).", flush=True)
    return True


def _ersatzclip(quelle, ziel):
    """Auftrag 2.1: Faellt ein Clip aus, wird er ersetzt statt den Reel zu kippen.
    Gespiegelt und leicht herangezoomt, damit es nicht als plumpe Wiederholung liest."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(quelle),
                    "-vf", "hflip,scale=1188:2112,crop=1080:1920,setsar=1",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-an", str(ziel)], check=True, timeout=300)
    print(f"  ERSATZ: {Path(ziel).name} aus {Path(quelle).name} (gespiegelt).", flush=True)


def gen_music(prompt, out):
    import kk_budget as budget
    budget.buchen("musik")            # bezahlter Aufruf, wird vorher gebucht
    body = json.dumps({"prompt": prompt, "customMode": False, "instrumental": True, "model": "V4",
                       "callBackUrl": "https://example.com/cb"}).encode()
    tid = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://api.kie.ai/api/v1/generate", data=body, headers=KH, method="POST"), timeout=60).read().decode())["data"]["taskId"]
    for _ in range(120):
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"https://api.kie.ai/api/v1/generate/record-info?taskId={tid}", headers=KH), timeout=60).read().decode()).get("data") or {}
        for it in (d.get("response") or d).get("sunoData") or []:
            if isinstance(it, dict) and it.get("audioUrl"):
                Path(out).write_bytes(urllib.request.urlopen(urllib.request.Request(
                    it["audioUrl"], headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
                return
        time.sleep(5)
    raise TimeoutError("music")


# Der verwaschene Look wird NICHT abrupt entfernt, sondern von Video zu Video sanft
# herausgenommen (Wunsch Dario 2026-07-25). Ein Schrittzaehler in grade_state.json
# interpoliert von t=0 (aktueller, milchiger Look) zu t=1 (sauber: echtes Schwarz,
# volle Saettigung, mehr Kontrast, weniger Korn/Vignette) ueber GRADE_STEPS Videos.
GRADE_STEPS = 6
GRADE_STATE = HERE / "grade_state.json"


def _lerp(a, b, t):
    return a + (b - a) * t


def _grade_filter(t):
    """t=0 = alter verwaschener Look, t=1 = natuerlicher Look (Dario-Vorgabe 2026-08-13).

    Vorgeschichte in zwei Schritten. Erst war der Look milchig und wirkte wie eine
    billige Kopie, dagegen kam am 02.08.2026 ein HDR-Grade: Saettigung 1.14, Kontrast
    1.20, S-Kurve, Teal-Orange-Splitting, Mikrokontrast 0.9 und Vignette. Das schlug ins
    andere Extrem, die Videos sahen bearbeitet aus statt echt (Dario 13.08.2026:
    "wirken aktuell zu stark bearbeitet").

    Zielpunkt jetzt: so wenig Eingriff wie moeglich.
      - Saettigung 1.02 und Kontrast 1.03 statt 1.14/1.20, Farben wie gesehen
      - Kurve fast linear (0.22 auf 0.20, 0.78 auf 0.79), Schatten bleiben offen
      - Teal-Orange-Splitting (colorbalance) und colorchannelmixer ganz raus, das war
        der eigentliche Kino-Filter-Eindruck
      - Vignette raus, die liest sofort als Effekt
      - unsharp nur noch 0.25, gleicht die Hochskalierung nach dem Crop aus, mehr nicht
    Echtes Schwarz und kein Korn bleiben, beides ist realistisch und nicht "bearbeitet".
    """
    sat = round(_lerp(0.82, 1.02, t), 3)    # knapp neutral, Farben wie gesehen
    blk = round(_lerp(0.055, 0.0, t), 3)    # echtes Schwarz statt Milch
    sh = round(_lerp(0.16, 0.20, t), 3)     # fast linear, Schatten bleiben offen
    hl = round(_lerp(0.85, 0.79, t), 3)     # Lichter nicht mehr hochziehen
    hi = round(_lerp(0.97, 1.0, t), 3)      # bis reinweiss
    con = round(_lerp(1.08, 1.03, t), 3)    # nur ein Hauch Kontrast
    gam = round(_lerp(1.02, 1.0, t), 3)     # neutral
    schaerfe = round(_lerp(0.0, 0.25, t), 2)  # gleicht nur die Hochskalierung aus
    korn = "" if t >= 0.75 else f"noise=alls={int(round(_lerp(8, 0, t)))},"
    return (f"eq=saturation={sat}:contrast={con}:brightness=0.0:gamma={gam},"
            f"curves=m='0/{blk} 0.22/{sh} 0.5/0.5 0.78/{hl} 1/{hi}',"
            f"{korn}unsharp=5:5:{schaerfe}:5:5:0.0")


def _next_grade():
    """Liest den Schritt, liefert (grade-Filter, step, t). Schreibt NICHT (erst nach Erfolg)."""
    step = 0
    try:
        if GRADE_STATE.exists():
            step = int(json.loads(GRADE_STATE.read_text()).get("step", 0))
    except Exception:
        step = 0
    t = min(1.0, step / GRADE_STEPS)
    return _grade_filter(t), step, t


def _advance_grade(step):
    try:
        GRADE_STATE.write_text(json.dumps({"step": min(step + 1, GRADE_STEPS)}))
    except Exception:
        pass


def _inhaltscrop(clip):
    """Findet per cropdetect den echten Bildinhalt und gibt einen crop-Filter zurueck.

    Veo rendert trotz Prompt oft einen Rahmen bzw. Letterbox in das 1080x1920-Bild
    (gemessen am 16.07.: nur 1080x1630 echter Inhalt, 146px Balken oben). Wer das blind
    wegzoomt, verliert Aufloesung und trifft es mal zu knapp, mal zu grosszuegig.
    Faellt die Messung aus, wird nicht gecroppt und der Rahmen faellt beim Fuellen weg.
    """
    try:
        p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(clip),
                            "-vf", "cropdetect=limit=24:round=2", "-frames:v", "120",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=120)
        treffer = [l.split("crop=")[1].strip() for l in (p.stderr or "").splitlines()
                   if "crop=" in l]
        if not treffer:
            return ""
        w, h, x, y = (int(v) for v in treffer[-1].split(":"))
        # Nur uebernehmen, wenn plausibel: mindestens 60 Prozent Hoehe, sonst schneidet
        # eine dunkle Szene den halben Bildinhalt weg.
        if w < 200 or h < 200 or h < 0.6 * 1920:
            print(f"  cropdetect unplausibel ({w}x{h}), kein Inhalts-Crop.", flush=True)
            return ""
        if h >= 1900 and y <= 8:
            return ""          # kein Rahmen vorhanden
        print(f"  Inhalts-Crop {w}x{h}+{x}+{y} (Rahmen weg, "
              f"Hochskalierung nur {1920 / h:.2f}x statt 1.28x)", flush=True)
        return f"crop={w}:{h}:{x}:{y},"
    except Exception as e:
        print(f"  cropdetect fehlgeschlagen ({repr(e)[:100]}), kein Inhalts-Crop.", flush=True)
        return ""


def compose_montage(clips, cl, out):
    """3 Clips -> weiche Cross-Dissolves (1,2s) -> Grade + Korn + Vignette (schrittweise entwascht)."""
    grade, step, t = _next_grade()
    ins = []
    for c in clips:
        ins += ["-i", str(c)]
    k = len(clips)
    parts = []
    for i in range(k):
        # Staerkerer Zoom-Crop (~1.28x): schneidet den von Veo gerenderten Archiv-Film-
        # Rahmen (inkl. des runden Elements links) zuverlaessig weg. Die Prompts sagen zwar
        # "no film strip border", Veo rendert ihn aber trotzdem -> hier hart wegcroppen.
        # Frueher: blind auf 1382x2458 hochskalieren und auf 1080x1920 zurueckschneiden,
        # also pauschal 1.28x. Das kostete echte Aufloesung und war die Unschaerfe, die
        # wie eine billige Kopie aussah.
        # Jetzt inhaltsgenau: Veo rendert das Bild letterboxed in den Rahmen (gemessen
        # 1080x1630 mit 146px Balken oben). cropdetect findet den echten Bildinhalt, der
        # wird weggeschnitten und nur noch um das Noetige hochgezogen. Lanczos haelt die
        # Kanten scharf.
        # Nach dem Inhalts-Crop noch ein kleiner Sicherheitszoom von 5 Prozent. cropdetect
        # misst an einzelnen Bildern und trifft den Rand nicht immer symmetrisch, dann
        # bleiben duenne dunkle Streifen an den Kanten stehen. 5 Prozent kosten kaum
        # Schaerfe und raeumen sie zuverlaessig weg.
        # clips[i], NICHT c: c war die Laufvariable der Schleife darueber und zeigte
        # immer auf den LETZTEN Clip. Gemessen wurde also dreimal derselbe, und das
        # Ergebnis auf alle drei angewendet. Solange alle drei frisch von Veo kamen,
        # fiel es nicht auf, weil sie denselben Rahmen hatten. Sobald ein Clip keinen
        # Rahmen hat (Sparmodus), findet cropdetect am letzten nichts, es wird gar
        # nicht gecroppt und der Rahmen des ersten Clips steht im fertigen Video.
        cd = _inhaltscrop(clips[i])
        parts.append(f"[{i}:v]trim=0:{cl},setpts=PTS-STARTPTS,{cd}"
                     f"scale=1134:2016:force_original_aspect_ratio=increase:flags=lanczos,"
                     f"crop=1080:1920,fps=24,setsar=1,format=yuv420p[c{i}]")
    # xfade-Kette. Beim Kurzformat gibt es nur EINEN Clip, dann faellt sie weg und
    # [c0] geht direkt in den Grade. Ohne diesen Fall bleibt [m] unbelegt und ffmpeg
    # bricht mit "Filter 'format:default' has output 0 (c0) unconnected" ab.
    prev = "c0"
    for i in range(1, k):
        off = round(i * cl - i * DISSOLVE, 3)
        tag = f"x{i}" if i < k - 1 else "m"
        parts.append(f"[{prev}][c{i}]xfade=transition=fade:duration={DISSOLVE}:offset={off}[{tag}]")
        prev = tag
    quelle = "m" if k > 1 else "c0"
    parts.append(f"[{quelle}]{grade},setsar=1,format=yuv420p[out]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[out]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                    "-pix_fmt", "yuv420p", str(out)], check=True, timeout=600)
    print(f"  Entwaschen Schritt {step}/{GRADE_STEPS} (t={t:.2f})", flush=True)
    _advance_grade(step)


def compose_final(montage, cards, endcard_png, music, out, foot_len):
    """cards: Liste (png, s, e, fade_in). Overlay auf Montage, Dissolve in Schlusskarte, Musik loudnorm."""
    total = round(foot_len + END_LEN, 3)
    mont_len = round(foot_len + HEADROOM, 3)
    ins = ["-i", str(montage)]
    for (png, *_r) in cards:
        ins += ["-loop", "1", "-t", str(mont_len), "-i", str(png)]
    ins += ["-loop", "1", "-t", str(END_LEN), "-i", str(endcard_png), "-i", str(music)]
    n = len(cards)
    end_idx = 1 + n
    mus_idx = 1 + n + 1
    parts = []
    for i, (_png, s, e, fin) in enumerate(cards):
        idx = 1 + i
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={round(s,3)}:d={fin}:alpha=1,"
                     f"fade=t=out:st={round(e-FADE_OUT,3)}:d={FADE_OUT}:alpha=1[c{i}]")
    chain = "[0:v]"
    for i in range(n):
        nxt = f"[o{i}]" if i < n - 1 else "[vtext]"
        parts.append(f"{chain}[c{i}]overlay=0:0{nxt}")
        chain = nxt
    parts.append("[vtext]fps=24,format=yuv420p,setsar=1,settb=AVTB[vt]")
    parts.append(f"[{end_idx}:v]scale=1080:1920,fps=24,format=yuv420p,setsar=1,settb=AVTB[ve]")
    parts.append(f"[vt][ve]xfade=transition=fade:duration={END_XF}:offset={round(foot_len,3)}[v]")
    parts.append(f"[{mus_idx}:a]atrim=0:{total},asetpts=PTS-STARTPTS,highpass=f=30,afftdn=nr=6,"
                 f"loudnorm=I=-14:TP=-1.5,afade=t=in:st=0:d=0.8,afade=t=out:st={round(total-2.0,3)}:d=2.0[a]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-t", str(total),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-b:v", "15M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", str(out)],
                   check=True, timeout=600)
    return total


def _fenster(thoughts, kurz):
    sts = [standzeit(t, kurz) for t in thoughts]
    wins, s = [], 0.0
    for st in sts:
        wins.append((round(s, 3), round(s + st, 3)))
        s = round(s + st - OVERLAP, 3)
    return wins, sts


def produce(name, r):
    kurz = KURZ
    if kurz:
        r = kurzfassung(r)
        print(f"[{name}] Kurzformat: {len(r['thoughts'])} Beats, "
              f"{len(r['clips'])} Clip, Frage \"{r['cta']}\"", flush=True)
    elif SPARMODUS:
        # EIN Kauf, der selbst drei Szenen enthaelt. Ab hier ist es genau ein Clip,
        # die Montage braucht damit auch keine Blenden mehr, die Schnitte sitzen
        # bereits im gekauften Material.
        r = dict(r)
        r["clips"] = [szenen_prompt(r)]
        print(f"[{name}] Sparmodus: 1 Kauf mit 3 Szenen statt 3 Kaeufen.", flush=True)
    thoughts = r["thoughts"]
    n = len(thoughts)
    wins, sts = _fenster(thoughts, kurz)
    foot_len = wins[-1][1]
    cl = round((foot_len + HEADROOM + (len(r["clips"]) - 1) * DISSOLVE) / len(r["clips"]), 3)
    # Ein Veo-Clip liefert 8 Sekunden. Passt die Textphase nicht hinein, werden die
    # Standzeiten gestaucht statt einen zweiten Clip zu kaufen.
    if SPARMODUS and not kurz:
        grenze = round(8.0 * DEHNUNG_MAX, 2)
        for _ in range(20):
            if cl <= grenze:
                break
            skala = grenze / cl
            sts = [max(2.6, round(st * skala, 3)) for st in sts]
            wins, s = [], 0.0
            for st in sts:
                wins.append((round(s, 3), round(s + st, 3)))
                s = round(s + st - OVERLAP, 3)
            foot_len = wins[-1][1]
            neu = round(foot_len + HEADROOM, 3)
            if abs(neu - cl) < 0.01:
                break
            cl = neu
        print(f"[{name}] Textphase {foot_len:.1f}s, Gesamt rund "
              f"{foot_len + END_LEN:.1f}s", flush=True)
    if kurz:
        for _ in range(20):
            if cl <= KURZ_CLIP_MAX:
                break
            skala = KURZ_CLIP_MAX / cl
            sts = [max(2.4, round(st * skala, 3)) for st in sts]
            wins, s = [], 0.0
            for st in sts:
                wins.append((round(s, 3), round(s + st, 3)))
                s = round(s + st - OVERLAP, 3)
            foot_len = wins[-1][1]
            neu = round((foot_len + HEADROOM) / len(r["clips"]), 3)
            if abs(neu - cl) < 0.01:
                break
            cl = neu
        print(f"[{name}] Textphase {foot_len:.1f}s, Clip {cl:.1f}s, "
              f"Gesamt rund {foot_len + END_LEN:.1f}s", flush=True)
    (OUT / f"{name}.caption.txt").write_text(r["caption"], encoding="utf-8")

    # 1) Footage + Musik PARALLEL erzeugen (kuerzt Bauzeit, vermeidet Timeouts)
    import concurrent.futures as cf
    clips_raw = [OUT / f"{name}_clip{i}_raw.mp4" for i in range(len(r["clips"]))]
    mus = OUT / f"{name}_music.mp3"
    jobs = []
    for i, cp in enumerate(r["clips"]):
        cr = clips_raw[i]
        if not (cr.exists() and cr.stat().st_size > 100000):
            jobs.append(("clip", cp, cr))
    music_ready = mus.exists() and mus.stat().st_size >= 10000
    if not music_ready and not MUSIK_NEU and musik_aus_lager(mus, name):
        music_ready = True
    if not music_ready:
        jobs.append(("music", r["music"], mus))
    if jobs:
        print(f"[{name}] 1/4 {len(jobs)} Assets (Veo/Suno) parallel ...", flush=True)
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            futs = {}
            for (k, p, o) in jobs:
                fut = (ex.submit(veo_generate, p, o, duration=8) if k == "clip"
                       else ex.submit(gen_music, p, o))
                futs[fut] = (k, o)
            # Auftrag 2.1: Ausfaelle einsammeln statt den ersten Fehler durchschlagen
            # zu lassen. Was fehlt, wird danach ersetzt.
            import kk_budget as budget
            budgetstop = None
            for f in cf.as_completed(futs):
                k, o = futs[f]
                try:
                    f.result()
                except budget.BudgetErschoepft as e:
                    # Die Ausgabenbremse ist KEIN Asset-Ausfall. Sie wird nicht durch
                    # einen Ersatzclip geheilt, sondern beendet den Lauf.
                    budgetstop = e
                    print(f"  BUDGET-STOPP: {e}", flush=True)
                except Exception as e:
                    print(f"  ASSET-AUSFALL ({k}) {Path(o).name}: {repr(e)[:200]}", flush=True)
            if budgetstop is not None:
                raise budgetstop
    else:
        print(f"[{name}] 1/4 Assets vorhanden", flush=True)

    # --- Ersatzteil-Lager: fehlende Clips auffuellen (Auftrag 2.1) ---
    def _da(p):
        return p.exists() and p.stat().st_size > 100000
    fehlend = [c for c in clips_raw if not _da(c)]
    vorhanden = [c for c in clips_raw if _da(c)]
    if fehlend:
        if not vorhanden:
            raise RuntimeError(f"Alle {len(clips_raw)} Clips ausgefallen, Reel nicht baubar.")
        print(f"[{name}] {len(fehlend)} von {len(clips_raw)} Clips ausgefallen, "
              f"ersetze aus den gelungenen.", flush=True)
        for i, miss in enumerate(fehlend):
            _ersatzclip(vorhanden[i % len(vorhanden)], miss)
    if not (mus.exists() and mus.stat().st_size >= 10000):
        alt = sorted(OUT.glob("*_music.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        alt = [a for a in alt if a != mus and a.stat().st_size >= 10000]
        if not alt:
            raise RuntimeError("Musik ausgefallen und kein Ersatz im Lager.")
        shutil.copyfile(alt[0], mus)
        print(f"  ERSATZ-MUSIK aus {alt[0].name}.", flush=True)
    if SPARMODUS and not kurz:
        # Die gekauften 8 Sekunden auf die Textphase ziehen. Reicht die Dehnung nicht
        # ganz, wird die Textphase auf das Machbare gekuerzt, damit am Schluss kein
        # eingefrorenes Bild steht.
        gedehnt = OUT / f"{name}_clip0_lang.mp4"
        echt = _dehnen(clips_raw[0], gedehnt, cl)
        clips_raw = [gedehnt]
        if echt + 0.05 < cl:
            fehlt = cl - echt
            sts = [max(2.4, round(st - fehlt / len(sts), 3)) for st in sts]
            wins, s = [], 0.0
            for st in sts:
                wins.append((round(s, 3), round(s + st, 3)))
                s = round(s + st - OVERLAP, 3)
            foot_len = wins[-1][1]
            cl = round(min(echt, foot_len + HEADROOM), 3)
            print(f"  Textphase auf {foot_len:.1f}s gekuerzt, Material reicht nur "
                  f"{echt:.1f}s.", flush=True)
    # 2) Montage + Grade
    montage = OUT / f"{name}_montage.mp4"
    print(f"[{name}] 2/5 Montage + Grade + Korn ...", flush=True)
    compose_montage(clips_raw, cl, montage)
    # 3) Textkarten + Schlusskarte
    print(f"[{name}] 3/5 Textkarten (Fraunces) ...", flush=True)
    cards = []
    for i, t in enumerate(thoughts):
        png = OUT / f"{name}_card{i}.png"
        render_card(r.get("kicker", "") if i == 0 else "", t, png, hook=(i == 0))
        s0, e0 = wins[i]
        cards.append((png, s0, e0, HOOK_IN if i == 0 else FADE_IN))
    endcard = OUT / f"{name}_end.png"
    render_endcard(r.get("endcard_term", ""), r["cta"], endcard)
    # 4) Final (Musik wurde in Schritt 1 parallel erzeugt)
    print(f"[{name}] 4/4 Compose final ...", flush=True)
    fin = OUT / f"{name}.mp4"
    dur = compose_final(montage, cards, endcard, mus, fin, foot_len)
    # Laengen-Check (§0)
    # Laengen-Gate haengt am Format: das Kurzformat SOLL 8 bis 13 Sekunden haben.
    hart_max, weich_max, min_len = (13.5, 12.5, 8.0) if kurz else (28.0, 27.0, 18.0)
    verdict = "OK"
    if dur > hart_max:
        verdict = f"FAIL hart ({dur:.1f}s > {hart_max}s)"
    elif dur > weich_max:
        verdict = f"WARN weich ({dur:.1f}s > {weich_max}s)"
    elif dur < min_len:
        verdict = f"WARN kurz ({dur:.1f}s < {min_len}s)"
    print(f"FERTIG -> {fin}  ({dur:.1f}s, {verdict})", flush=True)
    return fin


def _queue_today(name, caption):
    from datetime import date
    QUEUE = HERE / "queue.jsonl"; PT = HERE / "posting_times.json"
    wd = date.today().weekday(); tm = "12:00:00"
    if PT.exists():
        try: tm = json.loads(PT.read_text()).get(str(wd), tm)
        except Exception: pass
    day = date.today().strftime("%Y-%m-%d")
    entry = {"id": f"reel-{name}-{day}", "datetime": f"{day}T{tm}", "theme": name,
             "format": "reel", "video_url": f"assets/video_reels/{name}.mp4",
             "caption": caption, "status": "pending"}
    with QUEUE.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _find(name):
    data = json.loads((HERE / "reel_pipeline.json").read_text())
    for c in data.get("approved", []) + data.get("built", []):
        if c.get("name") == name:
            return c
    raise KeyError(name)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--pipeline":
        pf = HERE / "reel_pipeline.json"
        data = json.loads(pf.read_text())
        approved = data.get("approved", [])
        if not approved:
            print("Pipeline leer."); return
        c = approved[0]; name = c["name"]
        produce(name, c)
        _queue_today(name, c["caption"])
        data["approved"] = approved[1:]
        data.setdefault("built", []).append({"name": name, "theme": c.get("theme")})
        pf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"PIPELINE: {name} gebaut, {len(data['approved'])} verbleiben")
    elif args:
        produce(args[0], _find(args[0]))
    else:
        print("Aufruf: build_video_reel.py <name> | --pipeline")


if __name__ == "__main__":
    main()
