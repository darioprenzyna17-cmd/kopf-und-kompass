# PRODUKTIONS-BLUEPRINT @kopfundkompass — Wie EIN Reel autonom entsteht

Dieses Dokument ist die Schritt-fuer-Schritt-Bauanleitung fuer genau ein Reel im **Autonom-Standard** (Default, kein Mensch im Loop ausser der vorgelagerten Satz-Kuratierung). Alle Zahlen sind bereits konfliktbereinigt: Wo Strategie und Designsprache sich widersprachen, gewinnt die Strategie. Die Maschine liest Pacing aus dieser Spezifikation und Begriffe ausschliesslich aus `kk_lexikon.json`. Sie stellt keine Rueckfragen.

---

## 0. Eingaben, die vor dem Lauf feststehen

Die Maschine startet mit fixen Assets aus Woche 0. Fehlt eines, bricht der Lauf ab, statt zu improvisieren.

- `kk_lexikon.json` mit genau 8 aktiven Begriffen (`status:"aktiv"`): **Kurskorrektur, die Peilung, Abdrift, die Nadel, Kurs halten, losmachen, wahrer Norden, auf Sicht fahren.** Alles andere ist gesperrt und fuer den Generator unsichtbar. (Kanonisch nach Strategie: "Gegenwind" ist NICHT aktiv, es steht nicht im 8er-Kern der Strategie.)
- `kk_style.json`: Palette, Fraunces-Setzung, Grade-Kette, Grain, Vignette, Ein-/Ausblende, Scrim-Floor, Suno-QA-Kette, TTS-Voice-ID plus Signaturkette, Grade-Variante-Flag (`A` provisorisch bis Woche-0-Test).
- Satz-Bank mit Klassen-Tag (`save`/`send`), Thema, und den Gate-Ergebnissen aus Abschnitt 3 der Strategie.
- Content-Slot des Tages: Format (1/2/3), Thema aus dem "Kurs der Woche", VO ja/nein (VO Pflicht bei Big-Swing, 3er-Set, Serien-Segment, sonst musik-only).
- Eingefrorenes Signatur-Insert (maschinell einmal gerendert, dann Repo-Asset).

**Ein Reel = ein Hero-Satz plus 2 bis 3 stuetzende Beats.** Der Satz kommt aus der Bank, die Maschine erfindet ihn nicht.

---

## 1. Skript-JSON bauen (die Blaupause des Reels)

Die Maschine erzeugt zuerst ein Skript-JSON, das jede spaetere Stufe deterministisch fuettert.

**Gedankenzahl:** 3 ist der Sweet Spot, 4 die Obergrenze, 3 der harte Boden. Default 3, ausser das Format "Wenn du das gerade brauchst" braucht 4 Beats.

**Pro Gedanke:**
- Text, maximal etwa **6 Woerter pro Zeile**, maximal **2 Zeilen gleichzeitig**. (Kanonisch nach Strategie, nicht der Design-Deckel von 7 Woertern pro Karte, weil zweizeilige Beats erlaubt bleiben muessen.)
- Killer-/Hook-Zeile: 5 bis 7 Woerter.
- Standzeit, berechnet als `Lesezeit = Wortzahl × 0,42s + 1,6s`, dann hart geklemmt auf **3,5 bis 5,0s**. Der Boden 3,5s bricht nie.
- Optional 1 Emphasis-Wort, ausschliesslich Petrol `#3B6E6A`, Fraunces Italic, 200ms verzoegertes Nachgluehen. Nie mehr als eines pro Karte.

**Signatur-Gate (2 Pflicht-Anker, hart):**
- Der erste Gedanke (Hook/Killer-Zeile) traegt **genau einen aktiven Lexikon-Begriff.**
- Die Schlusskarte traegt **genau einen aktiven Lexikon-Begriff.**
- Im Korpus dazwischen: hoechstens ein weiterer aktiver Begriff, oft keiner. **Kein Quoten-Ziel, kein Stempel auf jeder Karte, kein Zwei-Drittel-Korridor.** Wer Nautik auf jede Karte zwingt, produziert die abstossende Vokabellisten-Dichte, die die Strategie verwirft.
- Kein gesperrter Begriff, kein Begriff ausserhalb der 8er-Aktiv-Menge.

