# Adapting Third-Party Skills from Other Agent Systems

Skills from Claude Code, Codex, Cursor, Gemini CLI, etc. often work in Hermes with zero changes. The key check: **is it pure markdown, or does it contain executable code?**

## Quick Compatibility Check

| Signal | Compatible? | Action |
|--------|-------------|--------|
| Pure `.md` files, no code blocks with imports/runs | ✅ Yes | Copy directly to `~/.hermes/skills/<name>/` |
| Markdown + Python/JS code blocks meant as *examples* (not execution) | ✅ Yes | Copy as-is |
| References `.claude/` or `.agents/` directories | ✅ Yes | Hermes also checks `.agents/` — no change needed |
| Uses Claude-specific slash commands (`/plugin`, `/skill`) in instructions | ⚠️ Partial | Copy the skill; ignore Claude-specific install instructions |
| Contains executable Python/JS that imports from Claude SDK | ❌ No | Rewrite tool-calling sections for Hermes tool schema |
| Uses Claude's `CLAUDE.md` / `AGENTS.md` conventions | ✅ Yes | Hermes reads these natively |

## Install Steps

```bash
# 1. Clone or download the repo
git clone https://github.com/<owner>/<skill-repo>.git /tmp/<skill-repo>

# 2. Find the skill directory (usually skills/<name>/ or just the repo root)
ls /tmp/<skill-repo>/skills/

# 3. Copy to Hermes skills directory
cp -r /tmp/<skill-repo>/skills/<name> ~/.hermes/skills/<name>

# 4. Verify it loads
# Start a new session and run: /skill <name>
# Or: skill_view(name='<name>')
```

## What to Adapt

**Usually nothing.** But check these:

1. **Install instructions** — rewrite any Claude-specific commands (`/plugin marketplace add`) to `cp -r` or `skill_manage`
2. **Directory references** — `.claude/` works in Hermes (AGENTS.md is read natively), but `.agents/` is the Hermes-native equivalent
3. **Subagent fan-out** — if the skill describes spawning Claude subagents, map to Hermes `delegate_task` tool
4. **MCP references** — Claude MCP and Hermes MCP are compatible; no changes needed

## Pitfalls

- Some Claude skills assume `CLAUDE.md` exists in the project root. Hermes reads `AGENTS.md` the same way — both work.
- Skills with heavy Claude Code plugin dependencies (custom slash commands) won't transfer. Pure markdown skills always work.
- After copying, the skill won't appear until the next session (`/reset` or new invocation).
