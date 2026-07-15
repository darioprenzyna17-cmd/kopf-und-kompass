# Designsprache „Archivkino" — Kopf & Kompass (@kopfundkompass)

Verbindliche Bau-Anleitung für autonome Reel-Produktion. Direkt umsetzbar in Chrome-HTML-Render (Text-Overlays), ffmpeg (Schnitt, Grade, Grain, Audio) und Veo/kie.ai (Footage). Kern-Signal: Ruhe. KK wirkt wie ein gefundener 16mm-Film aus einem Archiv, warm, körnig, leicht ausgebleicht, zeitlos, von Hand geschnitten. Sog statt Reiz.

**Bewusst und komplett anders als DC.** DC ist dunkles Navy, gesättigtes Gold, geometrische Sans, gefüllte Gold-Pille, aggressiver Impact. KK ist warmes Filmschwarz, ein einziger kühler Petrol-Akzent nur als Haarlinie, die Serifenschrift Fraunces, keine gefüllte Fläche, keine Härte. Text steht ruhig und lange, wechselt nie zu schnell, ist immer gut leserlich.

---

## 0. Single Source of Truth: die einzige Zahlentafel

Alle Bau-Zahlen stehen genau einmal hier. Renderer und Strategie lesen nur diese Zeilen. Das `kk_style.json`-Preset ist ein reiner Spiegel dieser Tafel.

| Parameter | Kanonischer Wert | Hart / weich |
|---|---|---|
| Gemessene Reel-Länge (ffprobe) | Zielband 18,0 bis 27,0s | weicher Korridor |
| Weiche Warnschwelle | 27,0s (löst Gedanke-Streichen aus) | weich |
| Harte Obergrenze (Fallbeil) | 28,0s (Render fällt durch) | hart |
| Standzeit pro Gedanke | 3,5 bis 5,0s | Floor 3,5s hart |
| Cross-Dissolve-Dauer | 1,0 bis 1,5s (asymmetrisch) | hart als Band |
| Gedanken pro Reel | 3 bis 4 | hart |
| Signatur-Anker (Lexikon) | genau 2 Pflicht: Hook + Schlusskarte | hart |
| Korpus-Zusatzbegriff | höchstens 1 weiterer, oft keiner | hart als Obergrenze |
| Lexikon-Quelle | eine Datei `kk_lexikon.json`, 19 Einträge, davon 8 `aktiv` | einzige Liste |
| Ein-/Ausblende | 900ms / 700ms, Hook 500ms | hart |
| Max. Wörter pro Karte (auch Hook) | 7 | hart |
| Emphasis-Wort pro Karte | max. 1, nur Petrol | hart |
| Default-Modus | Autonom-Standard (Veo + Suno + TTS, Ende zu Ende) | hart |
| Grade-Variante bis Woche-0-Test | `A` provisorisch | Test entscheidet A/B |

**Konfliktregel:** Wo Ruhe und eine Zahl kollidieren, gewinnt die Ruhe. Der Floor Standzeit 3,5s bricht nie zugunsten einer Ziellänge.

**Längen-Logik:** Unterer Rand 18s erlaubt kurze, sehr ruhige 3-Gedanken-Reels. Oberer Bereich weich bei 27s (zuerst Gedanke streichen). Hartes Fallbeil bei 28s ist reines Sicherheitsnetz gegen Ausreisser, nie das Arbeitsziel.

---

## 1. Farbpalette: warmer Korpus, kühler Akzent

**Basis / Grading-Anker (nie reines Schwarz), warm:**
- Filmschwarz warm: `#1A1712`
- Tiefe Schatten: `#241C15`
- Sepia-Mitteltöne: `#4A3F30`

**Text / Licht (nie reines Weiss), warm:**
- Papierweiss (Kernaussagen): `#F2E9D8`
- Gedämpftes Licht: `#E4D5BC`
- Untertext / Meta: `#C9B79A`

**Akzent, kühl (der on-mute-Hebel Nr. 2):**
- Petrol / gedecktes Teal: `#3B6E6A` (Haarlinien, Kicker-Tick, Emphasis-Wort, Endkarten-Haarlinie)
- Lichtes Petrol (dünne Haarlinie auf dunklem Grund): `#5C9089`

Es gibt genau EINE Akzentfarbe: Petrol. Kein warmer Gegenakzent, keine Peak-Ausnahme. Amber lebt nur im Grade selbst (Lichter, Halation) als Teil der warmen Bühne, nie als Marken-Akzentlinie.

**Mischung:** ca. 80% warmes Filmschwarz-Fundament, ca. 15% Papierweiss-Licht, ca. 5% Petrol. Immer nur EINE Akzentfarbe sichtbar. Der Akzent erscheint nur als Haarlinie (max. 2px) oder kleiner Tick, nie als gefüllte Fläche.

**Hartes Verbot (maschinell prüfbar):** kein `#07070d`, kein `#FFC000`, kein gesättigtes Gold, kein `#A85B3C`, kein Terrakotta/Amber/Creme als Akzent, keine geometrische Sans, keine gefüllte CTA-Pille.

