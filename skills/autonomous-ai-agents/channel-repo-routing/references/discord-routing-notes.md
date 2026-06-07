# Discord routing notes (migrated)

- Keep a mapping file at `~/.hermes/repo-map.yaml`.
- Suggested header at thread start:
  - Repo path
  - Branch name
  - Task summary
  - Constraints/tests
- If thread header repo conflicts with mapped repo, resolve before edits.
- Verify repo path existence before git/file actions.
- Common pitfall: `~/...` vs absolute path mismatch; confirm canonical path once and update mapping notes.
