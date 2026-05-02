"""Baut queue.jsonl für Woche 1 mit proper JSON-Escaping."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/darioprenzyna17-cmd/montagsluege-autopilot/main"


def carousel_urls(slug):
    return [f"{RAW}/assets/carousels/{slug}/slide-{i}.png" for i in range(1, 6)]


def reel_url(slug):
    return f"{RAW}/assets/reels/{slug}/reel.mp4"


WEEK_1 = [
    {
        "date": "2026-05-03",
        "format": "reel",
        "pillar": "montagsluege",
        "video_url": reel_url("test-w1d7"),
        "caption": (
            "Du bist nicht müde. Du bist feige.\n\n"
            "Drei Jahre 'ab Montag'. Er kommt nicht. "
            "Du bist der Feigling, der du nie sein wolltest.\n\n"
            "Schreib MONTAG in die DM, wenn du raus willst.\n\n"
            "—\n#mindset #disziplin #stoiker #montagsluege #kalterwille"
        ),
    },
    {
        "date": "2026-05-04",
        "format": "carousel",
        "pillar": "montagsluege",
        "image_urls": carousel_urls("test-w1d1"),
        "caption": (
            "Du hast gestern wieder 'ab Montag' gesagt.\n\n"
            "Der Mann, der ab Montag startet — er existiert nicht. "
            "Er ist die Geschichte, die du dir heute erzählst, "
            "damit du jetzt nicht starten musst.\n\n"
            "Schreib MONTAG in die DM, wenn du raus willst.\n\n"
            "—\n#mindset #disziplin #stoiker #montagsluege #kalterwille"
        ),
    },
    {
        "date": "2026-05-05",
        "format": "carousel",
        "pillar": "komfort",
        "image_urls": carousel_urls("w1-d2-komfort"),
        "caption": (
            "Komfort tötet leise.\n\n"
            "Du nimmst zu, ohne es zu merken. Du wirst gereizt ohne Grund. "
            "Du verlierst Respekt vor dir selbst — leise, jeden Tag.\n\n"
            "Speicher das. Lies's am Sonntagabend nochmal.\n\n"
            "—\n#mindset #disziplin #stoiker #komforttötet #hardtruth"
        ),
    },
    {
        "date": "2026-05-06",
        "format": "carousel",
        "pillar": "potenzial",
        "image_urls": carousel_urls("w1-d3-potenzial"),
        "caption": (
            "In 10 Jahren bist du genau hier.\n\n"
            "Selbe Wohnung. Selbe Frau, die dich nicht mehr ernst nimmt. "
            "Selber Job, der dich langsam tötet.\n\n"
            "Schick das einem, der's lesen muss.\n\n"
            "—\n#mindset #disziplin #stoiker #montagsluege #mittelmaß"
        ),
    },
    {
        "date": "2026-05-07",
        "format": "carousel",
        "pillar": "vater-sohn",
        "image_urls": carousel_urls("w1-d4-vater-sohn"),
        "caption": (
            "Dein Vater wäre nicht stolz.\n\n"
            "Aber er hat's auch nie geschafft, der Mann zu werden, den du brauchst. "
            "Du wirst zu dem Mann, dem du als Kind nicht vertraut hast.\n\n"
            "Was bricht die Kette? Schreib's in die DM.\n\n"
            "—\n#mindset #mannsein #stoiker #montagsluege #generation"
        ),
    },
    {
        "date": "2026-05-08",
        "format": "carousel",
        "pillar": "frame-shift",
        "image_urls": carousel_urls("w1-d5-frame-shift"),
        "caption": (
            "Disziplin ist nicht das Problem.\n\n"
            "Optionen sind das Problem. Du brauchst nicht mehr Willenskraft — "
            "du brauchst weniger Wege ins Versagen.\n\n"
            "Streich Optionen. Reduzier Friction.\n\n"
            "—\n#mindset #disziplin #mentalmodel #montagsluege #klarheit"
        ),
    },
    {
        "date": "2026-05-09",
        "format": "carousel",
        "pillar": "quiet-power",
        "image_urls": carousel_urls("w1-d6-quiet-power"),
        "caption": (
            "Der gefährlichste Mann ist nicht der lauteste.\n\n"
            "Er ist der Ruhige. Der, der nichts beweisen muss. "
            "Weil er weiß, was er ist.\n\n"
            "Sei unmöglich zu ignorieren. Sag wenig.\n\n"
            "—\n#mindset #stoiker #sigma #quietpower #montagsluege"
        ),
    },
]


def main():
    out = ROOT / "queue.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for entry in WEEK_1:
            entry["status"] = "pending"
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Validierungs-Check
    print(f"=== Geschriebene Einträge ===")
    for line in out.read_text().splitlines():
        e = json.loads(line)
        first_line = e["caption"].split("\n")[0][:60]
        print(f"  {e['date']} | {e['format']:8s} | {e['pillar']:14s} | {first_line}")
    print(f"\n✅ {len(WEEK_1)} Einträge → {out}")


if __name__ == "__main__":
    main()
