"""
Generiert ein 15s-Reel im horyzen-Style.

Pipeline (V1, Seedance native German audio):
1. Seedance 2 generiert Video + deutsches Voice-Over in einem Pass
2. Speichert lokal in assets/reels/<slug>/reel.mp4

Verwendung:
    python3 gen_reel.py <slug> "<voice_over_text_de>"

Beispiel:
    python3 gen_reel.py test-w1d7 "Du bist nicht müde. Du bist feige."

Wenn die deutsche Voice-Qualität von Seedance nicht passt, fallen wir später
auf macOS `say` + ffmpeg-Compositing zurück (gen_reel_v2.py).
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIE_BASE = "https://api.kie.ai/api/v1/jobs"


def load_kie_key():
    env_path = Path("/Users/dario/Desktop/mindset-agents-bundle/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("KIE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("KIE_API_KEY nicht in bundle .env")


KIE_KEY = load_kie_key()
HEADERS = {
    "Authorization": f"Bearer {KIE_KEY}",
    "Content-Type": "application/json",
}
DOWNLOAD_HEADERS = {"User-Agent": "Mozilla/5.0"}


B_ROLL_BRIEF = """A cinematic 15-second slow-motion sequence in deep monochromatic dark blue-grey with subtle warm orange highlights. Atmospheric, melancholic, no people visible, no faces, no text. Deep film-grain look, magazine-cover quality, 9:16 vertical, professional cinematography.

Beat sequence:
- 0–3s: Slow camera push into an empty foggy German city street at dawn, single warm sodium streetlight, wet asphalt reflections, no cars
- 3–6s: Hard cut to a silent empty walnut writing desk in a dim study, single warm brass desk lamp pooling light on closed leather-bound books and a fountain pen
- 6–10s: Hard cut to heavy rain streaming down a moving train window at night, blurred neon city lights outside, melancholic
- 10–13s: Hard cut to a worn closed leather notebook with a fountain pen lying on dark wood, single hard side light, dust particles in the air
- 13–15s: Slow fade to deep black

Color grade: dark teal-blue shadows, deep blacks, muted single warm highlight, subtle film grain, anamorphic lens feel."""


VOICE_BRIEF = """Audio: A single calm grounded mid-30s German male voice speaking the following text slowly with deliberate pauses between sentences, like an older brother who is done being polite. Calm, low volume, restrained — pauses hit harder than volume. Slight rasp. No music, no other sound, no ambient effects, just clean voice on a quiet room tone.

The voice says, in German, with real pauses:

"{voice_text}"

Voice direction: native German pronunciation, slow pacing 130–150 wpm, deliberate. No accent. Studio-clean recording quality."""


def post_json(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers=HEADERS, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def submit(prompt):
    body = {
        "model": "bytedance/seedance-2",
        "input": {
            "prompt": prompt,
            "generate_audio": True,
            "resolution": "720p",
            "aspect_ratio": "9:16",
            "duration": 15,
        },
    }
    resp = post_json(f"{KIE_BASE}/createTask", body)
    if resp.get("code") != 200:
        raise RuntimeError(f"createTask failed: {resp}")
    return resp["data"]["taskId"]


def extract_video_url(data):
    rj = data.get("resultJson")
    if isinstance(rj, str):
        try:
            rj = json.loads(rj)
        except Exception:
            rj = {}
    rj = rj or {}
    for k in ("videoUrl", "video_url", "resultUrls", "urls", "videoUrls", "videos"):
        v = rj.get(k)
        if v:
            return v if isinstance(v, str) else v[0]
    return None


def poll(task_id, label, timeout=900):
    start = time.time()
    last = None
    while time.time() - start < timeout:
        resp = get_json(f"{KIE_BASE}/recordInfo?taskId={urllib.parse.quote(task_id)}")
        data = resp.get("data") or {}
        state = data.get("state")
        if state != last:
            print(f"  [{label}] +{int(time.time() - start)}s state={state}", flush=True)
            last = state
        if state == "success":
            url = extract_video_url(data)
            if not url:
                raise RuntimeError(f"success but no URL: {json.dumps(data)[:400]}")
            return url
        if state == "fail":
            raise RuntimeError(f"task failed: {data.get('failMsg') or data}")
        time.sleep(8)
    raise TimeoutError(f"task {task_id} timed out")


def download(url, dest):
    req = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def main(slug, voice_text):
    out_dir = ROOT / "assets" / "reels" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "reel.mp4"

    print(f"=== Generiere Reel: {slug} ===")
    print(f"  Output: {dest}")
    print(f"  Voice (DE): \"{voice_text}\"\n")

    full_prompt = B_ROLL_BRIEF + "\n\n" + VOICE_BRIEF.format(voice_text=voice_text)

    print("  → Submitting bei Seedance 2 …")
    tid = submit(full_prompt)
    print(f"    task: {tid}")

    print("\n  → Polling (Generierung 4–8 Min üblich) …")
    url = poll(tid, "reel")
    print(f"\n  → Download von: {url}")
    download(url, dest)
    print(f"\n✅ Reel fertig: {dest} ({dest.stat().st_size // 1024} KB)")
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
