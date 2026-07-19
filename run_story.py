"""
Kopf & Kompass — taeglicher Story-Post.
Sorgt dafuer, dass IMMER mind. eine Story aktiv ist (Stories laufen nach 24 h ab).
Waehlt den naechsten unbenutzten Impuls (Rotation, Ledger gegen Dubletten),
nutzt vorgerenderte, committete Kacheln (assets/stories/daily/) -> kein Chrome in CI.

  python3 run_story.py              # posten (nutzt committete Kachel)
  python3 run_story.py --dry        # nur pruefen, nicht posten
  python3 run_story.py --render-all # alle Kacheln lokal rendern (Chrome, zum Committen)
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path

HERE = Path(__file__).parent
LEDGER = HERE / "story_ledger.json"
STORIES_DIR = HERE / "assets" / "stories" / "daily"

# Eigenstaendige Impulse im Archivkino-Ton: tiefe Ein-Satz-Wahrheiten, Du, ruhig.
# "|" trennt Zeilen, "*" am Zeilenanfang = Petrol-Akzentzeile (kursiv).
BANK = [
    "Du bist nicht zu viel.|*Du warst nur zu lange leise.",
    "Ruhe ist keine Schwäche.|*Sie ist Kontrolle.",
    "Disziplin ist Selbstachtung,|*in Handlung übersetzt.",
    "Nicht jeder verdient|*eine Antwort von dir.",
    "Loslassen heisst nicht aufgeben.|*Es heisst Platz machen.",
    "Klarheit kommt nicht vor dem Mut.|*Sie kommt danach.",
    "Grenzen sind kein Streit.|*Sie sind Selbstschutz.",
    "Geduld ist nicht Warten.|*Es ist Vertrauen mit Ausdauer.",
    "Dein Wert sinkt nicht,|*weil jemand ihn nicht sieht.",
    "Stille Stärke braucht|*kein Publikum.",
    "Echtheit kostet dich Leute,|*die nie zu dir gehörten.",
    "Fokus ist,|*wozu du Nein sagst.",
    "Der Mut fehlt selten.|*Meist fehlt die Entscheidung.",
    "Du schuldest niemandem|*die Version, die er gewohnt ist.",
]


def tile_path(idx):
    return STORIES_DIR / f"story_{idx:02d}.png"


def load_env():
    envf = HERE / ".env"
    if not envf.exists():
        return
    for line in envf.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_ledger():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"used": [], "posted": []}


def pick(ledger):
    used = set(ledger.get("used", []))
    if len(used) >= len(BANK):
        used = set()
        ledger["used"] = []
    for i in range(len(BANK)):
        if i not in used:
            return i
    return 0


def render_all():
    """Rendert lokal alle Kacheln nach assets/stories/daily/ (Chrome noetig)."""
    import build_story as st
    STORIES_DIR.mkdir(parents=True, exist_ok=True)
    for i, quote in enumerate(BANK):
        st.story_gedanke(quote, str(tile_path(i)))
    print(f"{len(BANK)} Kacheln in {STORIES_DIR} gerendert.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--render-all", action="store_true")
    a = ap.parse_args()

    if a.render_all:
        render_all()
        return

    load_env()
    ledger = load_ledger()
    idx = pick(ledger)
    quote = BANK[idx]
    print(f"Story #{idx}: {quote.replace('|', ' / ').replace('*', '')}")

    tile = tile_path(idx)
    if not tile.exists():          # lokaler Fallback: fehlende Kachel just-in-time rendern
        import build_story as st
        STORIES_DIR.mkdir(parents=True, exist_ok=True)
        st.story_gedanke(quote, str(tile))

    if a.dry:
        print(f"DRY: nicht gepostet ({tile}).")
        return

    import lib_meta as meta
    url = meta.ensure_public_url(str(tile))
    media_id, permalink = meta.post_story(url, is_video=False)
    print(f"STORY LIVE: {media_id} {permalink}")

    ledger.setdefault("used", []).append(idx)
    ledger.setdefault("posted", []).append({
        "when": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "idx": idx, "quote": quote, "media_id": media_id, "permalink": permalink,
    })
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2))
    print("Ledger aktualisiert.")


if __name__ == "__main__":
    main()