**Frame-0-Regel:** Der erste Gedanke ist ein Spannungsoeffner (Frage oder Widerspruch), erscheint innerhalb 0,3s ueber bereits laufendem Footage, mit verkuerzter 500ms-Einblende. Kein leerer Fade-from-black-Vorlauf laenger als 300ms.

**Bookend/Loop:** Die Schluss-Zeile fuehrt sinngemaess zu Zeile 1 zurueck, damit der Loop sprachlich schliesst.

---

## 2. Footage via Veo (kie.ai): Prinzipien, Shots, Timing

Veo liefert **Atmosphaere, nicht Wiedererkennung.** Die Serienwiedererkennung traegt die deterministische Huelle (Grade, Petrol-Akzent, Serif, Komposition, Loop) plus das eingefrorene Signatur-Insert, nicht das Veo-Motiv.

**Anzahl Shots:** 3 bis 4 Atmosphaere-Clips pro Reel, einer pro Gedanke, jeder 5 bis 7s Rohlaenge (laenger als die Standzeit, damit der Dissolve Reserve hat). Ein Gedanke = ein Bild.

**Prompt-Prinzipien (fixe Bausteine, damit die Motiv-Familie konstant bleibt):**
- Eine feste **Motiv-Familie** ueber die Serie: Kategorie, Farbwelt und Bewegungsart konstant (z. B. Kueste zur blauen Stunde, Material im Streiflicht, Ruecken-/Handbewegung an einem Handwerk). Nicht ein pixelgleiches Objekt, das kann Veo ueber Wochen nicht.
- Enges Tonwert-Band, atypischer spezifischer Ort-Typ, wo die API es zulaesst wiederverwendete Seeds.
- **Barnum-Blacklist als harte Negativliste:** kein Regen an Glas mit Bokeh, kein generischer Nebelwald, kein Meer im reinen Gegenlicht, kein Fenster im Gegenlicht, keine driftenden Bokeh-Lichter als Selbstzweck. Diese Median-Motive sind zugleich generisch und KI-Label-riskant.
- **Keine Gesichter, keine Menschen frontal.** Haende und Rueckenfiguren nur in langsamer Bewegung. Menschliche Figuren sind autonom nicht auf Artefakte pruefbar, deshalb bleibt der Autonom-Standard hand- und gesichtsfrei.
- Bewegung immer langsam und kontemplativ.

**Prompt-Basis:**
> "abstract cinematic 16mm film texture, [MOTIV-FAMILIE], warm faded colors, teal shadows, soft natural light, film grain, muted desaturated palette, no text, no people facing camera, no faces, no rain on glass, no bokeh lights, no window backlight, slow contemplative motion, 9:16 vertical, 24fps"

**N-aus-M-Regenerier-Loop:** Pro Shot mehrere Takes ziehen, automatisch verwerfen per Frame-Difference (zu wenig Bewegung), Optical-Flow (zu hektisch), Schwarzframe-Filter. Nur der beste Take geht weiter. Grundsatz: die Quelle einschraenken, nicht in der Post reparieren.

**Signatur-Insert:** Das maschinell einmal gerenderte, dann eingefrorene Synthetik-Asset (prozedural via Chrome-Headless SVG/Canvas oder einmaliger Bild-Modell-Output, danach nur wiederverwendet, nie neu generiert) wird deterministisch eingebaut und traegt spaeter auch die Schlusskarte. **Kein reales Foto, kein Dreh, keine Insert-Plate im Autonom-Standard.** Ein real gedrehtes Signatur-Objekt gaebe es nur in der Dreh-Aufwertung.

**Kein Kompass, nirgends.** Keine Nadel, keine Windrose, kein Kompass-Icon, weder im Footage noch im Insert.

---

## 3. Schnitt-Timing (cineastisch, wie von Hand)

**Uebergaenge:** ausschliesslich weiche Cross-Dissolves, **1,0 bis 1,5s**, asymmetrisch getimt (mal 1,0s, mal 1,4s, das ist der Handgemacht-Trick). **Keine Hardcuts, kein Whip, kein Shake, kein Blitz, kein Slow-Mo-Kitsch.**

