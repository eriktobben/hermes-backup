# Kimaki Worktree Cleanup

## Bakgrunn

Kimaki oppretter git worktrees + branches per Discord-thread via `--use-worktrees`-flagget.
Worktrees legges under `~/.kimaki/worktrees/<project-id>/<navn>/` og branches får navn som
`opencode/kimaki-<beskrivelse>`. Over tid hoper dette seg opp — både lokale worktree-kataloger,
lokale branches og (om de er pushet) remote branches på origin.

Dette skriptet rydder opp automatisk: worktrees som har vært **inaktive i > 14 dager** fjernes.

## Skript

**Sti:** `~/.hermes/scripts/kimaki-worktree-cleanup.py` (Python 3)

### Kjøring

```bash
# Tørrkjøring — viser hva som skal ryddes uten å endre noe
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py

# Faktisk cleanup
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py --apply
```

### Terskelverdi

Default: **14 dager** siden siste aktivitet. Endre `DAYS_THRESHOLD`-variabelen øverst i skriptet.

## Aktivitetsdeteksjon (3 kilder, prioritert)

Skriptet bruker følgende kilder for å finne "siste aktivitet" i en session, i prioritert rekkefølge:

| Prioritetsnivå | Kilde | Data |
|---|---|---|
| **1. PRIMÆR** | `session_events.timestamp` i Kimaki DB | Alle events i OpenCode-sessionen: meldinger, toolbruk, spørsmål, feil — alt. Millisekund-presisjon. |
| **2. FALLBACK** | `git log origin/<branch>` / `git log <branch>` | Brukes hvis session-en ikke har events (f.eks. eksterne sessions eller eldre data). |
| **3. SISTE FALLBACK** | `thread_worktrees.created_at` i Kimaki DB | Brukes hvis verken events eller commits finnes (worktree ble opprettet men aldri aktivt brukt). |

**Nøkkelinnsikt:** En session kan ha mye aktivitet (diskusjon, filutforsking, agent-kall) uten at det
resulterer i git-commits. Derfor er `session_events` mer presis enn git-commit-datoer.

### Hva skjer med en inaktiv worktree

1. **`git worktree remove --force <katalog>`** — fjerner worktree-et fra git
2. **`git branch -D <branch>`** — sletter lokal branch
3. **`git push origin --delete <branch>`** — sletter remote branch (hvis den finnes på origin)
4. **`shutil.rmtree(<katalog>)`** — fjerner katalogen fysisk
5. **`UPDATE thread_worktrees SET status = 'cleaned'`** — oppdaterer Kimaki DB

### Orphaned worktrees

Worktree-kataloger som finnes på disk men **ikke** har noen oppføring i Kimaki DBs
`thread_worktrees`-tabell. Disse ryddes i Fase 2 av skriptet. Skriptet finner main repo
fra `.git`-filas `gitdir:`-peker, så det kan gjøre `git worktree remove` for å holde
git-konfigurasjonen ren.

### Hva som IKKE håndteres

- **OpenCode `.worktrees/`** — kataloger under `<prosjekt>/.worktrees/<navn>/`
  (OpenCodes egen worktree-mekanisme, ikke Kimaki). Ryddes manuelt eller via OpenCode selv.
- **Manuelle worktrees** — opprettet utenfor Kimaki. Ryddes manuelt.
- **Error-entries i DB** — worktrees med status `'error'` (f.eks. mislykket opprettelse).
  Disse er harmløse og blir ikke ryddet av skriptet.

## Database (Kimaki SQLite)

```sql
-- Hent alle ready worktrees med sessions
SELECT tw.*, ts.session_id, ts.last_synced_name as session_name
FROM thread_worktrees tw
LEFT JOIN thread_sessions ts ON tw.thread_id = ts.thread_id
WHERE tw.status = 'ready'
ORDER BY tw.created_at;

-- Siste aktivitet per session (millisekund-timestamps)
SELECT session_id, MAX(timestamp) as last_activity,
       datetime(MAX(timestamp)/1000, 'unixepoch') as last_activity_readable
FROM session_events
GROUP BY session_id;
```

## Cron-jobb (daglig cleanup)

Skriptet kjøres via Hermes cron hver natt kl 04:00. Siden cron-jobben kjører `no_agent` (script
leverer stdout direkte), brukes en wrapper-shell for å kunne sende `--apply`:

**Wrapper:** `~/.hermes/scripts/kimaki-worktree-cleanup-wrapper.sh`
```bash
#!/usr/bin/env bash
cd ~/.hermes/scripts && python3 kimaki-worktree-cleanup.py --apply 2>&1
```

**Cron-oppsett (allerede aktivt):**
```bash
hermes cron list  # viser jobben med ID 3fca63db50fc
```

## Real-world resultater

Ved første kjøring (8. juni 2026) ryddet skriptet:

| Kategori | Antall |
|---|---|
| DB-oppføringer (worktree allerede borte) | 70 → `cleaned` |
| Orphaned kataloger (disksøppel) | 20 → slettet |
| Aktive worktrees (beholdt) | 3 |
| Feil | 0 |

De 20 orphaned katalogene kom fra 3 prosjekter:
- **cloudPrint-deamon** (`d4079fc4`): 5 kataloger, branches fra 6.-7. mai
- **masterfeed-app** (`e15dc3a4`): 7 kataloger, branches fra 7. mai
- **cloudprint_mac_app** (`df6916d0`): 8 kataloger, branches fra 7. mai
