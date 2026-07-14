"""
Wochen-Generator (Weg A, laeuft auf dem Mac, launchd Montag 02:00).
Erzeugt 7 Posts (eine ganze Woche, 1 Post/Tag) im fortlaufenden Muster
Foto, Foto, Foto, Carousel, Animation(Reel, nur Musik), Carousel, ...
Das Muster laeuft ueber die Wochen weiter (state), damit das Profil-Raster saubere
Dreier-Reihen behaelt. Die Uhrzeiten variieren pro Tag, um zu lernen, welcher Tag/welche
Zeit am besten performt (Auswertung spaeter im woechentlichen Report via Insights).
"""
import json
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
STATE = HERE / "gen_state.json"
QUEUE = HERE / "queue.jsonl"
START_OFFSET = 0
DAYS = 7
PATTERN = ["photo", "photo", "photo", "carousel", "animation", "carousel"]  # alt, ersetzt durch SCHEDULE
# Feste Wochen-Routine (Mon=0 .. Sun=6): welcher Typ an welchem Tag.
# "reel" = cineastisches Footage-Reel (build_video_reel.py, Veo + Abnahme). Diese Tage
# ueberspringt der Auto-Generator; die Footage-Reels werden manuell via queue_reel.py
# eingeplant. So laufen die guenstigen Typen automatisch, die teuren gehen durch die Abnahme.
SCHEDULE = {0: "reel", 1: "carousel", 2: "reel", 3: "animation", 4: "carousel", 5: "reel", 6: "photo"}
# Postzeit pro Wochentag aus posting_times.json (Startwerte aus Web-Recherche,
# spaeter vom Lern-Report mit echten Account-Bestwerten ueberschrieben).
PT_FILE = HERE / "posting_times.json"
PT = {k: v for k, v in json.loads(PT_FILE.read_text()).items() if not k.startswith("_")} if PT_FILE.exists() else {}


def time_for(d):
    return PT.get(str(d.weekday()), "12:00:00")
HASH = "#SchweizerKMU #Schweiz #Recruiting #Mitarbeitergewinnung"

STYLE = (" Clean chest-up or waist-up portrait, the person clearly separated from the background, head in the "
         "upper third. NO strong horizontal line, floor edge, counter, workbench or reflective surface cutting "
         "across the person's body or waist. Keep the lower part of the frame soft and uncluttered (room for a "
         "caption banner). Do not crop the body awkwardly. Authentic candid documentary photograph, warm natural "
         "light, real skin texture, shallow depth of field, editorial, 4:5 vertical.")