**Bewegung im Bild:** konstante Mikro-Bewegung traegt die Watch-Time, nicht Schnitt-Tempo. Variante A: langsamer Ken-Burns-Push 1.00 → 1.04-1.06 pro Clip. Variante B: kein Push, mehr Ruhe.

**Text-Cuts nie auf denselben Frame wie Bild-Cuts.** Text haelt ueber den Bildwechsel. Uebergaenge sitzen auf Musikpausen/Downbeats.

**Normalisierung Pflicht vor xfade:** alle Clips auf 24fps, 1080×1920, yuv420p.

```bash
ffmpeg -i A.mp4 -i B.mp4 -filter_complex \
"[0][1]xfade=transition=fade:duration=1.2:offset=5.8,format=yuv420p" out.mp4
```

**Loop:** Start max. 300ms Fade-from-warm-black. Ende 1,2s Fade-to-warm-black `#1A1712`, das exakt dem Anfangsschwarz entspricht, damit der Loop nahtlos schliesst.

**Laengen-Budget (die einzige Regel, kanonisch aus Strategie Abschnitt 5):**
- Planungsrechnung wie im Strategie-Beispiel: Standzeiten plus Dissolves plus Schlusskarte. Beispiel 3 Gedanken × 4,5s + 2 Dissolves × 1,25s + 2,5s Schlusskarte ≈ 18,5s. 4 Gedanken × 4,5s ≈ 24s.
- **Schlusskarte-Halt: bis 2,5s** (kanonisch Strategie, nicht 3,5s).
- **Zielband: 18 bis 27s gemessene ffprobe-Timeline.**
- **Harter Deckel 28,0s mit Fallbeil.** Liegt der Render darueber, greift diese feste Reihenfolge: erstens einen Gedanken streichen (bis Boden 3), zweitens Dissolves auf 1,0s straffen, drittens und nur zuletzt die Standzeit senken, **nie unter 3,5s.** So bleibt Ruhe die Konstante, die Gedankenzahl die Variable. Der Deckel ist ein Fallbeil gegen Ausreisser, kein Taktgeber gegen die Ruhe.

---

## 4. Text-Overlays via Chrome-HTML-Render

Textkarten werden als PNG-Sequenz mit Alpha gerendert, Fonts lokal per `@font-face`, dann nach dem Grade per `overlay` scharf drueber.

**Typografie:** Fraunces (variabel, Gewicht ≥ 440, `opsz` hoch, `SOFT ~40`, `line-height 1.20-1.35`, `letter-spacing 0.01em`). Kicker/Lexikon-Begriff in Fraunces small-caps, uppercase, `letter-spacing 0.30em`, 30px, Farbe `#C9B79A`, mit 64px×2px Petrol-Tick davor. **Keine Sans als Headline** (staerkster Anti-DC-Move). Max. 2 Schriftschnitte pro Karte, nie Bold, nie condensed-Impact.

**Groessen (Canvas 1080×1920):** Kernaussage 78-96px (max. 3 Zeilen, `text-wrap:balance`), Reflexions-Fliesstext 54-60px, Handle Schlusskarte 40px small-caps.

**Platzierung / Safe-Zone:** Text linksbuendig im **Band 40 bis 65 Prozent Hoehe (768-1248px)**, Baseline bei ca. 1210px. Innenrand 108px. **Untere 35 Prozent frei** (IG-UI), oben 230px frei. Baseline bei etwa 71 Prozent ist verboten, sie laeuft in die UI.

**Scrim (Pflicht):** weicher radialer Scrim hinter jedem Textblock, Deckung adaptiv per `signalstats` YAVG auf der Textregion, ausgewertet als **Worst-Case ueber alle Frames der Zeile**, nie unter 45 Prozent im Zentrum bei hellem Footage. Zusaetzlich `text-shadow:0 2px 24px rgba(0,0,0,.55)`.

```css
.scrim{position:absolute;inset:0;
 background:radial-gradient(120% 52% at 20% 52%,rgba(26,23,18,.62),transparent 68%)}
@keyframes riseIn{
 0%{opacity:0;filter:blur(10px);transform:translateY(16px)}
 100%{opacity:1;filter:blur(0);transform:translateY(0)}}
.thought{animation:riseIn 900ms cubic-bezier(.22,.61,.36,1) both}
```

