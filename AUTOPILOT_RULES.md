# Kopf & Kompass — Autopilot-Regeln (autonomer Mindset-Account)

Account: **@kopfundkompass**. Ziel: ein Mindset-Account, der **langfristig viral** geht,
aus den eigenen Zahlen lernt und sich weiterentwickelt. Nordstern: nicht Likes, sondern
**Save + Share + Follow** (Content, den Leute weiterschicken und behalten wollen).

## Stil (fixiert)
- **Ton:** ruhig, tief, ehrlich, leicht männlich-warm, klar. Bringt zum Nachdenken UND richtet auf. Nie kitschig-platt, nie Kalenderspruch.
- **Bild:** cineastisches, ruhiges KI-Footage (Veo), atmosphärisch, filmische Farbwelt (dunkel, warm). Einsame Figuren, Natur, Licht, Alltagsmomente mit Tiefe. 9:16.
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

## Betrieb
- Reel-Vorrat immer ≥ 4 approved halten (Konzept → `kk-abnahme` → committen).
- Footage-Reels erst nach PASS bauen, dann via Queue einplanen, mp4 + Queue committen/pushen.
- Alles wird protokolliert (`used_reels.json`, Metrics), damit jederzeit auditierbar bleibt.
