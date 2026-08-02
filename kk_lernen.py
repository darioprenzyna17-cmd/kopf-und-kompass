"""Lernsystem nach dem Content-Agent-Auftrag (Dario 2026-08-02).

Der alte Lern-Loop hat Themen nach Save plus Share bewertet und die Gewinner gedoppelt.
Das hat zwei Wochen lang nichts bewegt, weil das Thema nicht entscheidet, ob jemand
nach Sekunde vier bleibt. Dieses Modul misst stattdessen den Nordstern in der
vorgegebenen Reihenfolge und zwingt jedes Posting zu einer Hypothese, die danach
bestaetigt oder widerlegt wird.

Dateien:
  postings.jsonl  ein Eintrag pro Posting, mit Hypothese und Ergebnis nach 48 Stunden
  regeln.md       die aktuell gueltigen, datenbasierten Regeln, je mit Datum und Belegzahl
"""
import json
import os
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
POSTINGS = HERE / "postings.jsonl"
REGELN = HERE / "regeln.md"
GRAPH = "https://graph.facebook.com/v21.0"

# Nordstern in der vorgegebenen Rangfolge. Die Gewichte bilden genau diese Reihenfolge ab.
GEWICHTE = {"watchtime_anteil": 5.0, "nonfollower_anteil": 4.0,
            "sends_pro_1k": 3.0, "saves_pro_1k": 2.0, "follower_pro_1k": 1.0}

# Testverteilung 70/20/10 (Auftrag Abschnitt 6). Deterministisch ueber den Tag verteilt,
# damit der Anteil ueber Wochen wirklich stimmt und nicht am Zufall haengt.
def testklasse(tag=None):
    n = (tag or date.today()).toordinal() % 10
    if n < 7:
        return "basis"      # bewaehrtes Muster aus regeln.md
    if n < 9:
        return "variation"  # genau EINE Variable bewusst geaendert
    return "wagnis"         # neues Format, neuer Ton, neuer Winkel


def _creds():
    ig = os.environ.get("IG_USER_ID")
    tok = os.environ.get("IG_ACCESS_TOKEN")
    if not (ig and tok) and (HERE / ".env").exists():
        d = dict(l.strip().split("=", 1) for l in (HERE / ".env").read_text().splitlines()
                 if "=" in l and not l.startswith("#"))
        ig, tok = ig or d.get("IG_USER_ID"), tok or d.get("IG_ACCESS_TOKEN")
    return ig, tok


def _get(url):
    return json.loads(urllib.request.urlopen(url, timeout=40).read().decode())


# ------------------------------------------------------------- Protokollieren

def protokollieren(eintrag):
    """Schreibt ein Posting ins Log. Ohne Hypothese wird nicht protokolliert
    (Auftrag Abschnitt 7: kein Posting ohne Hypothese)."""
    if not eintrag.get("hypothese"):
        raise ValueError("Posting ohne Hypothese wird nicht protokolliert.")
    eintrag.setdefault("id", datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M"))
    eintrag.setdefault("gepostet", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    eintrag.setdefault("urteil", "offen")
    with POSTINGS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    print(f"  [Lernen] protokolliert: {eintrag['id']} | Hypothese: {eintrag['hypothese']}", flush=True)
    return eintrag


def alle():
    if not POSTINGS.exists():
        return []
    out = []
    for l in POSTINGS.read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if l:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def _schreiben(eintraege):
    POSTINGS.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in eintraege),
                        encoding="utf-8")


# ------------------------------------------------------------------- Messen

