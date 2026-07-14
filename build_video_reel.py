"""
Kopf & Kompass — cineastisches Nachdenk-/Mindset-Reel.
Ein ruhiges, atmosphaerisches KI-Footage (Veo 3.1) + kinetische Text-Beats,
die einen Gedanken aufbauen (Haken -> Vertiefung -> Wende/Aufrichtung) + tiefe
Musik + leise Wortmarken-Schlusskarte. Kein lautes Pattern-Interrupt, sondern Sog
durch Bild, Wahrheit und Ruhe.

Baut EIN Reel:  python3 build_video_reel.py <name>        (Name aus reel_pipeline.json)
                python3 build_video_reel.py --pipeline     (naechstes approved-Konzept, dequeued)
Footage wird gecacht (assets/video_reels/<name>_*.mp4); erneuter Lauf spart Veo-Credits.
Postet NICHT (nur Erzeugung).
"""
import base64
import json
import os
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

# --- Kopf & Kompass Look (bewusst anders als jeder andere Account: dunkel, warm, filmisch) ---
BG = "#0b0c10"          # tiefes, warmes Nachtschwarz
BG_RGB = "11,12,16"
INK = "#f4efe6"         # warmes Elfenbein
ACC = "#d8b57f"         # gedaempftes, edles Amber (nicht grell)

# Timing: ruhig, gut lesbar. Echtzeit (kein Slow-Mo), harte Textschnitte (kein Weg-Bluren).
FOOT_SRC = 8.0
SLOW = 1.0
FOOT_LEN = FOOT_SRC * SLOW
OUTRO_LEN = 3.6
TOTAL = FOOT_LEN + OUTRO_LEN
XF = 0.05


def make_windows(has_hook, n_beats):
    """Gleichmaessige, ueberlappende Fenster ueber 0..FOOT_LEN, damit der Textbereich
    durchgehend sichtbar bleibt (nur Inhalt wechselt). Hook = harter Cut ab Frame 1."""
    k = (1 if has_hook else 0) + n_beats
    seg = FOOT_LEN / k
    wins = []
    for i in range(k):
        s = 0.0 if i == 0 else round(i * seg - XF, 2)
        e = FOOT_LEN if i == k - 1 else round((i + 1) * seg + XF, 2)
        din = 0.0 if (i == 0 and has_hook) else XF
        dout = XF
        wins.append((s, e, din, dout))
    return wins


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
    return (f"@font-face{{font-family:'Quote';src:url(data:font/ttf;base64,"
            f"{_b64(FONTS/'PlayfairDisplay.ttf')}) format('truetype');}}"
            f"@font-face{{font-family:'Sans';src:url(data:font/ttf;base64,"
            f"{_b64(FONTS/'Inter.ttf')}) format('truetype');}}")


def _shoot(html, out_png, transparent):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html); hp = f.name
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage",
            "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920",
            f"--screenshot={out_png}", f"file://{hp}"]
    if transparent:
        args.insert(-1, "--default-background-color=00000000")
    subprocess.run(args, check=True, capture_output=True)


def render_beat(headline, out_png):
    """Ein Gedanken-Beat: zwei Zeilen, ruhig und gross. Letzte Zeile im Amber-Akzent."""
    l1, l2 = (headline.split("|") + [""])[:2]
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Quote',serif;}}
.topgrad{{position:absolute;left:0;right:0;top:0;height:260px;background:linear-gradient(to bottom,rgba({BG_RGB},.62),rgba({BG_RGB},0));}}
.botgrad{{position:absolute;left:0;right:0;bottom:0;height:60%;background:linear-gradient(to top,rgba({BG_RGB},.97) 28%,rgba({BG_RGB},.8) 60%,rgba({BG_RGB},0));}}
.wrap{{position:absolute;left:84px;right:84px;bottom:380px;}}
.bar{{width:70px;height:5px;background:{ACC};margin-bottom:46px;opacity:.9;}}
.h div{{font-weight:600;font-size:96px;line-height:1.12;letter-spacing:-.5px;color:{INK};}}
.h div:last-child{{color:{ACC};font-style:italic;}}
.handle{{position:absolute;left:84px;bottom:130px;font-family:'Sans';font-weight:500;font-size:32px;letter-spacing:.5px;color:rgba(244,239,230,.55);}}
</style></head><body>
<div class="topgrad"></div><div class="botgrad"></div>
<div class="wrap"><div class="bar"></div><div class="h"><div>{l1}</div><div>{l2}</div></div></div>
<div class="handle">@kopfundkompass</div>
</body></html>"""
    _shoot(html, out_png, transparent=True)


def render_hook(top, line, out_png):
    """Cold-Open-Hook: kurze Amber-Zeile + grosser Gedanke, hart eingeschnitten.
    Groesse passt sich der Laenge an."""
    tsize = 52 if len(top) <= 22 else 42
    lsize = 108 if len(line) <= 22 else 86 if len(line) <= 40 else 68
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Quote',serif;}}
.topgrad{{position:absolute;left:0;right:0;top:0;height:260px;background:linear-gradient(to bottom,rgba({BG_RGB},.62),rgba({BG_RGB},0));}}
.botgrad{{position:absolute;left:0;right:0;bottom:0;height:62%;background:linear-gradient(to top,rgba({BG_RGB},.97) 28%,rgba({BG_RGB},.82) 60%,rgba({BG_RGB},0));}}
.wrap{{position:absolute;left:84px;right:84px;bottom:380px;}}
.top{{font-family:'Sans';font-weight:600;font-size:{tsize}px;letter-spacing:3px;text-transform:uppercase;color:{ACC};margin-bottom:30px;}}
.line{{font-weight:600;font-size:{lsize}px;line-height:1.1;letter-spacing:-.5px;color:{INK};}}
.handle{{position:absolute;left:84px;bottom:130px;font-family:'Sans';font-weight:500;font-size:32px;letter-spacing:.5px;color:rgba(244,239,230,.55);}}
</style></head><body>
<div class="topgrad"></div><div class="botgrad"></div>
<div class="wrap"><div class="top">{top}</div><div class="line">{line}</div></div>
<div class="handle">@kopfundkompass</div>
</body></html>"""
    _shoot(html, out_png, transparent=True)


