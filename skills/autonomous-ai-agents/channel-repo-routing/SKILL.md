---
name: channel-repo-routing
description: Route chat channels/threads to the correct local repository and branch, with strict per-task workspace hygiene across messaging platforms.
---

# Channel/Thread → Repo Routing

## Umbrella class
Use this for any chat-driven coding workflow where the agent receives tasks in channels/threads and must avoid cross-repo mistakes.

## Core protocol
1. Map channel/thread identity to project repo path.
2. Require a task header at thread start with repo, branch, task scope, constraints.
3. Restate resolved repo+branch before touching files.
4. Verify repo exists locally; resolve path ambiguity before any edits.
5. Restrict file/terminal actions to mapped repo unless user explicitly broadens scope.
6. Before destructive actions, re-verify repo and branch.
7. Finish with changed files, tests run, and next git commands.

## Platform-specific subsection: Discord
- Derive project from channel/thread naming conventions.
- Optionally maintain ID-level mapping in `~/.hermes/repo-map.yaml`.
- Use feature/fix/chore thread naming and same branch slug.

## Suggested support files
- `templates/thread-header.md` for task kickoff header
- `references/repo-map-schema.md` for mapping conventions and examples

## Verification checklist
- Repo path matches channel mapping
- Branch matches thread intent
- No edits outside mapped repo
- Tests/lint run (or explicitly skipped)
