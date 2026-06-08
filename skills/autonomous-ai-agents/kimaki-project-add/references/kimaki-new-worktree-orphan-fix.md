# Kimaki `new-worktree.js` — orphaned duplicate line fix

## Symptom
```
file:///home/erik/.npm-global/lib/node_modules/kimaki/dist/commands/new-worktree.js:111
    return `opencode/kimaki-${raw}--${suffix}`;
    ^^^^^^
SyntaxError: Illegal return statement
```

Kimaki enters a crash loop (5 crashes → exits), unable to start. Any command (`kimaki --version`, `kimaki project add`) fails.

## Root cause
The `formatAutoWorktreeName` function in `new-worktree.js` has orphaned duplicate lines after its closing `}` — leftover from a partial upgrade or re-patch. The function body was updated to the new naming scheme, but 3 extraneous lines were not cleaned up:

```javascript
// End of formatAutoWorktreeName (correct):
    const suffix = Date.now().toString(36).slice(-4);
    return `opencode/kimaki-${raw}--${suffix}`;
}
// ORPHANED duplicates (should not exist):
    const suffix = Date.now().toString(36).slice(-4);
    return `opencode/kimaki-${raw}--${suffix}`;
}
```

## Detection
1. Look at the file around the `formatAutoWorktreeName` function:
   ```bash
   grep -n "formatAutoWorktreeName" /home/erik/.npm-global/lib/node_modules/kimaki/dist/commands/new-worktree.js
   ```
2. Check for duplicate `return \`opencode/kimaki-${raw}--${suffix}\`` lines:
   ```bash
   grep -c 'return `opencode/kimaki-${raw}' /home/erik/.npm-global/lib/node_modules/kimaki/dist/commands/new-worktree.js
   ```
   Should be exactly **1** (the one inside the function). If it's 2, there are orphans.

## Manual fix
Open `/home/erik/.npm-global/lib/node_modules/kimaki/dist/commands/new-worktree.js` and remove lines 110–112 (the orphaned duplicate). The function should end cleanly:

```javascript
export function formatAutoWorktreeName(name) {
    const translit = name
        .replace(/æ/gi, 'ae').replace(/ø/gi, 'o').replace(/å/gi, 'a');
    const raw = slugifyWorktreeName(translit).replace(/^-+|-+$/g, '');
    if (!raw) {
        return '';
    }
    const suffix = Date.now().toString(36).slice(-4);
    return `opencode/kimaki-${raw}--${suffix}`;
}
// Next function's doc comment starts here
```

## Automated fix
The `~/.local/bin/kimaki-patch-worktree` script has a **Patch 3** step that detects and removes these orphaned lines automatically. Run it after any Kimaki upgrade:

```bash
bash ~/.local/bin/kimaki-patch-worktree
```

If a future Kimaki upgrade introduces a different orphan pattern, update Patch 3 in the script to match the new shape.