def render_outro(headline, cta, out_png):
    """Leise, edle Schlusskarte: Wortmarke KOPF & KOMPASS, Kernsatz, dezenter CTA."""
    l1, l2 = (headline.split("|") + [""])[:2]
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Quote',serif;background:{BG};overflow:hidden;}}
.glow{{position:absolute;left:50%;top:42%;transform:translate(-50%,-50%);width:1250px;height:1250px;background:radial-gradient(circle,rgba(216,181,127,.12),rgba({BG_RGB},0) 62%);}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 100px;}}
.mark{{font-family:'Sans';font-weight:700;font-size:38px;letter-spacing:8px;text-transform:uppercase;color:{INK};}}
.rule{{width:66px;height:3px;background:{ACC};margin:34px auto 60px;}}
.h div{{font-weight:600;font-size:92px;line-height:1.12;letter-spacing:-.5px;color:{INK};}}
.h div:last-child{{color:{ACC};font-style:italic;}}
.cta{{display:inline-block;margin-top:64px;border:2px solid rgba(216,181,127,.75);color:{ACC};font-family:'Sans';font-weight:600;font-size:38px;
      padding:26px 54px;border-radius:60px;letter-spacing:.3px;}}
.handle{{position:absolute;left:0;right:0;bottom:150px;text-align:center;font-family:'Sans';font-weight:500;font-size:36px;letter-spacing:.5px;color:rgba(244,239,230,.6);}}
</style></head><body>
<div class="glow"></div>
<div class="mid">
  <div class="mark">Kopf &amp; Kompass</div>
  <div class="rule"></div>
  <div class="h"><div>{l1}</div><div>{l2}</div></div>
  <div class="cta">{cta}</div>
