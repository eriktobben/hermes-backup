# OpenCode v2 Migration Notes

## Status (Aug 2026)
- OpenCode v2 is in beta
- Kimaki v0.25.0 does NOT support v2
- V1 and V2 can coexist (`opencode` vs `opencode2`)

## Breaking Changes

### 1. Plugins (new API)
```javascript
// V1
"plugin": ["opencode-example-plugin", ["./plugin/local.ts", { "enabled": true }]]

// V2  
"plugins": ["opencode-example-plugin", {"package": "./plugin/local.ts", "options": {...}}]
```
V1 plugins will not work in V2.

### 2. Server API and clients
- Must use `@opencode-ai/client` instead of `@opencode-ai/sdk`
- New contracts, still being finalized during beta

### 3. TUI configuration
- Moves from layered `tui.json(c)` to one global `cli.json` (auto-migrated)

## What still works
- Existing config files are read automatically
- Agent definitions, commands, skills in `.opencode/` should work without changes
- Project config at `<project>/opencode.json(c)` or `<project>/.opencode/opencode.json(c)`

## Install
```bash
npm install -g @opencode-ai/cli@beta
opencode2  # starts v2
```

## Migration path
Ask OpenCode to migrate config:
```
Migrate my OpenCode configuration, including file-based definitions, from the V1 format to the native V2 format.
```

## Kimaki impact
Kimaki uses:
- `@opencode-ai/plugin` v1.16.x (V1 API)
- `@opencode-ai/sdk` v1.16.x (V1 API)

Both need updating before Kimaki can support OpenCode v2.
