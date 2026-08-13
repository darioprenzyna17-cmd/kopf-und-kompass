# Kopf & Kompass — Autopilot-Regeln (autonomer Mindset-Account)

Account: **@kopfundkompass**. Ziel: ein Mindset-Account, der **langfristig viral** geht,
aus den eigenen Zahlen lernt und sich weiterentwickelt. Nordstern: nicht Likes, sondern
**Save + Share + Follow** (Content, den Leute weiterschicken und behalten wollen).

**Wachstumsziel: 40'000 Follower in 4 Wochen** (Start ~35k, rund 180 neue pro Tag netto).
Dafür: hohe Reel-Frequenz, jedes Reel auf Save/Share optimiert, Gewinner-Themen schnell doppeln,
schwache Muster sofort streichen. 2 Stories pro Tag halten die Bestands-Audience aktiv (Ranking-Signal).

## Stories — IMMER mindestens ZWEI pro Tag (Dario-Vorgabe 2026-07-19)
Auf @kopfundkompass sind **täglich mindestens zwei Stories** live und durchgehend mind. eine aktiv, nie eine Lücke.
- **Zwei feste Läufe (morgens ~07:30 + abends ~17:30 Zürich)** via Cloud-Cron `story.yml`, jeder postet einen Impuls über `run_story.py`, unabhängig vom Reel-Lauf. Fällt ein Lauf aus, beim nächsten sofort nachholen.
- Inhalt = eigenständiger Impuls im Archivkino-Ton (`build_story.story_gedanke`, tiefe Ein-Satz-Wahrheit, „Antworte mit einem Wort."), Rotation über eine Impuls-Bank mit `story_ledger.json` gegen Dubletten. Vorgerenderte, committete Kacheln in `assets/stories/daily/` → kein Chrome in CI.
- Stories kommen AUSSCHLIESSLICH aus diesem Story-Cron (genau 2/Tag). Das reel-gekoppelte Story-Posten in `cloud_build_post.py` ist bewusst deaktiviert, damit es an Reel-Tagen nicht auf 3-4 hochläuft (Dario-Vorgabe 2026-07-19).

## Ton & Produktionsprinzip (Dario-Vorgabe 2026-07-19, verbindlich)
- **Grundstimmung: nachdenklich, aber positiv und aufbauend.** Ernster, ruhiger Ton, nie düster-resigniert, nie kitschig-motivierend. Der Gedanke darf wehtun, muss aber am Ende aufrichten, nicht runterziehen.
- **Grammatik ist Pflicht:** jeder Satz grammatikalisch einwandfrei, korrekte Rechtschreibung und Zeichensetzung. Keine langen Gedankenstriche, kein Komma vor „und". Vor jeder Freigabe Grammatik-Check.
- **Lean produzieren, aus Daten lernen:** NICHT auf Wochen vorproduzieren. Immer nur wenige Tage Vorrat (Ziel: ~3-5 approved Konzepte), dann aus den echten Account-Zahlen lernen und winner-biased nachlegen. Bereits produzierte Konzepte weiterverwenden, nicht wegwerfen.

## Kurzformat (Dario-Freigabe 2026-08-02, verbindlich)
Gemessen über 14 Reels: Watchtime 3,8 bis 5,7 Sekunden bei rund 21 Sekunden Länge, also
etwa 23 Prozent Completion. Instagram verteilt danach nicht weiter. Deshalb der Bruch:
- **Rund 10 Sekunden statt 21.** Gate: 8 bis 13 Sekunden, hart ab 13,5.
- **ZWEI Beats statt vier, EIN Bild statt drei.** Beat 1 ist der Aufbau (`thoughts[1]`),
  Beat 2 die Pointe (`thoughts[-1]`). Die fertige Kernaussage (`thoughts[0]`) kommt bewusst
  NICHT mehr an den Anfang: Wer die Auflösung in Sekunde eins liest, hat keinen Grund zu bleiben.
- **Frage auf der Schlusskarte.** Über 14 Reels kamen null Kommentare, weil nie jemand
  gefragt wurde. Fragen je Thema in `build_video_reel.FRAGEN`.
- **Trial Reels sind Standard.** Jedes Reel geht zuerst nur an Nicht-Follower
  (`graduation_strategy: SS_PERFORMANCE`) und rollt bei guter Leistung automatisch an die
  Follower aus. Grund: Die 35k Bestandsfollower sind träge (3,2 Likes, 0 Kommentare pro
  Reel), und als erste Testgruppe des Algorithmus würgen sie jede Verteilung ab.
- Nebeneffekt: ein Veo-Clip statt drei, also rund ein Drittel der Produktionskosten.
- Abschaltbar über `KK_KURZFORMAT=0` und `KK_TRIAL_REELS=0`.

## Stil (fixiert)
- **Ton:** ruhig, tief, ehrlich, leicht männlich-warm, klar. Bringt zum Nachdenken UND richtet auf. Nie kitschig-platt, nie Kalenderspruch.
- **Bild:** ruhiges, **realistisch wirkendes** Footage (Veo), atmosphärisch, echte Lichtstimmung. Einsame Figuren, Natur, Licht, Alltagsmomente mit Tiefe. 9:16.
- **Bild-Look (Dario-Vorgabe 13.08.2026, verbindlich):** Es soll aussehen wie gefilmt, nicht wie bearbeitet. Clip-Prompts enthalten darum `filmed on a modern full-frame camera with a 35mm lens, natural true-to-life colours, realistic daylight, natural contrast, no colour grading, no film look` und beginnen mit `Realistic documentary-style vertical 9:16 footage`. **Nicht mehr verwenden:** „warm faded film", „teal shadows", „muted desaturated palette", „16mm", „film grain". Der ffmpeg-Grade (`_grade_filter`) greift passend dazu kaum noch ein: keine Vignette, kein Teal-Orange-Splitting, Sättigung 1.02, Kontrast 1.03.
- **Text:** EIN Gedanke, in Beats aufgebaut (Haken → Vertiefung → Wende/Aufrichtung). Serifen-Schrift für den Gedanken, harte Textschnitte (kein Weg-Bluren), Text bleibt lesbar stehen. Du-Ansprache.
- **Hook (Sek 1):** Kontrast- oder Wahrheits-Satz, der stoppt (Vorbild: „Der Ruhigste im Raum ist fast nie der Schwächste"). Anstossend, nicht brav.
- **Musik:** tief, warm, cineastisch (Piano/Ambient), ruhig, nie aggressiv. Je Thema variieren.
- **Schluss:** leise Wortmarke „Kopf & Kompass" + Kernsatz + dezenter CTA. Kein lautes Logo oben (kollidiert mit dem Instagram-Header).

## Inhaltssäulen
Selbstwert & innere Ruhe · stille Stärke & Disziplin · Echtheit & Charakter · Klarheit & Fokus ·
Loslassen & Vergangenheit · Mut & eigener Weg · Geduld & langfristiges Denken · Grenzen & Umgang mit Menschen.

## Harte Gates vor JEDEM Post
1. **Abnahme-Gate:** Konzept durch `kk-abnahme`, Verdikt PASS nötig (Tiefe, Logik, Lesbarkeit).
2. **Sprache:** korrektes Deutsch. **Keine langen Gedankenstriche.** **Kein Komma vor „und".** Kein leeres Phrasendreschen (Barnum/Toxic Positivity).
3. **Keine Dubletten:** Thema, Hook und Kernsatz nicht wiederholen (gegen `used_reels.json` + Live-Captions von @kopfundkompass).
4. **Eigenständig:** keine fremden Marken, keine Firma, kein Recruiting. Reiner Mindset-/Nachdenk-Content.

## Viral- und Lern-Logik
- **Trigger:** Identifikation („das bin ich"), unbequeme Wahrheiten, stille Stärke, Kontrast, eine Frage, die im Kopf bleibt.
- **Nach jedem Zyklus** `track_performance.py` auswerten: welches Thema/Hook zog die meisten **Saves/Shares/Profilbesuche/Follows**. Gewinner-Muster doppeln (neues Thema, gleiche Technik), Verlierer streichen. `perf.py` gewichtet Motive automatisch.
- **Zeiten** lernen sich über `learn_times.py` aus den Insights je Wochentag.
- **Kaltstart-Disziplin:** solange kaum Daten, gleichmässig Themen streuen und nichts überinterpretieren. Sobald echte Daten da sind: SCHEDULE + Zeiten an die Audience anpassen.
- **A/B:** immer nur EINE Variable ändern (Hook ODER Bildwelt ODER Zeit).

## Stories (2 pro Tag)
- **Story 1 (Teaser):** weist auf den neuen Feed-Beitrag hin (Repost-Logik), Marken-Story-Karte mit dem Hook-Satz. `build_story.py` -> `story_teaser`.
- **Story 2 (Gedanke):** eigenständiger kurzer Impuls, lädt zum Antworten ein („Antworte mit einem Wort"). DM-Antworten sind ein starkes Ranking-Signal. `build_story.py` -> `story_gedanke`.
- Look wie die Reels (dunkel, warm, Playfair/Inter, Wortmarke). Gepostet via `lib_meta.post_story` (media_type STORIES).
- API-Grenze: native Sticker (Umfrage/Link/Beitrag-Sticker) sind über die Graph-API nicht setzbar, darum saubere Bild-Karten mit Text-Aufforderung.

## Betrieb
- Reel-Vorrat immer ≥ 4 approved halten (Konzept → `kk-abnahme` → committen).
- Footage-Reels erst nach PASS bauen, dann via Queue einplanen, mp4 + Queue committen/pushen.
- Alles wird protokolliert (`used_reels.json`, Metrics), damit jederzeit auditierbar bleibt.
