#!/usr/bin/env python3
"""Switch the pinned model of opencode sessions (v1-safe, direct DB).

Why: each session stores its model in opencode.db `session.model`. The clean v2
endpoint (POST /api/session/{id}/model) FAILS on non-migrated v1 sessions with
`SQLiteError: FOREIGN KEY constraint failed` (session_message -> session_v2),
so the working fallback is a direct UPDATE with the same JSON shape the API
would write.

Usage:
  python3 switch-session-model.py <provider>/<model> <session_id> [<session_id> ...]
  python3 switch-session-model.py deepseek/deepseek-flash ses_aaa ses_bbb

After switching, restart the relay unit so opencode loads fresh rows:
  systemctl --user restart mission-control-relay
"""
import json
import os
import sqlite3
import sys

DB = os.path.expanduser("~/.local/share/opencode/opencode.db")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    provider, _, model = sys.argv[1].partition("/")
    if not provider or not model:
        print("model must be <provider>/<model>")
        return 1
    sids = sys.argv[2:]
    new_model = json.dumps({"id": model, "providerID": provider})

    con = sqlite3.connect(DB, timeout=30)
    try:
        for sid in sids:
            cur = con.execute("UPDATE session SET model=? WHERE id=?", (new_model, sid))
            print(f"{sid}: rows={cur.rowcount}")
        con.commit()
        print("--- read-back ---")
        for sid in sids:
            r = con.execute("SELECT model FROM session WHERE id=?", (sid,)).fetchone()
            print(sid, "->", r[0] if r else "NOT FOUND")
    finally:
        con.close()
    print("Now restart to reload: systemctl --user restart mission-control-relay")
    return 0


if __name__ == "__main__":
    sys.exit(main())
