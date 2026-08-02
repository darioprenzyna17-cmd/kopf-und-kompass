"""Betriebs-Sicherungen fuer den @kopfundkompass-Autopiloten.

Setzt die Abschnitte 3 (Quarantaene), 4 (Geld) und 1 (Wahrheitspflicht) aus
AUTOPILOT_AUFTRAG.md im Code um. Bewusst ohne externe Abhaengigkeiten, damit es
in GitHub Actions ohne Installationsschritt laeuft.
"""
import json
import os
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
QUARANTAENE = HERE / "quarantaene.json"
LAUFSTATUS = HERE / "run_status.json"

MAX_FEHLVERSUCHE_PRO_TAG = 3      # Auftrag 4.2
FEHLER_BIS_QUARANTAENE = 2        # Auftrag 3.1
CREDIT_WARNSCHWELLE = 150         # Auftrag 4.1


# ---------------------------------------------------------------- Quarantaene

def _laden():
    if QUARANTAENE.exists():
        try:
            return json.loads(QUARANTAENE.read_text())
        except Exception:
            pass
    return {"_hinweis": "Konzepte, die beim Bauen scheitern. Ab 2 Fehlschlaegen gesperrt, "
                        "bis Dario sie freigibt (status auf 'frei' setzen).",
            "konzepte": {}, "fehlversuche": {}}


def _sichern(d):
    QUARANTAENE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def ist_gesperrt(name):
    """Auftrag 3.1: gesperrte Konzepte werden nicht mehr gezogen."""
    e = _laden()["konzepte"].get(name)
    return bool(e) and e.get("status") == "gesperrt"


def gesperrte():
    return [k for k, v in _laden()["konzepte"].items() if v.get("status") == "gesperrt"]


def fehler_vermerken(name, grund):
    """Zaehlt einen Fehlschlag. Ab FEHLER_BIS_QUARANTAENE wird das Konzept gesperrt.
    Zaehlt zusaetzlich das Tagesbudget an Fehlversuchen hoch (Auftrag 4.2)."""
    d = _laden()
    e = d["konzepte"].setdefault(name, {"fehler": 0, "status": "frei", "gruende": []})
    e["fehler"] += 1
    e["gruende"] = (e.get("gruende", []) + [str(grund)[:300]])[-5:]
    e["zuletzt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if e["fehler"] >= FEHLER_BIS_QUARANTAENE:
        e["status"] = "gesperrt"
        e["gesperrt_seit"] = e["zuletzt"]
        print(f"QUARANTAENE: '{name}' nach {e['fehler']} Fehlschlaegen gesperrt.", flush=True)
    heute = date.today().isoformat()
    d["fehlversuche"][heute] = d["fehlversuche"].get(heute, 0) + 1
    d["fehlversuche"] = {k: v for k, v in d["fehlversuche"].items() if k >= heute}
    _sichern(d)
    return e


def erfolg_vermerken(name):
    """Ein geglueckter Bau setzt den Fehlerzaehler des Konzepts zurueck."""
    d = _laden()
    if name in d["konzepte"]:
        d["konzepte"][name]["fehler"] = 0
        d["konzepte"][name]["status"] = "frei"
        _sichern(d)


# ---------------------------------------------------------------------- Geld

def fehlversuche_heute():
    return _laden()["fehlversuche"].get(date.today().isoformat(), 0)


def guthaben():
    """kie.ai-Guthaben. None, wenn nicht abfragbar."""
    key = os.environ.get("KIE_API_KEY")
    if not key:
        env = HERE / ".env"
        if env.exists():
            for l in env.read_text().splitlines():
                if l.startswith("KIE_API_KEY="):
                    key = l.split("=", 1)[1].strip()
    if not key:
        return None
    try:
        r = urllib.request.Request("https://api.kie.ai/api/v1/chat/credit",
                                   headers={"Authorization": f"Bearer {key}"})
        return json.loads(urllib.request.urlopen(r, timeout=25).read().decode()).get("data")
    except Exception as e:
        print("Guthaben nicht abfragbar:", repr(e)[:150], flush=True)
        return None


def budget_ok():
    """Auftrag 4.1 + 4.2. Gibt (ok, grund) zurueck."""
    n = fehlversuche_heute()
    if n >= MAX_FEHLVERSUCHE_PRO_TAG:
        return False, (f"Tagesbudget erschoepft: {n} Fehlversuche heute "
                       f"(Grenze {MAX_FEHLVERSUCHE_PRO_TAG}). Kein Dauerfeuer auf bezahlte APIs.")
    g = guthaben()
    if g is not None and g < CREDIT_WARNSCHWELLE:
        return False, f"kie.ai-Guthaben zu tief: {g} (Warnschwelle {CREDIT_WARNSCHWELLE})."
    if g is not None:
        print(f"Guthaben kie.ai: {g}", flush=True)
    return True, ""


# ------------------------------------------------------- Wahrheitspflicht (1)

def _graph(pfad, params):
    ig = os.environ.get("IG_USER_ID")
    tok = os.environ.get("IG_ACCESS_TOKEN")
    if not (ig and tok):
        env = HERE / ".env"
        if env.exists():
            d = dict(l.strip().split("=", 1) for l in env.read_text().splitlines()
                     if "=" in l and not l.startswith("#"))
            ig, tok = ig or d.get("IG_USER_ID"), tok or d.get("IG_ACCESS_TOKEN")
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://graph.facebook.com/v21.0/{pfad.format(ig=ig)}?{q}&access_token={tok}"
    return json.loads(urllib.request.urlopen(url, timeout=30).read().decode())


def wirklich_online(media_id):
    """Auftrag 1.1: Beweis holen, statt dem eigenen Exit-Code zu glauben."""
    tok = os.environ.get("IG_ACCESS_TOKEN")
    if not tok:
        env = HERE / ".env"
        if env.exists():
            for l in env.read_text().splitlines():
                if l.startswith("IG_ACCESS_TOKEN="):
                    tok = l.split("=", 1)[1].strip()
    try:
        url = (f"https://graph.facebook.com/v21.0/{media_id}"
               f"?fields=id,permalink,media_product_type&access_token={tok}")
        d = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
        return bool(d.get("id")), d.get("permalink")
    except Exception as e:
        return False, f"Nachweis fehlgeschlagen: {repr(e)[:200]}"


def letzter_beitrag(art="REELS"):
    """Zeitstempel des letzten echten Beitrags laut Instagram (nicht laut Log)."""
    d = _graph("{ig}/media", {"fields": "media_product_type,timestamp,permalink", "limit": "15"})
    for m in d.get("data", []):
        if m.get("media_product_type") == art:
            return datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")), m.get("permalink")
    return None, None


def aktive_stories():
    try:
        d = _graph("{ig}/stories", {"fields": "timestamp"})
        return d.get("data", [])
    except Exception:
        return []


def status_schreiben(ok, name=None, permalink=None, grund=""):
    """Auftrag 1.2: der Lauf hinterlaesst eine ehrliche Spur, die der Workflow liest."""
    LAUFSTATUS.write_text(json.dumps({
        "ok": bool(ok), "konzept": name, "permalink": permalink, "grund": grund,
        "zeit": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
