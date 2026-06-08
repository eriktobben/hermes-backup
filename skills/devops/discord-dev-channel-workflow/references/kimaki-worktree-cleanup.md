# Kimaki Worktree Cleanup

## Bakgrunn

Kimaki oppretter git worktrees + branches per Discord-thread via `--use-worktrees`-flagget. Worktrees legges under `~/.kimaki/worktrees/<project-id>/<navn>/` og branches får navn som `opencode/kimaki-<beskrivelse>`.

Over tid hoper dette seg opp — både lokale worktree-kataloger, lokale branches og (om de er pushet) remote branches på origin.

## Skript

**Sti:** `~/.hermes/scripts/kimaki-worktree-cleanup.py`

### Kjøring

```bash
# Tørrkjøring — viser hva som skal ryddes uten å gjøre noe
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py

# Faktisk cleanup
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py --apply
```

### Terskelverdi

Default: **14 dager** siden siste aktivitet. Endre `DAYS_THRESHOLD` variabelen øverst i skriptet for å justere.

### Hva skjer med en inaktiv worktree

1. **`git worktree remove --force <katalog>`** — fjerner worktree-et fra git
2. **`git branch -D <branch>`** — sletter lokal branch
3. **`git push origin --delete <branch>`** — sletter remote branch (hvis den finnes)
4. **`shutil.rmtree(<katalog>)`** — fjerner katalogen fysisk
5. **`UPDATE thread_worktrees SET status = 'cleaned'`** — oppdaterer Kimaki DB

### Aktivitetsdeteksjon

| Scenario | Hva brukes som "siste aktivitet" |
|----------|----------------------------------|
| Branch finnes på origin | `git log origin/<branch>` — siste commit-dato |
| Branch finnes kun lokalt | `git log <branch>` — siste commit-dato |
| Ingen commits (initial checkout) | `created_at` fra Kimaki DB |

### Orphaned worktrees

Worktree-kataloger som finnes på disk men **ikke** har noen oppføring i Kimaki DBs `thread_worktrees`-tabell. Disse ryddes i Fase 2 av skriptet. Skriptet finner main repo fra `.git`-filas `gitdir:`-peker, så det kan gjøre `git worktree remove` for å holde git-konfigurasjonen ren.

### Eksisterende worktrees som ikke håndteres

- **OpenCode `.worktrees/`** — kataloger under `<prosjekt>/.worktrees/<navn>/` (OpenCode sin egen worktree-mekanisme). Disse må ryddes manuelt eller via OpenCode selv.
- **Manuelle worktrees** — opprettet utenfor Kimaki. Ryddes manuelt.

## Database

```sql
-- Hent alle ready worktrees med sessions
SELECT tw.*, ts.session_id, ts.last_synced_name as session_name
FROM thread_worktrees tw
LEFT JOIN thread_sessions ts ON tw.thread_id = ts.thread_id
WHERE tw.status = 'ready'
ORDER BY tw.created_at;
```

## Cron-jobb (anbefalt oppsett)

Kjør daglig for å unngå opphopning:

```bash
hermes cron create \
  --name "Kimaki worktree cleanup (daglig)" \
  --schedule "0 4 * * *" \
  --script ~/.hermes/scripts/kimaki-worktree-cleanup.py \
  --no-agent \
  --deliver local
```

Bruk `--deliver origin` hvis du vil få rapport i chatten hver morgen.
