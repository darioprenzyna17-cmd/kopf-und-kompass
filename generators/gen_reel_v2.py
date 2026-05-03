"""
V2: Re-baut ein Reel mit deutscher Stimme + Untertiteln (PIL + ffmpeg overlay).

Pipeline (umgeht fehlenden drawtext-Filter):
1. Bestehende B-Roll, Audio strippen
2. Deutsche Stimme via macOS `say` (Voice: Reed)
3. Text-Overlays als transparente PNGs via PIL rendern:
   - Hook (Playfair Black) — erste 2.5s
   - Subtitles (Inter Bold) — pro Satz
   - Brand-Mark (Inter Medium) — dauerhaft
4. ffmpeg overlay-Filter compositiert alles

Verwendung:
    python3 gen_reel_v2.py <slug> "<satz1>" "<satz2>" ...
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYFAIR = ROOT / "assets" / "fonts" / "PlayfairDisplay.ttf"
INTER = ROOT / "assets" / "fonts" / "Inter.ttf"

GERMAN_VOICE = "Reed"
SAY_RATE = 165


def run(cmd, **kwargs):
    res = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if res.returncode != 0:
        err = res.stderr
        for marker in ["Error", "error", "Invalid"]:
            idx = err.find(marker)
            if idx > 0:
                err = err[idx:]
                break
        raise RuntimeError(f"Command failed:\n  cmd: {' '.join(str(c) for c in cmd[:6])}…\n  stderr: {err[:600]}")
    return res.stdout


def get_duration(media_path):
    out = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(media_path),
    ])
    return float(out.strip())


def estimate_duration(sentence, wpm=SAY_RATE):
    return max(1.2, len(sentence.split()) / wpm * 60 + 0.4)


def render_text_png(text, font_path, font_size, weight, max_width_px,
                    output_path, color=(245, 240, 230), shadow=True):
    """Rendert Text als transparenten PNG mit Word-Wrap, Schatten."""
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(str(font_path), font_size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass

    # Dummy-Draw für Text-Bbox
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dummy)

    # Word-Wrap
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        bbox = dd.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))

    # Image-Größe berechnen
    line_height = int(font_size * 1.2)
    img_h = line_height * len(lines) + 20
    img_w = max_width_px + 40

    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (img_w - line_w) // 2
        y = i * line_height + 10
        # Schatten (4-fach soft)
        if shadow:
            for dx, dy in [(2, 2), (-2, 2), (2, -2), (-2, -2), (3, 3), (-3, 3)]:
                draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=color + (255,))

    img.save(output_path, "PNG")
    return img_w, img_h


def main(slug, sentences):
    if len(sentences) < 2:
        raise ValueError("Mindestens 2 Sätze")

    out_dir = ROOT / "assets" / "reels" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    base_video = out_dir / "reel.mp4"
    if not base_video.exists():
        raise RuntimeError(f"B-Roll fehlt: {base_video}")

    silent = out_dir / "_silent.mp4"
    voice_aiff = out_dir / "_voice.aiff"
    voice_wav = out_dir / "_voice.wav"
    final = out_dir / "reel_v2.mp4"
    overlay_dir = out_dir / "_overlays"
    overlay_dir.mkdir(exist_ok=True)

    print(f"=== Reel V2: {slug} ===")
    print(f"  Voice: {GERMAN_VOICE}, Rate: {SAY_RATE} WPM\n")

    # 1. Audio strippen
    print("[1/5] Audio strippen …")
    run(["ffmpeg", "-y", "-i", str(base_video),
         "-c:v", "copy", "-an", str(silent)])

    # 2. Deutsche Stimme
    print("[2/5] Stimme generieren (say) …")
    full_text = " ".join(sentences)
    run(["say", "-v", GERMAN_VOICE, "-r", str(SAY_RATE),
         "-o", str(voice_aiff), full_text])
    run(["ffmpeg", "-y", "-i", str(voice_aiff),
         "-acodec", "pcm_s16le", "-ar", "44100", str(voice_wav)])

    voice_dur = get_duration(voice_aiff)
    video_dur = get_duration(silent)
    print(f"  voice: {voice_dur:.1f}s | video: {video_dur:.1f}s")

    # 3. Text-PNGs rendern
    print("\n[3/5] Text-Overlays rendern (PIL) …")
    # Annahme: 720×1280 9:16
    VIDEO_W, VIDEO_H = 720, 1280

    hook_text = sentences[0].upper()
    hook_png = overlay_dir / "hook.png"
    render_text_png(hook_text, PLAYFAIR, 56, 900, int(VIDEO_W * 0.85),
                    hook_png, color=(245, 240, 230))
    print(f"  hook.png ({hook_png.stat().st_size // 1024} KB)")

    sub_pngs = []
    for i, sent in enumerate(sentences):
        sp = overlay_dir / f"sub-{i+1}.png"
        render_text_png(sent.upper(), INTER, 36, 700, int(VIDEO_W * 0.82),
                        sp, color=(245, 240, 230))
        sub_pngs.append(sp)
    print(f"  {len(sub_pngs)} subtitles")

    brand_png = overlay_dir / "brand.png"
    render_text_png("@montagsluege", INTER, 22, 500, int(VIDEO_W * 0.5),
                    brand_png, color=(200, 195, 180), shadow=False)

    # 4. Subtitle-Timing
    raw = [estimate_duration(s) for s in sentences]
    pause = 0.15
    total_raw = sum(raw) + pause * (len(sentences) - 1)
    factor = (voice_dur - 0.3) / total_raw

    timings = []
    t = 0.3
    for d in raw:
        scaled = d * factor
        timings.append((t, t + scaled))
        t += scaled + pause

    # 5. ffmpeg overlay chain
    print("\n[4/5] ffmpeg compositing …")
    target_dur = max(voice_dur + 0.5, video_dur)

    # Build inputs
    inputs = [
        "-stream_loop", "-1", "-i", str(silent),     # 0
        "-i", str(voice_wav),                          # 1
        "-i", str(hook_png),                           # 2
    ]
    for sp in sub_pngs:
        inputs += ["-i", str(sp)]
    # brand index = 3 + len(sub_pngs)
    inputs += ["-i", str(brand_png)]
    brand_idx = 3 + len(sub_pngs)

    # Filter complex
    parts = []
    # Hook overlay (input 2)
    parts.append(
        f"[0:v][2:v]overlay=x=(W-w)/2:y=H*0.18:"
        f"enable='between(t,0.3,2.5)'[v1]"
    )
    # Subtitle overlays
    last = "v1"
    for i, (start, end) in enumerate(timings):
        sub_idx = 3 + i
        next_label = f"v{i+2}"
        parts.append(
            f"[{last}][{sub_idx}:v]overlay=x=(W-w)/2:y=H-h-180:"
            f"enable='between(t,{start:.2f},{end:.2f})'[{next_label}]"
        )
        last = next_label
    # Brand mark immer
    parts.append(
        f"[{last}][{brand_idx}:v]overlay=x=W-w-28:y=H-h-28[vfinal]"
    )

    filter_complex = ";".join(parts)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vfinal]", "-map", "1:a",
        "-t", f"{target_dur:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(final),
    ]
    run(cmd)

    # Cleanup
    print("\n[5/5] Cleanup …")
    for tmp in [silent, voice_aiff, voice_wav]:
        if tmp.exists():
            tmp.unlink()
    # Overlays werden behalten (für debug / re-run)

    print(f"\n✅ Reel V2 fertig: {final} ({final.stat().st_size // 1024} KB)")
    return final


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
