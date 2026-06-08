---
name: discord-dev-channel-workflow
description: Oppretter Discord thread + git worktree/branch når bruker skriver i en -dev kanal
triggers:
  - Bruker skriver i en Discord channel med "-dev" i navnet og der boten er aktiv (enten pga @mention eller fordi bruker startet samtalen)
---

# Discord Dev Channel Workflow

## Oversikt
Når brukeren skriver i en `-dev` kanal og boten er aktiv i tråden, oppretter jeg:
1. Auto-thread whitelist (legg til kanal-ID hvis ny)
2. En Discord-thread med et beskrivende navn (basert på meldingen)
3. Et git worktree + branch for oppgaven

**OBS: Dette er en manuell flyt, ikke en automagisk gateway-hook.**

## Flyt

### 1. Sjekk kanal-type
Hvis kanalnavnet inneholder `-dev`, kjør denne flyten.

### 2. Sjekk/sync auto-thread whitelist
Sjekk om kanalens ID allerede står i `discord.auto_thread_channels` i `~/.hermes/config.yaml`:

```bash
grep -q "<channel_id>" ~/.hermes/config.yaml
```

Hvis **ikke** funnet — legg den til i YAML-lista og restart gateway:

```bash
# Legg til kanal-ID i auto_thread_channels-lista
cd ~/.hermes
hermes config set discord.auto_thread_channels "[$(sed -n '/auto_thread_channels:/,/^[a-z]/p' config.yaml | grep '^\s*-' | sed 's/.*- //' | tr '\n' ', ' | sed 's/, $//'), <channel_id>]" 2>/dev/null || true

# Alternativ: bruk Python for å redigere YAML trygt
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
lst = c['discord'].setdefault('auto_thread_channels', [])
ch = '<channel_id>'
if ch not in [str(x) for x in lst]:
    lst.append(int(ch))
    with open('$HOME/.hermes/config.yaml', 'w') as f:
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f'Added {ch} to whitelist')
else:
    print(f'{ch} already in whitelist')
"
```

Hvis ID ble lagt til — restart gateway så endringen trer i kraft:

```bash
hermes gateway restart
```

**Resultat:** Nye meldinger i denne kanalen vil heretter få auto-thread.

### 3a. Sett session reset policy for threads

For `-dev` kanaler som får auto-threads, sett session reset policy til **idle 24 timer** så tråder ikke mister konteksten kl 04:00 hver natt:

```bash
# Sett at Discord-threads bruker idle 24t i stedet for daily reset
hermes config set gateway.reset_by_type.thread.mode idle
hermes config set gateway.reset_by_type.thread.idle_minutes 1440
hermes gateway restart  # trenger restart for å tre i kraft
```

Dette gjør at en samtale i en Discord-thread kan fortsette dagen etter uten å miste konteksten.
Sjekk memory for eksisterende mapping `Channel <channel_id> → <repo>`.

Hvis ingen mapping finnes, prøv pattern-matching:
```
<project>-dev → <org>/<ProjectName> (PascalCase)
f.eks: "masterfeed-dev" → "eriktobben/masterfeed"
```

Hvis ingen mapping fungerer, spør brukeren.

### 4. Generer thread-navn
Analyser brukerens melding og generer et beskrivende navn:
- **Features:** `feat: <beskrivelse>` eller `<project>: <beskrivelse>`
- **Bugfixes:** `fix: <beskrivelse>`
- **Alt annet:** `<beskrivelse>`