**Text-Timing:** Einblende 900ms, Ausblende 700ms (opacity → 0, blur → 4px, translateY 0 → -8px). Hook verkuerzt auf 500ms, sichtbar innerhalb 0,3s. Zeilen-Stagger 120ms bei mehrzeilig. **Kein Typewriter, kein Wort-Pop, kein Shake/Bounce.** Die Standzeit aus Schritt 1 (3,5 bis 5,0s) ist die volle Lesezeit bei voller Deckkraft, grosszuegig, nicht gequetscht.

---

## 5. Grade, Grain, Vignette (die deterministische Huelle)

Feste Reihenfolge: **Grade → Grain → Light-Leak → Vignette → dann Text-Overlay ganz oben.**

```bash
# Grade (Variante A)
ffmpeg -i in.mp4 -vf "
eq=saturation=0.82:contrast=1.08:brightness=0.01:gamma=1.02,
curves=master='0/0.055 0.22/0.16 0.5/0.5 0.78/0.85 1/0.97',
colorbalance=rs=-0.03:gs=0.01:bs=0.05:rm=0.04:gm=0.0:bm=-0.03:rh=0.06:gh=0.02:bh=-0.05,
colorchannelmixer=rr=1.02:gg=1.0:bb=0.97
" -c:v libx264 -crf 17 -preset slow graded.mp4

# Grain + Vignette
ffmpeg -i graded.mp4 -vf "noise=alls=9:allf=t+u,vignette=PI/5:mode=backward,gblur=sigma=0.3" finished.mp4
```

Schatten leicht ins Petrol, Mitteltoene und Lichter warm. Grain `alls=8-12` (A) bzw. `5-6` (B), bevorzugt festes 16mm-Grain-Plate via `blend=mode=softlight` bei ca. 15 Prozent. Vignette `PI/5`. Light-Leaks nur Variante A, sparsam, 1 bis 2 Peaks, Petrol-Plate (`blend=screen`, 12-20 Prozent). Variante B: `saturation=0.90`, `contrast=1.04`, keine Halation, keine Leaks, kein Ken-Burns.

**Signature-Uebergang "Kalt-Warm-Dissolve"** (nur Variante A, 1 bis 2× pro Reel): kurzes Petrol-Aufglimmen ueber dem xfade, der naechste Clip taucht aus dem kuehlen Schimmer auf.

**Farb-Guardrails (maschinell geprueft):** nur Palette-Hex. Verboten `#07070d`, `#FFC000`, gesaettigtes Gold, `#A85B3C`, Terrakotta/Amber/Creme als Akzent, geometrische Sans, gefuellte CTA-Pille. Petrol `#3B6E6A` erscheint nur als Haarlinie (max. 2px) oder kleiner Tick, nie als gefuellte Flaeche. Sichtbar immer nur EINE Akzentfarbe.

---

## 6. Musik via Suno (kie.ai) mit Rausch-QA

**Suno-Prompt:** neoklassisch/cineastisch-ambient, warm, aufrichtend, Solo-Filzklavier plus warme Streicher/Cello, sanfter Sub-Drone, langsamer Bogen (Moll nach Dur-Aufloesung zur Schlusskarte), 66-72 BPM, keine Drums (max. weicher Herzschlag-Sub), **keine Lo-Fi-Textur, kein Vinyl, kein Tape-Hiss.** Laengengenau auf die geplante Reel-Dauer.

**Klang-QA (jeder Track, autonom):** `afftdn` konservativ gegen Grundrauschen, `silencedetect` gegen Dropouts, Spektral-Check auf Clipping und Hiss, Loudness/True-Peak-Messung. **Tracks, die durchfallen, werden verworfen und neu gezogen.** Erst ein sauberer Track geht in den Mix. So wird die "kein Rauschen"-Vorgabe auch autonom eingehalten.

Post: High-Pass 30Hz, `loudnorm=I=-14:TP=-1.5`, 800ms Fade-in, 2s Fade-out.

---

## 7. Erzaehler-Stimme (VO), nur wenn tragend

VO nur bei Big-Swing, gepinntem 3er-Set, Serien-Segment. Nebenreels laufen musik-only mit fester Standzeit (70 bis 85 Prozent der Discovery passieren ohnehin lautlos, die Stimme ist Bindungs-Bonus, kein Discovery-Hebel).

