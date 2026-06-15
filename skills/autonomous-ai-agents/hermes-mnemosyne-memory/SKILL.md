---
name: hermes-mnemosyne-memory
description: "Install and configure Mnemosyne as Hermes' memory backend — switch from built-in MEMORY.md/USER.md, migrate existing memories, and install the dashboard UI."
version: 1.0.0
author: agent
tags: [hermes, memory, mnemosyne, migration]
---

# Hermes Mnemosyne Memory Setup

Replace Hermes' built-in file-based memory (`MEMORY.md` / `USER.md`) with [Mnemosyne](https://github.com/AxDSan/mnemosyne) — a SQLite-backed, zero-dependency memory layer with vector search, knowledge graphs, and 23 management tools.

## When to use

- User asks to install Mnemosyne for Hermes
- User asks to switch from Hermes' built-in memory to a better provider
- User wants a visual dashboard for browsing memory
- User asks to migrate existing MEMORY.md/USER.md content to a structured memory store

## Installation

### 1. Install packages

```bash
# Core + Hermes plugin (with local embeddings via fastembed)
~/.hermes/hermes-agent/venv/bin/pip install mnemosyne-hermes
```

Available extras: `[embeddings]` (~800 MB RAM) or `[all]` (~1.5 GB RAM) for local LLM consolidation.

### 2. Link Hermes plugin

Symlink the installed package into Hermes' plugin directory:

```bash
mkdir -p ~/.hermes/plugins/mnemosyne
ln -sfn "$(~/.hermes/hermes-agent/venv/bin/python -c 'import pathlib, mnemosyne_hermes; print(pathlib.Path(mnemosyne_hermes.__file__).resolve().parent)')"/* ~/.hermes/plugins/mnemosyne/
```

### 3. Activate memory provider

```bash
hermes config set memory.provider mnemosyne
hermes memory setup
```

### 4. Disable built-in memory

Set these in `~/.hermes/config.yaml` (via `hermes config set`):

```bash
hermes config set memory.memory_enabled false
hermes config set memory.user_profile_enabled false
```

> Do NOT use `hermes tools disable memory` — that also kills all 23 Mnemosyne-registered tools.

### 5. Verify

```bash
hermes memory status        # Should show: Provider: mnemosyne, Plugin: installed ✓, Status: available ✓
hermes mnemosyne stats      # Should return working/episodic memory counts
```

## Migrating old MEMORY.md / USER.md to Mnemosyne

Hermes' built-in memory lives in `~/.hermes/memories/MEMORY.md` and `~/.hermes/memories/USER.md`. Sections are separated by `§`.

### Steps

1. Read both files with `read_file`
2. Split on `§`, strip whitespace, discard empty sections
3. Store each section as a global Mnemosyne memory using `mnemosyne_remember`:

**Source classification:**
- MEMORY.md sections → `source='fact'`, importance 0.6-0.8
- USER.md sections about identity → `source='identity'`, importance 0.85-0.95
- USER.md work preferences → `source='preference'`, importance 0.7-0.85
- USER.md factual plans → `source='fact'`, importance 0.7-0.8

All stored with `scope='global'` for cross-session availability.

### Verify migration

```bash
hermes mnemosyne stats        # Check total count
mnemosyne_recall("keyword")   # Test retrieval
```

Old MEMORY.md/USER.md can be kept as backup — they're no longer read when `memory_enabled: false`.

## Mnemosyne Dashboard

A local-first web UI for browsing, visualising, and safely maintaining the Mnemosyne store.

### Install

```bash
hermes plugins install wysie/mnemosyne-dashboard --enable
```

Default: `http://0.0.0.0:8765/` (LAN-accessible). Config at `~/.hermes/plugin-data/mnemosyne-dashboard/config.json`.

### Start / Stop (via Hermes tools)

The plugin registers four tools: `mnemosyne_dashboard_start`, `mnemosyne_dashboard_stop`, `mnemosyne_dashboard_status`, `mnemosyne_dashboard_config`.

### Update

```bash
hermes plugins update mnemosyne-dashboard
```

## Key facts

- **Data location**: `~/.hermes/mnemosyne/data/mnemosyne.db` (SQLite)
- **Working memory limit**: 10,000 items default (set via `MNEMOSYNE_WM_MAX_ITEMS`)
- **Episodic memory**: no practical limit — disk-bound
- **Consolidation**: `mnemosyne sleep` compresses working → episodic
- **Embeddings**: local via fastembed (bge-small-en-v1.5) — no external API needed
- **Multilingual**: set `MNEMOSYNE_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Updating**: `pip install --upgrade mnemosyne-hermes` then `hermes gateway restart`

## Pitfalls

- ✗ `hermes config set memory.provider mnemosyne` may show success but not persist if the key name is wrong — always verify with `grep -A10 '^memory:' ~/.hermes/config.yaml`
- ✗ `patch` tool cannot write to `~/.hermes/config.yaml` (security guard) — always use `hermes config set` instead
- ✗ If memory setup says "built-in only" after setting provider, the plugin link in step 2 failed — relink it
- ✗ The old `MEMORY.md`/`USER.md` files remain on disk but inactive — don't delete unless user requests it
- ✗ Dashboard changes require gateway restart to take effect in-session
