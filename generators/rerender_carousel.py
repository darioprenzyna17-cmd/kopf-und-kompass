"""
Re-rendert ein Carousel mit aktuellem BRAND.md ohne neue API-Kosten.

Voraussetzung: assets/carousels/<slug>/slide-N-base.png existieren (textfreie Originale).

Verwendung:
    python3 rerender_carousel.py <slug> <hook> "<s2>" "<s3>" "<s4>" "<cta>"
"""
import sys
from pathlib import Path
from shutil import copyfile

from gen_carousel import add_text_overlay

ROOT = Path(__file__).resolve().parent.parent


def main(slug, slide_texts):
    if len(slide_texts) != 5:
        raise ValueError(f"5 Slide-Texte nötig, {len(slide_texts)} gegeben")

    out_dir = ROOT / "assets" / "carousels" / slug
    if not out_dir.exists():
        raise RuntimeError(f"Slug '{slug}' existiert nicht in assets/carousels/")

    print(f"=== Re-render: {slug} ===")
    for i, text in enumerate(slide_texts):
        base = out_dir / f"slide-{i+1}-base.png"
        dest = out_dir / f"slide-{i+1}.png"
        if not base.exists():
            print(f"  ⚠️  slide-{i+1}-base.png fehlt — skip")
            continue
        copyfile(base, dest)
        add_text_overlay(dest, text, i)
        print(f"  ✓ slide-{i+1}.png aktualisiert")

    print(f"\n✅ Re-render fertig: {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:7])
