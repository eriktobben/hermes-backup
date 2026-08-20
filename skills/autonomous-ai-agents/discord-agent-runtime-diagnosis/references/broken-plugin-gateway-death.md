# Broken Plugin → Silent Gateway Death

## Session: 2026-08-20

### Symptoms
- Kimaki PM2 process: `online`, 25+ min uptime
- OpenCode serve: running on port (e.g. 36349), API responds
- Discord bot: "Connected to Discord!", "Found 30 channel(s)", slash commands registered
- **Zero** `DISCORD Message in thread` entries in logs after startup
- Error log:32x `failed to load plugin path=file:///home/erik/.config/opencode/plugins/claude-mem.js error="Plugin export is not a function"`

### Root cause
`claude-mem.js` in `~/.config/opencode/plugins/` was a bundled Zod library (~335KB minified) that exported an object with `ClaudeMemPlugin` and `default` properties, not a function. OpenCode's plugin loader expected a function export.

The file was auto-discovered by OpenCode from the `plugins/` directory — it was NOT referenced in `~/.kimaki/opencode-config.json` (Kimaki's config). It WAS referenced in `~/.config/opencode/opencode.json` (global config), but removing it from config alone did NOT stop the errors because OpenCode auto-discovers all `.js` files in the `plugins/` directory.

### Discovery path
1. `pm2 list` → Kimaki online, 25 min uptime
2. `pm2 logs kimaki` → startup logs, then silence
3. Error log → `claude-mem.js` plugin errors spam
4. Checked `~/.config/opencode/opencode.json` → found `claude-mem.js` in plugin array
5. Removed from config → errors persisted (auto-discovery)
6. Moved file to `.disabled` → errors stopped
7. After second restart → messages started arriving

### Key insight
OpenCode has **two** plugin loading mechanisms:
1. Explicit `plugin` array in `opencode.json`
2. Auto-discovery of `.js` files in `~/.config/opencode/plugins/`

Both must be cleared to stop a broken plugin from loading.

### Fix applied
```bash
# Remove from config
# (edited ~/.config/opencode/opencode.json to remove "./plugins/claude-mem.js")

# Move file out of plugins directory
mv ~/.config/opencode/plugins/claude-mem.js ~/.config/opencode/plugins/claude-mem.js.disabled

# Restart Kimaki (twice for clean gateway)
pm2 restart kimaki
```

### Verification
After fix, logs showed:
- No `claude-mem.js` errors
- `DISCORD Message in thread` entries appearing
- `SESSION [INGRESS] promptAsync accepted` for incoming messages
