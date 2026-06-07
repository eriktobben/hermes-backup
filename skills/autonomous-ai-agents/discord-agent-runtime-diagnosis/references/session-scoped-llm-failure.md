# Session-scoped LLM failure while other threads succeed

Use this reference when users report: "Thread A stopped replying, thread B still works."

## Log signatures to confirm

1. Failing thread/session:
- `service=llm ... AI_APICallError ... session.id=<failing_session>`
- May also show question-flow mismatch:
  - `service=question ... reply for unknown request`

2. Healthy comparator thread in same window:
- `SESSION  DURATION: Session completed ...`
- `[ASSISTANT COMPLETED]`

3. Optional noisy but non-root-cause events:
- Gateway reconnect/resume lines
- Duplicate skill warnings
- Slash-command registration timeout warnings

## Why this matters
These incidents are often misread as full bot outage. If another thread completes normally, prioritize per-session recovery over global restarts.

## Recovery playbook
1. Capture `threadId` + `sessionId` for failing and healthy comparators.
2. Preserve logs around first `AI_APICallError` timestamp.
3. Recover only failing session first:
   - archive stuck session / start fresh session on next user turn
   - if still broken, archive thread and create new thread
4. Escalate to process restart or DB reset only if failures broaden.

## Minimal evidence package for escalation
- failing `threadId/sessionId`
- one healthy comparator `threadId/sessionId`
- first `AI_APICallError` line
- any `reply for unknown request` lines
- whether fresh thread reproduces
