---
name: opens
description: List what's waiting on the user in this session (decisions, approvals, opt-ins, worker questions), skipping anything an agent, worker, or peer session is still working on. Read-only and non-blocking. Use for /opens, "what's on me", "what's waiting on me", "what do you need from me", "anything on me", "what's blocked on me".
---

# Opens: what's waiting on the user

For orchestration sessions with several threads running. The user wants to see what's in
their court so they can clear it while the other threads keep working. This skill only
lists. It doesn't ask, launch, or change anything.

**Not a decision flow.** If the user wants to decide through the AskUserQuestion UI, they
say so. `/opens` prints a short list and returns at once.

## The rule

**Free-form asks are this skill.** "what's waiting on me", "what's open on me" or
"anything on me" typed as plain text runs these rules too. Don't write the list by hand
from memory: a hand-written list tends to include work an agent is still doing, and
"how is this waiting on me if you're working on it" is the failure this skill prevents.

List an item only when **the ball is in the user's court**:

- A worker or peer returned options or a question and is waiting on their pick.
- A run is parked on their approval: a send, a publish, a live-browser or Computer Use
  opt-in, a secret grant, a merge or deploy call, spend over a cap.
- The session asked them something they never answered.
- Something is blocked on information or an action only they have (a 2FA code, a
  CAPTCHA, a login, a signature).

Leave out:

- **Anything in flight.** If an agent owns it and isn't waiting on the user, it's
  cooking. That includes a background worker with no completion notice yet, a peer
  session still working, a background job, Monitor, or loop still running, a PR with
  auto-merge armed and CI pending, and a task marked in_progress.
- Anything they already answered, in any wording.
- Anything they were offered and left unmentioned. Unmentioned means declined, not pending.
- Anything the agent can decide itself, by convention or a sensible default.
- New topics. Extract from this session only; don't go looking for work.

## Process

1. **Check live state first** (in parallel, all read-only):
   - `TaskList`, then `TaskGet` on anything ambiguous.
   - Background `Agent` and fork launches in this session: which have sent a completion
     notice and which haven't.
   - `ListAgents` for peers this session messaged with `SendMessage`.
   - Background Bash jobs, Monitors, and `/loop` or `CronList` schedules this session started.
   - For each PR or ticket the session names whose state decides whether it's waiting on
     the user: `gh pr view <n> --json state,autoMergeRequest,reviewDecision,statusCheckRollup`,
     or your issue tracker's equivalent.
   - For each item that says the user should send, reply to, or email someone: search
     their sent mail (or the sent side of that channel) for that recipient. People often
     send things themselves; one already sent is done, not on them.
     Don't fetch anything else.
2. **Walk the session** for asks, returned options, parked approvals, and unanswered
   questions. For each one, mark it cooking, done, or on the user, using the live state
   from step 1. Live state wins over what the transcript last said: a worker that
   finished since its last update may now be waiting on the user.
3. **Order** by what unblocks the most parked work, then one-way doors before two-way.
4. **Print** the list (format below). Stop there. No AskUserQuestion, no follow-up actions.

## Output

```
3 on you:
1. <What's needed, one line>. Rec: <pick>. (<thread>)
2. ...
3. ...

4 cooking: <name>, <name>, <name>, <name>

Answer inline, or ask to decide in the question UI.
```

- One line per item: the ask, the recommended pick if one exists (`Rec:`), and the thread
  it came from (worker or peer name, ticket, or PR).
- Say what the thing is. An item from an older or side thread the user may not remember
  names it in a few words (who or what, and when it stopped) and still carries a `Rec:`.
  A bare "Say when to resume the paused session" with no context and no Rec gets back
  "?" and costs a second round.
- Tickets and PRs as markdown links to their https URLs, never bare IDs. Times in the
  user's timezone.
- The `cooking` line lists names only, no detail. Leave it out when nothing is running.
- Nothing on the user: print `Nothing on you. N cooking: ...` and stop.
- No tables. No preamble or recap.