---

## 2. Typografie (Google / Open-Source)

- **Kernaussage / Hero: Fraunces** (variabel). `font-optical-sizing:auto`, `opsz` hoch, `SOFT ~40`, `WONK 0`. Gewicht 440 als Untergrenze, `line-height:1.20 bis 1.35`, `letter-spacing:0.01em`.
- **Emphasis-Wort: Fraunces Italic, ausschliesslich Petrol `#3B6E6A`**, mit 200ms verzögertem Fade (nachglühen). Max. 1 Wort pro Karte.
- **Kicker / Lexikon-Begriff / Handle / Meta: Fraunces small-caps**, `text-transform:uppercase`, `letter-spacing:0.30em`, klein, Farbe `#C9B79A`, der Tick davor in Petrol. Keine Sans (stärkster Anti-DC-Move). Fallback nur wenn technisch nötig: Archivo/Inter Tight, uppercase, `0.30em`.

Nie Bold, nie condensed-Impact. Max. 2 Schriftschnitte pro Karte.

**Grössen (Canvas 1080×1920):**
- Kicker / Lexikon-Begriff: 30px, tracking 0.30em (bei schwachem Idiolekt-Test auf 34px anheben)
- Kernaussage: 78 bis 96px, max. 3 Zeilen, `text-wrap:balance`
- Reflexions-Fliesstext: 54 bis 60px, line-height 1.36
- Handle Schlusskarte: 40px small-caps

**Fonts lokal einbinden** (`@font-face` mit lokaler Datei), nicht per Google-`@import`, sonst kein reproduzierbarer Offline-Render.

### 2a. Das KK-Lexikon (eine Liste, eine Datei)

Es gibt genau eine Datei `kk_lexikon.json` mit 19 Begriffen. Jeder Eintrag trägt ein `status`-Feld: `aktiv` oder `reserve`. Genau 8 Einträge sind `aktiv`. Der Generator zieht ausschliesslich aus den `aktiv`-Einträgen. Reserve-Begriffe werden erst nach bestandenem Blindtest freigeschaltet, indem in dieser Datei ein `status` von `reserve` auf `aktiv` gekippt wird. Nie eine zweite Datei, nie eine zweite Liste.

