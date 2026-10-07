#!/usr/bin/env python3
"""End-to-end model probe against the local opencode server.

Creates a scratch session in an isolated directory, sends a minimal prompt,
prints the assistant's provider/model/text (or error), then deletes the session.

Usage:
  python3 probe-model-e2e.py                          # configured default model
  python3 probe-model-e2e.py deepseek/deepseek-flash  # force a model

Run after any provider/config/session-model change to prove a real LLM turn
completes end-to-end.
"""
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("OPENCODE_URL", "http://127.0.0.1:4096")
PROBE_DIR = "/tmp/opencode-model-probe"
PROMPT = "Reply with exactly: PROBE-OK"


def req(method, path, body=None, headers=None, timeout=180):
    h = {"content-type": "application/json"}
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def report(msg):
    info = msg.get("info", {})
    txt = " ".join(p.get("text", "") for p in msg.get("parts", []) if p.get("type") == "text")
    err = info.get("error")
    print("provider/model:", info.get("providerID"), "/", info.get("modelID"))
    print("error:", json.dumps(err)[:300] if err else None)
    print("text:", txt[:300])
    return err


def main():
    model_arg = sys.argv[1] if len(sys.argv) > 1 else None
    os.makedirs(PROBE_DIR, exist_ok=True)
    body = {"title": "e2e model probe"}
    if model_arg:
        provider, _, mid = model_arg.partition("/")
        body["model"] = {"providerID": provider, "id": mid}

    st, raw = req("POST", "/session", body, headers={"x-opencode-directory": PROBE_DIR})
    if st != 200:
        print("create failed:", st, raw[:300])
        return 1
    sid = json.loads(raw)["id"]
    print("probe session:", sid)
    try:
        st, raw = req("POST", f"/session/{sid}/message", {"parts": [{"type": "text", "text": PROMPT}]})
        msg = None
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and d.get("info"):
                msg = d  # synchronous response: the completed assistant message
        except Exception:
            pass
        deadline = time.time() + 180
        while msg is None and time.time() < deadline:
            time.sleep(5)
            st, raw = req("GET", f"/session/{sid}/message")
            try:
                msgs = json.loads(raw)
            except Exception:
                msgs = []
            for m in reversed(msgs):
                if m.get("info", {}).get("role") == "assistant":
                    msg = m
                    break
        if msg is None:
            print("!! no assistant reply within deadline")
            return 1
        err = report(msg)
        return 0 if not err else 1
    finally:
        st, raw = req("DELETE", f"/session/{sid}")
        print("delete:", st, raw[:100])
        shutil.rmtree(PROBE_DIR, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
