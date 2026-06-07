---
name: discord-channel-repo-routing
description: "Map Discord channels/threads to git repositories and enforce per-task session hygiene for Hermes coding workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, discord, repository, workflow, channel-mapping]
---

# Discord Channel → Repo Routing

Use this skill when working in Discord with multiple software projects and repositories.

## Goal

Ensure each project channel (and each feature/fix thread under it) stays pinned to the correct local git repo and branch context.

## What this skill standardizes

1. One project per channel (or parent thread)
2. One feature/fix per thread
3. Explicit repo+branch header at thread start
4. No cross-repo actions unless explicitly requested

## Setup

Create a mapping file at:

`~/.hermes/repo-map.yaml`

Example format:

```yaml
projects:
  serena:
    repo_path: ~/code/serena
    default_branch: main
  ig-flow:
    repo_path: ~/code/ig-flow
    default_branch: main

# Optional: exact Discord channel/thread IDs if you want strict routing docs
# discord:
#   channel_id_to_project:
#     "1498947405524107275": serena
```

## Thread start template (paste in first message)

```md
Repo: ~/code/<repo>
Branch: <feat/...|fix/...|chore/...>
Task: <short task description>
Constraints: <tests, style, deadlines>
```

## Operating procedure

1. Identify project from channel/thread name (e.g. `serena`, `ig-flow`).
2. Resolve expected repo from `~/.hermes/repo-map.yaml`.
3. If thread header has a different repo, ask user which one to use before any file edits.
4. Before coding, restate:
   - resolved repo path
   - target branch name
   - task scope
5. Verify the repo path exists on disk before running any git/file commands.
   - If a provided path fails (common `~/...` vs `/home/<user>/...` mismatch), quickly locate the repo under likely roots (e.g. `~/Projects`) and confirm/use the real absolute path.
   - Update the channel mapping note once the canonical path is confirmed.
6. Perform all file/terminal actions only in that repo path unless user explicitly broadens scope.
7. At completion, summarize changed files, tests run, and next git commands.

## Naming conventions

- Thread names: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`
- Branch names: same as thread name
- Session title: same as thread name

## Safety checks

Before destructive git or filesystem operations:

1. Verify current repo path and branch are correct for this thread.
2. Confirm if operation affects more than one repo.
3. If uncertain, stop and ask user.

## Verification checklist

- [ ] Repo path matches project mapping
- [ ] Branch matches feature/fix intent
- [ ] No files changed outside mapped repo
- [ ] Tests/lint executed (or explicitly skipped)

## Pitfalls

- Working from wrong cwd when switching projects quickly
- Reusing context from a different feature thread
- Running commits on `main` instead of feature branch

Mitigation: always include the thread start header and re-state repo/branch before edits.
