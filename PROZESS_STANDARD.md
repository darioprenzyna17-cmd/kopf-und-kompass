# Prozess-Standard der Autopiloten

Gilt gleichlautend für **DC-Group** (`dc-autopilot`) und **Kopf & Kompass** (`kopf-und-kompass`).
Festgelegt von Dario am 05.08.2026, nachdem K&K drei Tage still stand, während DC lief.

**Was hier geregelt ist:** nur der Ablauf, die Mechanik, das Betriebsverhalten.
**Was hier NICHT geregelt ist:** Design, Look, Ton, Themen, Marke. Die beiden Konten
bleiben inhaltlich vollständig getrennt und haben nichts miteinander zu tun. K&K weiß
nichts von DC. Getrennt bleiben in jedem Fall: Repo, Instagram-Konto, Meta-Token,
kie.ai-Schlüssel, Inhalte, Gestaltung.

---

## 1. Bauen und Posten sind zwei getrennte Vorgänge

Ein Postversuch darf niemals eine Produktion auslösen. Wer postet, greift auf etwas
Fertiges zu. Sonst kostet jeder Fehlversuch Geld.

Reihenfolge in jedem Lauf: **erst posten, dann bauen.** Scheitert der Bau, ist der Post
trotzdem raus.

## 2. Im Vorrat steht ein Pfad im Repo, keine Anbieter-URL

Die Adressen von kie.ai verfallen nach rund drei Tagen. Ein Vorrat aus solchen Adressen
verfault, und Instagram meldet dann nur ein nacktes `container ERROR`.

Deshalb: das fertige Video liegt im Repo (`assets/vorrat/` bei K&K, `assets/` bei DC).
Die öffentlich erreichbare Adresse entsteht **erst beim Posten** über
`lib_meta.ensure_public_url`. Nach bestätigtem Post wird die Datei gelöscht.

Folge davon: Zwischenstufen und Rohclips dürfen in `.gitignore` stehen, das fertige
Video nicht.

## 3. Der Sicherungsschritt darf nie am Dateinamen scheitern

Ein `git add` über eine feste Liste bricht mit Code 128 ab, sobald eine Datei fehlt.
Dann wird **gar nichts** gesichert, auch nicht die Ausgabenbremse. Genau das hat K&K
zwischen dem 02. und 05.08.2026 alle zwei Stunden ein Video auf Darios Rechnung bauen
lassen.

Regel: vor dem `git add` prüfen, welche Dateien es wirklich gibt, und nur die nennen.
Der Schritt läuft mit `if: always()`.

## 4. Jeder Push hat einen Rebase-Fänger

Poster, Story und Bau schreiben ins selbe Repo. Ein nacktes `git push` fällt an
`fetch first` rot aus, obwohl der Post längst online ist.

```
git push origin main || (git fetch -q origin main && git rebase -q origin/main && git push origin main)
```

## 5. Die Ausgabenbremse ist die Wahrheit, nicht das Log

Tageszähler (`budget.json` bei K&K) begrenzen bezahlte Aufrufe. Sie wirken nur, wenn sie
nach jedem Lauf zurückgeschrieben werden. Wird der Zähler nicht gesichert, gibt es keine
Bremse, nur die Illusion einer Bremse.

## 6. Gemessen wird gegen Instagram, nicht gegen das eigene Protokoll

Nach dem Posten wird bei Instagram nachgesehen, ob der Beitrag wirklich existiert. Die
Commit-Meldung sagt, was tatsächlich passiert ist, nicht was geplant war.

## 7. Ein Wächter meldet Stillstand aufs Handy

Bleibt zu lange nichts online, geht eine Push-Nachricht raus. Der Wächter hat am
04./05.08.2026 korrekt Alarm geschlagen. Ein Alarm ist kein Fehler des Wächters.

## 8. Keine Testreels

Reels werden normal gepostet. Der Trial-Reel-Modus von Instagram ist aus
(`KK_TRIAL_REELS` steht auf 0). Dario will keine Probe-Läufe auf seinen Konten.

## 9. Guthaben wird überwacht

Ein eigener Lauf prüft das kie.ai-Guthaben und meldet sich, bevor es leer ist. Läuft der
Schlüssel leer, fällt die Produktion aus, und zwar still.

## 10. Just in time, kein Lager

Es liegt höchstens **ein** fertiges Video auf Halde, und es wird höchstens **eines pro Tag**
produziert (K&K: `MAX_VORRAT` und `MAX_BAUTEN_PRO_TAG` in `kk_budget.py`). Damit ist nie viel
vorausbezahlt, und eine Änderung an Bau oder Look greift sofort beim nächsten Reel statt erst,
wenn ein altes Lager abgearbeitet ist.

## 11. Beim gemeinsamen Entwickeln wird nichts produziert

Während Dario und ich am System arbeiten: nur Trockenläufe. Echte Produktion passiert
über den Cron oder auf ausdrückliche Ansage.
