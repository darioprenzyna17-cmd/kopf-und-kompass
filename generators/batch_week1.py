"""Generiert die 5 fehlenden Carousels für Woche 1 sequenziell."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_carousel import main as gen

WEEK_1_BATCH = [
    (
        "w1-d2-komfort",
        [
            "Komfort tötet leise. Hier sind 5 Beweise.",
            "Du nimmst zu, ohne es zu merken.",
            "Du wirst gereizt, ohne Grund.",
            "Du verlierst Respekt vor dir selbst — leise, jeden Tag.",
            "Speicher das. Lies's am Sonntagabend nochmal.",
        ],
    ),
    (
        "w1-d3-potenzial",
        [
            "In 10 Jahren bist du genau hier.",
            "Selbe Wohnung. Selbe Frau, die dich nicht mehr ernst nimmt.",
            "Selber Job, der dich langsam tötet.",
            "Nur dicker. Müder. Gebrochener.",
            "Schick das einem, der's lesen muss.",
        ],
    ),
    (
        "w1-d4-vater-sohn",
        [
            "Dein Vater wäre nicht stolz.",
            "Aber er hat's auch nie geschafft, der Mann zu werden, den du brauchst.",
            "Du wirst zu dem Mann, dem du als Kind nicht vertraut hast.",
            "Wenn du nichts änderst, gibst du das weiter.",
            "Was bricht die Kette? Schreib's in die DM.",
        ],
    ),
    (
        "w1-d5-frame-shift",
        [
            "Disziplin ist nicht das Problem.",
            "Optionen sind das Problem.",
            "Du brauchst nicht mehr Willenskraft.",
            "Du brauchst weniger Wege ins Versagen.",
            "Streich Optionen. Reduzier Friction.",
        ],
    ),
    (
        "w1-d6-quiet-power",
        [
            "Der gefährlichste Mann ist nicht der lauteste.",
            "Er ist der Ruhige.",
            "Der, der nichts beweisen muss.",
            "Weil er weiß, was er ist.",
            "Sei unmöglich zu ignorieren. Sag wenig.",
        ],
    ),
]


def main():
    for i, (slug, slides) in enumerate(WEEK_1_BATCH, 1):
        print(f"\n{'=' * 60}")
        print(f"=== {i}/{len(WEEK_1_BATCH)}: {slug} ===")
        print(f"{'=' * 60}")
        try:
            gen(slug, slides)
        except Exception as e:
            print(f"❌ FEHLER bei {slug}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
