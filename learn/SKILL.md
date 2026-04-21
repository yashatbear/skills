---
name: learn
description: The user wants you to learn from feedback. This can happen in three ways: (1) user says "/learn" after correcting you, (2) user says "/learn" at end of a session to capture all corrections, (3) user explicitly asks you to remember something. Scan the recent transcript for corrections, then persist rules to the right places so the mistake never recurs.
---

# Learn — Capture corrections and persist them

## When to Use

Run `/learn` when:
- The user corrected your approach and you want to lock in the lesson
- End of a session to sweep for any corrections you missed
- The user says "remember this" or "don't do that again"

## How It Works

### Step 1: Scan the transcript

Look back through the recent conversation for moments where the user corrected you. Corrections take many forms:
- Explicit: "no, don't do that", "stop doing X", "use Y instead"
- Implicit: user undoes your change, re-does it differently, or sighs and provides the right approach
- Surprising: something you wouldn't have known without being told (project conventions, team preferences, external constraints)

For each correction, extract:
- **What you did wrong** (the behavior to avoid)
- **What to do instead** (the correct behavior)
- **Why** (the reason, if given — a past incident, a preference, a constraint)
- **Scope** — is this specific to one project/repo, or universal?

### Step 1b: Check for repeat offenses

For each correction found, **before creating anything new**, check if a rule already exists that covers this mistake:
- Search auto-memory feedback files (`~/.claude/projects/<project>/memory/feedback_*.md`)
- Check `AGENTS.md` corrections logs

If the rule already exists, this is a **repeat violation** — the agent failed to follow a known rule. In that case:
1. Open the existing feedback memory file
2. Increment the `strikes` field in the frontmatter (add it if missing, starting at 1)
3. Append a dated entry to a `## Violations` section at the bottom of the file:
   ```
   ## Violations
   - 2026-03-17: Sent a PR notification without a link, had to be asked to add it
   ```
4. Report the violation in the Step 4 summary with the total strike count

Frontmatter example after a repeat offense:
```markdown
---
name: Messages should be specific with links
description: When sending messages on user's behalf, include specific details and links
type: feedback
strikes: 2
---
```

High-strike rules (3+) indicate systemic failures. When reporting these, flag them prominently so the user can decide whether to escalate the rule (e.g., move it to AGENTS.md, add it to a skill doc, or restructure the prompt).

### Step 2: Classify where it belongs

Each correction maps to one or more persistence targets:

| Type of correction | Where to persist | Example |
|---|---|---|
| **Universal agent behavior** (applies across all projects) | Top-level `AGENTS.md` → Corrections Log | "Never use `rm`, always `mv` to Trash" |
| **Project-specific convention** (applies to one repo) | That repo's `AGENTS.md` → Corrections Log | "Never commit directly to main" |
| **Personal preference / user context** | Auto-memory (`~/.claude/projects/<project>/memory/`) | "User's email style is concise, no filler" |
| **Tool/skill usage rule** | The relevant skill's `SKILL.md` | "Don't use X MCP tool for replies" |
| **Workflow or process knowledge** | Auto-memory (project type) | "Merge freeze starts on release days" |

### Step 3: Write the rules

For each correction, update **all** relevant files. A single correction often needs changes in multiple places. **Do not default to only writing memory files** — memory is the weakest persistence mechanism because it's only loaded contextually. Skills, AGENTS.md, and other docs are loaded deterministically when relevant and are far more effective at preventing repeat mistakes.

Think about where the rule will actually be **read at the right moment**:
- A correction about PR reviews → update the **review-pr skill** (loaded every time `/review-pr` runs)
- A correction about a messaging tool → update that tool's skill
- A universal agent behavior → update **AGENTS.md** corrections log (loaded every session)
- A personal preference → memory file (loaded contextually)

**Always update the most specific, deterministic location first.** Memory files are supplementary, not primary.

#### Skills
If the correction involves a workflow that has a skill, **update that skill's SKILL.md first**. This is the highest-priority target because skill docs are loaded exactly when the relevant action happens.
- Add rules to the relevant section, or create a "Gotchas" or "Rules" section if one doesn't exist

#### AGENTS.md Corrections Log
Format: `- <what NOT to do> → <what TO do instead>`

There may be multiple AGENTS.md files that need updating:
- A top-level `AGENTS.md` — the canonical file (e.g. synced across machines via your dotfiles or a shared checkout)
- Repo-specific AGENTS.md files

If your top-level `AGENTS.md` is a symlink into a synced location, always edit the real file — the symlink is just for convenience.

#### Auto-memory files
Use the memory system at `~/.claude/projects/<project>/memory/` as a **supplement**, not the primary target:
- Create or update a memory file with proper frontmatter (name, description, type)
- Update `MEMORY.md` index if adding a new file
- Memory types: `user`, `feedback`, `project`, `reference`
- For corrections, use type `feedback` with the structure: rule, then **Why:** and **How to apply:** lines
- **If a correction is already captured in a skill or AGENTS.md, a memory file is optional** — don't create one just for completeness

### Step 4: Confirm with the user

After writing, summarize what you persisted and where. Keep it tight:

```
Learned 1 correction, 1 repeat violation:

1. Always check day-of-week for start dates (new)
   → AGENTS.md (corrections log)
   → memory/feedback_start_dates.md (new)

2. REPEAT: Include links in messages about PRs/tickets (strike 2)
   → memory/feedback_specific_messages.md (strikes: 1 → 2, violation logged)
```

When all corrections are repeat violations (nothing new to persist), report:

```
0 new corrections, 1 repeat violation:

1. REPEAT: Include links in messages about PRs/tickets (strike 2)
   → memory/feedback_specific_messages.md (strikes: 1 → 2, violation logged)
```

## Rules

- **Don't duplicate.** Before writing a new rule, check if the correction already exists in the target file. Update existing rules rather than adding duplicates.
- **Don't over-persist.** Not every correction needs to go everywhere. A one-time debugging tip doesn't need to be in AGENTS.md. Use judgment.
- **Be specific.** "Be more careful" is not a rule. "Don't chain .where().orderBy() on different Firestore fields without a composite index" is.
- **Include the why.** A rule without context becomes cargo cult. If the user gave a reason, capture it.
- **Remove stale rules.** If a correction supersedes an old one, remove or update the old rule.
- **Respect the file hierarchy.** Universal rules go in top-level AGENTS.md. Project rules go in project AGENTS.md. Personal preferences go in memory. Tool rules go in skill docs.
