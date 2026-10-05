#!/usr/bin/env python3
"""Replay a real, lost OpenCode event to the CodePulse app, signed as the relay.

Relay event batches are never retried app-side, so an event OpenCode actually
emitted (verify it in the opencode `event` table first) but the app dropped —
e.g. an ingest 500 killed the whole batch — can be re-signed with the relay's
own HMAC and replayed once. This is the supported recovery move for a stranded
session: "react to the lost events" rather than waiting for a retry that never
comes. Replays are idempotent: adopt-or-update, and a duplicate
`session.created` cannot double-dispatch a drain.

It doubles as the synchronous-path probe: run it with `--type session.updated`
and a real `--title`, and adoption dispatches `worktree.rename` on a broadcast
(never the queue) so the relay renames the git branch on disk
(`git -C <repo> branch --list 'session-*'`). Branch renames while queued
delivery stays silent => adoption + relay commands are healthy and the queue
worker is the broken link; nothing changes on a title replay => the app cannot
find/adopt the row (or is not running the code you think it is).

Signing: HMAC-SHA256 hex over "<unix timestamp>.<raw body>" with the relay
secret from ~/.config/mission-control/relay.json; POST to
<app_url>/api/relay/events with X-Relay-Id / X-Relay-Timestamp /
X-Relay-Signature. Run on the relay host.

Probe-title guardrail: pick a title whose slug keeps the `session-<6 alnum>`
branch shape (e.g. "session probe1" -> session-probe1); the app only
auto-renames branches matching ^session-[a-z0-9]{6}$, so a differently shaped
probe name would disable later real-title renames.

Usage:
  replay-relay-event.py --session ses_... --directory /abs/worktree
  replay-relay-event.py --session ses_... --directory /abs/worktree \\
      --type session.updated --title 'session probe1'
"""
import argparse
import hashlib
import hmac
import json
import pathlib
import time
import urllib.error
import urllib.request

CONFIG = pathlib.Path.home() / ".config/mission-control/relay.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--session", required=True, help="OpenCode session id (ses_...)")
    parser.add_argument("--directory", required=True, help="Session directory (the worktree path)")
    parser.add_argument("--title", default=None, help="Title payload; use for the rename probe")
    parser.add_argument(
        "--type",
        default="session.created",
        choices=["session.created", "session.updated"],
    )
    parser.add_argument("--seq", type=int, default=424242)
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    payload = {"session_id": args.session, "directory": args.directory}
    if args.title:
        payload["title"] = args.title

    batch = {
        "seq": args.seq,
        "events": [{
            "type": "relay.batch",
            "payload": {"events": [{"type": args.type, "payload": payload}]},
        }],
    }
    body = json.dumps(batch, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        config["relay_secret"].encode(), timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()

    request = urllib.request.Request(
        config["app_url"].rstrip("/") + "/api/relay/events",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Relay-Id": config["relay_id"],
            "X-Relay-Timestamp": timestamp,
            "X-Relay-Signature": signature,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"HTTP {response.status} (204 = accepted; watch the opencode DB for the effect)")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read()[:300].decode(errors='replace')}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