def messen(media_id, laenge_sek):
    """Holt die Nordstern-Kennzahlen zu einem Beitrag. Fehlende Werte bleiben None,
    statt sie mit Nullen zu erfinden."""
    _, tok = _creds()
    e = {"views": 0, "reach": 0, "watchtime_anteil": None, "nonfollower_anteil": None,
         "sends": 0, "saves": 0, "follower_gewonnen": None}
    try:
        d = _get(f"{GRAPH}/{media_id}/insights?metric=reach,views,saved,shares,likes,comments"
                 f"&access_token={tok}")
        v = {x["name"]: x["values"][0]["value"] for x in d.get("data", [])}
        e["views"], e["reach"] = v.get("views", 0), v.get("reach", 0)
        e["sends"], e["saves"] = v.get("shares", 0), v.get("saved", 0)
        e["likes"], e["kommentare"] = v.get("likes", 0), v.get("comments", 0)
    except Exception as ex:
        print("  Insights nicht lesbar:", repr(ex)[:140], flush=True)
    try:
        d = _get(f"{GRAPH}/{media_id}/insights?metric=ig_reels_avg_watch_time&access_token={tok}")
        ms = d["data"][0]["values"][0]["value"]
        if laenge_sek:
            e["watchtime_sek"] = round(ms / 1000.0, 2)
            e["watchtime_anteil"] = round(min(1.0, (ms / 1000.0) / laenge_sek), 3)
    except Exception:
        pass
    try:
        d = _get(f"{GRAPH}/{media_id}/insights?metric=views&breakdown=follow_type&access_token={tok}")
        res = d["data"][0]["total_value"]["breakdowns"][0]["results"]
        werte = {r["dimension_values"][0]: r["value"] for r in res}
        ges = sum(werte.values())
        if ges:
            e["nonfollower_anteil"] = round(werte.get("NON_FOLLOWER", 0) / ges, 3)
    except Exception:
        pass
    v = max(e.get("views") or 0, 1)
    e["sends_pro_1k"] = round(e["sends"] * 1000.0 / v, 2)
    e["saves_pro_1k"] = round(e["saves"] * 1000.0 / v, 2)
    if e.get("follower_gewonnen") is not None:
        e["follower_pro_1k"] = round(e["follower_gewonnen"] * 1000.0 / v, 2)
    return e


def nordstern_score(erg):
    """Ein Wert aus den Nordstern-Kennzahlen, gewichtet nach der vorgegebenen Rangfolge.
    Fehlende Kennzahlen zaehlen nicht mit, statt als Null zu bestrafen."""
    s = w = 0.0
    for k, g in GEWICHTE.items():
        v = erg.get(k)
        if v is None:
            continue
        # sends/saves/follower pro 1000 auf eine 0-bis-1-Skala bringen (10 pro 1000 = stark)
        norm = v if k.endswith("anteil") else min(1.0, v / 10.0)
        s += g * norm
        w += g
    return round(s / w, 4) if w else 0.0


# ------------------------------------------------------------ Auswertung 48h

def auswerten(mindestalter_h=48):
    """Traegt Zahlen nach, faellt ein Urteil und formuliert die Erkenntnis als REGEL."""
    eintraege = alle()
    if not eintraege:
        print("Noch keine Postings protokolliert.")
        return []
    jetzt = datetime.now(timezone.utc)
    neu = []
    for e in eintraege:
        if e.get("urteil") != "offen" or not e.get("media_id"):
            continue
        try:
            gep = datetime.fromisoformat(e["gepostet"].replace("Z", "+00:00"))
        except Exception:
            continue
        if (jetzt - gep) < timedelta(hours=mindestalter_h):
            continue
        erg = messen(e["media_id"], e.get("laenge_sek"))
        e["ergebnis_nach_48h"] = erg
        e["nordstern"] = nordstern_score(erg)
        schnitt = _durchschnitt_nordstern(eintraege, ausser=e.get("id"))
        if schnitt is None:
            e["urteil"] = "unklar"
            e["erkenntnis"] = "Zu wenig Vergleichsdaten, um die Hypothese zu pruefen."
        elif e["nordstern"] >= schnitt * 1.15:
            e["urteil"] = "bestaetigt"
            e["erkenntnis"] = _regelsatz(e, besser=True)
        elif e["nordstern"] <= schnitt * 0.85:
            e["urteil"] = "widerlegt"
            e["erkenntnis"] = _regelsatz(e, besser=False)
        else:
            e["urteil"] = "unklar"
            e["erkenntnis"] = ("Kein messbarer Unterschied zum Schnitt, die Variable "
                               f"'{e.get('variable', 'unbekannt')}' erklaert nichts.")
        neu.append(e)
        print(f"  {e['id']}: Nordstern {e['nordstern']} gegen Schnitt "
              f"{schnitt if schnitt is not None else '-'} -> {e['urteil']}", flush=True)
        print(f"    {e['erkenntnis']}", flush=True)
    if neu:
        _schreiben(eintraege)
        for e in neu:
            if e["urteil"] in ("bestaetigt", "widerlegt"):
                regel_buchen(e["erkenntnis"], e["urteil"] == "bestaetigt")
    else:
        print("Nichts faellig zur Auswertung.")
    return neu


