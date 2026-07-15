"""Kopf & Kompass — Lern- und Anpass-Loop (das "entwickle dich weiter"-Herz).

Zieht fuer jedes gepostete Reel die echten Instagram-Insights (Reichweite, Saves,
Shares, Watchtime), gewichtet sie nach dem Nordstern (Save + Share + Follow), aggregiert
nach THEMA und nach Lexikon-Begriff (kicker) und schreibt learnings.json:
  - Rangliste der Themen und Begriffe nach Score
  - klare Empfehlung: welche Themen ausbauen, welche streichen
cloud_build_post.py liest learnings.json und baut das naechste Reel bevorzugt aus einem
Gewinner-Thema. So passt sich der Account datenbasiert selbst an.

Zugang aus Umgebung (IG_USER_ID, IG_ACCESS_TOKEN). Aufruf: python3 learn_and_adapt.py
"""
import json
import os
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
GRAPH = "https://graph.facebook.com/v21.0"
# Nordstern-Gewichte (Strategie: Save + Share + Follow zaehlen mehr als Reichweite)
W = {"saved": 3.0, "shares": 4.0, "reach": 0.001, "total_interactions": 0.3, "watch": 0.5}
METRICS = "reach,saved,shares,total_interactions,ig_reels_avg_watch_time"


def env(name):
    v = os.environ.get(name)
    if not v and (HERE / ".env").exists():
        for l in (HERE / ".env").read_text().splitlines():
            if l.startswith(name + "="):
                v = l.split("=", 1)[1].strip()
    if not v:
        raise RuntimeError(f"{name} fehlt")
    return v


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def media_index(ig, token):
    """permalink -> media_id fuer die letzten Videos."""
    idx = {}
    url = f"{GRAPH}/{ig}/media?fields=id,permalink,media_type&limit=50&access_token={token}"
    try:
        for m in _get(url).get("data", []):
            if m.get("permalink"):
                idx[m["permalink"].rstrip("/")] = m["id"]
    except Exception as e:
        print("media_index Fehler:", e)
    return idx


def insights(mid, token):
    url = f"{GRAPH}/{mid}/insights?metric={METRICS}&access_token={token}"
    out = {}
    try:
        for row in _get(url).get("data", []):
            vals = row.get("values") or [{}]
            out[row["name"]] = vals[0].get("value", 0)
    except Exception:
        pass
    return out


def score(ins):
    watch = (ins.get("ig_reels_avg_watch_time", 0) or 0) / 1000.0  # ms -> s
    return round(
        W["saved"] * ins.get("saved", 0)
        + W["shares"] * ins.get("shares", 0)
        + W["reach"] * ins.get("reach", 0)
        + W["total_interactions"] * ins.get("total_interactions", 0)
        + W["watch"] * watch, 2)


def main():
    ig, token = env("IG_USER_ID"), env("IG_ACCESS_TOKEN")
    data = json.loads((HERE / "reel_pipeline.json").read_text())
    built = data.get("built", [])
    idx = media_index(ig, token)
    by_theme = defaultdict(lambda: {"score": 0.0, "n": 0, "reach": 0, "saves": 0, "shares": 0})
    by_term = defaultdict(lambda: {"score": 0.0, "n": 0})
    per_reel = []
    # kicker je gebautem Reel aus approved+built-Historie nachschlagen (falls vorhanden)
    concept_by_name = {c["name"]: c for c in data.get("approved", []) + built if isinstance(c, dict)}
    for b in built:
        link = (b.get("permalink") or "").rstrip("/")
        mid = idx.get(link)
        if not mid:
            continue
        ins = insights(mid, token)
        sc = score(ins)
        theme = b.get("theme") or "unbekannt"
        by_theme[theme]["score"] += sc; by_theme[theme]["n"] += 1
        by_theme[theme]["reach"] += ins.get("reach", 0)
        by_theme[theme]["saves"] += ins.get("saved", 0)
        by_theme[theme]["shares"] += ins.get("shares", 0)
        term = (concept_by_name.get(b["name"], {}) or {}).get("kicker", "")
        if term:
            by_term[term]["score"] += sc; by_term[term]["n"] += 1
        per_reel.append({"name": b["name"], "theme": theme, "score": sc, **ins})

    def rank(d):
        return sorted(([k, v] for k, v in d.items()),
                      key=lambda kv: (kv[1]["score"] / max(kv[1]["n"], 1)), reverse=True)

    themes_ranked = rank(by_theme)
    terms_ranked = rank(by_term)
    winners = [t for t, v in themes_ranked if v["score"] / max(v["n"], 1) > 0][:3]
    losers = [t for t, v in themes_ranked if v["n"] >= 2 and v["score"] / max(v["n"], 1) == 0]
    learnings = {
        "_hinweis": "Automatisch aus Instagram-Insights. Nordstern: Save+Share+Follow. cloud_build_post.py priorisiert Gewinner-Themen.",
        "updated_utc": None,
        "n_reels_mit_daten": len(per_reel),
        "themen_rang": [{"thema": t, "score_avg": round(v["score"] / max(v["n"], 1), 2), "n": v["n"],
                          "reichweite": v["reach"], "saves": v["saves"], "shares": v["shares"]} for t, v in themes_ranked],
        "begriff_rang": [{"begriff": t, "score_avg": round(v["score"] / max(v["n"], 1), 2), "n": v["n"]} for t, v in terms_ranked],
        "gewinner_themen": winners,
        "verlierer_themen": losers,
        "empfehlung": (
            f"Ausbauen: {', '.join(winners)}." if winners else
            "Noch zu wenig Daten (Reels frisch). Gleichmaessig streuen, in 2-3 Tagen erneut auswerten."),
        "per_reel": per_reel,
    }
    (HERE / "learnings.json").write_text(json.dumps(learnings, ensure_ascii=False, indent=2))
    print(f"Reels mit Daten: {len(per_reel)}")
    print("THEMEN:", [(t, round(v['score']/max(v['n'],1), 2)) for t, v in themes_ranked])
    print("Empfehlung:", learnings["empfehlung"])
    return learnings


if __name__ == "__main__":
    main()