**Autonom lieferbar ist Konsistenz, nicht warmes Timbre.** Eine fest gewaehlte neuronale TTS-Stimme (fixe Voice-ID, langsames Preset, Du-Ansprache, 4 Wochen eingefroren) plus feste Nachbearbeitungskette. Die warme, leicht rauhe menschliche Faerbung gehoert ausdruecklich in die Dreh-Aufwertung, nicht in den Default.

```bash
ffmpeg -i tts_raw.wav -af "
highpass=f=90,
equalizer=f=180:t=q:w=1.0:g=2.0,
equalizer=f=3200:t=q:w=1.4:g=-2.0,
equalizer=f=250:t=q:w=1.2:g=1.5,
acompressor=threshold=-18dB:ratio=3:attack=8:release=180,
aexciter=amount=1.2:blend=0.2,
loudnorm=I=-16:TP=-1.5" vo.wav
```

WhisperX erzeugt Wort-Level-Timestamps, jede VO-Zeile als eigene Datei. VO-Onset ca. 150ms nach riseIn-Start der zugehoerigen Textkarte, Alignment nur innerhalb der Zeile fuer die Overlay-Fades.

---

## 8. Composite und Audio-Mix

```bash
# PNG-Alpha-Overlay ueber den Grade
ffmpeg -i graded_timeline.mp4 -framerate 24 -i text_%04d.png \
-filter_complex "[0][1]overlay=0:0:format=auto,format=yuv420p" \
-i out_audio.m4a -shortest -c:v libx264 -crf 18 -b:v 15M -pix_fmt yuv420p final.mp4
```

**Audio-Mix mit Ducking** (Musik unter der Stimme):

```bash
ffmpeg -i music.mp3 -i vo.wav -filter_complex \
"[1]highpass=f=90,acompressor=threshold=-18dB:ratio=3:attack=8:release=180,\
 loudnorm=I=-16:TP=-1.5[voc];\
 [0][voc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=350[duck];\
 [duck][voc]amix=inputs=2:weights=1 1:normalize=0,\
 loudnorm=I=-14:TP=-1.5[mix]" -map "[mix]" out_audio.m4a
```

`loudnorm` steht zuletzt in der Kette, Summenmix -14 LUFS integriert, TP -1.5. VO-Zielpegel -16 LUFS vor dem Summenmix.

**Export-Haertung gegen Banding:** 1080×1920, H.264 High, 24fps, `-crf 18`, Bitrate 14 bis 16 Mbit, `yuv420p`, AAC 320k. Grain wirkt als Dithering gegen Blockbildung in warmen Schattenflaechen nach IG-Rekompression.

---

## 9. Laengen-Check und Fallbeil

```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 final.mp4)
awk -v d="$DUR" 'BEGIN{
  if (d+0 > 28.0)      { print "FAIL (hart): "d"s > 28.0s -> Render verwerfen"; exit 2 }
  else if (d+0 > 27.0) { print "TRIM (weich): "d"s > 27.0s -> Gedanke streichen"; exit 1 }
  else if (d+0 < 18.0) { print "WARN (sehr kurz): "d"s < 18.0s"; exit 1 }
  else                 { print "OK: "d"s" }
}'
```

Ueber 27,0s: Reduktions-Reihenfolge aus Schritt 3 (Gedanke streichen, dann Dissolve straffen, nie Standzeit unter 3,5s). Ueber 28,0s selbst nach Streichen: **harter Fehlschlag, kein Upload.**

---

## 10. Publish via Graph API

- Upload mit `cover_url` oder exaktem `thumb_offset` (Pflicht), Cover ist Frame 1 mit lesbarer Killer-Zeile.
- **Fixierter Erst-Kommentar** autonom gesetzt, traegt ein gemuenztes Wort und erzwingt Replies. In der ersten Stunde jede Antwort beantworten (manuell/gescriptet).
- Caption folgt denselben Grammatik-Regeln wie die Overlays.

---

## 11. Ableitung der 2 Stories (pro Reel, autonom generiert, Platzierung manuell)

Genau 2 Stories, jede mit Hook plus **genau einem** niederschwelligen Interaktions-Trigger nach Wochentag.