def _durchschnitt_nordstern(eintraege, ausser=None):
    werte = [e["nordstern"] for e in eintraege
             if e.get("nordstern") is not None and e.get("id") != ausser]
    return round(sum(werte) / len(werte), 4) if werte else None


def _laengenklasse(s):
    if not s:
        return "unbekannter Laenge"
    if s < 12:
        return "unter 12s"
    if s <= 20:
        return "12 bis 20s"
    return "ueber 20s"


def _regelsatz(e, besser):
    """Erkenntnis als Regel formulieren, nicht als Beobachtung.

    Bewusst OHNE die exakte Sekundenzahl des einzelnen Postings. Sonst entsteht aus
    9,9s und 10,1s zweimal dieselbe Regel mit je einem Beleg, statt einmal mit zwei.
    Die Belegzahl ist der ganze Wert des Regelwerks, also muss der Wortlaut
    wiederverwendbar sein."""
    var = e.get("variable") or e.get("hook_typ") or "das gewaehlte Muster"
    richtung = "traegt" if besser else "traegt nicht"
    return (f"{var} {richtung}: Reels {_laengenklasse(e.get('laenge_sek'))} mit Hook-Typ "
            f"'{e.get('hook_typ', '?')}' liegen im Nordstern "
            f"{'ueber' if besser else 'unter'} dem Kontodurchschnitt.")


# ------------------------------------------------------------------- Regeln

