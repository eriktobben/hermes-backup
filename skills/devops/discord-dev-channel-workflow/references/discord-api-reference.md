# Discord API Reference

## Thread Creation

### Endpoint
```
POST /channels/{channel_id}/messages/{message_id}/threads
```

### Body
```json
{
  "name": "Thread name (max 100 chars)",
  "auto_archive_duration": 1440  // minutes: 60, 1440, 4320, or 10080
}
```

### Permission Requirements
- `CREATE_PUBLIC_THREADS` permission for public threads
- `CREATE_PRIVATE_THREADS` for private threads

## Relevant Channel IDs

| Channel | ID | Type |
|---------|-----|------|
| serena-dev | 1511404097302171818 | Text Channel |
| masterfeed-dev | 1511501933180092478 | Text Channel |

## Thread Naming Conventions

- Features: `feat: <description>` or `<project>: <description>`
- Bugfixes: `fix: <description>`
- Refactoring: `refactor: <description>`
- Docs: `docs: <description>`

## Auto-Thread Behavior in Hermes

The Discord adapter has built-in auto-threading but:
- Skips replies (MessageType.reply)
- Skips free-response channels (to avoid double-threading)
- Skips voice-linked channels

For `-dev` channels, we manually create threads to avoid the free_channel skip.