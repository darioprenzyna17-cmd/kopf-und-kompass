# @montagsluege — Status & Live-Ready Checkliste

**Stand:** 2026-05-02, 11:00 (Zurich)
**Geplanter Launch:** **Sonntag 2026-05-03, 18:00 MEZ** (automatisch via Cron)

---

## TEIL 1 — Was wir gebaut haben

### A) Instagram-Account & Meta-Setup ✅
- IG `@montagsluege` (Creator/Business)
- FB-Page `Rich.and.risk` mit IG verknüpft
- Meta Developer App "Montagsluege Posting" erstellt
- 6 Permissions konfiguriert (instagram_basic, content_publish, manage_insights, pages_show_list, pages_read_engagement, business_management)
- Long-Lived Page Access Token generiert (effektiv permanent)
- IG Business Account ID + Page ID gespeichert

### B) Auto-Posting-Infrastruktur ✅
- GitHub Repo: `darioprenzyna17-cmd/montagsluege-autopilot` (privat)
- `scheduler.py` — Tagesläufer mit Idempotenz-Check
- `lib_meta.py` — Reel + Carousel Posting via Graph API
- GitHub Action — Cron täglich 16:00 UTC = **18:00 MEZ** (Sommerzeit)
- 2 GitHub Secrets verschlüsselt gesetzt
- Auto-Commit von `queue.jsonl` zurück ins Repo nach jedem Post

### C) Brand-Identität ✅
- `BRAND.md` — Locked Style Guide
- Fonts: **Playfair Display** (Headline, Black 900) + **Inter** (CTA, Bold 700)
- Farben: text/primary `#F5F0E6` (warm white), brand-mark `#C8C3B4`
- Layout: Vignette für Legibility, 4-fach Soft-Shadow, Brand-Mark unten rechts
- Visuelle Linie: monochrom blau-grau, ein warmer Highlight, niemals Personen

### D) Content-Generatoren ✅
- `gen_carousel.py` — NanoBanana Pro → 5 Slides → PIL Text-Overlay
- `gen_reel.py` — Seedance 2 → 15s Cinematic B-Roll + deutsches Voice-Over
- `rerender_carousel.py` — Re-Overlay ohne API-Kosten (Base-PNGs lokal gespeichert)
- `batch_week1.py` — Sequenzielle Batch-Generierung
- `build_queue_w1.py` — Queue-Builder mit JSON-Escaping

### E) Content für Woche 1 ✅
- **1 Reel** (`test-w1d7/reel.mp4`, ~$1.40) — "Du bist nicht müde. Du bist feige."
- **6 Carousels** (~$1.40 total) — alle 6 Pillars abgedeckt:
  - test-w1d1 — Montagslüge
  - w1-d2-komfort — Komfort tötet
  - w1-d3-potenzial — Verschwendetes Potenzial
  - w1-d4-vater-sohn — Vater-Sohn
  - w1-d5-frame-shift — Frame Shift
  - w1-d6-quiet-power — Quiet Power

### F) Queue (queue.jsonl) ✅
7 Einträge für Sonntag 03.05. bis Samstag 09.05., jeweils mit:
- Datum
- Format (reel/carousel)
- Pillar
- Asset-URL(s) auf raw.githubusercontent.com
- Caption (Hook + Tiefe + DM-CTA + 5 Hashtags)
- Status: pending

### G) Budget-Stand
- Bisher ausgegeben: **~$2.60** von $10
- Übrig: **~$7.40**

---

## TEIL 2 — Pre-Launch Checkliste (vor So 18:00)

### 🔴 Blocker (ohne geht's nicht)

- [ ] **Test-Post in IG-App löschen** (du, 30 Sek)
  Sonst ist der erste Eindruck "Test."

- [ ] **Manueller Trigger-Test der GitHub-Action** (ich, 3 Min)
  Workflow einmal `workflow_dispatch` antriggern, ohne dass was Live geht (heute hat queue keinen Eintrag → Scheduler skipt sauber → bestätigt: alles OK).

### 🟡 Stark empfohlen (vor So 18:00)

- [ ] **Profilbild setzen** (du, 1 Min)
  Vorschlag: `mindset-agents-bundle/avatar-images-v2-credibility/05_editorial_closeup.png` (oder Slide 1 aus einem Carousel)

- [ ] **Bio schreiben** (du, 3 Min, max. 150 Zeichen)
  Vorschlag:
  > *Du redest viel, machst nichts.*
  > *Dieser Account holt dich da raus.*
  > *Reels Mo–Sa.*

- [ ] **Kategorie auf "Persönliche Marke"** umstellen (du, 30 Sek)

- [ ] **Reel-Audio testweise prüfen** (du, 30 Sek)
  Hast du das deutsche Voice-Over gehört? Akzent okay? Pacing passt? Falls nein: ich generiere Variante mit Fallback-Pipeline (macOS `say` + ffmpeg) für ~$1.

### 🟢 Optional (kann später)

- [ ] Reel-Text-Overlay via ffmpeg (für 60% Sound-off-Viewer)
- [ ] Linktree / Newsletter-Sign-up im Bio-Link
- [ ] Highlight-Cover gestalten (ab 5+ Stories)

---

## TEIL 3 — Was nach Woche 1 dran ist

### Geplant für nächste Woche (vor 10.05.)

- **Woche 2 Content** (~$3.60):
  - 5 Carousels ($1)
  - 2 Reels ($2.80) — einer davon Sunday-Hero-Slot
- Queue für Woche 2 erweitern
- Erste Insights-Auswertung (montags Morgen check)

### Ab dann monatlich

- **Token-Renewal** — User-Access-Token läuft 2026-07-01 ab. Setze ich dir einen Reminder?
- **Insights-Report** — `fetch_insights.py` einmal/Woche laufen lassen
- **Pillar-Performance prüfen** — Plan sagt: Pillar mit ø Reach < 500 Views nach 5 Posts → killen

---

## TEIL 4 — Was du vielleicht vergessen hast

Drei Sachen, die noch nicht entschieden sind und Einfluss haben:

1. **Englische Reels (`variant_a_coward`, `variant_b_cage`)** im Bundle:
   Du hattest gesagt: alle neuen Reels auf Deutsch. Die zwei Englischen werden also NICHT verwendet. Behalten oder löschen?

2. **GitHub-Action-Zeit:** Cron läuft täglich um **18:00 MEZ**. Sonntag-Slot wäre laut Audience-Research ideal **19:00** (Hochsensitivitätsfenster). Soll ich Sonntags auf 19:00 verschieben? (Setup: 5 Min, eigener Cron-Job für So.)

3. **Monetisierung-Schwelle:** Du hast gesagt "ab 10k Followern Gedanken machen". In `BRAND.md` und `content-plan-month-1.md` ist das nicht festgehalten. Soll ich's als Milestone einbauen?

---

## TL;DR — Bist du Live-Ready?

**Technisch:** ✅ Ja. Pipeline läuft, Content für 7 Tage gequeued, Cron aktiv.

**Brand:** ✅ Ja. Brand-Spec gelockt, alle Assets folgen ihr.

**Persönlich (du):** 🟡 4 Klicks fehlen — Test-Post löschen, Profilbild + Bio + Kategorie setzen.

**Risiko:** Reel-Stimme ist Seedance-Native-Deutsch — ob's natürlich klingt, hast du noch nicht bestätigt. Wenn nein: $1 Fallback. Wenn ja: alles bereit.

**Budget:** $7.40 übrig — reicht für Woche 2-4 (~$6.50 prognostiziert).