</div>
<div class="handle">@kopfundkompass</div>
</body></html>"""
    _shoot(html, out_png, transparent=False)


def veo_generate(prompt, out_mp4, model="veo3_fast", res="1080p", duration=8):
    body = json.dumps({"prompt": prompt, "model": model, "aspect_ratio": "9:16",
                       "resolution": res, "duration": duration}).encode()
    tid = json.loads(urllib.request.urlopen(urllib.request.Request(GEN, data=body, headers=KH, method="POST"),
                                             timeout=60).read().decode())["data"]["taskId"]
    print(f"  Veo-Task {tid} laeuft ...", flush=True)
    for _ in range(150):
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
                raise RuntimeError(f"Veo: keine Video-URL: {d}")
            Path(out_mp4).write_bytes(urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read())
            return
        if flag in (2, 3):
            raise RuntimeError(f"Veo fehlgeschlagen: {d.get('errorMessage') or d}")
        time.sleep(4)
    raise TimeoutError("veo timeout")


def gen_music(prompt, out):
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


def compose_story(raw, overlay_specs, outro_png, music, out):
    """Ein Clip + Text-Beats + Schlusskarte, NUR unsere Musik als Ton (ruhig, kein Impact).
    overlay_specs: Liste von (png_pfad, start, ende, fade_in, fade_out)."""
    ins = ["-i", str(raw)]
    for spec in overlay_specs:
        ins += ["-loop", "1", "-t", str(FOOT_LEN), "-i", str(spec[0])]
    ins += ["-loop", "1", "-t", str(OUTRO_LEN), "-i", str(outro_png), "-i", str(music)]
    n = len(overlay_specs)
    outro_idx = 1 + n
    music_idx = 1 + n + 1
    parts = [f"[0:v]trim=0:{FOOT_SRC},setpts={SLOW}*PTS,scale=1080:1920:force_original_aspect_ratio=increase,"
             "crop=1080:1920,setsar=1,fps=30[v0]"]
    for i, (_p, s, e, din, dout) in enumerate(overlay_specs):
        idx = 1 + i
        fi = max(din, 0.02)
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={s}:d={fi}:alpha=1,"
                     f"fade=t=out:st={round(e-dout, 3)}:d={dout}:alpha=1[b{i}]")
    chain = "[v0]"
    for i in range(n):
        nxt = f"[o{i}]" if i < n - 1 else "[vfoot_raw]"
        parts.append(f"{chain}[b{i}]overlay=0:0{nxt}")
        chain = nxt
    parts.append("[vfoot_raw]format=yuv420p[vfoot]")
    parts.append(f"[{outro_idx}:v]scale=1080:1920,setsar=1,fps=30,fade=t=in:st=0:d=0.5,format=yuv420p[vout]")
    parts.append("[vfoot][vout]concat=n=2:v=1:a=0[vall]")
    # Nur unsere Musik, ruhige Ein-/Ausblende. Kein Footage-Ton, kein Impact-Boom.
    parts.append(f"[{music_idx}:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,volume=0.9,"
                 f"afade=t=in:st=0:d=0.6,afade=t=out:st={TOTAL-1.4}:d=1.4[a]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[vall]", "-map", "[a]", "-t", str(TOTAL),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True, timeout=300)


def produce(name, r):
    global FOOT_LEN, TOTAL
    seg_len = r.get("seg_len", 2.6)
    FOOT_LEN = round(seg_len * ((1 if r.get("hook") else 0) + len(r["beats"])), 2)
    FOOT_LEN = min(FOOT_LEN, FOOT_SRC)   # ein 8s-Clip traegt alle Beats
    TOTAL = FOOT_LEN + OUTRO_LEN
    raw = OUT / f"{name}_raw.mp4"; mus = OUT / f"{name}_music.mp3"; outro = OUT / f"{name}_outro.png"; fin = OUT / f"{name}.mp4"
    (OUT / f"{name}.caption.txt").write_text(r["caption"], encoding="utf-8")
    if raw.exists() and raw.stat().st_size > 100000:
        print(f"[{name}] 1/4 Footage vorhanden, Veo uebersprungen", flush=True)
    else:
        print(f"[{name}] 1/4 Footage (Veo) ...", flush=True)
        veo_generate(r["prompt"], raw, duration=8)
    print(f"[{name}] 2/4 Hook + Beats + Outro rendern ...", flush=True)
    has_hook = bool(r.get("hook"))
    wins = make_windows(has_hook, len(r["beats"]))
    specs = []
    if has_hook:
        hp = OUT / f"{name}_hook.png"; render_hook(r["hook"][0], r["hook"][1], hp)
        specs.append((hp, *wins[0]))
    off = 1 if has_hook else 0
    for i, b in enumerate(r["beats"]):
        bp = OUT / f"{name}_beat{i}.png"; render_beat(b, bp)
        specs.append((bp, *wins[off + i]))
    render_outro(r["outro_hl"], r["outro_cta"], outro)
    if not mus.exists() or mus.stat().st_size < 10000:
        print(f"[{name}] 3/4 Musik ...", flush=True)
        gen_music(r["music"], mus)
    else:
        print(f"[{name}] 3/4 Musik vorhanden, uebersprungen", flush=True)
    print(f"[{name}] 4/4 Compose ...", flush=True)
    compose_story(raw, specs, outro, mus, fin)
    print(f"FERTIG -> {fin}", flush=True)
    return fin


def _queue_today(name, caption):
    """Haengt den fertigen Reel als heute faelligen Eintrag an queue.jsonl (Zeit aus posting_times.json)."""
    from datetime import date
    QUEUE = HERE / "queue.jsonl"
    PT = HERE / "posting_times.json"
    wd = date.today().weekday()
    tm = "12:00:00"
    if PT.exists():
        try:
            tm = json.loads(PT.read_text()).get(str(wd), tm)
        except Exception:
            pass
    day = date.today().strftime("%Y-%m-%d")
    entry = {"id": f"reel-{name}-{day}", "datetime": f"{day}T{tm}", "theme": name,
             "format": "reel", "video_url": f"assets/video_reels/{name}.mp4",
             "caption": caption, "status": "pending"}
    with QUEUE.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _find_concept(name):
    data = json.loads((HERE / "reel_pipeline.json").read_text())
    for c in data.get("approved", []) + data.get("built", []):
        if c.get("name") == name:
            return c
    raise KeyError(f"Konzept '{name}' nicht in reel_pipeline.json")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--pipeline":
        pf = HERE / "reel_pipeline.json"
        data = json.loads(pf.read_text())
        approved = data.get("approved", [])
        if not approved:
            print("Pipeline leer, kein freigegebenes Konzept.")
            return
        concept = approved[0]
        name = concept["name"]
        produce(name, concept)
        _queue_today(name, concept["caption"])
        data["approved"] = approved[1:]
        data.setdefault("built", []).append({"name": name, "theme": concept.get("theme")})
        pf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"PIPELINE: {name} gebaut + fuer heute eingeplant, {len(data['approved'])} Konzepte verbleiben")
    elif args:
        name = args[0]
        produce(name, _find_concept(name))
    else:
        print("Aufruf: build_video_reel.py <name> | --pipeline")


if __name__ == "__main__":
    main()
