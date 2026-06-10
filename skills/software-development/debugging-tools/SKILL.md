---
name: debugging-tools
description: "Language-level debugging tools: Python (pdb, debugpy, remote-pdb), Node.js (node inspect, CDP), and Hermes TUI slash command debugging. For the systematic debugging PROCESS (root cause investigation), load `systematic-debugging` instead."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, pdb, nodejs, inspect, breakpoints, CDP, tui]
    category: software-development
---

# Debugging Tools (Umbrella)

Three language-level debugging tool sets. For the systematic debugging **process** (root cause investigation before fixing), load `systematic-debugging` instead.

---

## Section A: Python Debugging (pdb + debugpy)

### Quickest: `breakpoint()`
```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()  # drops into pdb REPL
    return result + y
```
Don't forget to remove before committing: `rg -n 'breakpoint\\(\\)' --type py`

### pdb Quick Reference
| Command | Action |
|---------|--------|
| `n` / `s` | Step over / step into |
| `c` | Continue |
| `l` / `ll` | List source around line / full function |
| `w` / `bt` | Where / backtrace |
| `u` / `d` | Move up/down stack |
| `p expr` / `pp expr` | Print / pretty-print |
| `!stmt` | Execute arbitrary Python |
| `interact` | Full REPL (then Ctrl+D to exit) |
| `q` | Quit |

### Debug pytest
```bash
scripts/run_tests.sh tests/test_file.py::test_name --pdb -p no:xdist
# xdist disables pdb - always add -p no:xdist or -n 0
```

### Remote Debug (for long-running processes)
```bash
pip install remote-pdb
# In code:
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)  # blocks until connection
# Connect: nc 127.0.0.1 4444
```

### debugpy (DAP protocol, IDE integration)
```bash
pip install debugpy
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client script.py
# Attach from VS Code via launch.json
```

Full reference: See archived `python-debugpy`.

---

## Section B: Node.js Debugging (node inspect + CDP)

### Quickest: `node inspect`
```bash
node inspect script.js
# Paused on first line - set breakpoints then continue
```

### node inspect REPL
| Command | Action |
|---------|--------|
| `c` / `cont` | Continue |
| `n` / `next` | Step over |
| `s` / `step` | Step into |
| `sb('file.js', 42)` | Set breakpoint |
| `bt` | Backtrace |
| `repl` | Full REPL in current scope |
| `exec expr` | Evaluate expression |

### Attach to running process
```bash
kill -SIGUSR1 <pid>              # enable inspector
node inspect -p <pid>            # attach
# or
node --inspect-brk script.js     # start paused
```

### TypeScript via tsx
```bash
node --inspect-brk --import tsx script.ts
```

### Programmatic CDP (chrome-remote-interface)
```bash
npm i -g chrome-remote-interface
# Then script breakpoints, scope inspection, heap snapshots
```

Full reference: See archived `node-inspect-debugger`.

---

## Section C: Hermes TUI Slash Commands Debugging

Three-layer architecture:
```
Python backend (hermes_cli/commands.py)  ← canonical COMMAND_REGISTRY
       ↓
TUI gateway (tui_gateway/server.py)      ← slash.exec / command.dispatch
       ↓
TUI frontend (ui-tui/src/app/slash/)     ← local handlers + fallthrough
```

### Common Issues
1. **Command missing from autocomplete** → missing from `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. **Command shows but doesn't work** → check handler in `tui_gateway/server.py` and `ui-tui/src/app/createSlashHandler.ts`
3. **CLI vs TUI behavior differs** → command may have separate implementations in `cli.py` vs TUI local handler
4. **Config persists but UI doesn't update** → also patch nanostore state (`patchUiState(...)`)

### Fixing Missing Autocomplete
Add a `CommandDef` entry:
```python
CommandDef("commandname", "Description", "Session",
    cli_only=True, aliases=("alias",),
    args_hint="[arg1|arg2]", subcommands=("arg1", "arg2")),
```

### Debug Tactics
- **Python side**: use `python-debugpy` (Section A) inside `_SlashWorker.exec`
- **Ink side**: use `node-inspect-debugger` (Section B) inside `app.tsx`
- **Rebuild TUI**: `npm --prefix ui-tui run build` before testing

Full reference: See archived `debugging-hermes-tui-commands`.

---

## Pitfalls

1. **pdb under pytest-xdist** — xdist silently suppresses pdb. Always add `-p no:xdist` or `-n 0`.
2. **`breakpoint()` in CI** — hangs the process. Never commit it. Add pre-commit grep.
3. **`node inspect` line numbers in TS source** — breakpoints hit emitted JS, not `.ts`. Use `sb('dist/app.js', N)` or enable sourcemaps.
4. **`--inspect` vs `--inspect-brk`** — `--inspect` doesn't pause; your script races past breakpoints. Use `--inspect-brk` to pause on first line.
5. **ffmpeg pipe deadlock** — never `stderr=subprocess.PIPE` with long-running ffmpeg; buffer fills at 64KB and deadlocks.
6. **`debugpy.listen` requires `wait_for_client()`** — without it, execution continues and breakpoints may fire before attach.
