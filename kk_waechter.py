"""Waechter fuer @kopfundkompass (AUTOPILOT_AUFTRAG.md Abschnitt 5).

Fragt Instagram, nicht das Log: Ist in den letzten 36 Stunden ein Reel und in den
letzten 16 Stunden eine Story online gegangen? Wenn nein, geht eine Meldung mit
Ursache an Darios Push-Kanal. Stillstand ist ein Vorfall, keine Randnotiz.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import kk_resilienz as res

HERE = Path(__file__).parent
NTFY_KANAL = "Dario-daily-Brief-k7p2m9qz"     # ausschliesslich Darios privater Kanal
GRENZE_REEL_H = 36
GRENZE_STORY_H = 16


def push(titel, text, prio="high"):
    try:
        r = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_KANAL}",
            data=text.encode("utf-8"),
            headers={"Title": urllib.parse.quote(titel), "Priority": prio, "Tags": "warning"},
            method="POST")
        urllib.request.urlopen(r, timeout=25).read()
        print("Push abgesetzt.", flush=True)
    except Exception as e:
        print("Push fehlgeschlagen:", repr(e)[:200], flush=True)


def main():
    now = datetime.now(timezone.utc)
    befunde, alarme = [], []

    letztes, link = res.letzter_beitrag("REELS")
    if letztes is None:
        alarme.append("Kein Reel auf dem Konto auffindbar.")
    else:
        h = (now - letztes).total_seconds() / 3600
        befunde.append(f"Letztes Reel vor {h:.1f} h ({letztes:%d.%m. %H:%M} UTC).")
        if h > GRENZE_REEL_H:
            alarme.append(f"Seit {h:.0f} h kein Reel (Grenze {GRENZE_REEL_H} h).")

    stories = res.aktive_stories()
    if stories:
        neuste = max(datetime.fromisoformat(s["timestamp"].replace("+0000", "+00:00"))
                     for s in stories)
        h = (now - neuste).total_seconds() / 3600
        befunde.append(f"{len(stories)} aktive Story(s), neuste vor {h:.1f} h.")
        if h > GRENZE_STORY_H:
            alarme.append(f"Neuste Story ist {h:.0f} h alt (Grenze {GRENZE_STORY_H} h).")
    else:
        alarme.append("Keine aktive Story auf dem Konto.")

    gesperrt = res.gesperrte()
    if gesperrt:
        befunde.append("In Quarantaene: " + ", ".join(gesperrt))
    g = res.guthaben()
    if g is not None:
        befunde.append(f"kie.ai-Guthaben: {g:.0f}")
        if g < res.CREDIT_WARNSCHWELLE:
            alarme.append(f"Guthaben unter Warnschwelle: {g:.0f}")

    # Ursache aus dem letzten Lauf mitgeben, statt Dario suchen zu lassen.
    ursache = ""
    sp = HERE / "run_status.json"
    if alarme and sp.exists():
        try:
            s = json.loads(sp.read_text())
            if not s.get("ok"):
                ursache = f"\nLetzter Lauf: {s.get('konzept')} -> {s.get('grund', '')[:200]}"
        except Exception:
            pass

    print("\n".join(befunde), flush=True)
    if alarme:
        text = "\n".join("- " + a for a in alarme) + ursache + "\n\n" + "\n".join(befunde)
        print("ALARM:\n" + text, flush=True)
        push("Kopf & Kompass steht still", text)
        return 1
    print("Alles im Rahmen.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
