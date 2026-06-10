---
name: github-workflows
description: "Complete GitHub workflow suite: auth setup, repo management, issues, PR lifecycle, and code review. Each section shows gh CLI first, then git+curl fallback. Shared auth detection pattern included once."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, git, workflow, pull-requests, issues, code-review, auth]
    category: github
---

# GitHub Workflows (Umbrella)

Covers the full GitHub interaction lifecycle: authentication, repository management, issues, pull requests, and code review. Each operation shows `gh` CLI first, then `git + curl` fallback for machines without `gh`.

---

## 0. Shared Auth Detection (use before any GitHub operation)

```bash
# Determine available auth method
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH_METHOD="gh"
else
  AUTH_METHOD="curl"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Auth: $AUTH_METHOD"

# Extract owner/repo from git remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ -n "$REMOTE_URL" ]; then
  OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
  OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
  REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
fi
```

For detailed auth setup (HTTPS tokens, SSH keys, headless token-based login), see [Section A](#section-a-authentication-setup).

---

## Section A: Authentication Setup

Two paths:

### Method 1: Git-Only (HTTPS with Personal Access Token)
Create token at https://github.com/settings/tokens (scopes: `repo`, `workflow`, `read:org`).
```bash
git config --global credential.helper store
git config --global user.name "Your Name"
git config --global user.email "email@example.com"
# First operation will prompt for username + token
```

### Method 2: gh CLI
```bash
gh auth login                    # interactive browser
# or headless:
echo "$TOKEN" | gh auth login --with-token
gh auth setup-git
```

### Troubleshooting
| Problem | Solution |
|---------|----------|
| `git push` asks for password | Use personal access token (GitHub disabled password auth) |
| SSH `Connection refused` on port 22 | Add `Port 443` + `Hostname ssh.github.com` to `~/.ssh/config` |
| `gh: command not found` + no sudo | Use git-only Method 1 |

Full reference: See archived `github-auth`.

---

## Section B: Repository Management

### Clone
```bash
git clone https://github.com/owner/repo.git
gh repo clone owner/repo           # shorthand
```

### Create
```bash
# gh
gh repo create my-project --public --clone

# curl
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name": "my-project", "private": false}'
```

### Fork & Sync
```bash
gh repo fork owner/repo --clone
git remote add upstream https://github.com/owner/repo.git
git fetch upstream && git merge upstream/main && git push
```

### Secrets (GitHub Actions)
```bash
gh secret set API_KEY --body "your-secret-value"
# curl requires encryption with repo public key - use gh for simplicity
```

### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
```

Full reference: See archived `github-repo-management`.

---

## Section C: Issues

### View
```bash
gh issue list --state open --label "bug"
gh issue view 42
```

### Create
```bash
gh issue create \
  --title "Login redirect ignores next parameter" \
  --body "## Description\n..." \
  --label "bug,backend"
```

### Manage
```bash
gh issue edit 42 --add-label "priority:high" --add-assignee username
gh issue close 42
gh issue reopen 42
gh issue comment 42 --body "Working on a fix."
```

### curl equivalents use `https://api.github.com/repos/$OWNER/$REPO/issues`

Full reference: See archived `github-issues`.

---

## Section D: PR Workflow

### Branch → Commit → Push
```bash
git checkout -b feat/my-feature
git add -A && git commit -m "feat: add feature"
git push -u origin HEAD
```

### Create PR
```bash
gh pr create --title "feat: ..." --body "Summary\nCloses #42"
# Use --draft for work-in-progress
```

### Monitor CI
```bash
gh pr checks --watch
```

### Auto-Fix CI Loop
1. Check CI status
2. Read failure logs: `gh run view <RUN_ID> --log-failed`
3. Fix, commit, push
4. Re-check (up to 3 attempts)

### Merge
```bash
gh pr merge --squash --delete-branch
```

### Fork-Based Flow (no write access to upstream)
```bash
gh repo fork owner/repo --clone=false
git remote add fork git@github.com:you/repo.git
git push -u fork HEAD
# Open PR from your fork
```

Full reference: See archived `github-pr-workflow`.

---

## Section E: Code Review

### Review Local Changes (Pre-Push)
```bash
git diff main...HEAD --stat          # scope
git diff main...HEAD                  # full diff
# Check for common issues:
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME"
git diff main...HEAD | grep -in "password\|secret\|api_key"
```

### Review a PR on GitHub
```bash
gh pr view 123
gh pr diff 123
gh pr checkout 123                    # check out locally
```

### Post Review
```bash
# Single comment
gh pr review 123 --comment --body "Some suggestions"

# Approve or request changes
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments"

# Inline comments via API (curl)
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')
gh api repos/$OWNER/$REPO/pulls/123/comments \
  --method POST \
  -f body="Use parameterized queries" \
  -f path="src/auth.py" \
  -f commit_id="$HEAD_SHA" \
  -f line=45
```

### Review Checklist
- **Correctness**: edge cases, error paths
- **Security**: no hardcoded secrets, SQL injection, XSS, path traversal
- **Quality**: clear naming, DRY, single responsibility
- **Testing**: new code paths tested (happy + error)
- **Performance**: no N+1 queries, no blocking in async

### curl-only review (submit multiple inline comments atomically)
```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d '{
    "commit_id": "'"$HEAD_SHA"'",
    "event": "COMMENT",
    "body": "Review from Hermes Agent",
    "comments": [
      {"path": "src/auth.py", "line": 45, "body": "SQL injection risk"},
      {"path": "src/models.py", "line": 23, "body": "Plaintext password storage"}
    ]
  }'
```

Full reference: See archived `github-code-review`.

---

## Section F: Codebase Inspection (pygount)

Use `pygount` for LOC counts, language breakdowns, and code-vs-comment ratios.

### Install
```bash
pip install pygount
```

### Basic Summary
```bash
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs" \
  .
```

**Always use `--folders-to-skip`** — without it, pygount crawls dependency trees and may hang.

### Filter by Language
```bash
pygount --suffix=py --format=summary .
```

### Interpreting Results
- **Language** — detected programming language
- **Files** — count per language
- **Code** — lines of actual code
- **Comment** — comment/doc lines
- Markdown shows 0 code lines (classified as comments)

Full detail: See archived `codebase-inspection`.

---

## Pitfalls

1. **Run auth detection before every workflow** — don't assume `gh` is available or authenticated.
2. **Workspace isolation** — when editing code, use worktree mode (`hermes -w`) or explicit branches.
3. **Secrets require `gh`** — the curl path requires Python+PyNaCl for encryption; use `gh secret set` when possible.
4. **Branch protection** — if PR merge fails, check branch protection rules via API.
5. **PR from fork** — upstream repos without write access require the fork flow (Section D).
6. **Large diffs** — split review by file when diff exceeds ~15K characters.
