"""
Performance-Gewichtung fuer generate_week.py.

Liest die echten Insights der bereits geposteten Motive und liefert:
 - scores_by_capkey: je Motiv (per Caption-Key) einen Score (reach + 5x Interaktionen),
   damit die Wochen-Generierung bewaehrte Motive bevorzugt.
 - fmt_avg / fmt_n: durchschnittliche Reichweite und Anzahl je Format,
   damit das Format-Muster (mehr Reels?) datenbasiert nachjustiert werden kann.

BEST EFFORT und BEWUSST VORSICHTIG:
 - Ohne Creds/Insights oder bei zu wenig Daten wird NICHTS veraendert.
 - Das Format-Muster wird erst geaendert, wenn genug Datenpunkte PRO FORMAT da sind
   (MIN_REELS), damit ein einzelnes starkes Reel (n=1) keine Ueberreaktion ausloest.
"""
import json
import os
import urllib.request
from pathlib import Path
from statistics import median

HERE = Path(__file__).parent
GRAPH = "https://graph.facebook.com/v21.0"

# Ab wann das Format-Muster ueberhaupt angefasst wird:
MIN_REELS = 3            # so viele Reels mit Daten, bevor Reels-Anteil erhoeht wird
REEL_ADVANTAGE = 1.5     # Reel-Reichweite muss >= 1.5x das beste andere Format sein

# Reel-lastigeres Muster, das erst bei belegtem Reel-Vorsprung aktiv wird
BASE_PATTERN = ["photo", "photo", "photo", "carousel", "animation", "carousel"]
REEL_HEAVY_PATTERN = ["photo", "photo", "carousel", "animation", "carousel", "animation"]


def _creds():
    ig = os.environ.get("IG_USER_ID")
    tok = os.environ.get("IG_ACCESS_TOKEN")
    envf = HERE / ".env"
    if (not ig or not tok) and envf.exists():
        for l in envf.read_text().splitlines():
            if l.startswith("IG_USER_ID=") and not ig:
                ig = l.split("=", 1)[1].strip()
            if l.startswith("IG_ACCESS_TOKEN=") and not tok:
                tok = l.split("=", 1)[1].strip()
    return ig, tok


def _get(url):
    with urllib.request.urlopen(url, timeout=45) as r:
        return json.loads(r.read().decode())


def _capkey(cap):
    for line in (cap or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def fetch():
    """Gibt (scores_by_capkey, fmt_avg, fmt_n, n_total).
    Leer/0, wenn keine Creds, keine Insights-Berechtigung oder keine Daten."""
    ig, tok = _creds()
    if not ig or not tok:
        return {}, {}, {}, 0
    try:
        feed = _get(f"{GRAPH}/{ig}/media?fields=id,caption,media_type,like_count,comments_count&limit=50&access_token={tok}")
    except Exception:
        return {}, {}, {}, 0
    scores = {}
    by_fmt = {}
    n = 0
    for m in feed.get("data", []):
        inter = (m.get("like_count", 0) or 0) + (m.get("comments_count", 0) or 0)
        reach = 0
        try:
            ins = _get(f"{GRAPH}/{m['id']}/insights?metric=reach,total_interactions&access_token={tok}")
            for d in ins.get("data", []):
                v = (d.get("values") or [{}])[0].get("value", 0)
                if d["name"] == "reach":
                    reach = v
                elif d["name"] == "total_interactions":
                    inter = max(inter, v)
        except Exception:
            pass  # keine Insights-Berechtigung o.ae. -> nur Likes/Kommentare
        if reach <= 0 and inter <= 0:
            continue
        n += 1
        s = reach + 5 * inter
        k = _capkey(m.get("caption"))
        if k:
            scores[k] = max(scores.get(k, 0), s)
        by_fmt.setdefault(m.get("media_type", ""), []).append(reach)
    fmt_avg = {f: sum(v) / len(v) for f, v in by_fmt.items() if v}
    fmt_n = {f: len(v) for f, v in by_fmt.items()}
    return scores, fmt_avg, fmt_n, n


def rank(pool, cap_of, scores, suffix=""):
    """capkey->score fuer diesen Pool; unbekannte Motive = Median (Exploration).
    'suffix' gleicht den Unterschied zwischen internem Pool-Key (cap_of) und dem
    real geposteten Caption-Key aus (Karussell '. Swipe.', Reel '.'), damit die
    live gemessenen Scores korrekt zugeordnet werden.
    Der Rueckgabe-Key ist der interne cap_of-Key (den _pick zum Nachschlagen nutzt).
    Leerer/None scores -> {} (Aufrufer faellt auf normale Rotation zurueck)."""
    if not scores:
        return {}
    keys = [_capkey(cap_of(x)) for x in pool]
    known = [scores[k + suffix] for k in keys if (k + suffix) in scores]
    neutral = median(known) if known else 0
    return {k: scores.get(k + suffix, neutral) for k in keys}


def pattern_for(fmt_avg, fmt_n):
    """Waehlt das Format-Muster datenbasiert. Standard bleibt BASE_PATTERN,
    bis genug Reels mit Daten UND ein klarer Reichweiten-Vorsprung vorliegen."""
    reel_avg = fmt_avg.get("VIDEO", 0)
    reel_n = fmt_n.get("VIDEO", 0)
    others = max(fmt_avg.get("IMAGE", 0), fmt_avg.get("CAROUSEL_ALBUM", 0))
    if reel_n >= MIN_REELS and reel_avg >= REEL_ADVANTAGE * max(others, 1):
        return REEL_HEAVY_PATTERN, True
    return BASE_PATTERN, False
