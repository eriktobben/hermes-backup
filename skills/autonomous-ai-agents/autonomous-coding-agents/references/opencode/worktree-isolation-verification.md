# Worktree Isolation Verification (Git + OpenCode)

Use this when users report cross-session contamination (files/commits ending up in the wrong thread/session).

## Goal
Guarantee each active session has:
- a unique working directory (worktree)
- a unique branch
- OpenCode running in that worktree only

## Minimal smoke test
From repo root:

```bash
WT=/tmp/opencode-wt-smoke-$$
git worktree add --detach "$WT" HEAD
cd "$WT"
opencode --pure run "Respond with exactly: OC_WT_SMOKE_OK" --model openai/gpt-5.4-mini
cd -
git worktree remove "$WT" --force
```

Expected: output contains `OC_WT_SMOKE_OK` and exit code 0.

## Session isolation checks
Run inside each active session workdir:

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
```

Interpretation:
- `pwd`/`--show-toplevel` must differ between sessions.
- `--show-current` must differ between sessions.

If either is shared, sessions are not isolated.

## Recommended creation command

```bash
git worktree add <worktree-path> -b <session-branch> <base-ref>
```

Example:

```bash
git worktree add ~/.kimaki/worktrees/<project>/<session-slug> -b feature/<session-slug> origin/main
```

## Notes
- This isolates git/file collisions, but does not fix provider/model API failures.
- If one model is unstable, keep isolation and switch model/provider separately.
