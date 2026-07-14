"""
Cineastisches DC-Story-Reel: echtes KI-Footage (Veo 3.1) + kinetische Text-Beats,
die eine Aussage aufbauen (Haken -> Problem -> Wende), + gebrandete Schluss-Karte
als Pointe + Musik. Kein bewegtes Wallpaper mit stehender Caption, sondern ein
Spannungsbogen.

Baut EIN Reel:  python3 build_video_reel.py <name>
Footage wird gecacht (assets/video_reels/<name>_raw.mp4); erneuter Lauf spart Veo-Credits.
Postet NICHT (nur Erzeugung zur Freigabe).
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

# Timing: Normal-Tempo = mehr Action/Punch (Slow-Mo wirkte zu weich).
FOOT_SRC = 8.0          # Quell-Laenge des Veo-Clips
SLOW = 1.0              # 1.0 = Echtzeit-Action; >1 waere Slow-Motion
FOOT_LEN = FOOT_SRC * SLOW
OUTRO_LEN = 3.6
TOTAL = FOOT_LEN + OUTRO_LEN
XF = 0.05               # sehr kurz = harter Schnitt (kein Weg-Bluren), Text bleibt durchgehend


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

REELS = {
    "dachdecker": {
        "clips": [
            ("Cinematic vertical 9:16, calm wide shot, a finished open timber roof truss structure (wooden rafters, "
             "Dachstuhl) newly built against a warm evening sky, no roof covering yet, still and cinematic, shallow "
             "depth of field, real, no on-screen text, no captions."),
            ("Cinematic vertical 9:16, a Swiss roofer in his early 30s on a pitched roof calmly hanging clay roof tiles onto the "
             "wooden battens working from the eave upward, NOT nailing, visible roofing underlay membrane and "
             "counter-battens and battens beneath the tiles, a safety scaffold with edge protection at the eave, the "
             "roofer wearing a safety harness, clean professional work, warm daylight, steady calm camera, real skin "
             "texture, no on-screen text, no captions."),
            ("Cinematic vertical 9:16, the same Swiss roofer in his early 30s taking a short break sitting on the roof, looking at his "
             "smartphone, calm and relaxed, warm light, shallow depth of field, real skin texture, no on-screen "
             "text, no captions."),
        ],
        "hook": ("Zimmermann ist fertig.", "Wer deckt das Dach?"),
        "beats": ["Gute Dachdecker?|Monatelang ausgebucht.", "Die Besten erreichst|du nur online."],
        "outro_hl": "Sichtbar sein,|bevor es eng wird.",
        "outro_cta": "Schreib uns START",
        "music": "modern cinematic corporate, confident and warm, gentle steady beat, uplifting and motivating, smooth, not aggressive, no vocals",
        "caption": ("Der Zimmermann ist fertig, aber wer deckt das Dach? Gute Dachdecker sind monatelang ausgebucht. "
                    "Die Besten suchen nicht aktiv, man erreicht sie online. Wir machen dich als Arbeitgeber "
                    "sichtbar, bevor es eng wird.\n\n📍 Schweiz\n#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"),
    },
    "sanitaer": {
        "clips": [
            ("Cinematic vertical 9:16, calm shot, a raw building-shell installation shaft and riser zone (Rohbau), "
             "bare concrete walls, unfinished copper and plastic pipe stubs sticking out of the wall, no fixtures "
             "yet, cool site light, cinematic, shallow depth of field, real, no on-screen text, no captions."),
            ("Cinematic vertical 9:16, a Swiss plumber in his late 20s calmly and cleanly pressing a press-fitting pipe connection "
             "with a modern electric pressing tool, the press jaw closing around a metal fitting (Optipress/Mapress "
             "style), precise focused work, no wrench, warm site light, steady camera, real skin texture, no "
             "on-screen text, no captions."),
            ("Cinematic vertical 9:16, the same Swiss plumber in his late 20s taking a short break on the construction site, looking "
             "at his smartphone, calm and relaxed, warm light, shallow depth of field, real skin texture, no "
             "on-screen text, no captions."),
        ],
        "hook": ("Rohbau steht.", "Wer macht die Installation?"),
        "beats": ["Gute Sanitäre?|Monatelang ausgebucht.", "Die Besten erreichst|du nur online."],
        "outro_hl": "Wir holen sie|dort ab.",
        "outro_cta": "Jetzt sichtbar werden",
        "music": "modern cinematic corporate, confident and warm, gentle steady beat, uplifting and motivating, smooth, not aggressive, no vocals",
        "caption": ("Der Rohbau steht, aber wer macht die Installation? Gute Sanitäre sind monatelang ausgebucht. "
                    "Die Besten suchen nicht aktiv, man erreicht sie online. Wir machen dich als Arbeitgeber "
                    "sichtbar.\n\n📍 Schweiz\n#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"),
    },
    "mechaniker": {
        "prompt": ("Cinematic vertical 9:16 video, a Swiss car mechanic in his early 30s in a clean modern garage, "
                   "focused, working on a car engine with a tool, soft natural window light from the side, shallow "
                   "depth of field, subtle slow camera push-in, authentic documentary look, real skin texture, warm "
                   "neutral color grade, no on-screen text, no captions."),
        "beats": ["Kaum noch gute|Bewerbungen?", "Die Besten suchen|nicht aktiv.", "Aber sie scrollen|jeden Tag."],
        "outro_hl": "Wir holen sie|dort ab.",
        "outro_cta": "Schreib uns START",
        "music": "modern uplifting corporate background, light beat, motivating, subtle, no vocals",
        "caption": ("Die besten Fachkräfte schreiben keine Bewerbung. Sie sind offen, aber sie suchen nicht aktiv. "
                    "Man erreicht sie dort, wo sie täglich sind: auf Social Media. Genau das machen wir für dich.\n\n"
                    "📍 Schweiz\n#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"),
    },
    "baeckerin": {
        "prompt": ("Cinematic vertical 9:16 video, a Swiss baker in her 30s in a warm artisan bakery in the early "
                   "morning, pulling a tray of fresh golden bread from the oven, gentle steam rising, warm golden "
                   "light, shallow depth of field, slow cinematic camera move, authentic documentary style, real "
                   "skin texture, no on-screen text, no captions."),
        "beats": ["Gute Leute sind|schnell weg.", "Wie frisches Brot|am Morgen.", "Sichtbar sein,|bevor sie weg sind."],
        "outro_hl": "Zeig dich, bevor|es andere tun.",
        "outro_cta": "Schreib uns START",
        "music": "calm modern cinematic corporate background, soft piano and subtle strings, hopeful, no vocals",
        "caption": ("Gute Leute sind schnell vergriffen, wie frisches Brot am Morgen. Wer zuletzt sichtbar wird, "
                    "sucht mit halbem Team. Wir machen dich sichtbar, bevor es die anderen sind.\n\n"
                    "📍 Schweiz\n#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"),
    },
    "pflege": {
        "prompt": ("Cinematic vertical 9:16 video, a friendly Swiss female nurse in her 30s in a bright modern care "
                   "facility, warm genuine smile, helping and caring, soft daylight, shallow depth of field, gentle "
                   "handheld camera, authentic documentary style, real skin texture, warm color grade, no on-screen "
                   "text, no captions."),
        "beats": ["Pflegekräfte gesucht?", "Sie suchen nicht|zurück.", "Man erreicht sie|nach der Schicht."],
        "outro_hl": "Genau dort|holen wir sie.",
        "outro_cta": "Schreib uns START",
        "music": "calm modern cinematic corporate background, soft piano, warm, hopeful, no vocals",
        "caption": ("Pflegekräfte suchen nicht zurück. Man erreicht sie nach der Schicht, am Handy, dort wo sie "
                    "wirklich sind. Genau da machen wir dich als Arbeitgeber sichtbar.\n\n"
                    "📍 Schweiz\n#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"),
    },
}


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
    return (f"@font-face{{font-family:'Hanken';font-weight:800;src:url(data:font/ttf;base64,"
            f"{_b64(FONTS/'HankenGrotesk-ExtraBold.ttf')}) format('truetype');}}"
            f"@font-face{{font-family:'Hanken';font-weight:600;src:url(data:font/ttf;base64,"
            f"{_b64(FONTS/'HankenGrotesk-SemiBold.ttf')}) format('truetype');}}"
            f"@font-face{{font-family:'Hanken';font-weight:500;src:url(data:font/ttf;base64,"
            f"{_b64(FONTS/'HankenGrotesk-Medium.ttf')}) format('truetype');}}")


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
    l1, l2 = (headline.split("|") + [""])[:2]
    logo = _b64(HERE / "assets" / "rr" / "logo_icon_whitegold.png")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Hanken',sans-serif;}}
.topgrad{{position:absolute;left:0;right:0;top:0;height:240px;background:linear-gradient(to bottom,rgba(7,7,13,.7),rgba(7,7,13,0));}}
.botgrad{{position:absolute;left:0;right:0;bottom:0;height:58%;background:linear-gradient(to top,rgba(7,7,13,.97) 26%,rgba(7,7,13,.78) 58%,rgba(7,7,13,0));}}
.logo{{position:absolute;top:70px;left:72px;height:56px;}}
.wrap{{position:absolute;left:72px;right:72px;bottom:360px;}}
.bar{{width:88px;height:11px;background:#FFC000;border-radius:6px;margin-bottom:40px;}}
.h div{{font-weight:800;font-size:112px;line-height:1.0;letter-spacing:-1.5px;color:#f5f2ee;}}
.h div:last-child{{color:#FFC000;}}
.handle{{position:absolute;left:72px;bottom:120px;font-weight:500;font-size:34px;color:rgba(245,242,238,.6);}}
</style></head><body>
<div class="topgrad"></div><div class="botgrad"></div>
<div class="wrap"><div class="bar"></div><div class="h"><div>{l1}</div><div>{l2}</div></div></div>
<div class="handle">@digital_century_group</div>
</body></html>"""
    _shoot(html, out_png, transparent=True)


