# Kopf & Kompass — Autopilot-Regeln (autonomer Betrieb)

Account: **@kopfundkompass** (IG-Business-ID 17841472104283157, FB-Seite „Kopfundkompass").
Aufbau **exakt wie DC-Group**, aber strikt getrennt: eigenes Repo, eigenes Meta-Portfolio
(„Dario Prenzyna"), eigene Meta-App („Kopf und Kompass"), eigener System-User-Token.
**Niemals mit DC vermischen** (kein geteilter Token, kein geteilter Content, kein geteiltes Ledger).

## Was schon steht (Maschinerie = „die Art und Weise von DC")
- **Poster** `scheduler.py --live` (GitHub Action `post.yml`, alle 30 Min) postet faellige Eintraege aus `queue.jsonl`.
- **Reel-Engine** `build_video_reel.py --pipeline` (Action `reel.yml`) baut das naechste approved-Konzept: echtes KI-Footage (Veo via kie.ai) + Overlay + Musik + Schlusskarte, Einschlag-Effekt, harte Textschnitte.
- **Cheap-Content** `generate_week.py` (Action `generate.yml`) fuellt Nicht-Reel-Tage (Bild/Carousel/Animation).
- **Abnahme-Gate** Agent `kk-abnahme` (Scaffold aus DC uebernommen): jedes Konzept muss PASS bekommen, bevor teures Video generiert wird.
- **Lern-Loop** `track_performance.py` + `perf.py` + `learn_times.py`: Reichweite/Interaktion je Typ/Tag/Zeit auswerten, Gewinner ausbauen.
- **Dubletten-Ledger** `used_reels.json` (`used_topics`, `used_hooks`).
- **Watchdog** `watchdog.py` faengt leere Tage mit Evergreen ab.

## Harte Gates vor JEDEM Post (wie DC)
1. **Abnahme-Gate:** Konzept durch `kk-abnahme`, Verdikt PASS noetig.
2. **Grammatik/Sprache:** korrektes Deutsch. Keine langen Gedankenstriche. Kein Komma vor „und".
3. **Keine Dubletten:** Thema, Hook und Kernsatz nicht wiederholen (gegen `used_reels.json` + Live-Captions).
4. **Marken-Fit + Sog:** muss zu Kopf & Kompass passen und wirklich sehenswert/anstossend sein.

## OFFEN — wird mit Dario besprochen (nachher), DANN hier eingetragen
> Bis das steht, laeuft NUR die Maschinerie; `reel_pipeline.json` approved[] bleibt leer, es wird nichts autonom gepostet.

- **Inhaltssaeulen / Themen:** nachdenklich, anstossend, „gutes Leben" / Reflexion (NICHT Recruiting wie DC). Genaue Saeulen offen.
- **Marken-Look:** Farben, Typo, Overlay-Stil, Schlusskarte, Logo-Regel fuer @kopfundkompass (DC-Gold/Navy gilt NICHT — eigener Look).
- **Ton & Zielgruppe:** Stimme, Ansprache, Pattern-Interrupt-Grad, Musik-Welt.
- **CTA / Funnel:** was soll ein Post ausloesen (Follow, Save, Share, DM, Link)?
- **Abnahme-Domaene:** `kk-abnahme` auf die Kopf-&-Kompass-Themen umschreiben (aktuell noch DC-Handwerk-Logik).
- **Wochen-Routine / Postzeiten:** `generate_week.py` SCHEDULE + `posting_times.json` an die 35k-Bestands-Audience anpassen.

## Sicherheit
- Getrennt von DC: eigener Token als GitHub-Secret `IG_ACCESS_TOKEN`, IG-ID als `IG_USER_ID` im Repo `kopf-und-kompass`.
- Alles wird protokolliert (`used_reels.json`, Metrics), damit Dario jederzeit auditieren kann.