**Die 8 aktiven Begriffe (Kanon):**
1. **Kurskorrektur** (statt „Veränderung")
2. **Peilung** (statt „Richtung/Fokus")
3. **Abdrift** (statt „sich verlieren")
4. **die Nadel** (der innere Wert/Kompass)
5. **losmachen** (statt „loslassen")
6. **Kurs halten** (Disziplin, Dranbleiben)
7. **Gegenwind** (Widerstand von aussen)
8. **wahrer Norden** (der eigene, unbestechliche Wert)

**Die 11 Reserve-Begriffe (gesperrt bis Blindtest):** blinder Kurs, Windschatten, Landmarke, Beikommen, untief, Schlagseite, die Bucht, Ankerlast, Tiefgang, auf Sicht fahren, Landfall.

**Datei-Schema (`kk_lexikon.json`):**
```json
{
  "begriffe": [
    { "term": "Kurskorrektur", "gloss": "statt Veränderung", "status": "aktiv" },
    { "term": "Peilung", "gloss": "statt Richtung/Fokus", "status": "aktiv" },
    { "term": "Abdrift", "gloss": "statt sich verlieren", "status": "aktiv" },
    { "term": "die Nadel", "gloss": "innerer Wert/Kompass", "status": "aktiv" },
    { "term": "losmachen", "gloss": "statt loslassen", "status": "aktiv" },
    { "term": "Kurs halten", "gloss": "Disziplin/Dranbleiben", "status": "aktiv" },
    { "term": "Gegenwind", "gloss": "Widerstand von aussen", "status": "aktiv" },
    { "term": "wahrer Norden", "gloss": "eigener, unbestechlicher Wert", "status": "aktiv" },
    { "term": "blinder Kurs", "gloss": "Handeln ohne Selbstkenntnis", "status": "reserve" },
    { "term": "Windschatten", "gloss": "Bequemlichkeit, stehenbleiben", "status": "reserve" },
    { "term": "Landmarke", "gloss": "fixer Orientierungspunkt", "status": "reserve" },
    { "term": "Beikommen", "gloss": "mühsames Näherkommen", "status": "reserve" },
    { "term": "untief", "gloss": "trügerisch flach, verborgene Gefahr", "status": "reserve" },
    { "term": "Schlagseite", "gloss": "aus dem Gleichgewicht", "status": "reserve" },
    { "term": "die Bucht", "gloss": "geschützter Rückzug", "status": "reserve" },
    { "term": "Ankerlast", "gloss": "Gewicht, das hält/niederdrückt", "status": "reserve" },
    { "term": "Tiefgang", "gloss": "wie tief ein Gedanke reicht", "status": "reserve" },
    { "term": "auf Sicht fahren", "gloss": "Schritt für Schritt ohne Gesamtplan", "status": "reserve" },
    { "term": "Landfall", "gloss": "Ankommen nach langer Passage", "status": "reserve" }
  ]
}
```

**Einsatzregel (gegen den Vokabellisten-Effekt):** Zwingend sind genau die zwei Pflicht-Anker: Hook und Schlusskarte tragen je einen aktiven Begriff. Im Korpus ist höchstens ein weiterer aktiver Begriff erlaubt, oft keiner. Kein Quoten-Ziel, keine Dichte-Vorgabe. QA prüft: kein Reel liest sich wie eine Vokabelliste, kein Begriff stammt von ausserhalb der `aktiv`-Menge, kein Reel läuft ganz ohne Idiolekt.

---

## 3. Textplatzierung, Bewegung, Lesbarkeit (Ruhe first)

**Platzierung:** linksbündig, Text im Band **40% bis 65% der Höhe** (768 bis 1248px), Baseline verankert bei ca. **1210px**. Innenrand 108px seitlich. **Untere 35% (ab 1248px) bleiben frei** von Kernaussage (IG-UI). Oben 230px frei. Über der Aussage: 64px×2px Petrol-Haarlinie plus ggf. Kicker small-caps mit aktivem Lexikon-Begriff.

**Text-Backplate (Pflicht):** weicher radialer Scrim hinter jedem Textblock.
```css
.scrim{position:absolute;inset:0;
 background:radial-gradient(120% 52% at 20% 52%,rgba(26,23,18,.62),transparent 68%)}
```
Scrim-Deckung adaptiv, nie unter 45% im Zentrum bei hellem Footage. Zusätzlich `text-shadow:0 2px 24px rgba(0,0,0,.55)`.

**Dichte und Standzeit:**
- **3 bis 4 Gedanken pro Reel.** Vier ist die Obergrenze für echte Ruhe.
- **Standzeit pro Gedanke 3,5 bis 5,0s. Floor 3,5s hart.** Faustregel Lesezeit = Wortzahl × 0,42s plus 1,6s Puffer, dann auf 3,5 bis 5,0s geklemmt.
- Max. 7 Wörter pro Karte (gilt auch für Hook- und Killer-Zeile). Ein Gedanke = ein Bild.

### Länge: Ruhe bestimmt die Länge, mit hartem Sicherheitsnetz

1. **Floor Standzeit 3,5s ist hart und geht immer vor.** Wird nie unterschritten, um eine Ziellänge zu treffen.
2. **Die Länge folgt aus Ruhe plus Gedankenzahl.** Der Cross-Dissolve überlappt, die reale Timeline ist deshalb kürzer als die naive Clipsumme. Bindend ist die per `ffprobe` gemessene Dauer.
3. **Zielband der gemessenen Länge: 18 bis 27s** (weich). Über 27s: zuerst einen Gedanken streichen (4 auf 3), erst danach wenig Dissolve-Zeit. Standzeit bleibt unberührt. Unter 20s zulässig, wenn drei Gedanken es ruhig füllen, bis hinunter zu 18s.
4. **Hartes Fallbeil 28,0s:** Liegt der Render selbst nach dem Streichen noch über 28,0s, fällt er durch (kein stiller Upload).

**Typische ruhige Konfigurationen (reale ffprobe-Länge, überlappend):**
- 3 Gedanken × 4,5s, Dissolves 1,2s, Schlusskarte 3,5s Halt: gemessen rund **20 bis 21s.**
- 4 Gedanken × 4,0s, Dissolves 1,2s, Schlusskarte 3,5s Halt: gemessen rund **24 bis 26s.**
- 4 Gedanken × 4,5s (Variante B, sehr still): gemessen rund **27s**, oberer Rand, akzeptiert wenn die Ruhe es rechtfertigt.

Die Schlusskarte ist Teil des Ganzen, kein Zusatzbudget.

**Ein-/Ausblende (weich, geatmet):**
```css
@keyframes riseIn{
 0%{opacity:0;filter:blur(10px);transform:translateY(16px) scale(1.0)}
 100%{opacity:1;filter:blur(0);transform:translateY(0) scale(1.006)}
}
.thought{animation:riseIn 900ms cubic-bezier(.22,.61,.36,1) both}
```
Einblende 900ms, Ausblende 700ms (opacity → 0, blur → 4px, translateY 0 → -8px). Über die Standzeit langsamer Scale 1.00 → 1.02 Drift (in Variante B entfällt der Scale). Zeilen-Stagger 120ms bei mehrzeilig. Kein Typewriter, kein Wort-Pop, kein Shake, kein Bounce.

---

## 4. Frame-0-Hook (verbindlich)

- Stärkste, spannungsöffnende Textzeile (Frage/Widerspruch) ab Sekunde 0,0. Erster Gedanke mit verkürzter 500ms-Einblende über einem bereits laufenden Footage-Frame.
- Kein leerer Fade-from-black-Vorlauf. Kein Dip-from-black länger als 300ms.
- Clip 1: die bewegungsstärkste, kompositorisch dichteste Aufnahme.
- Max. 7 Wörter, wie jede Karte.
- **Der Hook trägt einen aktiven Lexikon-Begriff** (Pflicht-Anker Nr. 1), damit das Idiolekt ab Sekunde 0 wirkt.
- Kein Kompass-Motion-Opener.

---

## 5. Schnitt- und Übergangssprache (cineastisch)

- Nur weiche Cross-Dissolves, **1,0 bis 1,5s** (asymmetrisch getimt). Keine Hardcuts, kein Whip, kein Shake, kein Blitz, kein Slow-Mo-Kitsch.
- 3 bis 4 Clips pro Reel, jeder 5 bis 7s.
- **Ken-Burns-Atmung (nur Variante A):** langsamer Push-in 1.00 → 1.04 bis 1.06 pro Clip. In Variante B entfällt der Push.
- **Handgemacht-Trick:** Übergänge asymmetrisch timen (mal 1,0s, mal 1,4s). Text-Cuts nie auf denselben Frame wie Bild-Cuts, Text hält über den Bildwechsel. Übergänge auf Musikpausen/Downbeats.
- **Signature-Übergang „Kalt-Warm-Dissolve" (nur Variante A, sparsam, 1 bis 2× pro Reel):** kurzes weiches Petrol-Aufglimmen (`#3B6E6A`, `blend=mode=screen`, 12 bis 20% Deckung) über den xfade, der nächste Clip taucht aus dem kühlen Schimmer auf.
- Start: max. 300ms Fade-from-warm-black. Ende: 1,2s Fade-to-warm-black `#1A1712` = Anfangsschwarz = nahtloser Loop.

```bash
ffmpeg -i A.mp4 -i B.mp4 -filter_complex \
"[0][1]xfade=transition=fade:duration=1.2:offset=5.8,format=yuv420p" out.mp4
```

**Normalisierung Pflicht vor xfade:** alle Clips auf 24fps, 1080×1920, yuv420p.

---

## 6. Color-Grading

**Variante A (warmer Korpus, kühler Schatten-Unterton):**
```bash
ffmpeg -i in.mp4 -vf "
eq=saturation=0.82:contrast=1.08:brightness=0.01:gamma=1.02,
curves=master='0/0.055 0.22/0.16 0.5/0.5 0.78/0.85 1/0.97',
colorbalance=rs=-0.03:gs=0.01:bs=0.05:rm=0.04:gm=0.0:bm=-0.03:rh=0.06:gh=0.02:bh=-0.05,
colorchannelmixer=rr=1.02:gg=1.0:bb=0.97
" -c:v libx264 -crf 17 -preset slow graded.mp4
```
Schatten leicht ins Petrol gezogen (Teal-Schatten, Warm-Lichter-Trennung), Mitteltöne und Lichter warm. Optionaler Halation-Layer nur an emotionalen Peaks, warm.

**Variante B (still-echt):** `saturation=0.90`, kein Halation, Contrast auf 1.04, flacherer, kühlerer, ruhigerer Look.

### 6a. Die deterministische Signaturschicht (visueller Wiedererkennungs-Träger)

Weil autonomes Veo ein Einzelobjekt über Wochen nicht pixelgleich reproduziert, hängt die Serienwiedererkennung nicht am Footage, sondern an dieser byte-stabilen Schicht, die auf jedem Reel identisch liegt:

1. **Fixe Grade-Kette** (§6, exakt dieselben Filterwerte je Variante).
2. **Fixes Grain-Plate** als 16mm-Overlay (§7), immer dieselbe Datei, `blend=mode=softlight` bei fixer Deckung.
3. **Feste Petrol-Signatur:** Kicker-Tick, Haarlinien, Kalt-Warm-Dissolve, alle aus `#3B6E6A`.
4. **Feste Typo-Signatur:** Fraunces plus small-caps-Lexikon-Kicker, linksbündiges Textband 40 bis 65%, immer gleiche Baseline.
5. **Feste Dissolve-Grammatik** (§5) und **feste Vignette** `PI/5`.
6. **Deterministisch erzeugtes Signatur-Insert:** ein bis zwei Signatur-Objekt-Assets (z. B. eine stilisierte Seekarten-Linie mit Petrol-Nadel im Streiflicht) werden maschinell einmal erzeugt, dann als feste Repo-Assets eingefroren und über Wochen unverändert wiederverwendet. Erzeugungsweg autonom, kein Mensch, kein Dreh: prozedural über den Chrome-Headless-Renderer (SVG/Canvas, gerastert zu PNG plus 2 bis 3s-Loop) oder als einmaliger Bild-Modell-Output, der danach nur wiederverwendet, nie neu generiert wird.

Das Signatur-Insert des Autonom-Standard ist ein maschinell einmal gerendertes, dann eingefrorenes Synthetik-Asset, kein real gefilmtes Objekt. Ein real gedrehtes Signatur-Objekt gehört ausschliesslich in die optionale Dreh-Aufwertung, nie in den Autonom-Standard.

---

## 7. Grain, Vignette, Light-Leaks

**Reihenfolge (verbindlich): Grade → Grain → Light-Leak → Vignette → dann Text-Overlay ganz oben.**
```bash
ffmpeg -i graded.mp4 -vf "
noise=alls=9:allf=t+u,
vignette=PI/5:mode=backward,
gblur=sigma=0.3
" finished.mp4
```
- Grain: `alls=8-12` (Variante A), `alls=5-6` (Variante B), temporal animiert (`t`). Bevorzugt festes 16mm-Grain-Plate via `blend=mode=softlight` bei ca. 15% (Teil der Signaturschicht §6a).
- Vignette: `PI/5`, weich, warm.
- Light-Leaks: nur Variante A, sparsam, 1 bis 2 Peaks, Petrol-Plate (`blend=screen`, 12 bis 20%). In Variante B keine Leaks.
- Mini-`gblur=0.3` bindet Korn und Bild.

---

## 8. Encoding-Härtung gegen Banding
- Export-Bitrate 14 bis 16 Mbit gegen Blockbildung in warmen Schattenflächen nach IG-Rekompression.
- Grain gezielt als Dithering nutzen.
- Export: 1080×1920, H.264 High, 24fps, `-crf 18 -pix_fmt yuv420p`, AAC 320k, Audio -14 LUFS integriert.

---

## 9. Footage-Sprache (Veo als Default, nicht als Wiedererkennungs-Träger)

**Grundsatz:** Veo/kie.ai ist die Standard-Bildquelle, Normalbetrieb vollständig maschinell. Veo liefert die bewegte Atmosphäre (Stimmung, Licht, Textur, langsame Bewegung), nicht die Serienwiedererkennung. Die trägt die deterministische Signaturschicht (§6a).

**Was Veo halten muss:** eine Motiv-Familie, nicht ein Einzelobjekt. Konstant über die Serie sind Kategorie, Farbwelt und Bewegungsart (z. B. Küste zur blauen Stunde, Hände an einem Handwerk von hinten, Papier/Holz/Messing im Streiflicht), festgelegt als fixe Prompt-Bausteine.

**Wie KK trotz KI-Footage nicht generisch wirkt:**
- **Barnum-Blacklist (verboten als Kern-Footage, auch als Veo-Negativliste):** Regen an Glas mit driftendem Bokeh, generischer Nebelwald, Meer im reinen Gegenlicht, Fenster im Gegenlicht, driftende Bokeh-Lichter als Selbstzweck.
- **Motiv-Familie als Prompt-Konstante**, nicht als Anspruch auf pixelgleiche Wiederholung.
- **Keine Menschen frontal, keine Gesichter.** Hände und Rückenfiguren nur in ruhiger, langsamer Bewegung.

**Veo-Prompt (Basis, Motiv-Familie wird eingesetzt):**
> „abstract cinematic 16mm film texture, [MOTIV-FAMILIE], warm faded colors, teal shadows, soft natural light, film grain, muted desaturated palette, no text, no people facing camera, no faces, no rain on glass, no bokeh lights, no window backlight, slow contemplative motion, 9:16 vertical, 24fps"

Bewegung immer langsam. Das maschinell eingefrorene Signatur-Insert (§6a) wird deterministisch eingesetzt.

**Optionale Dreh-Aufwertung:** bei einem Big-Swing kann frisch real gedrehtes Footage (inklusive real gefilmtem Signatur-Objekt) einen Veo-Clip ersetzen. Kür, keine Voraussetzung.

---

## 10. Marken-Device: kein Kompass, nirgends

Gestrichen und verboten: die animierte Kompassnadel, jede Windrosen- oder Kardinalmarken-Grafik, jedes statische Kompass-Symbol. Content-Farm-Signal.

**Das Marken-Device ist einstufig und sprachlich:** der Lexikon-Kicker, ein small-caps aktiver Lexikon-Begriff über der Aussage (`PEILUNG`, `ABDRIFT`, `KURS HALTEN`) mit 64px×2px Petrol-Tick davor. Der Kompass in KK ist ein Wort, kein Bild. Das maschinell erzeugte Signatur-Insert (§6a) ist ausdrücklich keine Kompass-Grafik, sondern ein archivartiger Objekt-Insert.

---

## 11. Schlusskarte (Save/Share/Follow durch Sog)

1. Fade auf warmes Filmschwarz `#1A1712` mit Sepia-Verlauf zur Mitte, Grain und Vignette bleiben. Als schwach durchscheinender Hintergrund dient bevorzugt das maschinell eingefrorene Signatur-Insert (§6a), damit die Schlusskarte über alle Reels visuell identisch ankommt.
2. **Kein Kompass-Symbol.** Die Karte trägt einen aktiven Lexikon-Begriff als sprachlichen Anker (Pflicht-Anker Nr. 2), small-caps, Petrol-Tick, mittig über der CTA (`WAHRER NORDEN`, `PEILUNG`). Musik-Swell oder VO-Schluss löst hier auf.
3. Handle small-caps: `KOPF & KOMPASS`, Papierweiss, tracking 0.30em.
4. Eine leise CTA-Zeile in Fraunces Italic, klein, entsättigt, kein Button, keine Pille. Rotierend, mit aktivem Lexikon-Begriff:
   - Save: *„Speichere das, bevor du wieder abdriftest."*
   - Share: *„Schick es jemandem, der eine Peilung braucht."*
   - Follow: *„Folge, wenn du die Nadel wieder spüren willst."*
   Darunter zeichnet sich eine Petrol-Haarlinie in 600ms (`width 0 → 180px`). Diese Haarlinie ist das einzige grafische Petrol-Element der Karte.
5. `@kopfundkompass` in Meta-Grau, klein.
6. **Standzeit 3,5s**, dann Loop-Schwarz = Anfangsschwarz.

---

## 12. Audio: Musik und Erzähler-Stimme

**Spur 1, Musik (Default: Suno/kie.ai):**
Jeder Suno-Track läuft durch eine automatische Klang-QA:
- `afftdn` konservativ gegen Grundrauschen, `silencedetect` gegen Dropouts, Spektral-Check auf Clipping und Hiss, Loudness- und True-Peak-Messung.
- Tracks, die die QA nicht bestehen, werden verworfen und neu generiert. Erst ein sauberer Track geht in den Mix.

Suno-Prompt-Vorgaben: neoklassisch-cineastisch-ambient, warm, aufrichtend, Solo-Filzklavier plus warme Streicher/Cello, sanfter Sub-Drone, langsamer emotionaler Bogen (Moll zu Dur-Auflösung zur Schlusskarte), 66 bis 72 BPM, keine Drums (max. weicher Herzschlag-Sub), keine Lo-Fi-Textur, kein Vinyl, kein Tape-Hiss.
Post: High-Pass 30Hz, `loudnorm=I=-14:TP=-1.5`, 800ms Fade-in, 2s Fade-out.

**Spur 2, Erzähler-Stimme / VO (feste TTS-Signatur, autonom lieferbar):**
Eine fest gewählte neuronale TTS-Stimme (fixe Voice-ID, langsames Preset, Du-Ansprache) plus eine feste Nachbearbeitungskette, über alle Reels reproduzierbar.

```bash
ffmpeg -i tts_raw.wav -af "
highpass=f=90,
equalizer=f=180:t=q:w=1.0:g=2.0,
equalizer=f=3200:t=q:w=1.4:g=-2.0,
equalizer=f=250:t=q:w=1.2:g=1.5,
acompressor=threshold=-18dB:ratio=3:attack=8:release=180,
aexciter=amount=1.2:blend=0.2,
loudnorm=I=-16:TP=-1.5
" vo.wav
```
Leichter Bauch bei 180 bis 250Hz für Wärme, sanfte Zischlaut-Absenkung bei 3,2kHz gegen den TTS-Metallklang, dezenter Exciter für „leicht rauhe" Textur ohne Rauschen. WhisperX erzeugt Wort-Level-Timestamps, der Generator synchronisiert die VO-Zeile mit dem Einblende-Zeitpunkt der Textkarte (VO-Onset ca. 150ms nach riseIn-Start).

**Mix/Ducking (identisch für TTS und echte Stimme):**
```bash
ffmpeg -i music.mp3 -i vo.wav -filter_complex \
"[1]highpass=f=90,acompressor=threshold=-18dB:ratio=3:attack=8:release=180,\
 loudnorm=I=-16:TP=-1.5[voc];\
 [0][voc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=350[duck];\
 [duck][voc]amix=inputs=2:weights=1 1:normalize=0,\
 loudnorm=I=-14:TP=-1.5[mix]" -map "[mix]" out_audio.m4a
```
- VO-Zielpegel -16 LUFS vor Summenmix, Summenmix -14 LUFS integriert. VO High-Pass 90Hz gegen Rumpeln, De-Esser bei Bedarf, kein hörbares Rauschen.
- **Wann VO:** Pflicht auf Big-Swings, dem wöchentlichen 3er-Set, jeder Serie. Einzelne Nebenreels dürfen musik-only laufen.

**Optionale Dreh-Aufwertung:** ist ein Mensch verfügbar, kann eine echte, line-by-line aufgenommene Stimme die TTS auf einem Big-Swing ersetzen. Kür, keine Voraussetzung.

---

## 13. Produktions-Pipeline (Autonom-Standard = Normalbetrieb)

**Der Normalbetrieb ist der vollständige Autonom-Standard:** eine Maschine baut das Reel Ende zu Ende aus Veo-Atmosphäre-Footage, dem maschinell eingefrorenen Signatur-Insert (§6a), Suno-Musik, TTS-VO mit fester Stimm-Signatur und Chrome/ffmpeg-Montage, ohne Menschen im Loop.

Die **Dreh-Aufwertung** ist eine optionale Qualitätsstufe, kein Pflicht-Gate. Fehlt der Mensch, läuft alles im Autonom-Standard weiter.

**Autonom-Standard-Stufen (alle maschinell):**
1. **Skript-JSON:** 3 bis 4 Gedanken (Text, Standzeit auf 3,5 bis 5,0s geklemmt, aktive Lexikon-Begriffe mit Pflicht-Anker auf Hook und Schlusskarte, höchstens 1 weiterer Korpusbegriff, optional 1 Emphasis-Wort Petrol, Sub-Zeile, max. 7 Wörter/Karte). Erster Gedanke = Spannungsöffner (§4).
2. **Footage:** Veo-Atmosphäre-Clips mit Motiv-Familie-Prompt und Barnum-Negativliste (§9), plus deterministischer Einbau des eingefrorenen Signatur-Inserts (§6a).
3. **Musik:** Suno-Track durch Klang-QA (§12).
4. **VO:** falls Big-Swing/3er-Set/Serie: TTS mit fester Voice-ID und Signaturkette (§12), WhisperX-Alignment, Ducking.
5. **Normalisieren:** alle Clips → 24fps, 1080×1920, yuv420p.
6. **Chrome-Headless:** Textkarten als PNG-Sequenz mit Alpha, Fonts lokal, CSS §2/§3. Keine Kompass-Mark.
7. **ffmpeg Footage:** graden (§6) → Grain/Vignette (§7) → xfade-Dissolves (§5, überlappend) → Kalt-Warm-Dissolve 1 bis 2× (nur Variante A).
8. **ffmpeg Composite:** PNG-Alpha-Overlay nach dem Grade `overlay`en (scharf, ungrainy).
9. **ffmpeg Audio:** Musik plus ggf. VO mischen und ducken (§12), loudnorm -14 LUFS, Fades.
10. **Export plus Längen-Check:** §8-Specs, dann `ffprobe`. Gemessene Dauer im Zielband 18 bis 27s. Über 27,0s: Gedanke streichen (4 → 3), danach Dissolves minimal kürzen, nie die Standzeit. Über 28,0s selbst nach Streichen: harter Fehlschlag, kein Upload.

```bash
# Render
ffmpeg -i graded_timeline.mp4 -framerate 24 -i text_%04d.png \
-filter_complex "[0][1]overlay=0:0:format=auto,format=yuv420p" \
-i out_audio.m4a -shortest -c:v libx264 -crf 18 -b:v 15M -pix_fmt yuv420p final.mp4

# Längen-Check: weiches Zielband 18-27s + hartes Fallbeil 28s
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 final.mp4)
awk -v d="$DUR" 'BEGIN{
  if (d+0 > 28.0)      { print "FAIL (hart): "d"s > 28.0s -> Render verwerfen"; exit 2 }
  else if (d+0 > 27.0) { print "TRIM (weich): "d"s > 27.0s -> Gedanke streichen"; exit 1 }
  else if (d+0 < 18.0) { print "WARN (sehr kurz): "d"s < 18.0s"; exit 1 }
  else if (d+0 < 20.0) { print "OK (kurz, zulaessig): "d"s" }
  else                 { print "OK: "d"s" }
}'
```

**`kk_style.json`-Preset (Serien-Konstanten, reiner Spiegel von §0):** Palette-Hex §1, Fraunces min-weight 440, Grade-Kette §6 (A) plus Variante-B-Werte, Grain alls=8-12 (A) / 5-6 (B), Vignette PI/5, Dissolve 1,0 bis 1,5s asymmetrisch, Text-Standzeit 3,5 bis 5,0s (Floor 3,5s hart), Ein-/Ausblende 900/700ms (Hook 500ms), Scrim-Floor 45%, keine Kompass-Mark, eingefrorenes Signatur-Insert §6a, Suno-QA-Kette §12, TTS-Signaturkette plus feste Voice-ID §12, VO-Ducking-Kette §12, Lexikon `kk_lexikon.json` (8 aktiv / 11 reserve), Text-Band 40 bis 65%, Zielband 18 bis 27s (weich) plus Fallbeil 28s (hart), 3 bis 4 Gedanken, max. 7 Wörter/Karte, Export 24fps/15Mbit/-14 LUFS, Flag `modus:"autonom-standard"|"dreh-aufwertung"` (Default `autonom-standard`) und `look:"A"|"B"`.

---

## 14. Woche-0-Tests (beide schlank)

**Grade-Test (A vs B):** EIN Stumm-Test. Hält der Look den Blick 3s? Entscheidet die Grade-Intensität.
- **Variante A, reich-cineastisch:** Halation, Light-Leak, Ken-Burns.
- **Variante B, still-echt:** weniger Halation, kein Light-Leak, Grain reduziert (`alls=5-6`), kein Ken-Burns-Push, mehr Leerraum, Standzeiten am oberen Rand.

**Idiolekt-Test:** 12 bis 15 Zielgruppen-Personen bekommen einen gemischten Stapel stehender Textkarten (stumm, Handle ab), echte KK-Karten und warme Benchmark-Karten ohne Idiolekt. Aufgabe: gruppieren nach „welche gehören zum selben Absender".
- Wird über die Sprache geclustert: der sprachliche Moat trägt, skalieren.
- Wird über den Look geclustert: Lexikon-Begriff früher und grösser in den Frame (§2 auf 34px), Test einmal wiederholen.

Test-unabhängig fix: Fraunces, Lexikon, Petrol-Akzent, Safe-Zone und Pacing, weiche Dissolves, Schlusskarte ohne Kompass, die deterministische Signaturschicht. Bis der Grade-Test entschieden ist, gilt A provisorisch.

---

## 15. Verbindliche Guardrails (maschinell prüfbar)

- Nur Fraunces (plus small-caps/italic). Keine Sans als Headline.
- Nur Palette-Hex §1. Kein `#07070d`, kein `#FFC000`, kein gesättigtes Gold, kein `#A85B3C`/Terrakotta/Amber/Creme als Akzent. Akzent ausschliesslich Petrol `#3B6E6A`, kühl, nur als Haarlinie oder Tick.
- **Lexikon: genau eine Liste, eine Datei `kk_lexikon.json`, 8 `aktiv`, 11 `reserve`.** Generator zieht nur aus `aktiv`. Hook und Schlusskarte tragen je einen aktiven Begriff, im Korpus höchstens ein weiterer, kein Quoten-Ziel, kein Begriff ausserhalb `aktiv`, kein Reel ganz ohne Idiolekt.
- Max. 1 Emphasis-Wort/Karte (nur Petrol), max. 7 Wörter/Karte (auch Hook/Killer-Zeile).
- **3 bis 4 Gedanken pro Reel, Standzeit 3,5 bis 5,0s, Floor 3,5s hart.** Länge folgt aus Ruhe, Zielband gemessen 18 bis 27s (weicher Check), hartes Fallbeil 28s. Bei Überlänge zuerst Gedanke streichen, dann Dissolve kürzen, nie Standzeit.
- **Text im Band 40 bis 65% Höhe, untere 35% frei.** Jede Blende min. 0,7s, jeder Übergang Cross-Dissolve 1,0 bis 1,5s. Keine Hardcuts, kein Shake, kein Blitz, kein Slow-Mo.
- **Footage Default: Veo/kie.ai als Atmosphäre mit Motiv-Familie-Prompt und Barnum-Negativliste, keine Gesichter, keine Menschen frontal.** Serienwiedererkennung trägt die deterministische Signaturschicht plus das eingefrorene Signatur-Insert (§6a). Ein real gedrehtes Signatur-Objekt existiert nur in der Dreh-Aufwertung.
- **Kein Kompass-Element, weder animiert noch statisch, nirgends.**
- **Audio Default: Suno/kie.ai mit bestandener Klang-QA (kein Knistern, kein Lo-Fi, kein Hiss). VO Default TTS mit fester Voice-ID und Signaturkette, Pflicht auf Big-Swings/3er-Set/Serie**, WhisperX-Alignment plus sidechaincompress-Ducking.
- CTA immer Text oder Outline, nie gefüllt. Grammatik korrekt, keine langen Gedankenstriche, kein Komma vor „und".
- Export min. 14 Mbit gegen Dunkelflächen-Banding.
- **Default-Modus `autonom-standard`** (Veo plus eingefrorenes Signatur-Insert plus Suno plus TTS-Signatur, Ende zu Ende ohne Mensch). Dreh-Aufwertung ist optionale Aufwertung, nie Voraussetzung.

---

## 16. Ziel-Ehrlichkeit

Die Zielzeile lautet „+5000 in 4 Wochen" (35k auf 40k). Diese Designsprache trägt das Ziel als Chance, nicht als Zusage.

- **+5000 in genau 4 Wochen ist kein planbarer Erwartungswert, sondern ein oberes Los mit rund 12 bis 20% Chance,** getragen von einem einzelnen viral gehenden Big-Swing.
- **Realistischer Erwartungswert bei voller Konfiguration** (10 bis 12 Collabs, 40 bis 50 aktiv gestellte Anfragen, ein Big-Swing-Reel pro Woche mit VO): **+2.600 bis +4.200 Follower.**
- **Verlässlicher Boden** aus Designsprache plus normaler Kadenz ohne Maximal-Aufwand: **+1.700 bis +2.900.**

Diese Designsprache maximiert die Wahrscheinlichkeit des +5000-Loses, statt sie zu behaupten: volle Collab-Konfiguration, mindestens ein Big-Swing pro Woche, on-mute-Signale (Lexikon plus Petrol plus deterministische Signaturschicht), die Save/Share/Follow über die vier Wochen hinaus zu Kohorten-Compounding aufbauen. Ruhe und Vollendbarkeit (drei bis vier tiefe Gedanken statt Reichweiten-Tricks) sind der Retention-Motor, der ein Los überhaupt erst virusfähig macht.