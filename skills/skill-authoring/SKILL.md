---
name: skill-authoring
description: "Create, edit, and manage Hermes Agent skills — both user-local (~/.hermes/skills/) via skill_manage and in-repo (shipped with hermes-agent package). Includes frontmatter validation, structure guides, and best practices for discoverability. Use when creating, writing, or building a new skill, or authoring in-repo skills for hermes-agent."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, skill-md, conventions, hermes-agent]
    related_skills: [hermes-agent, curator]
---

# Skill Authoring Guide

Two places a SKILL.md can live:

| Location | Use case | Creation method |
|----------|----------|-----------------|
| **User-local**: `~/.hermes/skills/<category>/<name>/SKILL.md` | Personal skills, reusable procedures | `skill_manage(action='create')` |
| **In-repo**: `skills/<category>/<name>/SKILL.md` in hermes-agent repo | Skills shipped with the package | `write_file` + `git add` |

## Description Requirements

The description is the only thing an agent sees when deciding which skill to load. It's surfaced in the system prompt alongside all other installed skills.

**Goal**: Give the agent just enough info to know:
1. What capability this skill provides
2. When/why to trigger it (specific keywords, contexts, file types)

**Format**: Max 1024 chars. First sentence: what it does. Second sentence: "Use when [specific triggers]".

**Good**: `"Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when user mentions PDFs, forms, or document extraction."`
**Bad**: `"Helps with documents."` — no way to distinguish from other document skills.

## Required Frontmatter

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars
description: "Use when <trigger>. <one-line behavior>."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

Hard requirements:
- Starts with `---` at byte 0 (no leading blank line or BOM)
- Closes with `\n---\n` before the body
- Parses as valid YAML mapping
- `name` field present (≤64 chars, lowercase + hyphens)
- `description` field present (≤1024 chars)
- Non-empty body after the closing `---`

## Size Limits

- Description: ≤ 1024 chars (enforced)
- Full SKILL.md: ≤ 100,000 chars (~36k tokens)
- Aim for 8-14k chars. Pushing past 20k → split into `references/*.md`

## Structure Template

```markdown
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables
- Code blocks with exact commands
- Hermes-specific recipes

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications
```

## When to Add Scripts

Add utility scripts (`scripts/`) when:
- Operation is deterministic (validation, formatting)
- Same code would be generated repeatedly
- Errors need explicit handling

## When to Split Files

Split into `references/`, `templates/`, `scripts/` when:
- SKILL.md exceeds ~20k chars
- Content has distinct domains
- Advanced features are rarely needed

## Creating User-Local Skills

Use `skill_manage(action='create')`:

```python
skill_manage(
    action="create",
    name="my-new-skill",
    content="""---
name: my-new-skill
description: "Use when ..."
version: 1.0.0
author: Hermes Agent
license: MIT
---
# My New Skill
...""",
    category="software-development"  # optional, creates subdirectory
)
```

To update: `skill_manage(action='patch', name='...', old_string='...', new_string='...')`
To add support files: `skill_manage(action='write_file', name='...', file_path='references/foo.md', file_content='...')`

## Creating In-Repo Skills (hermes-agent package)

Use `write_file` to place the skill in the repo tree:

```bash
# Path: skills/<category>/<name>/SKILL.md
write_file("skills/software-development/my-skill/SKILL.md", "...")
```

### Categories

Existing categories (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest. Don't invent new top-level categories casually.

### Workflow

1. Survey peers in the target category
2. Draft with `write_file`
3. Validate frontmatter (see required frontmatter section above)
4. `git add` + `git commit`

### Cross-Referencing

`metadata.hermes.related_skills` unions both trees (in-repo and user-local) at load time. Prefer referencing only in-repo skills from in-repo skills.

### Pitfalls

- `skill_manage(action='create')` writes to `~/.hermes/skills/`, NOT the repo tree
- Leading whitespace before `---` fails validation
- Description too generic → the agent can't distinguish it from peers
- Current session's skill loader is cached — new skills won't appear until next session
- Prefer extending an existing skill to creating a narrow sibling

## Review Checklist

After drafting, verify:
- [ ] Description includes triggers ("Use when...")
- [ ] Frontmatter starts at byte 0 with `---`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: Overview → When to Use → body → Pitfalls → Checklist
- [ ] No time-sensitive info
- [ ] Consistent terminology
