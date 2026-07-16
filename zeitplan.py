"""Zeit-Experiment fuer @kopfundkompass.

Ziel: herausfinden, welche Uhrzeit und welcher Wochentag am besten laufen.
Statt zufaellig zu wuerfeln, rotiert jeder Wochentag systematisch durch alle Slots
(lateinisches Quadrat). Nach 5 Wochen hat JEDER Wochentag JEDEN Slot genau einmal
gehabt, und jeder Slot hat jeden Wochentag gesehen. Das ist balanciert, Zufall waere
es nicht: der wuerde nach 5 Wochen Loecher und Doppelungen hinterlassen.

Slot-Wahl:  slot_index = (Kalenderwoche + Wochentag) % anzahl_slots
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import json

HERE = Path(__file__).parent
ZH = timezone(timedelta(hours=2))          # Europe/Zurich, Sommerzeit
LOG = HERE / "zeit_experiment.json"

# Kandidaten-Slots in Zuercher Zeit. Bewusst ueber den Tag verteilt, damit das
# Experiment eine echte Spannweite abdeckt statt nur Feinjustierung am Abend.
SLOTS = ["07:00", "12:30", "17:00", "19:00", "21:30"]

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def slot_fuer(tag: date) -> str:
    """Der fuer diesen Tag vorgesehene Slot (rotierend, balanciert)."""
    kw = tag.isocalendar()[1]
    return SLOTS[(kw + tag.weekday()) % len(SLOTS)]


def jetzt_zh() -> datetime:
    return datetime.now(ZH)


def ist_mein_slot(toleranz_min: int = 20) -> bool:
    """True, wenn der aktuelle Lauf zum heutigen Slot gehoert.
    Der Workflow feuert zu allen Slots; nur der richtige postet."""
    now = jetzt_zh()
    soll = slot_fuer(now.date())
    sh, sm = map(int, soll.split(":"))
    soll_dt = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    diff = abs((now - soll_dt).total_seconds()) / 60
    if diff > toleranz_min:
        print(f"Heutiger Slot ist {soll}, jetzt {now:%H:%M}. Dieser Lauf postet nicht.")
        return False
    print(f"Heutiger Slot {soll} erreicht (jetzt {now:%H:%M}).")
    return True


def schon_gepostet(tag: Optional[date] = None) -> bool:
    tag = tag or jetzt_zh().date()
    for e in _log():
        if e.get("datum") == tag.isoformat() and e.get("media_id"):
            print(f"Am {tag.isoformat()} wurde bereits gepostet ({e['media_id']}).")
            return True
    return False


def _log() -> list:
    if not LOG.exists():
        return []
    try:
        return json.loads(LOG.read_text()).get("posts", [])
    except Exception:
        return []


def eintragen(media_id: str, permalink: str, thema: Optional[str] = None) -> None:
    """Haelt fest, WANN was gepostet wurde. Das ist die Datengrundlage der Auswertung."""
    now = jetzt_zh()
    posts = _log()
    posts.append({
        "datum": now.date().isoformat(),
        "wochentag": WOCHENTAGE[now.weekday()],
        "slot": slot_fuer(now.date()),
        "echte_zeit": now.strftime("%H:%M"),
        "media_id": media_id,
        "permalink": permalink,
        "thema": thema,
    })
    LOG.write_text(json.dumps({
        "_hinweis": "Zeit-Experiment: welcher Slot an welchem Wochentag laeuft am besten? "
                    "Auswertung mit kk_zeitreport.py (holt die Insights dazu).",
        "slots": SLOTS,
        "posts": posts,
    }, ensure_ascii=False, indent=2))
    print(f"Zeit-Experiment: {now:%d.%m.} {WOCHENTAGE[now.weekday()]} {slot_fuer(now.date())} -> {media_id}")


if __name__ == "__main__":
    heute = jetzt_zh().date()
    print(f"Slots: {SLOTS}")
    print(f"\nPlan der naechsten 14 Tage:")
    for i in range(14):
        t = heute + timedelta(days=i)
        print(f"  {t.strftime('%d.%m.')} {WOCHENTAGE[t.weekday()]:<11} {slot_fuer(t)}")