PHOTOS = [
    {"scene": "a Swiss baker in his 30s in a warm bakery holding fresh bread", "hl": "Fachkräfte sind wie|frisches Brot: früh weg.", "sub": "Sei sichtbar, bevor sie vergriffen sind.", "banner": "dark", "variant": "a"},
    {"scene": "a friendly Swiss female nurse in her 30s in a bright modern care facility, warm smile", "hl": "Pflegekräfte gesucht?|Die suchen nicht zurück.", "sub": "Man erreicht sie nach der Schicht, am Handy.", "banner": "light", "variant": "a"},
    {"scene": "a confident Swiss construction professional in his 40s with a hard hat on a modern site", "hl": "Die Baustelle wartet.|Der Fachmann nicht.", "sub": "Wer zuletzt sichtbar ist, baut mit halbem Team.", "banner": "gold", "variant": "c"},
    {"scene": "a focused Swiss electrician in his 20s working in a modern building, tools in hand", "hl": "Gute Handwerker|findest du nicht mehr.", "sub": "Du musst sie dort abholen, wo sie täglich sind.", "banner": "dark", "variant": "a"},
    {"scene": "a Swiss chef in a professional kitchen plating a dish, steam and warm light", "hl": "Dein Küchenteam|ist unterbesetzt?", "sub": "Wir füllen es, bevor der Service leidet.", "banner": "light", "variant": "c"},
    {"scene": "a Swiss warehouse logistics worker in a modern warehouse with shelves", "hl": "Ohne Leute steht|das Lager still.", "sub": "Wir bringen dir Nachschub an Bewerbern.", "banner": "gold", "variant": "a"},
    {"scene": "a Swiss female hairdresser in a modern salon, warm friendly atmosphere", "hl": "Ein leerer Stuhl|kostet jeden Tag Geld.", "sub": "Wir besetzen ihn, schneller als du denkst.", "banner": "dark", "variant": "c"},
    {"scene": "a Swiss car mechanic in his 30s in a clean modern garage, confident", "hl": "Deine Werkstatt|braucht Hände.", "sub": "Wir bringen dir die richtigen, über Social Media.", "banner": "light", "variant": "a"},
    {"scene": "a Swiss painter in white work clothes in a bright renovated room, roller in hand", "hl": "Auftrag da,|Maler weg?", "sub": "Wir füllen dein Team, bevor der Kunde wartet.", "banner": "gold", "variant": "c"},
    {"scene": "a Swiss landscape gardener working in a green garden with tools, sunny", "hl": "Die Saison läuft.|Das Team fehlt.", "sub": "Wir holen dir die Leute rechtzeitig.", "banner": "dark", "variant": "a"},
    {"scene": "a Swiss office professional in a modern bright office at a laptop, focused", "hl": "Die richtige Fachkraft|sitzt woanders.", "sub": "Wir machen dich sichtbar, genau dort.", "banner": "light", "variant": "a"},
    {"scene": "a Swiss retail salesperson in a modern shop helping arrange products, friendly", "hl": "Leerer Verkauf,|leere Kasse.", "sub": "Wir besetzen deine offenen Stellen schneller.", "banner": "gold", "variant": "c"},
]
CAROUSELS = [
    {"theme": "dark", "slides": [
        {"kind": "cover", "title": "Fachkräftemangel<br>Schweiz 2025", "sub": "4 Zahlen, die jeder KMU-Chef kennen sollte.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "KMU im Alltag", "number": "44%", "fact": "der Schweizer KMU haben regelmässig Mühe, offene Stellen zu besetzen.", "bar": "h", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Insgesamt", "number": "84%", "fact": "finden zumindest teilweise nicht genug geeignetes Personal.", "bar": "v", "barcolor": "white"},
        {"kind": "stat", "kicker": "Am stärksten betroffen", "number": "Bau · Technik · Pflege", "fact": "Hier bleibt der Mangel 2025 am grössten.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Genau dort holen<br>wir dir die Leute.", "sub": "Recruiting über Social Media für Schweizer KMU.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "light", "slides": [
        {"kind": "cover", "title": "Warum ein Inserat<br>nicht mehr reicht", "sub": "3 unbequeme Wahrheiten.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Die Guten", "number": "70%+", "fact": "der Fachkräfte suchen nicht aktiv, sind aber offen für das richtige Angebot.", "bar": "h", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Erster Eindruck", "number": "7 Sek.", "fact": "entscheiden, ob deine Anzeige jemanden stoppt oder weiterscrollt.", "bar": "v", "barcolor": "dark"},
        {"kind": "stat", "kicker": "Wo sie sind", "number": "Jeden Tag", "fact": "scrollen deine Wunschkandidaten durch Social Media.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Zeig dich, wo<br>die Leute sind.", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "dark", "slides": [
        {"kind": "cover", "title": "3 Fehler, die dich<br>Bewerber kosten", "sub": "und wie du sie vermeidest.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Fehler 1", "number": "Warten", "fact": "Wer nur ein Inserat schaltet und wartet, verliert die Wechselwilligen.", "bar": "h", "barcolor": "white"},
        {"kind": "stat", "kicker": "Fehler 2", "number": "Zu langsam", "fact": "Wer Tage bis zur Antwort braucht, hat den Kandidaten längst verloren.", "bar": "v", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Fehler 3", "number": "Unsichtbar", "fact": "Kein Gesicht, keine Kultur, kein Grund zu wechseln.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Machen wir es<br>richtig.", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "light", "slides": [
        {"kind": "cover", "title": "Was Bewerber 2026<br>wirklich wollen", "sub": "3 Dinge, die den Ausschlag geben.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Klarheit", "number": "Ehrlichkeit", "fact": "Zeig, wie der Job wirklich ist. Floskeln überzeugen niemanden.", "bar": "h", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Tempo", "number": "Antwort", "fact": "Wer tagelang wartet, verliert die Guten an die Konkurrenz.", "bar": "v", "barcolor": "dark"},
        {"kind": "stat", "kicker": "Sinn", "number": "Ein Warum", "fact": "Menschen wechseln für Kultur und Perspektive, nicht nur für Lohn.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Zeig, warum man bei<br>dir arbeiten will.", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "dark", "slides": [
        {"kind": "cover", "title": "Warum Social<br>Recruiting funktioniert", "sub": "3 Gründe, warum es besser läuft als jedes Inserat.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Reichweite", "number": "Sichtbar", "fact": "Du erscheinst dort, wo deine Wunschkandidaten täglich Zeit verbringen.", "bar": "h", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Zielgenau", "number": "Passgenau", "fact": "Deine Stelle sieht nur, wer wirklich passt, nicht die ganze Masse.", "bar": "v", "barcolor": "white"},
        {"kind": "stat", "kicker": "Tempo", "number": "Schnell", "fact": "Erste Bewerbungen oft in Tagen, nicht in Monaten.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Bereit für echte<br>Bewerbungen?", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "dark", "slides": [
        {"kind": "cover", "title": "In 4 Schritten<br>zur Besetzung", "sub": "So arbeiten wir mit dir.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Schritt 1", "number": "Schärfen", "fact": "Wir klären gemeinsam, wen du wirklich brauchst.", "bar": "h", "barcolor": "white"},
        {"kind": "stat", "kicker": "Schritt 2", "number": "Ausspielen", "fact": "Anzeige auf Meta und TikTok, zielgenau ausgesteuert.", "bar": "v", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Schritt 3", "number": "Vorfiltern", "fact": "Du sprichst nur noch mit den passenden Leuten.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Sollen wir<br>loslegen?", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
    {"theme": "light", "slides": [
        {"kind": "cover", "title": "Was eine offene<br>Stelle wirklich kostet", "sub": "3 Zahlen, die wehtun.", "bar": "d", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Pro Tag", "number": "Jeden Tag", "fact": "unbesetzt bedeutet Umsatz, der liegen bleibt.", "bar": "h", "barcolor": "gold"},
        {"kind": "stat", "kicker": "Das Team", "number": "Überlastet", "fact": "Die anderen tragen die Lücke, bis sie selbst gehen.", "bar": "v", "barcolor": "dark"},
        {"kind": "stat", "kicker": "Der Ruf", "number": "Sichtbar", "fact": "Dauernd offene Stellen schrecken gute Leute ab.", "bar": "d", "barcolor": "gold"},
        {"kind": "cta", "title": "Besetzen wir<br>sie schneller.", "sub": "Digital Century Group.", "bar": "h", "barcolor": "gold"}]},
]
ANIMS = [
    {"cfg": {"title": "Fachkräftemangel<br>Schweiz 2025",
             "facts": [{"num": 44, "suf": "%", "size": 360, "line": "der KMU haben Mühe,<br>Stellen zu besetzen."},
                       {"num": 84, "suf": "%", "size": 360, "line": "finden nicht genug<br>geeignetes Personal."},
                       {"num": 4, "suf": " von 32", "size": 230, "line": "Berufsgruppen sind<br>noch betroffen."}],
             "story_cap": "Wir bringen die<br>richtigen Leute."},
     "music": "calm modern cinematic corporate background, soft piano and subtle strings, hopeful"},
    {"cfg": {"title": "Recruiting heute<br>ist Marketing",
             "facts": [{"num": 90, "suf": "%", "size": 360, "line": "der Zeit verbringen<br>Kandidaten am Handy."},
                       {"num": 3, "suf": " Sek.", "size": 300, "line": "hast du, um jemanden<br>zu stoppen."},
                       {"num": 1, "suf": " Kanal", "size": 300, "line": "entscheidet heute:<br>Social Media."}],
             "story_cap": "Zeig dich, wo<br>die Leute sind."},
     "music": "modern uplifting corporate background, light beat, motivating, subtle"},
    {"cfg": {"title": "Bewerber ticken<br>heute anders",
             "facts": [{"num": 7, "suf": " Sek.", "size": 320, "line": "entscheiden über<br>Interesse oder Weg."},
                       {"num": 80, "suf": "%", "size": 360, "line": "sind offen, aber<br>nicht aktiv am Suchen."},
                       {"num": 1, "suf": " Chance", "size": 300, "line": "hast du, sie<br>abzuholen."}],
             "story_cap": "Wir holen sie<br>für dich ab."},
     "music": "calm modern cinematic corporate background, soft piano, hopeful, subtle"},
]


def kie_key():
    v = os.environ.get("KIE_API_KEY")
    if v:
        return v
    envf = HERE / ".env"
    if envf.exists():
        for l in envf.read_text().splitlines():
            if l.startswith("KIE_API_KEY="):
                return l.split("=", 1)[1].strip()
    return None


def _capkey(cap):
    for line in (cap or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _pick(pool, key, st, used, cap_of, rank=None):
    """Waehlt das naechste Pool-Element, dessen Caption noch NICHT verwendet/live ist.
    Verhindert, dass wiederkehrende Motive mit noch live Posts kollidieren.
    Mit 'rank' (capkey->Performance-Score) werden bewaehrte Motive zuerst genommen;
    ohne 'rank' bleibt es die bisherige stumpfe Rotation (identisches Verhalten)."""
    n = len(pool)
    if rank:
        order = sorted(range(n), key=lambda i: rank.get(_capkey(cap_of(pool[i])), 0), reverse=True)
        for i in order:
            item = pool[i]; k = _capkey(cap_of(item))
            if k and k not in used:
                used.add(k); st[key] = i + 1; return item
        item = pool[order[0]]  # alle belegt -> bestbewertetes trotzdem
        used.add(_capkey(cap_of(item))); return item
    for _ in range(n):
        item = pool[st[key] % n]; st[key] += 1
        k = _capkey(cap_of(item))
        if k and k not in used:
            used.add(k); return item
    item = pool[st[key] % n]; st[key] += 1  # alle belegt -> trotzdem eines nehmen
    used.add(_capkey(cap_of(item))); return item


KIE = kie_key()
KH = {"Authorization": f"Bearer {KIE}", "Content-Type": "application/json"}
JOBS = "https://api.kie.ai/api/v1/jobs"


def _poll(tid, keys, tries=100):
    for _ in range(tries):
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{JOBS}/recordInfo?taskId={urllib.parse.quote(tid)}", headers=KH), timeout=60).read().decode()).get("data") or {}
        if d.get("state") == "success":
            rj = d.get("resultJson"); rj = json.loads(rj) if isinstance(rj, str) else (rj or {})
            for k in keys:
                if rj.get(k):
                    return rj[k][0] if isinstance(rj[k], list) else rj[k]
        if d.get("state") == "fail":
            raise RuntimeError(d.get("failMsg"))
        time.sleep(4)
    raise TimeoutError(tid)


def gen_photo(prompt, out):
    last = None
    for attempt in range(3):  # robust gegen kie.ai-Aussetzer
        try:
            body = json.dumps({"model": "nano-banana-pro", "input": {"prompt": prompt, "aspect_ratio": "4:5", "resolution": "2K"}}).encode()
            tid = json.loads(urllib.request.urlopen(urllib.request.Request(f"{JOBS}/createTask", data=body, headers=KH, method="POST"), timeout=60).read().decode())["data"]["taskId"]
            url = _poll(tid, ("resultUrls", "imageUrls", "urls", "images"))
            Path(out).write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
            return
        except Exception as e:
            last = e
            print(f"  Foto-Versuch {attempt+1} fehlgeschlagen: {e}, neuer Versuch ...")
            time.sleep(5)
    raise last


def gen_music(prompt, out):
    body = json.dumps({"prompt": prompt, "customMode": False, "instrumental": True, "model": "V4", "callBackUrl": "https://example.com/cb"}).encode()
    tid = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.kie.ai/api/v1/generate", data=body, headers=KH, method="POST"), timeout=60).read().decode())["data"]["taskId"]
    for _ in range(120):
        d = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://api.kie.ai/api/v1/generate/record-info?taskId={tid}", headers=KH), timeout=60).read().decode()).get("data") or {}
        for it in (d.get("response") or d).get("sunoData") or []:
            if isinstance(it, dict) and it.get("audioUrl"):
                Path(out).write_bytes(urllib.request.urlopen(urllib.request.Request(it["audioUrl"], headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
                return
        time.sleep(5)
    raise TimeoutError("music")


def run(py, *args):
    subprocess.run(["python3", str(HERE / py), *[str(a) for a in args]], check=True, cwd=HERE)


def main():
    # Vor dem Generieren mit GitHub syncen (der Poster committet dort laufend) -> sonst schlaegt git push unten fehl
    subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=HERE, check=False)
    subprocess.run(["git", "rebase", "-q", "origin/main"], cwd=HERE, check=False)
    # 1) Aus den Account-Zahlen der letzten Woche lernen (best effort; braucht instagram_manage_insights)
    global PT
    try:
        subprocess.run(["python3", str(HERE / "learn_times.py")], cwd=HERE, timeout=300)
        PT = {k: v for k, v in json.loads(PT_FILE.read_text()).items() if not k.startswith("_")}
    except Exception as e:
        print("Lern-Schritt uebersprungen:", e)
    # 1b) Performance-Schnappschuss loggen (Verlauf in metrics_history.jsonl)
    try:
        subprocess.run(["python3", str(HERE / "track_performance.py")], cwd=HERE, timeout=300)
    except Exception as e:
        print("Tracking-Schritt uebersprungen:", e)
    # 1c) Performance-Gewichtung laden (bewaehrte Motive/Formate bevorzugen; sicher degradierend)
    p_scores, p_fmt, p_n = {}, {}, 0
    try:
        import perf
        p_scores, p_fmt, p_fmt_n, p_n = perf.fetch()
        pattern, reel_heavy = perf.pattern_for(p_fmt, p_fmt_n)
        if p_n:
            print(f"Performance-Gewichtung aktiv ({p_n} Posts mit Daten). Format-Reichweite Ø: {p_fmt}")
            print(f"Muster: {'REEL-lastig' if reel_heavy else 'Standard'} -> {pattern}")
        else:
            print("Performance-Gewichtung: noch keine Daten, normale Rotation + Standard-Muster.")
    except Exception as e:
        pattern = PATTERN
        print("Performance-Gewichtung uebersprungen:", e)

    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    st.setdefault("pattern_pos", 0); st.setdefault("pi", 0); st.setdefault("ci", 0); st.setdefault("ai", 0)
    old = [json.loads(l) for l in QUEUE.read_text().splitlines() if l.strip()] if QUEUE.exists() else []
    used = {_capkey(e.get("caption", "")) for e in old}
    try:  # live Captions vom Konto dazunehmen (best effort, braucht IG-Creds)
        from lib_meta import _creds as _igc, get_json as _igg, GRAPH as _GR
        _ig, _tok = _igc()
        _d = _igg(f"{_GR}/{_ig}/media?fields=caption&limit=50&access_token={_tok}")
        for _m in (_d.get("data") or []):
            used.add(_capkey(_m.get("caption", "")))
        print(f"Dedup-Set: {len(used)} Captions (Queue + live)")
    except Exception as _e:
        print("Live-Captions fuer Dedup uebersprungen:", _e)
    day0 = date.today() + timedelta(days=START_OFFSET)
    tag = day0.strftime("%Y%m%d")
    adir = HERE / "assets" / f"wk_{tag}"; adir.mkdir(parents=True, exist_ok=True)
    entries = []

    # Performance-Ranking je Pool (suffix gleicht Pool-Key vs. geposteten Caption-Key aus)
    import perf as _perf
    r_photo = _perf.rank(PHOTOS, lambda x: x["hl"].replace("|", " "), p_scores)
    r_car = _perf.rank(CAROUSELS, lambda x: x["slides"][0]["title"].replace("<br>", " "), p_scores, ". Swipe.")
    r_anim = _perf.rank(ANIMS, lambda x: x["cfg"]["title"].replace("<br>", " "), p_scores, ".")

    for i in range(DAYS):
        d = day0 + timedelta(days=i)
        typ = SCHEDULE[d.weekday()]
        if typ == "reel":
            print(f"  Tag {i+1}/{DAYS} ({d.strftime('%a')}): Footage-Reel-Slot reserviert (manuell via queue_reel.py)")
            continue
        ptime = time_for(d)
        dt = d.strftime("%Y-%m-%d") + "T" + ptime
        if typ == "photo":
            p = _pick(PHOTOS, "pi", st, used, lambda x: x["hl"].replace("|", " "), r_photo)
            raw = adir / f"photo{i}.jpg"; outp = adir / f"post_photo{i}.png"
            gen_photo("A " + p["scene"] + "." + STYLE, raw)
            run("rr_template.py", "--photo", raw, "--variant", p["variant"], "--banner", p["banner"], "--headline", p["hl"], "--sub", p["sub"], "--out", outp)
            entries.append({"id": f"{tag}-{i}-photo", "datetime": dt, "theme": p["scene"][:30], "format": "image",
                            "image_urls": [f"assets/wk_{tag}/post_photo{i}.png"],
                            "caption": p["hl"].replace("|", " ") + "\n\n" + p["sub"] + "\n\n📍 Schweiz\n" + HASH, "status": "pending"})
        elif typ == "carousel":
            c = _pick(CAROUSELS, "ci", st, used, lambda x: x["slides"][0]["title"].replace("<br>", " "), r_car)
            spec = adir / f"car{i}.json"; spec.write_text(json.dumps(c)); cdir = adir / f"car{i}"
            run("stat_carousel.py", spec, cdir)
            entries.append({"id": f"{tag}-{i}-car", "datetime": dt, "theme": "carousel", "format": "carousel",
                            "image_urls": [f"assets/wk_{tag}/car{i}/slide{n}.png" for n in range(1, 6)],
                            "caption": c["slides"][0]["title"].replace("<br>", " ") + ". Swipe.\n\n📍 Schweiz\n" + HASH, "status": "pending"})
        else:  # animation (ausfallsicher: Zeitlimit + Rueckfall auf fertiges Reel)
            a = _pick(ANIMS, "ai", st, used, lambda x: x["cfg"]["title"].replace("<br>", " "), r_anim)
            acfg = adir / f"anim{i}.json"; acfg.write_text(json.dumps(a["cfg"]))
            raw = adir / f"anim{i}_raw.mp4"; music = adir / f"music{i}.mp3"; fin = adir / f"post_anim{i}.mp4"
            try:
                subprocess.run(["python3", str(HERE / "build_anim.py"), str(raw), str(acfg)], cwd=HERE, check=True, timeout=420)
                gen_music(a["music"], music)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-i", str(music),
                                "-filter_complex", "[1:a]atrim=0:14.3,asetpts=PTS-STARTPTS,volume=0.6,afade=t=in:st=0:d=1.2,afade=t=out:st=12.6:d=1.6[a]",
                                "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(fin)], check=True, timeout=180)
            except Exception as e:
                print(f"  Animation fehlgeschlagen ({e}) -> fertiges Reel als Rueckfall")
                fb = HERE / "assets" / "fallback_anim.mp4"
                subprocess.run(["cp", str(fb), str(fin)], check=True)
            entries.append({"id": f"{tag}-{i}-anim", "datetime": dt, "theme": "animation", "format": "reel",
                            "video_url": f"assets/wk_{tag}/post_anim{i}.mp4",
                            "caption": a["cfg"]["title"].replace("<br>", " ") + ".\n\n📍 Schweiz\n" + HASH, "status": "pending"})
        print(f"  Tag {i+1}/{DAYS} ({typ}) um {ptime} fertig")

    QUEUE.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in old + entries) + "\n")
    STATE.write_text(json.dumps(st))
    subprocess.run(["git", "add", "-A"], cwd=HERE, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"Wochenplan {tag}: 7 Posts (variierende Zeiten)"], cwd=HERE, check=True)
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=HERE, check=True)
    print(f"FERTIG: 7 Posts eingeplant ab {day0}, gepusht.")


def check_env():
    """Validiert die Umgebung (Chrome-Render, ffmpeg, kie.ai-Key) ohne Content zu erzeugen."""
    import shutil
    ok = True
    td = HERE / "assets" / "_check"; td.mkdir(parents=True, exist_ok=True)
    spec = {"theme": "dark", "slides": [
        {"kind": "cover", "title": "Check", "sub": "ok", "bar": "h", "barcolor": "gold"},
        {"kind": "cta", "title": "Check", "sub": "ok", "bar": "h", "barcolor": "gold"}]}
    (td / "spec.json").write_text(json.dumps(spec))
    try:
        subprocess.run(["python3", str(HERE / "stat_carousel.py"), str(td / "spec.json"), str(td)], check=True, cwd=HERE)
        assert (td / "slide1.png").exists()
        print("Chrome-Render: OK")
    except Exception as e:
        ok = False; print("Chrome-Render FEHLER:", e)
    print("ffmpeg:", shutil.which("ffmpeg") or "FEHLT")
    print("kie.ai-Key:", "gesetzt" if kie_key() else "FEHLT")
    if not ok or not shutil.which("ffmpeg") or not kie_key():
        raise SystemExit(1)
    print("ENV-CHECK OK")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check_env()
    else:
        main()
