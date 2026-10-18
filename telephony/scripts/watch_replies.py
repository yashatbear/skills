#!/usr/bin/env python3
"""Print every new message from the call assistants (one line per message). Run it through the Monitor tool.

  watch_replies.py [YYYY-MM-DD HH:MM]    only messages at/after this local time (default: now)
Reads Messages via messages.py (needs Full Disk Access). Reactions ("Liked", "Reacted") are skipped.
"""
import json, os, subprocess, sys, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IMSG = os.path.join(HERE, "messages.py")
with open(os.path.expanduser(os.environ.get("TELEPHONY_ASSISTANTS", "~/.claude/telephony/assistants.json"))) as f:
    H = {a["handle"]: n for n, a in json.load(f)["assistants"].items()}
since = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d %H:%M")
seen = set()
while True:
    out = subprocess.run(["python3", IMSG, "recent", "--hours", "3", "--limit", "150"], capture_output=True, text=True).stdout
    try: msgs = json.loads(out)["messages"]
    except Exception: msgs = []
    for m in msgs:
        if m["handle"] in H and m["from"] != "me" and m["date"] >= since and not m["text"].startswith(("Liked", "Reacted", "Loved", "Emphasized")):
            k = (m["handle"], m["date"], m["text"])
            if k not in seen:
                seen.add(k); print(H[m["handle"]], m["date"], "|", m["text"][:900].replace("\n", " / "), flush=True)
    time.sleep(20)
