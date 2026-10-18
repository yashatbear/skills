#!/usr/bin/env python3
"""Telephony dispatcher: spread outbound AI phone calls across several call-capable assistants.

The assistants (Tab, Pally, Fo, ... see ../assistants.json) are texted over iMessage with a call task.
This script owns the queue: who is due, who is open, which assistant gets which call, and when to retry.

  telephony.py status                    targets + assistant load
  telephony.py run [--dry]               dispatch everything that is due right now (one tick)
  telephony.py loop [MINUTES]            run a tick every MINUTES (default 20) until killed
  telephony.py set ID STATUS             pending | no_conversation | declined | done | hold
  telephony.py add 'JSON'                add or replace a target
  telephony.py assistant NAME STATUS     ok | depleted | disabled   (take an assistant in/out of rotation)
  telephony.py task ID                   print the task text that would be sent for a target

State (campaign facts, targets, counters) lives in $TELEPHONY_STATE (default ~/.claude/telephony/state.json),
NOT in the repo: it holds personal data. Assistant handles live in ~/.claude/telephony/assistants.json (copy
../assistants.example.json). See ../references/example-state.json for the shape.

Needs scripts/messages.py (sends via Messages). It must run from a process that macOS lets drive Messages
(a Claude Code session or Terminal). launchd and cron cannot (error -1743): do not schedule this with them.
"""
import json, os, subprocess, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.expanduser(os.environ.get("TELEPHONY_ASSISTANTS", "~/.claude/telephony/assistants.json"))
STATE = os.path.expanduser(os.environ.get("TELEPHONY_STATE", "~/.claude/telephony/state.json"))
IMSG = os.path.join(HERE, "messages.py")
TZ = ZoneInfo(os.environ["TELEPHONY_TZ"]) if os.environ.get("TELEPHONY_TZ") else None  # None = this machine's local time
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load():
    with open(STATE) as f: return json.load(f)

def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f: json.dump(s, f, indent=1, ensure_ascii=False)

def registry():
    with open(REGISTRY) as f: return json.load(f)["assistants"]


# ---------- opening hours ----------
def windows(hours, now):
    d = DAYS[now.weekday()]
    for key in (d, "mon-fri" if now.weekday() < 5 else None, "mon-thu" if now.weekday() < 4 else None):
        if key and key in hours: return hours[key]
    return []

def is_open(t, now, close_margin=30):
    m = now.hour * 60 + now.minute
    f = lambda s: int(s[:2]) * 60 + int(s[3:])
    return any(f(w.split("-")[0]) + 5 <= m <= f(w.split("-")[1]) - close_margin for w in windows(t["hours"], now))


# ---------- task text ----------
def task_text(s, t):
    c = s["campaign"]; lang = t["lang"]
    nums = t["numbers"]; alt = f" Alternate number: {', '.join(nums[1:])}." if len(nums) > 1 else ""
    goal = t.get("goal") or c["goal"]
    return (f"Call task: {t['name']}, {nums[0]}.{alt} Language: {c['languages'][lang]}. Goal: {goal} "
            f"Opener, ONE sentence, then stop and wait for a live person: '{c['openers'][lang]}'. {c['ask']} "
            f"Give only what is written in this task. {c['contact_rule']} "
            f"Facts you may share if asked, nothing beyond them: {c['facts']} "
            f"Rules: {c['rules']} Tell me how it goes.")


# ---------- balancing ----------
def pick_assistant(s, t, reg, load_today, busy, now):
    """Least-loaded assistant that can take this call. None if nobody can."""
    status = s.get("assistant_status", {})
    best = None
    for name, a in reg.items():
        if status.get(name, "ok") != "ok": continue                       # depleted / disabled
        if t["lang"] not in a["languages"]: continue                      # language fit
        if t.get("country", "CH") not in a["countries"]: continue          # can it dial there at all
        if load_today.get(name, 0) >= a["daily_cap"]: continue             # our own daily cap
        if name in busy: continue                                           # one live call per assistant
        if t.get("avoid") == name: continue                                 # last assistant failed on this number: rotate
        score = (load_today.get(name, 0), a.get("priority", 5))
        if best is None or score < best[0]: best = (score, name)
    return best[1] if best else None