def _regeln_laden():
    if not REGELN.exists():
        return []
    zeilen = [l for l in REGELN.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    out = []
    for l in zeilen:
        try:
            kopf, rest = l[2:].rsplit("  (", 1)
            datum, belege = rest.rstrip(")").split(", Belege ")
            out.append({"regel": kopf, "datum": datum, "belege": int(belege)})
        except Exception:
            out.append({"regel": l[2:], "datum": "", "belege": 1})
    return out


def _regeln_sichern(regeln):
    kopf = ("# Gueltige Regeln @kopfundkompass\n\n"
            "Datenbasiert, je mit Datum und Anzahl Belege. Beim naechsten Zyklus verbindlich.\n"
            "Eine Regel, die dreimal widerlegt wurde, wird geloescht (Auftrag Abschnitt 6).\n\n")
    zeilen = [f"- {r['regel']}  ({r['datum']}, Belege {r['belege']})" for r in regeln]
    REGELN.write_text(kopf + "\n".join(zeilen) + "\n", encoding="utf-8")


def regel_buchen(text, bestaetigt):
    """Belegt eine Regel oder zaehlt ihre Widerlegungen. Dreimal widerlegt heisst geloescht."""
    regeln = _regeln_laden()
    heute = date.today().isoformat()
    for r in regeln:
        if r["regel"][:60] == text[:60]:
            if bestaetigt:
                r["belege"] += 1
                r["datum"] = heute
            else:
                r["belege"] -= 1
                if r["belege"] <= -3:
                    regeln.remove(r)
                    print(f"  [Regel geloescht nach 3 Widerlegungen] {text[:70]}", flush=True)
            _regeln_sichern(regeln)
            return
    if bestaetigt:
        regeln.append({"regel": text, "datum": heute, "belege": 1})
        _regeln_sichern(regeln)
        print(f"  [Neue Regel] {text[:80]}", flush=True)


# ------------------------------------------------------------ Wochenrueckblick

def wochenrueckblick():
    """Beste und schwaechste drei nebeneinander, die unterscheidende Variable finden,
    Regeln nachziehen, drei neue Hypothesen setzen."""
    e = [x for x in alle() if x.get("nordstern") is not None]
    if len(e) < 6:
        print(f"Nur {len(e)} ausgewertete Postings, Rueckblick braucht mindestens 6.")
        return None
    e.sort(key=lambda x: x["nordstern"], reverse=True)
    top, flop = e[:3], e[-3:]
    print("BESTE 3:")
    for x in top:
        print(f"  {x['nordstern']:.3f}  {x.get('thema')} | {x.get('laenge_sek')}s | {x.get('hook_typ')}")
    print("SCHWAECHSTE 3:")
    for x in flop:
        print(f"  {x['nordstern']:.3f}  {x.get('thema')} | {x.get('laenge_sek')}s | {x.get('hook_typ')}")
    unterschied = _unterscheidende_variable(top, flop)
    print("Unterscheidende Variable:", unterschied)
    if unterschied:
        regel_buchen(unterschied, True)
    hyp = _neue_hypothesen(top, flop)
    print("Naechste Hypothesen:")
    for h in hyp:
        print("  -", h)
    return {"top": top, "flop": flop, "variable": unterschied, "hypothesen": hyp}


def _unterscheidende_variable(top, flop):
    """Die EINE Variable finden, die beste und schwaechste trennt."""
    for feld, name in (("laenge_sek", "Laenge"), ("hook_typ", "Hook-Typ"),
                       ("thema", "Thema"), ("postingzeit", "Postingzeit"),
                       ("testklasse", "Testklasse")):
        tw = [x.get(feld) for x in top if x.get(feld) is not None]
        fw = [x.get(feld) for x in flop if x.get(feld) is not None]
        if not tw or not fw:
            continue
        if all(isinstance(v, (int, float)) for v in tw + fw):
            mt, mf = sum(tw) / len(tw), sum(fw) / len(fw)
            if mf and abs(mt - mf) / max(abs(mf), 1e-9) > 0.25:
                return (f"{name} trennt: die besten liegen bei {mt:.1f}, "
                        f"die schwaechsten bei {mf:.1f}.")
        else:
            if set(map(str, tw)).isdisjoint(set(map(str, fw))):
                return f"{name} trennt: oben {sorted(set(map(str, tw)))}, unten {sorted(set(map(str, fw)))}."
    return None


def _neue_hypothesen(top, flop):
    laengen = [x.get("laenge_sek") for x in top if x.get("laenge_sek")]
    ziel = round(sum(laengen) / len(laengen)) if laengen else 10
    return [
        f"Reels um {ziel} Sekunden halten einen hoeheren Watchtime-Anteil als laengere.",
        "Ein Hook, der eine Spannung oeffnet, schlaegt einen Hook, der die Aussage vorwegnimmt.",
        "Eine konkrete Frage auf der Schlusskarte hebt Sends pro Reichweite messbar an.",
    ]


def regeln_text():
    r = _regeln_laden()
    if not r:
        return "(noch keine belegten Regeln)"
    return "\n".join(f"- {x['regel']} ({x['datum']}, Belege {x['belege']})" for x in r)


if __name__ == "__main__":
    import sys
    if "--woche" in sys.argv:
        wochenrueckblick()
    else:
        auswerten()
        print("\nGueltige Regeln:\n" + regeln_text())
