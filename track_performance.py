"""
Performance-Tracker fuer @digital_century_group.

Zieht bei jedem Lauf die Zahlen aller Posts (Basis-Felder + Insights, falls
berechtigt), haengt einen Zeit-Schnappschuss an metrics_history.jsonl an
(so wird Wachstum ueber Zeit sichtbar, nicht nur der Ist-Stand) und gibt eine
Rangliste aus: welches FORMAT und welches THEMA am besten performt.

Diese Datei liefert die Datengrundlage, damit generate_week.py kuenftig
Themen/Formate nach echter Performance gewichten kann (statt stumpf zu rotieren).

Voraussetzung fuer die vollen Zahlen (Reichweite/Saves/Shares): Token mit
Berechtigung 'instagram_manage_insights'. Ohne die laeuft der Tracker trotzdem,
nutzt dann nur Likes/Kommentare und markiert die Insights als 'no_permission'.

Aufruf:
    python3 track_performance.py            # ziehen, loggen, Rangliste zeigen
    python3 track_performance.py --no-log   # nur anzeigen, nichts anhaengen
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
HIST_FILE = HERE / "metrics_history.jsonl"
GRAPH = "https://graph.facebook.com/v21.0"

# Themen-Erkennung aus der Caption (grob, Stichworte -> Thema-Label).
TOPIC_KEYWORDS = {
    "fachkraeftemangel": ["fachkräfte", "fachkraft", "arbeitskräfte", "leute fehlen", "mangel"],
    "social_recruiting": ["social recruiting", "recruiting ist marketing", "social media"],
    "kosten_offene_stelle": ["kostet", "leerer stuhl", "jeden tag geld"],
    "prozess_schritte": ["schritten", "schritte", "so einfach", "swipe"],
    "recruiting_fehler": ["fehler", "reicht nicht", "inserat"],
    "branche_handwerk": ["werkstatt", "maler", "handwerk", "lager", "küche", "saison"],
    "employer_branding": ["employer branding", "sichtbar", "arbeitgeber"],
}


def env(name):
    v = os.environ.get(name)
    if not v and (HERE / ".env").exists():
        for l in (HERE / ".env").read_text().splitlines():
            if l.startswith(name + "="):
                v = l.split("=", 1)[1].strip()
    if not v:
        raise RuntimeError(f"{name} fehlt (weder Umgebung noch .env)")
    return v


def api(path, params):
    params = dict(params)
    params["access_token"] = TOKEN
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode())["error"]
            return None, err
        except Exception:
            return None, {"message": str(e), "code": e.code}


def classify_topic(caption):
    c = (caption or "").lower()
    for topic, words in TOPIC_KEYWORDS.items():
        if any(w in c for w in words):
            return topic
    return "sonstiges"


def fetch_media():
    out, err = api(f"{IG}/media", {
        "fields": "id,caption,media_type,timestamp,permalink,like_count,comments_count",
        "limit": "50",
    })
    if err:
        raise RuntimeError(f"Media-Abruf fehlgeschlagen: {err.get('message')}")
    return out.get("data", [])


def fetch_insights(media_id):
    """Insights je Post. Gibt (dict, permission_ok) zurueck."""
    out, err = api(f"{media_id}/insights", {"metric": "reach,total_interactions,saved,shares"})
    if err:
        if err.get("code") == 10:            # keine insights-Berechtigung
            return {}, False
        # manche Metriken je Medientyp nicht verfuegbar -> weicher Fallback
        out, err2 = api(f"{media_id}/insights", {"metric": "reach"})
        if err2:
            return {}, (err2.get("code") != 10)
    vals = {}
    for m in (out or {}).get("data", []):
        vals[m["name"]] = (m.get("values") or [{}])[0].get("value", 0)
    return vals, True


def engagement_score(row):
    """Ranking-Score. Mit Reichweite: Interaktionsrate; sonst rohe Interaktionen."""
    inter = row["likes"] + 2 * row["comments"] + 3 * row["saved"] + 4 * row["shares"]
    if row["reach"] and row["reach"] > 0:
        return round(100 * inter / row["reach"], 2)   # ~Engagement-Rate in %
    return float(inter)


def main():
    log = "--no-log" not in sys.argv
    media = fetch_media()
    rows = []
    insights_ok = None
    for m in media:
        ins, ok = fetch_insights(m["id"])
        if insights_ok is None:
            insights_ok = ok
        insights_ok = insights_ok and ok
        rows.append({
            "id": m["id"],
            "timestamp": m.get("timestamp", ""),
            "format": m.get("media_type", ""),
            "topic": classify_topic(m.get("caption")),
            "caption": (m.get("caption") or "").replace("\n", " ")[:60],
            "likes": m.get("like_count", 0) or 0,
            "comments": m.get("comments_count", 0) or 0,
            "reach": ins.get("reach", 0) or 0,
            "saved": ins.get("saved", 0) or 0,
            "shares": ins.get("shares", 0) or 0,
            "interactions": ins.get("total_interactions", 0) or 0,
        })
    for r in rows:
        r["score"] = engagement_score(r)

    # Schnappschuss anhaengen (Wachstum ueber Zeit)
    stamp = datetime.now(timezone.utc).isoformat()
    if log:
        snap = {"at": stamp, "insights_permission": bool(insights_ok), "posts": rows}
        with HIST_FILE.open("a") as f:
            f.write(json.dumps(snap, ensure_ascii=False) + "\n")

    # Ausgabe
    print(f"Schnappschuss {stamp}")
    print(f"Insights-Berechtigung: {'JA' if insights_ok else 'NEIN (nur Likes/Kommentare) -> instagram_manage_insights fehlt'}")
    print(f"Posts gesamt: {len(rows)}\n")

    def agg(key):
        buckets = defaultdict(lambda: {"n": 0, "score": 0.0, "reach": 0, "inter": 0})
        for r in rows:
            b = buckets[r[key]]
            b["n"] += 1
            b["score"] += r["score"]
            b["reach"] += r["reach"]
            b["inter"] += r["likes"] + r["comments"] + r["saved"] + r["shares"]
        ranked = sorted(buckets.items(), key=lambda kv: kv[1]["score"] / kv[1]["n"], reverse=True)
        return ranked

    print("=== FORMAT-Rangliste (Ø Score) ===")
    for name, b in agg("format"):
        print(f"  {name:15} n={b['n']:2}  Ø{b['score']/b['n']:6.2f}  Reichweite {b['reach']:5}  Interakt. {b['inter']}")
    print("\n=== THEMA-Rangliste (Ø Score) ===")
    for name, b in agg("topic"):
        print(f"  {name:22} n={b['n']:2}  Ø{b['score']/b['n']:6.2f}  Reichweite {b['reach']:5}  Interakt. {b['inter']}")

    print("\n=== TOP 5 EINZELPOSTS ===")
    for r in sorted(rows, key=lambda r: r["score"], reverse=True)[:5]:
        print(f"  Ø{r['score']:6.2f} | {r['format']:14} | {r['topic']:20} | {r['caption']}")

    if not insights_ok:
        print("\nHINWEIS: Solange 'instagram_manage_insights' fehlt und der Account kaum")
        print("Follower hat, ist die Rangliste noch Rauschen. Erst Berechtigung + Reichweite,")
        print("dann liefert dieser Tracker verwertbare Signale.")


if __name__ == "__main__":
    IG, TOKEN = env("IG_USER_ID"), env("IG_ACCESS_TOKEN")
    main()
