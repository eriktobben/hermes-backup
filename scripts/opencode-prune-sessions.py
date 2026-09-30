#!/usr/bin/env python3
"""Slett gamle, umappede opencode-sessioner (død vekt i DB).

Bare sessioner som: (a) ikke er knyttet til noen Discord-thread i
thread_sessions, og (b) er sist oppdatert før 2026-08-15.
"""
import json, os, sqlite3, subprocess, urllib.request, datetime

out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
port = None
for line in out.splitlines():
    if "opencode serve" in line and "--port" in line:
        port = line.split("--port")[1].split()[0]
        break
if not port:
    print("ingen opencode serve kjorer - hopper over")
    raise SystemExit(0)

db = os.path.expanduser("~/.kimaki/discord-sessions.db")
mapped = {r[0] for r in sqlite3.connect(db).execute(
    "SELECT session_id FROM thread_sessions")}
data = json.loads(urllib.request.urlopen(
    f"http://127.0.0.1:{port}/session").read())
cutoff = datetime.datetime(2026, 8, 15).timestamp() * 1000

deleted = kept = 0
for s in data:
    sid = s["id"]
    upd = s.get("time", {}).get("updated", 0)
    if sid in mapped or upd >= cutoff:
        kept += 1
        continue
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/session/{sid}", method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=15)
        deleted += 1
    except Exception as e:
        print(f"feil {sid}: {e}")
print(f"slettet {deleted} gamle sessioner, beholdt {kept} (mapped/nyere)")
