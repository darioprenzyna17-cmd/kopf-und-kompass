# Kopf & Kompass — Instagram-Autopilot

Autonomer Betrieb von **@kopfundkompass** (35k Follower), vollständig in der Cloud (kein Mac nötig).
Baugleich mit dem DC-Group-Autopilot, aber **strikt getrennt**: eigenes Repo, eigenes Meta-Portfolio,
eigene App, eigener System-User-Token.

## Status
- ✅ Meta-Anbindung steht (Portfolio „Dario Prenzyna", App „Kopf und Kompass", System-User „KopfKompass Bot", dauerhafter Token).
- ✅ GitHub-Secrets gesetzt: `IG_USER_ID`, `IG_ACCESS_TOKEN` (+ `KIE_API_KEY` für Reel-Generierung nachtragen).
- ✅ DC-Maschinerie portiert (Poster, Reel-Engine, Cheap-Content, Lern-Loop, Abnahme-Gate).
- ⏳ **Inhalt offen** — Themen, Look, Ton, CTA werden mit Dario besprochen, dann in `reel_pipeline.json` + `AUTOPILOT_RULES.md` eingetragen. Bis dahin postet nichts autonom (approved[] leer).

## Wichtigste Dateien
| Datei | Zweck |
|---|---|
| `scheduler.py` | Poster (Queue → Instagram) |
| `build_video_reel.py` | Reel-Engine (Veo-Footage + Overlay + Musik + Schlusskarte) |
| `generate_week.py` | Cheap-Content (Bild/Carousel/Animation) |
| `reel_pipeline.json` | Reel-Vorrat (approved → built) |
| `used_reels.json` | Dubletten-Ledger |
| `AUTOPILOT_RULES.md` | Verbindliche Regeln + offene Inhalts-Punkte |
| `.claude/agents/kk-abnahme.md` | Abnahme-/Logik-Prüfer (Domäne noch anzupassen) |

Siehe `AUTOPILOT_RULES.md` für die vollständigen Regeln und die offenen Inhalts-Entscheidungen.
