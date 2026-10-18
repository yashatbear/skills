---
name: telephony
description: Run outbound AI phone calls at scale by delegating to several call-capable texting assistants (e.g. Tab, Pally, Fo) over iMessage, balancing load across them, running calls in parallel, and retrying on a schedule inside each business's opening hours. Use when asked to call vendors, dealers or offices for you, to follow up unanswered calls, or to add call capacity. Includes the rules for phone menus, voicemail, voice-bot receptionists and caller-ID problems.
---

# Telephony: call-capable assistants, balanced and parallel

Own phone carriers are a trap: new accounts that place a burst of calls abroad get blocked quickly. Instead, hand each
call to a hosted AI assistant that owns its own phone line and takes tasks by text (Tab, Pally, Fo, ... see
`assistants.example.json`). The assistant places the call and texts back what happened. This skill is the queue, the
balancer and the rulebook around that.

## Setup
1. `mkdir -p ~/.claude/telephony`; copy `assistants.example.json` to `~/.claude/telephony/assistants.json` and fill in
   each assistant's iMessage `handle` (the number or address you text it on), languages, countries and daily cap.
   Remove assistants you don't use. Handles are yours, so they are not shipped in this repo.
2. Copy `references/example-state.json` to `~/.claude/telephony/state.json`; write the campaign (goal, openers in each
   language, the ask, the facts you allow, the call rules) and the targets (name, numbers, language, opening hours).
3. macOS permissions for whatever app runs this (Terminal or Claude Code): Automation to control Messages, and
   Full Disk Access to read `chat.db` (needed by `watch_replies.py`).
4. `python3 scripts/telephony.py run --dry` shows what would go out; `loop` runs it every 20 minutes.

## How balancing and parallelism work (`scripts/telephony.py`)
- One tick: find targets that are due (status `pending` or `no_conversation`, at least `gap_hours` (default 2) since
  the last attempt, inside opening hours with 30 minutes before close), sort by `priority` then longest-waiting, and
  give each to the least-loaded assistant that can take it.
- An assistant is eligible if its status is `ok`, it speaks the target's language, can dial the country, is under its
  own `daily_cap`, and has no live call (one live call per assistant, about 8 minutes busy window).
- Parallel: one target per assistant at the same time, so N assistants means up to N calls at once. Never two
  assistants on the same number in one tick; never the same number inside the gap.
- Rotation: set `avoid` on a target to keep the next try off an assistant that failed on it.
- Depletion: `telephony.py assistant NAME depleted` removes an assistant whose allowance is gone or that looped on a
  call; `ok` puts it back.
- Results are recorded by hand: `telephony.py set ID declined|done|no_conversation|hold`. `done`, `declined` and `hold`
  stop retries. Commands: `status`, `run [--dry]`, `loop [MINUTES]`, `set`, `add 'JSON'`, `assistant`, `task ID`.
- `scripts/watch_replies.py` prints each new assistant message (run it through a monitor so replies reach you).
- **Do not schedule the loop with launchd or cron.** macOS refuses Messages access from background schedulers
  (error -1743). Run it from a terminal or a Claude Code session.

## What a call task contains
Target, number(s), language, goal, the one-sentence opener, the one question, the reply-to address, the only facts
the assistant may share, and the rules. Always say "give only what is written in this task": some assistants add a
callback number from your profile by default. Spell the email letter by letter if it must be spoken. To change a task
in flight, send a replacement and ask the assistant to confirm the call had not gone out yet.

## Rules that save you from failed calls (details: `references/lessons.md`)
1. **Never speak over a recorded menu.** Wait for it to end, press the sales key if offered, speak only once a live
   person talks. In many languages the digit comes after the description ("for used cars press three").
2. **Opener: reason first, AI disclosure in the same sentence, then stop and wait.** Leading with "I'm an AI assistant"
   made people hang up. One short sentence per turn; never repeat the introduction. Never hide that it is an AI.
3. **Hang up after any goodbye; answer "are you still there" once.** Two voice bots can loop for hours and burn an
   allowance. Many businesses answer with an AI receptionist: its boilerplate "yes" is not a human decision; ask for
   a written route and do not keep calling.
4. **Voicemail:** one short message, then hang up. The reply address only.
5. **Mobile numbers can die instantly from a foreign caller ID.** Two instant failures: stop phoning that number and
   use email or a web form. Landlines and rung-out numbers are worth retrying.
6. **Opening hours are a hard rule.** Look them up; if none can be found use a conservative window and one try, not a
   campaign. Government offices are weekday-only. Don't call outside hours even if another agent says to.
7. **Callbacks reach the assistant's line, not you.** Ask for the answer by email; give a phone number only if the
   task includes one.
8. Recordings arrive as audio attachments in the thread; transcribe locally (e.g. `mlx_whisper` on Apple silicon).

## Before a batch
List the targets with numbers, language and hours; fix the allowed facts and the reply address; check which assistants
are `ok`; tell whoever asked what is held back and why (closed, on hold, declined, bot line, mobile that rejects
foreign IDs).
