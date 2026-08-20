# Session Context Bloat — Reset Procedure

## When to use
When a Kimaki/OpenCode session accumulates too many input tokens (typically 500K+) and the model starts producing empty responses.

## Symptoms
- `[ASSISTANT COMPLETED] no visible output, skipping footer` in Kimaki logs
- Session token count > 500K input tokens
- Other sessions on same bot work normally
- Session was working fine earlier, then stopped producing visible output

## Diagnosis

### Check session token count
```bash
# Find the OpenCode serve port
ps aux | grep 'opencode serve' | grep -v grep

# Query session token count
curl -s "http://localhost:<port>/api/session/<sessionID>" | python3 -c "
import json,sys; d=json.load(sys.stdin)['data']
print(f'Input tokens: {d[\"tokens\"][\"input\"]:,}')
print(f'Output tokens: {d[\"tokens\"][\"output\"]:,}')
print(f'Cache read: {d[\"tokens\"][\"cache\"][\"read\"]:,}')
print(f'Cost: \${d[\"cost\"]:.4f}')
"
```

### Find the session ID from Kimaki logs
```bash
pm2 logs kimaki --lines 500 | grep '<thread-name>' | grep 'sessionId='
```

## Reset procedure

### Step 1: Delete session from OpenCode
```bash
opencode session delete <sessionID>
```

### Step 2: Delete thread mapping from Kimaki DB
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/erik/.kimaki/discord-sessions.db')
cur = conn.cursor()
# Delete thread-session mapping
cur.execute(\"DELETE FROM thread_sessions WHERE thread_id = '<threadID>'\")
print(f'Deleted {cur.rowcount} thread_sessions row(s)')
# Delete part messages
cur.execute(\"DELETE FROM part_messages WHERE thread_id = '<threadID>'\")
print(f'Deleted {cur.rowcount} part_messages row(s)')
conn.commit()
conn.close()
"
```

### Step 3: Verify
- Next message in the Discord thread should create a fresh session
- Check Kimaki logs for new `SESSION [INGRESS]` entry with a new session ID

## What is preserved
- Git worktree and branch (untouched)
- Uncommitted changes in worktree (untouched)
- Project files (untouched)

## What is lost
- Session conversation history
- Session token/cost statistics

## Prevention tips
- Avoid uploading large files (CSV, SQL dumps, logs) directly into Kimaki threads
- Place files in the worktree directory and ask the agent to read them
- For long-running sessions (hours with many tool calls), consider starting fresh periodically
- If a session hits context limits, the `/compact` command (when available in OpenCode) may help
