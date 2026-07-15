"""Autonomer Cloud-Lauf: baut das naechste approved-Konzept im Archivkino-Look und
postet es direkt nach @kopfundkompass. Aktualisiert reel_pipeline.json + used_reels.json.
Zugang aus Umgebung (GitHub-Secrets IG_USER_ID, IG_ACCESS_TOKEN, KIE_API_KEY).
Aufruf in reel.yml. Committen/Pushen der Ledger macht der Workflow."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_video_reel as bvr   # noqa: E402
import lib_meta as meta          # noqa: E402


def main():
    pf = HERE / "reel_pipeline.json"
    data = json.loads(pf.read_text())
    approved = data.get("approved", [])
    if not approved:
        print("Pipeline leer, nichts zu tun.")
        return
    c = approved[0]
    name = c["name"]
    print(f"=== BUILD {name} ===", flush=True)
    mp4 = bvr.produce(name, c)
    print(f"=== POST {name} ===", flush=True)
    mid, link = meta.post_reel(meta.ensure_public_url(str(mp4)), c["caption"])
    print(f"=== LIVE {name}: {mid} {link} ===", flush=True)
    # Pipeline + Ledger
    data["approved"] = approved[1:]
    data.setdefault("built", []).append({"name": name, "theme": c.get("theme"), "permalink": link})
    pf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ur = HERE / "used_reels.json"
    u = json.loads(ur.read_text())
    u.setdefault("used_topics", []).append(c.get("theme"))
    u.setdefault("used_hooks", []).append(c["thoughts"][0])
    ur.write_text(json.dumps(u, ensure_ascii=False, indent=2))
    print(f"OK, {len(data['approved'])} Konzepte verbleiben.", flush=True)


if __name__ == "__main__":
    main()
