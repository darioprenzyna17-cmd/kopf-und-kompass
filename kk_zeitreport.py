"""Auswertung des Zeit-Experiments: welcher Slot, welcher Wochentag laeuft?

Holt zu jedem protokollierten Post die echten Instagram-Zahlen und mittelt sie
je Slot und je Wochentag. Aufruf: python3 kk_zeitreport.py

Ehrlich bleiben: Reichweite waechst mit dem Alter eines Posts. Darum wertet der
Report nur Posts aus, die mindestens REIFE_TAGE alt sind, sonst vergleicht man
einen frischen mit einem gereiften und der Slot bekommt die Schuld.
"""
import json
import os
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
ZH = timezone(timedelta(hours=2))
REIFE_TAGE = 3          # juengere Posts zaehlen noch nicht mit
MIN_PRO_ZELLE = 3       # ab so vielen Messungen reden wir von einem Befund

for line in (HERE / ".env").read_text().splitlines() if (HERE / ".env").exists() else []:
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def insights(media_id, tok):
    url = (f"https://graph.facebook.com/v21.0/{media_id}/insights"
           f"?metric=reach,saved,shares&access_token={tok}")
    try:
        d = json.load(urllib.request.urlopen(url, timeout=25))
        return {x["name"]: x["values"][0]["value"] for x in d.get("data", [])}
    except Exception:
        return {}


def main():
    tok = os.environ.get("IG_ACCESS_TOKEN")
    log = HERE / "zeit_experiment.json"
    if not log.exists():
        print("Noch keine Daten. Das Experiment startet mit dem naechsten Post.")
        return
    posts = json.loads(log.read_text()).get("posts", [])
    heute = datetime.now(ZH).date()

    reif, jung = [], 0
    for p in posts:
        if not p.get("media_id"):
            continue
        alter = (heute - datetime.fromisoformat(p["datum"]).date()).days
        if alter < REIFE_TAGE:
            jung += 1
            continue
        v = insights(p["media_id"], tok)
        if v:
            # Nordstern wie im Lern-Loop: Saves und Shares wiegen schwerer als Reichweite
            p["reach"] = v.get("reach", 0)
            p["score"] = v.get("saved", 0) * 3 + v.get("shares", 0) * 3 + v.get("reach", 0) / 100
            reif.append(p)

    print(f"=== Zeit-Experiment @kopfundkompass ===")
    print(f"{len(reif)} auswertbare Posts (mind. {REIFE_TAGE} Tage alt), {jung} noch zu jung")

    # Datenqualitaet: GitHub startet Laeufe manchmal 1-2h zu spaet. Dann gehoert der
    # Post nicht mehr zu dem Slot, unter dem er verbucht ist. Das muss sichtbar sein,
    # sonst bekommt ein Slot die Schuld fuer eine Uhrzeit, zu der nie gepostet wurde.
    schief = []
    for p_ in reif:
        soll_h, soll_m = map(int, p_["slot"].split(":"))
        ist_h, ist_m = map(int, p_["echte_zeit"].split(":"))
        abw = abs((ist_h * 60 + ist_m) - (soll_h * 60 + soll_m))
        p_["abweichung"] = abw
        if abw > 30:
            schief.append(p_)
    if schief:
        print(f"ACHTUNG: {len(schief)} Post(s) mehr als 30 Min neben dem Soll-Slot:")
        for p_ in schief:
            print(f"  {p_['datum']}  Soll {p_['slot']}, tatsaechlich {p_['echte_zeit']}  "
                  f"(+{p_['abweichung']} Min)")
        print("  Diese Zeilen verfaelschen die Slot-Rangliste.")
    print()
    if not reif:
        print("Noch nichts Reifes dabei. In ein paar Tagen nochmal.")
        return

    for titel, key in (("NACH SLOT", "slot"), ("NACH WOCHENTAG", "wochentag")):
        gruppen = defaultdict(list)
        for p in reif:
            gruppen[p[key]].append(p)
        print(f"--- {titel} ---")
        print(f"{'':<12}{'n':>4}{'Reach':>9}{'Score':>8}")
        for k, v in sorted(gruppen.items(), key=lambda x: -sum(p["score"] for p in x[1]) / len(x[1])):
            n = len(v)
            r = sum(p["reach"] for p in v) / n
            s = sum(p["score"] for p in v) / n
            warn = "" if n >= MIN_PRO_ZELLE else "  (zu wenig Daten)"
            print(f"{k:<12}{n:>4}{r:>9.0f}{s:>8.1f}{warn}")
        print()

    zellen = defaultdict(int)
    for p in reif:
        zellen[(p["wochentag"], p["slot"])] += 1
    voll = sum(1 for v in zellen.values() if v >= MIN_PRO_ZELLE)
    print(f"Abdeckung Wochentag x Slot: {len(zellen)}/35 Kombinationen getestet, "
          f"{voll} davon mit mind. {MIN_PRO_ZELLE} Messungen.")
    if voll < 10:
        print("Fuer eine Aussage 'Dienstag um 19 Uhr ist am besten' reicht das noch nicht.\n"
              "Die Rangliste nach Slot und nach Wochentag oben ist aber schon brauchbar.")


if __name__ == "__main__":
    main()