Regler:
- Maks 100 tegn (Discord-begrensning)
- Fjern Discord mention syntax (<@id>, <#id>, etc.)
- Bruk bindestreker i stedet for spaces
- Hold kort men deskriptivt

### 5. Opprett eller rename Discord thread

Gatewayen auto-oppretter allerede en thread med brukerens melding som navn. **Rename threaden** til noe beskrivende basert på oppgaven:

```bash
curl -s -X PATCH "https://discord.com/api/v10/channels/<thread_id>" \
  -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "<thread-navn>"}'
```

Thread-ID-en finner du i `SessionSource.thread_id` fra den innkommende meldingen, eller fra Discord channel-info via `hermes` profile/session context.

Hvis gatewayen **ikke** har auto-opprettet thread (f.eks. første gangs oppsett), kan du opprette en manuelt:

```python
# (Hvis discord_tool er tilgjengelig)
discord(action="create_thread", channel_id="<channel_id>", name="<thread-navn>", message_id="<brukerens_message_id>")
```

### 6. Sjekk/finn repo
```bash
# Sjekk om repo allerede er klona
ls -d /home/erik/Projects/<repo-navn>

# Hvis ikke, klon det
git clone https://github.com/<repo>.git /home/erik/Projects/<repo-navn>
```
### 7. Opprett worktree + branch

```bash
cd /home/erik/Projects/<repo-navn>

# Sjekk eksisterende worktrees
git worktree list

# Generer branch-navn fra thread-navn
# "feat: login-fix" → "feat/login-fix"
BRANCH_NAME=$(echo "<thread-navn>" | sed 's/ /-/g' | sed 's/:/-/g' | tr '[:upper:]' '[:lower:]')

# Unngå konflikter - legg til timestamp hvis nødvendig
TIMESTAMP=$(date +%H%M)
SHORT_DESC=$(echo "<thread-navn>" | sed 's/feat://' | sed 's/fix://' | tr '[:upper:]' '[:lower:]' | tr -d ' ' | cut -c1-20)

# Opprett worktree + branch
git worktree add ../<repo-navn>-${SHORT_DESC} -b ${BRANCH_NAME}
```

### 8. Verifiser worktree + branch

Etter at worktree er opprettet, **VERIFISER** at du faktisk står i worktree-et og på riktig branch:

```bash
cd /home/erik/Projects/<repo-navn>-${SHORT_DESC}
echo "=== VERIFISERING ==="
echo "PWD: $(pwd)"
echo "TOPLEVEL: $(git rev-parse --show-toplevel)"
echo "BRANCH: $(git branch --show-current)"
echo "WORKTREES:" && git worktree list
```

Alle 3 må samsvare:
- `pwd` = `git rev-parse --show-toplevel` (du er i roten av worktree-et)
- `git branch --show-current` = branch-navnet du opprettet (ikke `master`/`main`)
- `git worktree list` viser ditt worktree som en egen linje

### 9. Bruk worktree-et — VIKTIG!

Etter at worktree er opprettet og verifisert:

1. **BLI i worktree-mappen** — ALL påfølgende koding/terminalkjøring må foregå herfra
2. **For koding: bruk OpenCode** med `workdir` satt til worktree-stien (f.eks. `workdir="/home/erik/Projects/<repo>-<beskrivelse>"`)
3. **IKKE jobb i main-repoet** — alle endringer skal skje i worktree-et

Dette gjelder både for deg (Hermes agent) og når du delegerer til OpenCode.

### 10. Svar i tråden med verifisering

Send bekreftelse med **faktisk** worktree-info (hentet fra verifiseringen over):

```
✅ **Thread opprettet:** `<thread-navn>`
📁 **Worktree:** `/home/erik/Projects/<repo-navn>-<short-desc>` (verifisert ✅)
🌿 **Branch:** `<branch-name-alias>` (verifisert ✅)
💻 **Koding:** OpenCode med workdir i worktree-et

Klar for koding! Hva skal vi gjøre?
```

## Kjente channel→repo mappings
| Channel ID | Navn | GitHub Repo |
|------------|------|-------------|
| `1511404097302171818` | serena-dev | `Serena-AS/SerenaHome` |
| `1511501933180092478` | masterfeed-dev | `eriktobben/masterfeed` |

## Eksempel

**Input:** Bruker skriver i `#masterfeed-dev`: "Lag en JSON-parser for RSS-feeds"

**Trinn 1:** Kanal-type → `-dev` ✅
**Trinn 2:** Sjekk whitelist → 1511501933180092478 er allerede registrert ✅
**Trinn 3:** Thread-navn → `feat: rss-json-parser`
**Trinn 4:** `curl -X PATCH .../channels/<thread_id> -d '{"name": "feat: rss-json-parser"}'` (auto-thread rename)
**Trinn 5:** Branch → `feat/rss-json-parser`
**Trinn 6:** Worktree → `../masterfeed-rss-json-parser`
**Trinn 7:** Verifiser → pwd, branch, worktree list
**Trinn 8:** Svar i thread med verifisert info

## Feilhåndtering
- **Repo finnes ikke:** Klon det først
- **Worktree eksisterer:** Bruk alternativt navn (f.eks. `feat/rss-json-parser-v2`)
- **Thread-opprettelse feiler:** Logg feilen, fortsett med worktree uansett
- **Discord API-feil:** Prøv igjen med kortere navn hvis for langt

## Viktig: Hvordan boten aktiveres i dev-kanaler

Boten trigges i en dev-kanal på to måter:
1. **Bruker nevner boten** (`@bot Dette er en test`) → gateway auto-thread + dispatcherer til meg
2. **Bruker starter en samtale med meg først** → deretter kan bruker skrive i dev-kanal og jeg catcher det

Uten en av disse vil ikke boten svare og ingen thread opprettes.

## Gateway Auto-Thread vs Manuell Thread

Gatewayen har en **auto-thread-funksjon** (`discord.auto_thread: true` i `~/.hermes/config.yaml`) som automatisk oppretter en thread når boten blir aktivert. Dette skjer før agenten blir involvert.

**For Erik/Tobben:** Auto-threading er kun aktivert i `-dev`-kanaler via en whitelist-plugin. Se `references/auto-thread-config.md` for oppsett. **Du trenger ikke manuelt å opprette threads i `-dev`-kanaler** — gatewayen gjør det automatisk. Skillens rolle er derfor redusert til **git worktree + branch-opprettelsen**.

## Worktree Cleanup (automatisk)

Bruker Kimaki (`~/.kimaki/`) som oppretter worktrees per Discord-thread. Uten automatisk rydding hoper worktrees og branches seg opp både lokalt og på origin.

### Cleanup-skript

Skriptet ligger på `~/.hermes/scripts/kimaki-worktree-cleanup.py` (se `references/kimaki-worktree-cleanup.md`).

```bash
# Dry-run (rapport uten endringer)
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py

# Faktisk cleanup
python3 ~/.hermes/scripts/kimaki-worktree-cleanup.py --apply
```

### Hvordan det fungerer

1. Leser `thread_worktrees`-tabellen i Kimaki DB (`~/.kimaki/discord-sessions.db`)
2. For hver worktree med status `'ready'`:
   - Sjekker **siste session-event** i `session_events`-tabellen (PRIMÆR kilde)
   - Fallback til siste commit-dato på **origin**, så **lokal branch**
   - Siste fallback: `created_at` fra DB
3. Hvis siste aktivitet > **14 dager** siden:
   - `git worktree remove --force <dir>`
   - `git branch -D <branch>` (lokal)
   - `git push origin --delete <branch>` (hvis den finnes på origin)
   - Sletter mappa fysisk
   - Oppdaterer DB-status til `'cleaned'`
4. Fase 2: Orphaned worktree-kataloger (finnes på disk men ikke i DB) ryddes også

### Typer worktrees

| Hvor | Sti | Beskrivelse |
|------|-----|-------------|
| Kimaki | `~/.kimaki/worktrees/<project-id>/<navn>/` | Opprettet av Kimaki `--use-worktrees` |
| OpenCode | `<prosjekt>/.worktrees/<navn>/` | Opprettet av OpenCode direkte |
| Manuelle | `<prosjekt>-<beskrivelse>/` | Opprettet manuelt via denne skillen |

Skriptet håndterer **Kimaki-worktrees** (de som hopet seg opp). For OpenCode-worktrees og manuelle worktrees må du rydde manuelt eller utvide skriptet.

### Oppsett av cron-job

Slik setter du opp automatisk daglig cleanup via Hermes cron:

```bash
# Opprett daglig jobb som kjører kl 04:00
hermes cron create \
  --name "Kimaki worktree cleanup (daglig)" \
  --schedule "0 4 * * *" \
  --script ~/.hermes/scripts/kimaki-worktree-cleanup.py \
  --no-agent \
  --deliver local
```

Bruk `--deliver local` for stillest kjøring (ingen varsel) eller `--deliver origin` for å få rapport i chat.

## Pitfalls
- Thread-navn må være under 100 tegn
- Branch-navn må være gyldige (ingen spaces, start med bokstav)
- Sjekk alltid `git worktree list` før opprettelse for å unngå konflikter
- **Whitelist-plugin må være enabled** i `plugins.enabled` i config.yaml for at auto-thread skal virke i dev-kanaler. Se `references/auto-thread-config.md` og `templates/auto-thread-whitelist-plugin/` for oppsett.
- **Session reset kan "glemme" worktree** — default reset policy reseter sessions hver natt kl 04:00. Hvis en bruker kommer tilbake til en thread etter reset, starter agenten uten kontekst om eksisterende worktrees. Løsning: endre reset policy eller sjekk `git worktree list` ved oppstart. Se `references/session-reset-worktree-troubleshooting.md`.
- **Bruker Kimaki for worktrees, ikke manuell opprettelse** — Erik/Tobben bruker Kimaki med `--use-worktrees`, så denne skillens manuelle worktree-steg (seksjon 7) gjelder kun for ikke-Kimaki-oppsett. Hopp til seksjon 7 hvis du selv skal opprette worktree uten Kimaki.
- **Worktrees uten commits** — Kimaki oppretter en worktree/branch som peker til samme commit som main. Hvis brukeren aldri gjør endringer, har branchen **samme commit-dato som main**. Cleanup-skriptet har 3 kilder prioritert: (1) session-events, (2) git commit-dato, (3) `created_at` fra DB — så det treffer riktig uansett.