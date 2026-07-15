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


def pick(approved):
    """Waehlt das naechste Konzept: bevorzugt ein Gewinner-Thema aus learnings.json,
    sonst approved[0]. So wird die Produktion datenbasiert (entwickle dich weiter)."""
    lp = HERE / "learnings.json"
    if lp.exists():
        try:
            winners = json.loads(lp.read_text()).get("gewinner_themen", [])
            for w in winners:
                for cc in approved:
                    if cc.get("theme") == w:
                        print(f"Lern-Loop: waehle Gewinner-Thema '{w}'")
                        return cc
        except Exception:
            pass
    return approved[0]


def main():
    # 1) Erst lernen: echte Zahlen auswerten, learnings.json aktualisieren
    try:
        import learn_and_adapt
        learn_and_adapt.main()
    except Exception as e:
        print("Lern-Schritt uebersprungen:", e)
    pf = HERE / "reel_pipeline.json"
    data = json.loads(pf.read_text())
    approved = data.get("approved", [])
    if not approved:
        print("Pipeline leer, nichts zu tun.")
        return
    c = pick(approved)
    name = c["name"]
    print(f"=== BUILD {name} ===", flush=True)
    mp4 = bvr.produce(name, c)
    print(f"=== POST {name} ===", flush=True)
    mid, link = meta.post_reel(meta.ensure_public_url(str(mp4)), c["caption"])
    print(f"=== LIVE {name}: {mid} {link} ===", flush=True)
    # Pipeline + Ledger (das GEWAEHLTE Konzept entfernen, nicht zwingend approved[0])
    data["approved"] = [x for x in approved if x.get("name") != name]
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