def render_hook(number, line, out_png):
    """Cold-Open-Hook: grosse Gold-Zeile + Satz, wird hart eingeschnitten.
    Schriftgroesse passt sich der Laenge an (Zahl gross, ganzer Satz kleiner)."""
    logo = _b64(HERE / "assets" / "rr" / "logo_icon_whitegold.png")
    nsize = 168 if len(number) <= 9 else 120 if len(number) <= 15 else 92
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Hanken',sans-serif;}}
.topgrad{{position:absolute;left:0;right:0;top:0;height:240px;background:linear-gradient(to bottom,rgba(7,7,13,.7),rgba(7,7,13,0));}}
.botgrad{{position:absolute;left:0;right:0;bottom:0;height:60%;background:linear-gradient(to top,rgba(7,7,13,.97) 26%,rgba(7,7,13,.8) 58%,rgba(7,7,13,0));}}
.logo{{position:absolute;top:70px;left:72px;height:56px;}}
.wrap{{position:absolute;left:72px;right:72px;bottom:360px;}}
.num{{font-weight:800;font-size:{nsize}px;line-height:.98;letter-spacing:-2px;color:#FFC000;}}
.line{{margin-top:26px;font-weight:800;font-size:96px;line-height:1.02;letter-spacing:-1.5px;color:#f5f2ee;}}
.handle{{position:absolute;left:72px;bottom:120px;font-weight:500;font-size:34px;color:rgba(245,242,238,.6);}}
</style></head><body>
<div class="topgrad"></div><div class="botgrad"></div>
<div class="wrap"><div class="num">{number}</div><div class="line">{line}</div></div>
<div class="handle">@digital_century_group</div>
</body></html>"""
    _shoot(html, out_png, transparent=True)


def render_outro(headline, cta, out_png):
    l1, l2 = (headline.split("|") + [""])[:2]
    logo = _b64(HERE / "assets" / "rr" / "logo_icon_whitegold.png")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{width:1080px;height:1920px;position:relative;font-family:'Hanken',sans-serif;background:#07070d;overflow:hidden;}}
.glow{{position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);width:1200px;height:1200px;background:radial-gradient(circle,rgba(255,192,0,.14),rgba(7,7,13,0) 62%);}}
.mid{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;padding:0 90px;}}
.logo{{height:104px;margin-bottom:70px;}}
.h div{{font-weight:800;font-size:104px;line-height:1.02;letter-spacing:-1.5px;color:#f5f2ee;}}
.h div:last-child{{color:#FFC000;}}
.cta{{display:inline-block;margin-top:66px;background:#FFC000;color:#07070d;font-weight:800;font-size:44px;
      padding:30px 58px;border-radius:60px;letter-spacing:.2px;}}
.handle{{position:absolute;left:0;right:0;bottom:150px;text-align:center;font-weight:600;font-size:40px;color:rgba(245,242,238,.72);}}
</style></head><body>
<div class="glow"></div>
<div class="mid">
  <img class="logo" src="data:image/png;base64,{logo}">
  <div class="h"><div>{l1}</div><div>{l2}</div></div>
  <div class="cta">{cta}</div>
</div>
<div class="handle">@digital_century_group</div>
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
    """overlay_specs: Liste von (png_pfad, start, ende, fade_in, fade_out)."""
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
        fi = max(din, 0.02)  # harter Cut = minimale Blende
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={s}:d={fi}:alpha=1,"
                     f"fade=t=out:st={round(e-dout, 3)}:d={dout}:alpha=1[b{i}]")
    chain = "[v0]"
    for i in range(n):
        nxt = f"[o{i}]" if i < n - 1 else "[vfoot_raw]"
        parts.append(f"{chain}[b{i}]overlay=0:0{nxt}")
        chain = nxt
    parts.append("[vfoot_raw]format=yuv420p[vfoot]")
    parts.append(f"[{outro_idx}:v]scale=1080:1920,setsar=1,fps=30,fade=t=in:st=0:d=0.4,format=yuv420p[vout]")
    parts.append("[vfoot][vout]concat=n=2:v=1:a=0[vall]")
    # Ton: Original-Footage-Ton (z.B. Nagelpistole) laut fuer den Punch am Hook,
    # darunter die Musik leiser, damit die Action knallt.
    atempo = round(1.0 / SLOW, 4)
    parts.append(f"[0:a]atrim=0:{FOOT_SRC},asetpts=PTS-STARTPTS,atempo={atempo},volume=2.4,"
                 f"afade=t=in:st=0:d=0.05,afade=t=out:st={FOOT_LEN-0.8}:d=0.8[fa]")
    parts.append(f"[{music_idx}:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,volume=0.5,"
                 f"afade=t=in:st=0:d=0.4,afade=t=out:st={TOTAL-1.2}:d=1.2[mus]")
    parts.append("[fa][mus]amix=inputs=2:duration=longest:normalize=0[a]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[vall]", "-map", "[a]", "-t", str(TOTAL),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True, timeout=300)


def compose_broll(clips, overlay_specs, outro_png, music, out):
    """B-Roll-Schnitt: je Text-Segment ein eigener Clip, harte Cuts auf den Beat-Grenzen.
    len(clips) muss len(overlay_specs) entsprechen (ein Shot pro Text-Segment)."""
    k = len(clips)
    seg = round(FOOT_LEN / k, 3)
    ins = []
    for c in clips:
        ins += ["-i", str(c)]
    for spec in overlay_specs:
        ins += ["-loop", "1", "-t", str(FOOT_LEN), "-i", str(spec[0])]
    ins += ["-loop", "1", "-t", str(OUTRO_LEN), "-i", str(outro_png), "-i", str(music),
            "-f", "lavfi", "-i", "color=c=white:s=1080x1920:d=0.2:r=30",
            "-f", "lavfi", "-i", "sine=frequency=68:duration=0.5"]
    n_ov = len(overlay_specs)
    ov_base = k
    outro_idx = k + n_ov
    music_idx = k + n_ov + 1
    parts = []
    for i in range(k):
        parts.append(f"[{i}:v]trim=0:{seg},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio="
                     "increase,crop=1080:1920,setsar=1,fps=30[c%d]" % i)
    parts.append("".join(f"[c{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0[vbase]")
    for j, (_p, s, e, din, dout) in enumerate(overlay_specs):
        idx = ov_base + j
        fi = max(din, 0.02)
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={s}:d={fi}:alpha=1,"
                     f"fade=t=out:st={round(e-dout, 3)}:d={dout}:alpha=1[b{j}]")
    chain = "[vbase]"
    for j in range(n_ov):
        nxt = f"[o{j}]" if j < n_ov - 1 else "[vfoot_raw]"
        parts.append(f"{chain}[b{j}]overlay=0:0{nxt}")
        chain = nxt
    parts.append("[vfoot_raw]format=yuv420p[vfoot]")
    parts.append(f"[{outro_idx}:v]scale=1080:1920,setsar=1,fps=30,fade=t=in:st=0:d=0.4,format=yuv420p[vout]")
    parts.append("[vfoot][vout]concat=n=2:v=1:a=0[vall]")
    # EINSCHLAG am Hook: kurzer Kamera-Impact (leicht reinzoomen + wackeln, klingt in
    # ~0.3s aus) + weisser Blitz + tiefer Impact-Sound in der ersten Sekunde.
    flash_idx = music_idx + 1
    thump_idx = music_idx + 2
    parts.append("[vall]scale=1180:2098,crop=1080:1920:"
                 "x='(iw-ow)/2 + 26*sin(t*90)*exp(-t*13)':"
                 "y='(ih-oh)/2 + 20*cos(t*82)*exp(-t*13)',setsar=1[vshk]")
    parts.append(f"[{flash_idx}:v]format=rgba,fade=t=out:st=0:d=0.14:alpha=1[flash]")
    parts.append("[vshk][flash]overlay=0:0:eof_action=pass[vfinal]")
    # Nur unsere Musik als Ton (KI-Clip-Eigenton wird nicht gemischt), plus Impact-Boom.
    parts.append(f"[{music_idx}:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,volume=0.85,"
                 f"afade=t=in:st=0:d=0.5,afade=t=out:st={TOTAL-1.2}:d=1.2[amus]")
    parts.append(f"[{thump_idx}:a]volume=6,afade=t=out:st=0:d=0.3[thmp]")
    parts.append("[amus][thmp]amix=inputs=2:duration=first:normalize=0[a]")
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc,
                    "-map", "[vfinal]", "-map", "[a]", "-t", str(TOTAL),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True, timeout=300)


def produce(name, r):
    # Anzeigedauer: B-Roll pro Text-Segment ~seg_len Sek (gut lesbar), sonst 8s-Clip.
    global FOOT_LEN, TOTAL
    if r.get("clips"):
        seg_len = r.get("seg_len", 3.5)
        FOOT_LEN = round(seg_len * ((1 if r.get("hook") else 0) + len(r["beats"])), 2)
    else:
        FOOT_LEN = FOOT_SRC * SLOW
    TOTAL = FOOT_LEN + OUTRO_LEN
    raw = OUT / f"{name}_raw.mp4"; mus = OUT / f"{name}_music.mp3"; outro = OUT / f"{name}_outro.png"; fin = OUT / f"{name}.mp4"
    (OUT / f"{name}.caption.txt").write_text(r["caption"], encoding="utf-8")
    clips_raw = []
    if r.get("clips"):
        for i, cp in enumerate(r["clips"]):
            cr = OUT / f"{name}_clip{i}_raw.mp4"
            if cr.exists() and cr.stat().st_size > 100000:
                print(f"[{name}] 1/4 Clip {i} vorhanden", flush=True)
            else:
                print(f"[{name}] 1/4 Clip {i}/{len(r['clips'])} (Veo) ...", flush=True)
                veo_generate(cp, cr, duration=4)
            clips_raw.append(cr)
    elif raw.exists() and raw.stat().st_size > 100000:
        print(f"[{name}] 1/4 Video vorhanden, Veo uebersprungen", flush=True)
    else:
        print(f"[{name}] 1/4 Video (Veo) ...", flush=True)
        veo_generate(r["prompt"], raw)
    print(f"[{name}] 2/4 Hook + Beats + Outro rendern ...", flush=True)
    has_hook = bool(r.get("hook"))
    wins = make_windows(has_hook, len(r["beats"]))
    specs = []
    wi = 0
    if has_hook:
        hp = OUT / f"{name}_hook.png"; render_hook(r["hook"][0], r["hook"][1], hp)
        specs.append((hp, *wins[0])); wi = 1
    for i, b in enumerate(r["beats"]):
        bp = OUT / f"{name}_beat{i}.png"; render_beat(b, bp)
        specs.append((bp, *wins[wi + i]))
    render_outro(r["outro_hl"], r["outro_cta"], outro)
    if not mus.exists() or mus.stat().st_size < 10000:
        print(f"[{name}] 3/4 Musik ...", flush=True)
        gen_music(r["music"], mus)
    else:
        print(f"[{name}] 3/4 Musik vorhanden, uebersprungen", flush=True)
    if r.get("clips"):
        print(f"[{name}] 4/4 Compose (B-Roll) ...", flush=True)
        compose_broll(clips_raw, specs, outro, mus, fin)
    else:
        print(f"[{name}] 4/4 Compose (Story) ...", flush=True)
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


def main():
    args = sys.argv[1:]
    if args and args[0] == "--pipeline":
        # Naechstes freigegebenes Konzept bauen, einplanen, nach built verschieben.
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
        data.setdefault("built", []).append({"name": name, "job": concept.get("job")})
        pf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"PIPELINE: {name} gebaut + fuer heute eingeplant, {len(data['approved'])} Konzepte verbleiben")
    else:
        name = args[0] if args else "dachdecker"
        produce(name, REELS[name])


if __name__ == "__main__":
    main()
