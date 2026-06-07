# Discord Thread-Opprettelse: Feilsøkingsguide

## Symptom: Melding i `-dev` kanal oppretter ingen thread

### Sjekkliste (i prioritert rekkefølge)

1. **Er meldingen en reply?**
   - Replies hopper over auto-threading
   - Løsning: Send en ny melding (ikke en reply)

2. **Er `free_response_channels` konfigurert?**
   ```bash
   grep -A5 "free_response_channels" ~/.hermes/config.yaml
   ```
   - Sett til `'*'` for alle kanaler
   - Eller legg til spesifikk channel-ID: `'1511404097302171818'`

3. **Er `auto_thread: true`?**
   ```bash
   grep "auto_thread" ~/.hermes/config.yaml
   ```

4. **Gateway restart nødvendig?**
   Config-endringer krever restart:
   ```bash
   hermes restart
   ```

5. **Er `auto-thread-whitelist` pluginen enabled?**
   Sjekk config.yaml:
   ```bash
   grep -A2 "enabled" ~/.hermes/config.yaml | grep auto-thread
   ```
   Hvis pluginen mangler, må den være i `plugins.enabled` og gatewayen restartes.

6. **Er kanalen i `discord.auto_thread_channels`?**
   Sjekk config.yaml:
   ```bash
   grep -A5 "auto_thread_channels" ~/.hermes/config.yaml
   ```
   Auto-thread skjer KUN i kanaler som står i denne whitelisten (via pluginen).

---

## Viktige miljøvariabler

| Variabel | Default | Beskrivelse |
|----------|---------|-------------|
| `DISCORD_AUTO_THREAD` | `true` | Enable/disable auto-threading |
| `DISCORD_FREE_RESPONSE_CHANNELS` | `*` | Kanaler uten @mention-krav |
| `DISCORD_NO_THREAD_CHANNELS` | (empty) | Kanaler som SKAL IKKE ha auto-thread |
| `DISCORD_IGNORE_NO_MENTION` | `true` | Svar uten @mention i visse kanaler |
| `DISCORD_REQUIRE_MENTION` | `false` | Krever @mention for å svare |

---

## Hermes Discord Adapter: Viktige metoder

### `_auto_create_thread(message)`
- Oppretter thread automatisk for nye meldinger
- Thread-navn genereres av AI
- Trigger: kun for `MessageType.default` og `MessageType.reply` som IKKE er replies

### `_discord_free_response_channels()`
- Leser channel-IDs fra config eller env
- Støtter `'*'` wildcard for alle kanaler
- Støtter både streng og liste-formater

### `_threads.mark(thread_id)`
- Tracker hvilke tråder boten har deltatt i
- Tillater oppfølging uten @mention i deltatte tråder

---

## Kjente begrensninger

1. **Replies** → ingen auto-thread (designet for å unngå overflødige tråder)
2. **Voice-linkede kanaler** → hopper over auto-threading
3. **System-meldinger** (thread renames, pins, joins) → ignorert
4. **Bot-meldinger** (med `DISCORD_ALLOW_BOTS=none`) → ignorert

---

## Oppdaget via debugging

Under debugging av manglende thread-opprettelse fant vi:
- Hermes har `feat/discord-ai-thread-naming` branch med AI-drevet thread-naming
- Discord adapter bruker `discord.MessageType.reply` for å sjekke om melding er en reply
- `is_reply_message = getattr(message, 'type', None) == discord.MessageType.reply`

## Kritisk innsikt: Skill ≠ Gateway Hook

**Problemet:** Skillen beskriver en idealisert flyt der thread + worktree opprettes automatisk når bruker skriver i en `-dev` kanal. Dette er IKKE hvordan systemet faktisk fungerer.

**Faktisk oppførsel:**
- Discord gateway har ingen automatisk trigger basert på kanalnavn alene
- Boten aktiveres KUN når: (a) bruker nevner boten med @, eller (b) bruker starter en samtale med boten først
- Skillen er en MANUELL arbeidsflyt som agenten KAN utføre når boten er aktiv i tråden

**Konsekvens:** Hvis bruker skriver "Dette er en test" i en dev-kanal uten å nevne boten eller ha startet en dialog, vil boten enten:
- Ignorere meldingen (hvis `require_mention: true`)
- Svare direkte i kanalen uten thread (hvis `require_mention: false` og `auto_thread: false`)

**Løsning for dev-kanal workflow:**
1. Bruker må nevne boten (`@bot <melding>`) for å aktivere gateway auto-thread
2. DERETTER kan agent overta og kjøre worktree/branch-flyten
3. Alternativt: start samtalen med boten først, deretter bruk dev-kanaler