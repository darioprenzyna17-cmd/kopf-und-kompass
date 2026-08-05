"""Baut die Commit-Meldung des Reel-Laufs aus dem Laufstatus.

Bewusst eine eigene Datei und kein Heredoc im Workflow: Python-Zeilen auf Spalte 0
beenden den YAML-Block, und die ganze Datei wird ungueltig. Genau daran ist reel.yml
am 05.08.2026 kurz gescheitert.

Drei Faelle, drei Meldungen. "bestaetigt online" darf NUR dastehen, wenn in DIESEM Lauf
wirklich ein Reel online ging. Vorher reichte ein altes ok:true aus einem frueheren
Lauf, und ein reiner Bau-Lauf meldete einen Post, den es nie gab (AUTOPILOT_AUFTRAG 1.2).
"""
import datetime
import json
from pathlib import Path

STATUS = Path(__file__).parent / "run_status.json"


def meldung() -> str:
    jetzt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        s = json.loads(STATUS.read_text())
    except Exception:
        return f"Ledger gesichert {jetzt} :: kein Laufstatus lesbar"
    grund = (s.get("grund") or "")[:120]
    if s.get("gepostet"):
        return f"reel bestaetigt online {jetzt} :: {s.get('konzept')}"
    if s.get("ok"):
        return f"Lauf ok, kein Post faellig {jetzt} :: {grund}"
    return f"FEHLSCHLAG reel nicht gepostet {jetzt} :: {grund}"


if __name__ == "__main__":
    print(meldung())
