# Brand-Spec @montagsluege

**Stand:** 2026-05-02 — Locked, alle Posts müssen das einhalten.

## Typografie

| Use | Font | Weight | Pixel Size (von Bildbreite W) |
|---|---|---|---|
| **Hook** (Slide 1, große Reel-Hook) | Playfair Display | Black (900) | W / 14 (≈ 77px bei 1080) |
| **Body** (Slide 2–4) | Playfair Display | SemiBold (600) | W / 18 (≈ 60px bei 1080) |
| **CTA** (Slide 5, Reel CTA) | Inter | Bold (700) | W / 19 (≈ 57px bei 1080) |
| **Brand Mark** (`@montagsluege`) | Inter | Medium (500) | W / 50 (≈ 22px) |

Fonts liegen in `assets/fonts/` — werden bei Generierung referenziert, **nicht von System geladen**.

## Farben

| Token | HEX | Use |
|---|---|---|
| `text/primary` | `#F5F0E6` | Hauptschrift (warm white) |
| `text/brand-mark` | `#C8C3B4` | `@montagsluege`-Wasserzeichen |
| `bg/dark-overlay` | `rgba(0,0,0, gradient)` | Vignette für Legibility |
| `bg/seed-base` | aus NanoBanana-Brief | Cinematic monochrom blue-grey |

## Layout

### Carousel (4:5, 1080 × 1350)

- Text **vertikal zentriert** (außer Brand-Mark)
- Max. **82% Breite** (innerer Margin)
- Text-Schatten: 4-fach Soft-Shadow `(0,0,0,200)` mit ±2px Offset
- Brand-Mark: unten rechts, `28px` Margin von Rand
- Vignette: subtle dark gradient zentral → außen (Legibility)

### Reel (9:16, 720p oder 1080p, 15s)

- Hook-Text erscheint Sekunde **0.5–3.0**, oben-zentral, Playfair Black
- Body/CTA-Text bei Bedarf untere Hälfte, max. 8 Wörter
- Brand-Mark dauerhaft unten rechts
- Voice-Over deutsch, ruhig, calm (siehe Voice-Brief in `gen_reel.py`)

## Text-Inhalt-Regeln

- Anführungszeichen: deutsche „"  oder einfach' '
- Em-Dash: — (nicht --)
- Keine Emojis, niemals
- Punkt am Ende jeder Zeile (außer beim Hook → harter cut)
- Wörter pro Slide: max. 12
- Wörter pro Reel-Hook: max. 6

## Visueller Stil (für NanoBanana / Seedance)

**Der Look:**
- Monochrom blau-grau, ein einziger warmer Highlight (Sodium-Lampe, Brass-Lamp)
- Slow-Motion oder static cinematic
- Niemals Personen, niemals Gesichter, niemals Text (Text legen wir lokal drauf)
- Atmosphäre: melancholisch, ruhig, leise Bedrohung

**Motiv-Bibliothek:**
- Leere deutsche Stadtstraße im Morgennebel
- Walnuss-Schreibtisch im Halbdunkel mit Brass-Lampe
- Regen am Zugfenster bei Nacht
- Lederne Notizbuch geschlossen auf dunklem Holz
- Berge / Nebel / einzelner Lichtkegel
- Wasser / Wellen langsam, monochrom
- Anzug-Silhouette ohne Gesicht in Korridor

## Was NIE drinsteht

- Logos außer eigenes Brand-Mark
- Stockphoto-typische Composition (people-smiling, freigestellt)
- Bunte Farben (Sättigung max. 30% außer einer Akzent-Farbe)
- Generic motivational quotes
