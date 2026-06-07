# Session Reset og Worktree — Feilsøking

## Symptom

En agent oppretter worktree og jobber der, men når du kommer tilbake til tråden senere, starter agenten i main-repoet — som om worktree-et ikke finnes.

## Scenario

```
Kl 00:46 — Melding 1: "Gjør oppgave X" 
           → Agent oppretter worktree og jobber derfra ✅
Kl 07:20 — Melding 2: "Status?" 
           → Agent starter i main-repoet, aner ikke om worktree ❌
```

## Root Cause

Hermes har en **default session reset policy**:

```yaml
# Default (hvis ikke overstyrt i config.yaml):
reset_policy:
  mode: both          # "daily" ELLER "idle" — den som slår til først
  at_hour: 4          # Reset hver natt kl 04:00 lokal tid
  idle_minutes: 1440  # Reset etter 24 timer inaktivitet
```

Når reset-en slår til, **forsvinner all kontekst** — agenten vet ikke at den jobbet i et worktree. Neste melding i samme Discord-thread starter en splitter ny session.

### Hvorfor session key ikke hjelper

Session key-en er deterministisk basert på `platform + chat_type + chat_id + thread_id` — så den *samme* nøkkelen brukes for begge meldingene. Men `get_or_create_session()` i gatewayen sjekker reset policy og oppretter en NY session hvis den gamle er utløpt, selv om nøkkelen er den samme.

## Løsninger

### A) Endre reset policy (anbefalt for lange tråder)

I `~/.hermes/config.yaml`:

```yaml
gateway:
  default_reset_policy:
    mode: idle          # Kun idle-timeout, ingen daglig reset
    at_hour: 4          # Irrelevant når mode=idle
    idle_minutes: 4320  # 72 timer (3 dager)
```

Eller per platform/chat-type:

```yaml
gateway:
  reset_by_type:
    thread:
      mode: none        # Aldri reset threads — kun compression
    dm:
      mode: idle
      idle_minutes: 1440
```

### B) Sjekk alltid worktrees ved oppstart (sikkerhetsnett)

Memory-regelen sier nå:

```
WORKTREE-REGLER:
1. FØR du starter: sjekk `git worktree list` — bruk eksisterende
   worktree hvis det matcher oppgaven
2. Opprett NYTT worktree FRA main: `git worktree add ... -b ... main`
3. FLYTT STRAKS til worktree-mappen — ALL koding/terminalkjøring
   skal ha worktree som cwd/workdir
4. For koding: bruk ALLTID OpenCode med workdir satt til worktree-stien
5. ALDRI jobb i main/master
```

Denne regelen ligger i MEMORY.md, så den gjelder for ALLE sessions uansett reset-status.

## Verifisering

Sjekk gjeldende reset policy:

```bash
grep -A10 reset_policy ~/.hermes/config.yaml
```

Sjekk om en session ble auto-reset:

```bash
hermes sessions list | grep <channel/thread-navn>
# Se etter "was_auto_reset: True" i session-metadata
```
