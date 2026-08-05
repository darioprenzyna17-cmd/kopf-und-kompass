"""Taegliche Guthaben-Pruefung fuer den kie.ai-Schluessel von Kopf & Kompass.

Faellt das Guthaben unter die Schwelle, geht eine Push-Nachricht an Darios privaten
Kanal. Ohne diese Pruefung laeuft der Schluessel irgendwann leer und die Produktion
faellt still aus: kie.ai antwortet dann nur mit "Credits insufficient", der Reel-Lauf
bricht ab und niemand erfaehrt davon.

Der Schwellwert liegt hoeher als bei DC (150 statt 80), weil ein Reel hier Veo UND Suno
braucht und ein einzelner Bau entsprechend mehr kostet.
"""
import json
import os
import urllib.request

from kk_waechter import push

SCHWELLE = float(os.environ.get("CREDITS_MIN", "150"))


def guthaben() -> float:
    req = urllib.request.Request(
        "https://api.kie.ai/api/v1/chat/credit",
        headers={"Authorization": f"Bearer {os.environ['KIE_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    return float((d or {}).get("data") or 0)


def main() -> None:
    stand = guthaben()
    print(f"KIE-CREDITS: {stand} (Schwelle {SCHWELLE})", flush=True)
    if stand < SCHWELLE:
        push("Kopf & Kompass: kie.ai Guthaben niedrig",
             f"Nur noch {stand:.0f} Credits (Schwelle {SCHWELLE:.0f}). "
             f"Bitte aufladen, sonst faellt die Reel-Produktion still aus.")


if __name__ == "__main__":
    main()
