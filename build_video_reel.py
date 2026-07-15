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
ST_MIN = 3.5; ST_MAX = 5.0


def standzeit(text):
    w = len(text.replace("|", " ").split())
    return max(ST_MIN, min(ST_MAX, w * 0.42 + 1.6))


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
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Fraunces',serif;
  background:radial-gradient(90% 60% at 50% 46%,{SHADOW},{FILMBLACK} 72%);overflow:hidden;}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 120px;}}
.term{{font-weight:600;font-size:32px;letter-spacing:.30em;text-transform:uppercase;color:{META};
  margin-bottom:42px;}}
.term .tick{{display:inline-block;width:24px;height:2px;background:{PETROL};vertical-align:middle;margin-right:16px;margin-bottom:6px;}}
.mark{{font-weight:600;font-size:66px;letter-spacing:.14em;color:{PAPER};margin-bottom:44px;}}
.cta{{font-style:italic;font-weight:440;font-size:40px;line-height:1.35;color:{META};}}
.hair{{width:180px;height:2px;background:{PETROL};margin:52px auto 0;}}
.handle{{position:absolute;left:0;right:0;bottom:150px;text-align:center;font-weight:500;
  font-size:30px;letter-spacing:.10em;color:#8A7C66;}}
</style></head><body>
<div class="mid">
  <div class="term"><span class="tick"></span>{term}</div>
  <div class="mark">Kopf &amp; Kompass</div>
  <div class="cta">{cta}</div>
  <div class="hair"></div>
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


GRADE = ("eq=saturation=0.82:contrast=1.08:brightness=0.01:gamma=1.02,"
         "curves=m='0/0.055 0.22/0.16 0.5/0.5 0.78/0.85 1/0.97',"
         "colorbalance=rs=-0.03:gs=0.01:bs=0.05:rm=0.04:gm=0.0:bm=-0.03:rh=0.06:gh=0.02:bh=-0.05,"
         "colorchannelmixer=rr=1.02:gg=1.0:bb=0.97,"
         "noise=alls=9:allf=t+u,vignette=PI/5:mode=backward,gblur=sigma=0.3")


def compose_montage(clips, cl, out):
    """3 Clips -> weiche Cross-Dissolves (1,2s) -> Archivkino-Grade + Korn + Vignette."""
    ins = []
    for c in clips:
        ins += ["-i", str(c)]
    k = len(clips)
    parts = []
    for i in range(k):
        parts.append(f"[{i}:v]trim=0:{cl},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio="
                     f"increase,crop=1080:1920,fps=24,setsar=1,format=yuv420p[c{i}]")
    # xfade-Kette
    prev = "c0"
    for i in range(1, k):
        off = round(i * cl - i * DISSOLVE, 3)
        tag = f"x{i}" if i < k - 1 else "m"
        parts.append(f"[{prev}][c{i}]xfade=transition=fade:duration={DISSOLVE}:offset={off}[{tag}]")
        prev = tag
    parts.append(f"[m]{GRADE},format=yuv420p[out]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[out]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", str(out)], check=True, timeout=600)


def compose_final(montage, cards, endcard_png, music, out, foot_len):
    """cards: Liste (png, s, e, fade_in). Overlay auf Montage, Dissolve in Schlusskarte, Musik loudnorm."""
    total = round(foot_len + END_LEN - END_XF, 3)
    ins = ["-i", str(montage)]
    for (png, *_r) in cards:
        ins += ["-loop", "1", "-t", str(foot_len), "-i", str(png)]
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
    parts.append("[vtext]format=yuv420p[vt]")
    parts.append(f"[{end_idx}:v]scale=1080:1920,setsar=1,fps=24,format=yuv420p[ve]")
    parts.append(f"[vt][ve]xfade=transition=fade:duration={END_XF}:offset={round(foot_len-END_XF,3)}[v]")
    parts.append(f"[{mus_idx}:a]atrim=0:{total},asetpts=PTS-STARTPTS,highpass=f=30,afftdn=nr=6,"
                 f"loudnorm=I=-14:TP=-1.5,afade=t=in:st=0:d=0.8,afade=t=out:st={round(total-2.0,3)}:d=2.0[a]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-t", str(total),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-b:v", "15M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", str(out)],
                   check=True, timeout=600)
    return total


def produce(name, r):
    thoughts = r["thoughts"]
    n = len(thoughts)
    # Standzeit-Fenster (weich ueberlappend)
    wins = []
    s = 0.0
    for i, t in enumerate(thoughts):
        st = standzeit(t)
        wins.append((s, round(s + st, 3)))
        s = round(s + st - OVERLAP, 3)
    foot_len = wins[-1][1]
    cl = round((foot_len + (len(r["clips"]) - 1) * DISSOLVE) / len(r["clips"]), 3)
    (OUT / f"{name}.caption.txt").write_text(r["caption"], encoding="utf-8")

    # 1) Footage
    clips_raw = []
    for i, cp in enumerate(r["clips"]):
        cr = OUT / f"{name}_clip{i}_raw.mp4"
        if cr.exists() and cr.stat().st_size > 100000:
            print(f"[{name}] 1/5 Clip {i} vorhanden", flush=True)
        else:
            print(f"[{name}] 1/5 Clip {i+1}/{len(r['clips'])} (Veo) ...", flush=True)
            veo_generate(cp, cr, duration=8)
        clips_raw.append(cr)
    # 2) Montage + Grade
    montage = OUT / f"{name}_montage.mp4"
    print(f"[{name}] 2/5 Montage + Grade + Korn ...", flush=True)
    compose_montage(clips_raw, cl, montage)
    # 3) Textkarten + Schlusskarte
    print(f"[{name}] 3/5 Textkarten (Fraunces) ...", flush=True)
    cards = []
    for i, t in enumerate(thoughts):
        png = OUT / f"{name}_card{i}.png"
        render_card(r["kicker"] if i == 0 else "", t, png, hook=(i == 0))
        s0, e0 = wins[i]
        cards.append((png, s0, e0, HOOK_IN if i == 0 else FADE_IN))
    endcard = OUT / f"{name}_end.png"
    render_endcard(r["endcard_term"], r["cta"], endcard)
    # 4) Musik
    mus = OUT / f"{name}_music.mp3"
    if not mus.exists() or mus.stat().st_size < 10000:
        print(f"[{name}] 4/5 Musik (Suno) ...", flush=True)
        gen_music(r["music"], mus)
    else:
        print(f"[{name}] 4/5 Musik vorhanden", flush=True)
    # 5) Final
    print(f"[{name}] 5/5 Compose final ...", flush=True)
    fin = OUT / f"{name}.mp4"
    dur = compose_final(montage, cards, endcard, mus, fin, foot_len)
    # Laengen-Check (§0)
    verdict = "OK"
    if dur > 28.0:
        verdict = f"FAIL hart ({dur:.1f}s > 28s)"
    elif dur > 27.0:
        verdict = f"WARN weich ({dur:.1f}s > 27s)"
    elif dur < 18.0:
        verdict = f"WARN kurz ({dur:.1f}s < 18s)"
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
