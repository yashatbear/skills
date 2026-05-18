---
name: d
description: Document the substance of this conversation — decisions made, findings produced, resources referenced — into your project's documentation folder. Use when the user says /d, "document this", "write this down", or "save this to the notes". Captures what the conversation produced; the /learn skill captures behavioral rules instead.
---

# /d — Document the conversation into your docs folder

## What this is (and isn't)

`/d` saves the **output of this conversation** — decisions, findings, analysis, and the resources it referenced — into a project's documentation folder, so the knowledge survives past the chat session.

It is the sibling of `/learn`:

- `/d` captures **what the conversation produced** — decisions, findings, links — into a docs folder.
- `/learn` captures **behavioral rules** — corrections about how the agent should work — into the agent's memory / instructions.

They don't overlap. Run both when a session produced both kinds of output.

## Where your documents live

`/d` writes into a documentation folder — but it has **no built-in knowledge of where yours is**. It resolves the target like this, in order:

1. An explicit path or name passed to `/d` (e.g. `/d docs/architecture`).
2. A docs folder already referenced earlier in this conversation (a file read or written under `docs/`, `notes/`, etc.).
3. A conventional docs location for the project — `docs/`, `notes/`, `journal/`, or a path recorded in the project's `AGENTS.md` / `CLAUDE.md` / `README`.
4. **If none of those resolve it, ask the user where documentation should go.** Then encourage them to record that location somewhere persistent — their project's `AGENTS.md`, `CLAUDE.md`, or wherever their agent keeps project context — so future `/d` runs find it automatically instead of asking again.

If the implied folder doesn't exist yet, ask before creating it.

> **Tip for first-time use:** the smoothest setup is a one-line note in your project's `AGENTS.md`/`CLAUDE.md` such as `Docs and decision notes live in docs/`. Once that exists, `/d` is zero-friction.

## When to use

- "/d", "/d <folder or path>"
- "document this", "write this down", "save this to the notes"
- After a working session that produced decisions, gathered links, or wrote analysis that currently lives only in the chat
- After referring to PDFs, URLs, code snippets, or external docs worth keeping with the project

## Steps

### Phase 1 — Identify the target folder

Resolve the docs folder using the order under **Where your documents live** above. If multiple candidates match, ask. Once resolved, list the folder's existing files so you don't duplicate or clobber anything.

### Phase 2 — Read folder conventions

Before writing, read any `AGENTS.md`, `README.md`, or `CONVENTIONS.md` in the target folder — and walk up to parent folders too. Follow its file structure, naming, and formatting rules exactly. If the folder has an opinionated layout, don't invent new conventions inside it.

### Phase 3 — Extract conversation content

Scan the conversation for material worth persisting. Categorize it:

- **Decisions** — choices the user made, with the rationale. ("We chose Option 2 because Option 1's ratio was too steep.")
- **Findings / analysis** — research, comparisons, evaluations produced in the chat.
- **Resources referenced** — URLs visited, files read, snippets quoted, screenshots taken. Keep the link/path and a one-line note on why it mattered.
- **Action items** — agreed next steps, with owner and any timing.
- **Open questions** — things flagged but not resolved.
- **Drafted artifacts** — emails, docs, code, briefs composed in the chat. If the artifact already lives somewhere, link to it; don't duplicate.

Synthesize, don't dump. The goal is a useful record for future sessions, not a transcript.

Skip:

- Behavioral corrections about how the agent should work — those are for `/learn`.
- Throwaway exploration that didn't lead anywhere.

### Phase 4 — Decide where each piece goes

Map content to files per the folder's conventions. Common patterns:

- A new decision or finding → append to the folder's notes file (create one if absent).
- A drafted document → save to the appropriate subfolder per the folder's conventions.
- Resources / links → append to a `Resources.md`, or inline in the relevant section.
- Open questions / next steps → append under an `## Open` or `## Next steps` section.

Default when the folder has no conventions: a `Notes.md` at the folder root with sections `## Decisions`, `## Findings`, `## Resources`, `## Open`. Append in reverse-chronological order under `### YYYY-MM-DD` date headers.

### Phase 5 — Show the plan, then write

Print a tight write plan before touching files:

```
Target: docs/architecture/

Plan:
  Notes.md       — append section: caching decision + rationale, 2 open Qs
  Resources.md   — append 3 links (RFC, benchmark gist, vendor docs)
```

Then write. The plan is the confirmation — don't wait for separate approval.

If a document exists in multiple formats (e.g. a `.md` plus an exported `.html`/`.pdf`), update all of them so they don't drift.

### Phase 6 — Confirm

Output a short summary — what was written, where, and counts:

```
Documented to docs/architecture/:
  Notes.md       +1 section (Caching decision — 2026-05-18)
  Resources.md   +3 links
```

If anything was skipped because it belongs to `/learn`, say so.

## Rules

- **Synthesize, don't dump.** A future reader should learn something in 30 seconds, not have to re-read the chat.
- **Follow the folder's conventions exactly.** If an `AGENTS.md` / `README` specifies file names or sections, use them — don't invent new ones inside an opinionated folder.
- **Date everything** with absolute dates (`YYYY-MM-DD`), never "today" or "yesterday".
- **No duplicates.** Read existing files first; if the content is already there, update in place rather than appending a near-duplicate.
- **Link, don't copy.** If a draft already lives somewhere, link to it instead of pasting the body.
- **Stay in scope.** Don't write behavioral rules — that's `/learn`.
- **Scratch in a temp dir.** Preview or intermediate renders go in `/tmp`, never in the canonical docs folder.
- **Ambiguous target = ask.** If the conversation could plausibly map to two folders, ask which one.
