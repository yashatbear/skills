#!/usr/bin/env python3
"""Minimal Messages helper (macOS): send an iMessage and read recent messages. No dependencies.

  messages.py send --to HANDLE --message TEXT      -> {"status": "sent", ...} or {"status": "error", ...}
  messages.py recent [--hours 2] [--limit 150]     -> {"messages": [{from, handle, text, date}, ...]}

`send` needs Automation permission for the calling app to control Messages (System Settings > Privacy & Security >
Automation). `recent` reads ~/Library/Messages/chat.db and needs Full Disk Access for the calling app.
Neither works from launchd/cron (macOS refuses with error -1743): run from a terminal or a Claude Code session.
"""
import argparse, datetime, json, os, sqlite3, subprocess, sys

CHAT_DB = os.path.expanduser("~/Library/Messages/chat.db")
EPOCH = 978307200  # Core Data epoch (2001-01-01) -> Unix

SEND_SCRIPT = '''on run argv
  set recipientId to item 1 of argv
  set msgText to item 2 of argv
  tell application "Messages"
    set targetService to 1st account whose service type = iMessage
    set targetBuddy to participant recipientId of targetService
    send msgText to targetBuddy
  end tell
end run'''


def decode_attributed_body(blob):
    """Plain text from a typedstream attributedBody blob (newer macOS stores text there)."""
    if not blob: return None
    data = bytes(blob); i0 = data.find(b"NSString")
    if i0 < 0: return None
    start0 = i0 + len(b"NSString")
    for i in range(start0, min(start0 + 200, len(data))):
        if data[i] == 0x2B:
            lb = data[i + 1]
            if lb & 0x80:
                n = lb & 0x7F; length = int.from_bytes(data[i + 2:i + 2 + n], "little"); start = i + 2 + n
            else:
                length = lb; start = i + 2
            if length > 0 and start + length <= len(data):
                try: return data[start:start + length].decode("utf-8")
                except UnicodeDecodeError: pass
    return None


def send_text(handle, text, timeout=45):
    try:
        r = subprocess.run(["osascript", "-e", SEND_SCRIPT, handle, text], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "timed out"}
    if r.returncode == 0: return {"status": "sent", "to": handle, "service": "iMessage"}
    return {"status": "error", "error": r.stderr.strip()[:300]}


def recent(hours=2, limit=150):
    conn = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    since = (datetime.datetime.now().timestamp() - hours * 3600 - EPOCH) * 1_000_000_000
    rows = conn.execute(
        "SELECT m.is_from_me, h.id, m.text, m.attributedBody, m.date FROM message m LEFT JOIN handle h ON m.handle_id = h.ROWID "
        "WHERE m.date > ? ORDER BY m.date DESC LIMIT ?", (since, limit)).fetchall()
    out = []
    for me, handle, text, blob, date in reversed(rows):
        text = text or decode_attributed_body(blob) or ""
        when = datetime.datetime.fromtimestamp(date / 1_000_000_000 + EPOCH).strftime("%Y-%m-%d %H:%M")
        out.append({"from": "me" if me else handle, "handle": handle or "", "text": text, "date": when})
    return {"messages": out}


if __name__ == "__main__":
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send"); s.add_argument("--to", required=True); s.add_argument("--message", required=True)
    r = sub.add_parser("recent"); r.add_argument("--hours", type=float, default=2); r.add_argument("--limit", type=int, default=150)
    a = p.parse_args()
    print(json.dumps(send_text(a.to, a.message) if a.cmd == "send" else recent(a.hours, a.limit), ensure_ascii=False))
