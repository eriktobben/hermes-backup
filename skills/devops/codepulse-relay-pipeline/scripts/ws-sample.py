#!/usr/bin/env python3
"""Sample the relay's TCP byte counters toward the app to observe command traffic
without root — see SKILL.md "Observing the command channel live".

Typical per-15s deltas on a healthy idle relay:
  uplink connection   ~286 B (heartbeat response)
  websocket           ~0-47 B (pusher pong every 30 s)
Larger jumps = command batches broadcast by the app (session.prompt, session.sync,
worktree ops). A websocket local port vanishing + a new port appearing = Reverb
restart (deploy blip). No bursts across several minute boundaries = the app
dispatched nothing in that window.

Usage: ws-sample.py [seconds]   (default 280)
"""
import re
import subprocess
import sys
import time


def relay_pid():
    out = subprocess.run(
        ['systemctl', '--user', 'show', '-p', 'MainPID', 'mission-control-relay'],
        capture_output=True, text=True).stdout
    m = re.search(r'MainPID=(\d+)', out)
    if not m or m.group(1) == '0':
        raise SystemExit('could not resolve the relay MainPID (is mission-control-relay running?)')
    return m.group(1)


def sample(pid):
    out = subprocess.run(['ss', '-tinp'], capture_output=True, text=True).stdout
    res, cur = {}, None
    for line in out.splitlines():
        if f'pid={pid}' in line and 'ESTAB' in line:
            addrs = re.findall(r'(\d+\.\d+\.\d+\.\d+):(\d+)', line)
            # Skip loopback (opencode SSE etc.); keep the app connections.
            cur = addrs[0][1] if len(addrs) >= 2 and addrs[1][0] != '127.0.0.1' else None
        elif cur and 'bytes_received' in line:
            m = re.search(r'bytes_received:(\d+)', line)
            if m:
                res[cur] = int(m.group(1))
            cur = None
    return res


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 280
    pid = relay_pid()
    print(f'# relay pid {pid}', flush=True)
    prev = sample(pid)
    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(15)
        now = sample(pid)
        ts = time.strftime('%H:%M:%S', time.gmtime())
        deltas = {k: now.get(k, 0) - v for k, v in prev.items() if k in now}
        gone = [k for k in prev if k not in now]
        new = [k for k in now if k not in prev]
        extra = (' vanished:' + str(gone) if gone else '') + (' new:' + str(new) if new else '')
        print(f'{ts} deltas: {deltas}{extra}', flush=True)
        prev = now


if __name__ == '__main__':
    main()
