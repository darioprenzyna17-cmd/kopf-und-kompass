"""
Instagram Graph API Helfer fuer den DC-Autopilot.
Unterstuetzt: Einzelbild, Carousel (2-10 Bilder), Reel (Video).

Zugangsdaten aus Umgebungsvariablen (lokal via .env exportiert, in der Cloud via GitHub-Secrets):
  IG_USER_ID        = Instagram-Business-Konto-ID
  IG_ACCESS_TOKEN   = dauerhafter System-User-Token
  GRAPH_VERSION     = optional, Standard v21.0
"""
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v21.0")

KIE_UPLOAD = "https://kieai.redpandaai.co/api/file-base64-upload"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def env(name):
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Fehlende Umgebungsvariable: {name}")
    return v


def _creds():
    return env("IG_USER_ID"), env("IG_ACCESS_TOKEN")


def _kie_upload(path):
    """Laedt eine lokale Datei in den kie.ai-Speicher und gibt die oeffentliche URL zurueck."""
    key = env("KIE_API_KEY")
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"Bilddatei nicht gefunden: {p}")
    suf = p.suffix.lower()
    mime = "image/jpeg" if suf in (".jpg", ".jpeg") else "image/png" if suf == ".png" else "video/mp4" if suf == ".mp4" else "application/octet-stream"
    raw = p.read_bytes()
    # Eindeutiger Dateiname per Inhalts-Hash: gleiche Basisnamen (slide1.png) in verschiedenen
    # Ordnern kollidieren sonst im kie.ai-Speicher und liefern dieselbe URL zurueck.
    uniq = hashlib.md5(raw).hexdigest()[:12]
    data = base64.b64encode(raw).decode("ascii")
    body = json.dumps({
        "base64Data": f"data:{mime};base64,{data}",
        "uploadPath": "dc-autopilot",
        "fileName": f"{uniq}_{p.name}",
    }).encode("utf-8")
    req = urllib.request.Request(
        KIE_UPLOAD, data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": _UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        j = json.loads(r.read().decode("utf-8"))
    url = (j.get("data") or {}).get("downloadUrl")
    if not url:
        raise RuntimeError(f"kie.ai-Upload fehlgeschlagen: {j}")
    return url


def ensure_public_url(src):
    """Gibt eine oeffentlich erreichbare URL zurueck.
    - http(s)-Quelle: unveraendert (z. B. frische kie.ai-Generierung).
    - lokaler Repo-Pfad: wird zum Postzeitpunkt in den kie.ai-Speicher geladen.
    So bleibt das GitHub-Repo privat.
    """
    if src.startswith("http://") or src.startswith("https://"):
        return src
    p = Path(src)
    if not p.is_absolute():
        p = Path(__file__).parent / src
    return _kie_upload(p)


_TRANSIENT = {403, 429, 500, 502, 503, 504}


def post_form(url, body):
    data = urllib.parse.urlencode(body).encode("utf-8")
    last = None
    for attempt in range(4):  # transiente 403/5xx abfedern
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in _TRANSIENT and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            raise
    raise last


def get_json(url):
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in _TRANSIENT and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            raise
    raise last


def wait_for_finished(container_id, token, timeout_min=10):
    """Pollt einen Container bis status_code == FINISHED (fuer Carousel/Reel noetig)."""
    deadline = time.time() + timeout_min * 60
    last = None
    while time.time() < deadline:
        st = get_json(f"{GRAPH}/{container_id}?fields=status_code&access_token={token}")
        code = st.get("status_code")
        if code != last:
            print(f"  [container {container_id}] {code}")
            last = code
        if code == "FINISHED":
            return True
        if code == "ERROR":
            raise RuntimeError(f"Verarbeitung fehlgeschlagen: {st}")
        time.sleep(6)
    raise TimeoutError(f"container {container_id} nicht fertig nach {timeout_min}min")


def _publish(ig, token, creation_id):
    pub = post_form(
        f"{GRAPH}/{ig}/media_publish",
        {"creation_id": creation_id, "access_token": token},
    )
    mid = pub.get("id")
    if not mid:
        raise RuntimeError(f"publish fehlgeschlagen: {pub}")
    # Post ist live; Link-Abruf darf nicht mehr fehlschlagen lassen
    try:
        info = get_json(f"{GRAPH}/{mid}?fields=permalink&access_token={token}")
        return mid, info.get("permalink", "")
    except Exception:
        return mid, ""


def _caption_key(caption):
    """Eindeutiger Schluessel einer Caption = erste nicht-leere Zeile (der Hook).
    Die Hashtag-/Standortzeilen sind bei allen Posts gleich, nur der Hook ist eindeutig."""
    for line in (caption or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def find_live_by_caption(caption, limit=25, within_minutes=20):
    """Sucht in den letzten Media-Posts des Kontos einen mit gleicher Caption (Hook),
    der INNERHALB der letzten `within_minutes` gepostet wurde.
    Rueckgabe (media_id, permalink) oder (None, None).

    Zweck: Idempotenz gegen Doppel-Posts. Die Instagram-Graph-API meldet gelegentlich
    einen Fehler (z. B. 400 bei Carousels), obwohl der Post trotzdem live gegangen ist.
    Ohne Pruefung bliebe der Eintrag 'pending'/'failed' und der Cron wuerde ihn erneut
    posten.

    WICHTIG: Die Zeitgrenze verhindert Fehlalarme, wenn der Generator dieselbe Caption
    wiederverwendet und ein GLEICHNAMIGER, aber Wochen alter Post noch live ist. Ohne
    Grenze wuerde der neue Post faelschlich als 'schon gepostet' uebersprungen. Nur ein
    Post, der eben erst (innerhalb `within_minutes`) entstand, gilt als Wiedergaenger
    des aktuellen Versuchs."""
    key = _caption_key(caption)
    if not key:
        return None, None
    try:
        ig, token = _creds()
        data = get_json(f"{GRAPH}/{ig}/media?fields=id,caption,permalink,timestamp&limit={limit}&access_token={token}")
    except Exception:
        return None, None
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    for m in (data.get("data") or []):
        if _caption_key(m.get("caption", "")) != key:
            continue
        ts = m.get("timestamp")
        if within_minutes is not None and ts:
            try:
                when = _dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")
                if (now - when).total_seconds() > within_minutes * 60:
                    continue  # zu alt -> nicht derselbe Post-Versuch
            except Exception:
                pass
        return m.get("id"), m.get("permalink", "")
    return None, None


def post_single_image(image_url, caption):
    """Einzelbild-Post. image_url muss oeffentlich erreichbar sein."""
    ig, token = _creds()
    c = post_form(
        f"{GRAPH}/{ig}/media",
        {"image_url": image_url, "caption": caption, "access_token": token},
    )
    cid = c.get("id")
    if not cid:
        raise RuntimeError(f"container fehlgeschlagen: {c}")
    wait_for_finished(cid, token, timeout_min=3)   # verhindert 400 beim zu fruehen Publish
    return _publish(ig, token, cid)


def post_carousel(image_urls, caption):
    """Carousel mit 2 bis 10 Bildern (oeffentlich erreichbare URLs)."""
    if not (2 <= len(image_urls) <= 10):
        raise ValueError(f"Carousel braucht 2-10 Bilder, hat {len(image_urls)}")
    ig, token = _creds()
    children = []
    for i, url in enumerate(image_urls, 1):
        c = post_form(
            f"{GRAPH}/{ig}/media",
            {"image_url": url, "is_carousel_item": "true", "access_token": token},
        )
        cid = c.get("id")
        if not cid:
            raise RuntimeError(f"Child {i} fehlgeschlagen: {c}")
        children.append(cid)
        print(f"  Child {i}/{len(image_urls)}: {cid}")
    parent = post_form(
        f"{GRAPH}/{ig}/media",
        {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
            "access_token": token,
        },
    )
    pid = parent.get("id")
    if not pid:
        raise RuntimeError(f"Carousel-Parent fehlgeschlagen: {parent}")
    wait_for_finished(pid, token, timeout_min=3)
    return _publish(ig, token, pid)


def post_reel(video_url, caption):
    """Reel via oeffentlich erreichbare Video-URL."""
    ig, token = _creds()
    c = post_form(
        f"{GRAPH}/{ig}/media",
        {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
    )
    cid = c.get("id")
    if not cid:
        raise RuntimeError(f"Reel-Container fehlgeschlagen: {c}")
    wait_for_finished(cid, token, timeout_min=10)
    return _publish(ig, token, cid)


def publish_entry(entry):
    """Postet einen Queue-Eintrag je nach Format. Gibt (media_id, permalink) zurueck."""
    fmt = entry.get("format", "image")
    caption = entry.get("caption", "")
    if fmt == "image":
        srcs = entry.get("image_urls") or ([entry["image_url"]] if entry.get("image_url") else [])
        if not srcs:
            raise ValueError("image-Post ohne image_url(s)")
        return post_single_image(ensure_public_url(srcs[0]), caption)
    if fmt == "carousel":
        urls = [ensure_public_url(s) for s in entry["image_urls"]]
        return post_carousel(urls, caption)
    if fmt == "reel":
        return post_reel(ensure_public_url(entry["video_url"]), caption)
    raise ValueError(f"Unbekanntes Format: {fmt}")