def tick(dry=False):
    s = load(); reg = registry(); now = datetime.now(TZ); today = now.strftime("%Y-%m-%d")
    gap = s["campaign"].get("gap_hours", 2)
    load_today, busy = {}, set()
    for t in s["targets"]:
        ts = t.get("last_ts")
        if ts and ts[:10] == today and t.get("assistant"):
            load_today[t["assistant"]] = load_today.get(t["assistant"], 0) + 1
            if (now - datetime.fromisoformat(ts)).total_seconds() < s["campaign"].get("busy_minutes", 8) * 60:
                busy.add(t["assistant"])
    due = []
    for t in s["targets"]:
        if t["status"] not in ("pending", "no_conversation"): continue
        ts = t.get("last_ts")
        if ts and (now - datetime.fromisoformat(ts)).total_seconds() < gap * 3600: continue
        if not is_open(t, now): continue
        due.append(t)
    due.sort(key=lambda t: (t.get("priority", 5), t.get("last_ts") or ""))     # priority first, longest-waiting next
    sent = 0
    for t in due:
        a = pick_assistant(s, t, reg, load_today, busy, now)
        if not a: print(f"  no assistant free for {t['name']}"); continue
        print(("DRY  " if dry else "SEND ") + f"{t['name']} -> {a}")
        if not dry:
            ok = False
            for attempt in range(3):                                           # Messages AppleScript times out now and then
                r = subprocess.run(["python3", IMSG, "send", "--to", reg[a]["handle"], "--message", task_text(s, t)],
                                   capture_output=True, text=True)
                if '"sent"' in r.stdout: ok = True; break
                print("   attempt", attempt + 1, "failed:", r.stdout[:150], r.stderr[-150:], flush=True)
                if "Not authorized" in r.stdout: break
            if not ok: continue
            t["last_ts"] = now.isoformat(timespec="minutes"); t["assistant"] = a
            t["dispatches"] = t.get("dispatches", 0) + 1; t.pop("avoid", None)
        load_today[a] = load_today.get(a, 0) + 1; busy.add(a); sent += 1
    if not dry: save(s)
    print(f"{now:%a %H:%M}: dispatched {sent}, due {len(due)}", flush=True)


def status():
    s = load(); reg = registry(); st = s.get("assistant_status", {})
    print("assistants:", ", ".join(f"{n}={st.get(n, 'ok')}" for n in reg))
    for t in s["targets"]:
        print(f"{t['id']:<16} {t['status']:<16} p{t.get('priority', 5)} {(t.get('last_ts') or '-')[:16]:<16} "
              f"{t.get('assistant', '-'):<6} n={t.get('dispatches', 0)} {t['name']} {t['numbers'][0]}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["status"]
    c = a[0]
    if c == "run": tick("--dry" in a)
    elif c == "loop":
        mins = int(a[1]) if len(a) > 1 else 20
        while True:
            try: tick()
            except Exception as e: print("tick error:", e, flush=True)
            time.sleep(mins * 60)
    elif c == "status": status()
    elif c == "set":
        s = load(); [t.update(status=a[2]) for t in s["targets"] if t["id"] == a[1]]; save(s); status()
    elif c == "add":
        s = load(); n = json.loads(a[1]); s["targets"] = [t for t in s["targets"] if t["id"] != n["id"]] + [n]; save(s); status()
    elif c == "assistant":
        s = load(); s.setdefault("assistant_status", {})[a[1]] = a[2]; save(s); status()
    elif c == "task":
        s = load(); print(task_text(s, next(t for t in s["targets"] if t["id"] == a[1])))
    else: print(__doc__)
