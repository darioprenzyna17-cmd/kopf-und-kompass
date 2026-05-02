"""
Generiert ein 5-Slide-Carousel im horyzen-Style.

Pipeline:
1. NanoBanana Pro generiert 5 cinematische Hintergrund-Bilder (4:5)
2. PIL legt deutschen Text als Overlay drauf
3. Speichert lokal in assets/carousels/<slug>/slide-1.png … slide-5.png

Verwendung:
    python3 gen_carousel.py <slug> <hook> "<slide2>" "<slide3>" "<slide4>" "<slide5>"

Beispiel:
    python3 gen_carousel.py montagsluege-w1d1 \\
        "Du hast gestern wieder 'ab Montag' gesagt." \\
        "Der Mann, der ab Montag startet — er existiert nicht." \\
        "Er ist die Geschichte, die du dir heute erzählst." \\
        "Damit du heute nicht starten musst." \\
        "Schreib MONTAG in die DM, wenn du raus willst."
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIE_BASE = "https://api.kie.ai/api/v1/jobs"

# kie.ai key aus dem bundle .env (zentral gespeichert)
def load_kie_key():
    env_path = Path("/Users/dario/Desktop/mindset-agents-bundle/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("KIE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("KIE_API_KEY nicht in bundle .env gefunden")


KIE_KEY = load_kie_key()
HEADERS = {
    "Authorization": f"Bearer {KIE_KEY}",
    "Content-Type": "application/json",
}
DOWNLOAD_HEADERS = {"User-Agent": "Mozilla/5.0"}


# Stil-Briefs für jede Slide-Position (variiert für visuelles Interesse)
SLIDE_BRIEFS = [
    "Cinematic dark moody photograph, ultra-shallow depth of field, monochromatic deep blue-grey tones with single warm orange highlight, slow morning fog over an empty German city street at dawn, no people, no text, atmospheric, magazine-cover quality, 4:5 vertical, dramatic lighting, raw photographic style",
    "Cinematic dark moody photograph, monochromatic deep blue-grey, lone empty wooden writing desk in a dim study with one brass lamp, leather-bound books, no people, no text, melancholic atmosphere, 4:5 vertical, shallow depth of field, raw photographic style",
    "Cinematic dark moody photograph, monochromatic deep blue-grey, rain on a window of a moving train at night, blurred city lights, no people, no text, lonely atmosphere, 4:5 vertical, shallow depth of field, raw photographic style",
    "Cinematic dark moody photograph, monochromatic deep blue-grey with single warm highlight, shadows of a tall man's silhouette walking through long empty hallway at twilight, no faces visible, no text, ominous atmosphere, 4:5 vertical, shallow depth of field, raw photographic style",
    "Cinematic dark moody photograph, monochromatic deep blue-grey, close-up of a closed worn leather notebook with a pen on a dark wooden desk, single hard side light, no people, no text, contemplative atmosphere, 4:5 vertical, raw photographic style",
]


def post_json(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=HEADERS, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def submit_image(prompt, idx):
    body = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "aspect_ratio": "4:5",
            "resolution": "2K",
        },
    }
    resp = post_json(f"{KIE_BASE}/createTask", body)
    if resp.get("code") != 200:
        raise RuntimeError(f"createTask {idx} failed: {resp}")
    return resp["data"]["taskId"]


def extract_image_url(data):
    rj = data.get("resultJson")
    if isinstance(rj, str):
        try:
            rj = json.loads(rj)
        except Exception:
            rj = {}
    rj = rj or {}
    for k in ("resultUrls", "imageUrls", "urls", "images"):
        v = rj.get(k)
        if v:
            return v[0] if isinstance(v, list) else v
    return None


def poll(task_id, label, timeout=300):
    start = time.time()
    last = None
    while time.time() - start < timeout:
        resp = get_json(f"{KIE_BASE}/recordInfo?taskId={urllib.parse.quote(task_id)}")
        data = resp.get("data") or {}
        state = data.get("state")
        if state != last:
            print(f"      [{label}] +{int(time.time() - start)}s state={state}", flush=True)
            last = state
        if state == "success":
            url = extract_image_url(data)
            if not url:
                raise RuntimeError(f"success but no URL: {json.dumps(data)[:400]}")
            return url
        if state == "fail":
            raise RuntimeError(f"task {task_id} failed: {data.get('failMsg') or data}")
        time.sleep(4)
    raise TimeoutError(f"task {task_id} timed out")


def download(url, dest):
    req = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)
    with urllib.request.urlopen(req, timeout=180) as r:
        dest.write_bytes(r.read())


PLAYFAIR = ROOT / "assets" / "fonts" / "PlayfairDisplay.ttf"
INTER = ROOT / "assets" / "fonts" / "Inter.ttf"

# Variable-Font-Achsen-Setting für Gewicht
def _font(path, size, weight):
    """Lädt Variable Font mit konkreter Gewichts-Achse."""
    from PIL import ImageFont
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def add_text_overlay(image_path, text, slide_index):
    """Legt deutschen Text gemäß BRAND.md als Overlay auf das Bild."""
    from PIL import Image, ImageDraw

    img = Image.open(image_path).convert("RGB")
    W, H = img.size

    # Vignette für Legibility — dunkler an den Rändern + leicht in Mitte
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        # Stärker am Rand, leichter in der Mitte
        edge_dist = abs(y - H / 2) / (H / 2)
        alpha = int(60 + 40 * edge_dist)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Brand-Spec laut BRAND.md
    if slide_index == 0:
        # Hook — Playfair Black 900
        font_path, weight, divisor = PLAYFAIR, 900, 14
    elif slide_index == 4:
        # CTA — Inter Bold 700
        font_path, weight, divisor = INTER, 700, 19
    else:
        # Body — Playfair SemiBold 600
        font_path, weight, divisor = PLAYFAIR, 600, 18

    font_size = max(50, W // divisor)
    font = _font(font_path, font_size, weight)

    # Word wrap auf 82% Breite
    draw = ImageDraw.Draw(img)
    max_width = int(W * 0.82)
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))

    # Vertikal zentriert
    line_height = int(font_size * 1.20)
    total_h = line_height * len(lines)
    start_y = (H - total_h) // 2

    primary = (245, 240, 230)  # text/primary aus BRAND.md
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        y = start_y + i * line_height
        # 4-fach soft shadow für Legibility
        for dx, dy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=primary)

    # Brand-Mark unten rechts — Inter Medium 500
    brand_font = _font(INTER, max(22, W // 50), 500)
    brand = "@montagsluege"
    bb = draw.textbbox((0, 0), brand, font=brand_font)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((W - bw - 28, H - bh - 28), brand, font=brand_font, fill=(200, 195, 180))

    img.save(image_path, "PNG", quality=92)


def main(slug, slide_texts):
    if len(slide_texts) != 5:
        raise ValueError(f"5 Slide-Texte nötig, {len(slide_texts)} gegeben")

    out_dir = ROOT / "assets" / "carousels" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Generiere Carousel: {slug} ===")
    print(f"  Output: {out_dir}\n")

    # Submit alle 5 Bilder parallel
    print("  → Submitting 5 Bilder bei NanoBanana Pro …")
    task_ids = []
    for i, brief in enumerate(SLIDE_BRIEFS):
        tid = submit_image(brief, i + 1)
        task_ids.append((i, tid))
        print(f"    [{i+1}/5] task: {tid}")

    print("\n  → Polling auf alle 5 …")
    image_urls = [None] * 5

    def fetch(idx, tid):
        return idx, poll(tid, f"slide-{idx+1}")

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fetch, i, t): i for i, t in task_ids}
        for fut in as_completed(futures):
            idx, url = fut.result()
            image_urls[idx] = url

    print("\n  → Download + Text-Overlay …")
    for i, url in enumerate(image_urls):
        base = out_dir / f"slide-{i+1}-base.png"
        dest = out_dir / f"slide-{i+1}.png"
        download(url, base)
        # Kopie für Overlay (Original bleibt unangetastet, damit re-render gratis)
        from shutil import copyfile
        copyfile(base, dest)
        add_text_overlay(dest, slide_texts[i], i)
        print(f"    ✓ slide-{i+1}.png ({dest.stat().st_size // 1024} KB)")

    print(f"\n✅ Carousel fertig: {out_dir}")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:7])
