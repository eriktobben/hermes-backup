# Memory Migration Example (Tobben/Erik)

Concrete migration of `~/.hermes/memories/MEMORY.md` and `~/.hermes/memories/USER.md` into Mnemosyne global memories.

## Source classification

| File | Source tag | Importance range |
|------|-----------|-----------------|
| MEMORY.md — project facts, env config | `fact` | 0.6-0.8 |
| USER.md — identity (name, language, role) | `identity` | 0.85-0.95 |
| USER.md — workflow preferences, timezone | `preference` | 0.7-0.85 |
| USER.md — factual plans (bilkjop) | `fact` | 0.7-0.8 |

## MEMORY.md sections

1. `Laravel: Livewire i Blade views (unngå full-page). Krev tester (feature+unit), suite må passere. Norsk ÆØÅ.` → fact, 0.8
2. `Nye prosjekter: ~/Projects/REPONAVN` → fact, 0.7
3. `masterfeed-dev + masterfeed-scroll i ~/Projects/...` → fact, 0.8
4. `Epost-klassifisering: ~/Projects/epost-klassifisering/...` → fact, 0.7
5. `Kimaki: patch worktree (~/.local/bin/kimaki-patch-worktree)...` → fact, 0.75
6. `Kimaki-prosjekt embermail: git@github.com:Tobbens-Empire/embermail.git...` → fact, 0.7
7. `here.now: trailing slash BUG...` → fact, 0.7
8. `Veronica Bremnes – bloggprofil for Tobben...` → fact, 0.6

## USER.md sections

1. `Workflow: project channels + feature/fix threads...` → preference, 0.85
2. `Bruker: Erik. Uformell tone...` → identity, 0.95
3. `User is in Norwegian timezone (CET/CEST, Europe/Oslo)...` → preference, 0.7
4. `Tobben (Erik) - bilkjøp 2026...` → fact, 0.75

## Verification

- `hermes mnemosyne stats` — 14 working memories (12 migrated + 2 from conversation)
- `mnemosyne_recall("Laravel Livewire tester")` — returns both the Laravel rule and user profile