- **Story A, Teaser:** die Killer-/Hook-Zeile als stehende Textkarte (gleiche Fraunces, gleicher Petrol-Tick, gleicher Grade) ueber einem Standframe des staerksten Footage-Clips. Darauf der Wochentags-Trigger:
  - Montag Emoji-Slider, Dienstag Poll, Mittwoch Quiz, Donnerstag Fragen-Box (speist die Satz-Quelle), Freitag Reveal-Sticker (fuettert die Mail und cliffhangt auf die Peilung der naechsten Woche).
- **Story B, Verteiler:** das Reel selbst geteilt, mit einem Sticker "Neuer Gedanke" und einem Link/Sticker in den IG-Broadcast-Channel bzw. die Morgen-Mail ("Ein Gedanke, jeden Morgen"). Ziel: DM- und Mail-Zubringer.

Beide Stories tragen keinen Kompass, keine gefuellte Pille, dieselbe Safe-Zone-Logik.

---

## 12. Abnahme-Kriterien (harte Gates, sonst kein Upload)

**Sprache und Grammatik:**
- Korrekte Grammatik. **Keine langen Gedankenstriche** (— oder –) als Stil-Trenner, stattdessen Doppelpunkt oder Komma. **Kein Komma vor "und".** Gilt fuer Overlays, Caption, Bio, Erst-Kommentar, beide Stories.
- **Lexikon-Gate:** Hook-Zeile und Schluss-Zeile tragen je genau einen aktiven Begriff aus `kk_lexikon.json`, natuerlich gesetzt. Kein gesperrter Begriff, kein Begriff ausserhalb der 8er-Aktiv-Menge, im Korpus hoechstens ein weiterer, **kein Reel liest sich wie eine Vokabelliste.**

**Lesbarkeit:**
- Text im Band 40 bis 65 Prozent, Baseline nicht bei 71 Prozent. Untere 35 Prozent frei.
- Max. etwa 6 Woerter pro Zeile, max. 2 Zeilen gleichzeitig, Killer-Zeile 5 bis 7 Woerter, Kernaussage max. 3 Zeilen.
- Scrim-Kontrast-Floor eingehalten (YAVG-Worst-Case ueber alle Frames der Zeile, Deckung nie unter 45 Prozent im Zentrum). Text scharf, ungrainy (Overlay nach dem Grade).
- Standzeiten nicht gequetscht, jeder Gedanke mindestens 3,5s voll lesbar.

**Pacing und Bewegung:**
- 3 bis 4 Gedanken, Standzeit 3,5 bis 5,0s (Floor hart), Dissolves 1,0 bis 1,5s, gemessene Timeline 18 bis 27s, nie ueber 28,0s.
- Nur Cross-Dissolves, kein Hardcut/Whip/Shake/Blitz/Slow-Mo. Konstante langsame Mikro-Bewegung. Loop schliesst nahtlos in warmem Fast-Schwarz.
- Frame 1: Bewegung mit Sog plus lesbare Killer-Zeile innerhalb 0,3s, alles auf stumm verstaendlich.

**Look:**
- Nur Palette-Hex, nur Fraunces als Headline, Petrol nur als Haarlinie/Tick. Keine verbotenen Farben, keine Sans-Headline, keine gefuellte CTA.
- **Kein Kompass-Element, weder animiert noch statisch, nirgends.** Der Kompass lebt nur in der Sprache.
- Footage hand- und gesichtsfrei, Barnum-Blacklist eingehalten, Motiv-Familie konsistent.

**Audio:**
- Suno-Track hat die Klang-QA bestanden (kein Knistern, kein Lo-Fi, kein Hiss). Summe -14 LUFS, TP -1.5.
- VO nur wo tragend, feste Voice-ID, sauber geduckt, kein hoerbares Rauschen.

**Technik:**
- 1080×1920, H.264 High, 24fps, crf 18, ≥14 Mbit, yuv420p, AAC 320k.
- Cover gesetzt (`cover_url` oder `thumb_offset`), Erst-Kommentar fixiert.

Besteht ein Reel alle Gates, geht es autonom online. Faellt ein Gate, greift die vordefinierte Reaktion (Laenge: Reduktions-Reihenfolge; Footage: N-aus-M neu ziehen; Musik: neu generieren). Nur der harte 28,0s-Deckel und ein fehlendes Pflicht-Asset stoppen den Lauf ganz.