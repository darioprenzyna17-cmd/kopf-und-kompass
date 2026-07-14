# Kopf & Kompass — Instagram-Autopilot

Autonomer Aufbau von **@kopfundkompass** zu einem Mindset-Account, der langfristig viral
geht. Cineastische Nachdenk-Reels (ruhig, tief, motivierend), vollständig in der Cloud
(kein Mac nötig). Der Account lernt aus den eigenen Zahlen und entwickelt sich weiter.

## Prinzip
Ein starkes, atmosphärisches KI-Footage (Veo via kie.ai) + ein Gedanke, der in Beats
aufgebaut wird + tiefe Musik + leise Wortmarken-Schlusskarte. Kein lautes Pattern-Interrupt,
sondern Sog durch Bild, Wahrheit und Ruhe. Ziel pro Post: Save und Share („das musste ich
lesen") und Follow.

## Kreislauf (autonom)
1. **Konzept** → Vorrat in `reel_pipeline.json` (`approved` → `built`).
2. **Abnahme** → Agent `kk-abnahme` prüft Logik, Sprache, Dubletten, Tiefe. Nur PASS wird gebaut.
3. **Bau** → `build_video_reel.py --pipeline` (Footage + Text-Beats + Musik + Schlusskarte).
4. **Post** → `scheduler.py --live` postet fällige Reels aus `queue.jsonl` (kie.ai hostet das Video, Repo bleibt privat).
5. **Lernen** → `track_performance.py` + `perf.py` werten Reichweite/Saves/Shares je Thema aus, `learn_times.py` die besten Zeiten. Gewinner-Muster werden ausgebaut, schwache ersetzt.

## Wichtigste Dateien
| Datei | Zweck |
|---|---|
| `build_video_reel.py` | Reel-Engine (Footage + Text-Beats + Musik + Schlusskarte) |
| `scheduler.py` | Poster (Queue → Instagram) |
| `reel_pipeline.json` | Reel-Vorrat (approved → built) |
| `used_reels.json` | Dubletten-Ledger (Themen/Hooks) |
| `perf.py` / `track_performance.py` / `learn_times.py` | Lern-Loop |
| `AUTOPILOT_RULES.md` | Verbindliche Regeln (Stil, Gates, Viral-Prinzipien) |
| `.claude/agents/kk-abnahme.md` | Abnahme-/Logik-Prüfer |

## Zugang
Eigenes Meta-Portfolio, eigene App, eigener System-User-Token. GitHub-Secrets:
`IG_USER_ID`, `IG_ACCESS_TOKEN`, `KIE_API_KEY`. Nichts wird mit anderen Projekten geteilt.
