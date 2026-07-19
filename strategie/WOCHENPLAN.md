# Kopf & Kompass — Experten-Wochenplan (operatives Betriebssystem)

Stand 2026-07-19. Ziel: Reichweite über Nicht-Follower neu zünden und viral gehen.
Grundlagen: siehe `STRATEGIE.md` (normativ), `PLAYBOOK_HOOK_SHARE.md` (Hooks/Retention) und
`ALGORITHMUS_UND_MENTOREN.md` (Algorithmus + Vorbilder). Ton: nachdenklich, aber positiv und
aufbauend, ernst, grammatikalisch einwandfrei. Keine langen Gedankenstriche, kein Komma vor „und".

## Diagnose (aus echten Zahlen)
- Reichweite nur 0,7 bis 1,2 Prozent pro Reel. Normal wären 8 bis 10 Prozent.
- Ursache: Jeder Reel stirbt an der grösstenteils inaktiven 35k-Audience und bricht nie zu Nicht-Followern durch.
- Watchtime nur ~3,7 Sekunden, genau an der Abbruchschwelle.
- Einziger Reel mit Shares und bester Reichweite: Thema „Grenzen".

## Nordstern
Sends (DM-Weiterleitungen) + Saves + Follows pro Reel. NICHT Views oder Likes.
Sends sind das stärkste Signal für neue Reichweite (drei- bis fünffach ein Like).

## Die vier Hebel, an denen wir arbeiten
1. **Durchbruch zu Nicht-Followern:** Trial Reels nutzen (testen direkt an Nicht-Followern, umgehen die schlafende Audience). Hinweis: Trial Reels lassen sich derzeit nur manuell in der App aktivieren, nicht über die API. Für Tests also manuell posten, für den Dauerbetrieb der Autopilot.
2. **3-Sekunden-Hook:** Der zentrale Gedanke steht in Sekunde 0 als Bild plus Text. Ziel 3-Sekunden-Hold über 60 Prozent.
3. **Schickbarkeit:** Jeder Reel muss ein Gedanke sein, den man sofort jemandem weiterleiten will. CTAs sind darum jetzt sends-orientiert (Schick/Teile), nicht mehr nur „Speichern".
4. **Konstanz:** 3 bis 5 Reels pro Woche in Batches. Reichweite kommt in Kaskaden, sobald ein Reel die Nicht-Follower-Testgruppe übersteht.

## Format (fix)
Ein Gedanke pro Reel, cineastische Naturbilder, ruhige emotionale Musik, unter 45 Sekunden,
Ton-aus-tauglich (Text trägt allein), als wiederkehrende Serie erkennbar.

## Eine Testvariable pro Woche (sauber lernen)
- **Woche 1: Hook / 3-Sekunden-Hold.** Zwei Hook-Bauweisen gegeneinander (benannte Szene vs. stille Erlaubnis). Messen: 3s-Hold und Watchtime.
- **Woche 2: Sends-CTA.** Welche Teilen-Formulierung erzeugt am meisten DM-Weiterleitungen.
- **Woche 3: Serie/Thema.** „Grenzen"-Reihe konsequent gegen gemischte Themen.
- **Woche 4: Kadenz.** 3 vs. 5 Reels/Woche, Wirkung auf Kaskaden.
Immer nur EINE Variable pro Woche ändern, sonst lernt man nichts.

## Kadenz und Nachschub
- 3 bis 5 Reels/Woche über den Autopilot (`reel.yml`), plus 2 Stories/Tag (`story.yml`).
- Vorrat bewusst schlank halten (Ziel ~3 bis 5 approved). Nur wenige Tage vorproduzieren, dann aus den Zahlen lernen und winner-biased nachlegen (`learn_and_adapt.py` priorisiert Gewinner-Themen).

## Engagement (manuell, sicher, KEIN Bot)
Automatisches Folgen/Kommentieren über Bots riskiert die Sperre des 35k-Accounts und ist über die
offizielle API ohnehin nicht möglich. Darum menschlich und dosiert, 10 bis 15 Minuten pro Tag:
- Kommentiere unter 8 bis 10 frischen Beiträgen artverwandter, AKTIVER Accounts (nicht der toten Grossen), echte, nachdenkliche Sätze im Marken-Ton, keine Floskeln, keine Eigenwerbung.
- Antworte auf jeden Kommentar unter den eigenen Reels in der ersten Stunde (Reply-Signal + Bindung).
- Ziel: Sichtbarkeit bei fremden, aktiven Zielgruppen, ohne Risiko.
Kommentar-Vorlagen (anpassen, nie 1:1 spammen):
- „Der Satz bleibt hängen. Besonders der Teil über [X]."
- „Genau das habe ich diese Woche gebraucht. Danke dafür."
- „Ruhig gesagt und trotzdem klar. Stark."
- „Das ist der Unterschied zwischen laut und wahr."

## Review-Rhythmus
Wöchentlich `learn_and_adapt.py` laufen lassen (zieht Insights, Score nach Nordstern, schreibt
`learnings.json`). Gewinner-Themen und Gewinner-Hooks ausbauen, Verlierer streichen. Ergebnis der
Testvariable dokumentieren, dann nächste Woche eine neue Variable.
