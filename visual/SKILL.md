---
name: visual
description: Show an open decision as screenshots, one per option, of what the result would look like (Today beside A, B…) on one board, inline in chat. Picture only; the user answers in chat. Not a question flow and not a list of open items (that's opens). Use for /visual, "show me visually", "what would it look like", "screenshot the options", "draw the options".
---

# /visual: screenshot each option's result

The user wants to **see each outcome**: a screenshot of what it would look like with
this decision, and a screenshot of it with that decision. So every card on the board is
a real screenshot of the result, not a scorecard. Show **Today** first when there is a
current state, then one card per option, the Rec outlined.

The skill only shows the picture. The user answers in chat as usual: do not open an
AskUserQuestion and do not list other open items (that's `opens`).

## When to use it unprompted

Run `/visual` on your own, without being asked, whenever a picture of each outcome would
help the user decide: a choice between screens, layouts, copy, an email as the recipient
sees it, a site or report row, or a doc section. Skip it for calls with nothing to see
(a date, a yes/no on spend) and for picks already made. One board per decision; don't
re-send an unchanged board.

## Dependencies

- Node.js 18+.
- Playwright with Chromium. By default `render.mjs` loads it from the sibling `browse`
  skill (`../browse/node_modules/playwright/index.mjs`; see that skill's setup). To use
  another install, set `VISUAL_PLAYWRIGHT` to its `playwright/index.mjs`.

## Steps

1. **Pick the decision.** With an argument, use the decision it names (ticket, topic).
   With none, use the open decision(s) in this session. Several → one board each.
   None → say so in one line and stop.
2. **Find the surface each option changes**, and how to render it for real:

   | Decision is about | Screenshot of | How |
   |---|---|---|
   | A UI (page, component, copy) | The real page at the device width in question | The app's local dev server (with its own test mock API when it needs a session), or a public/staging URL. Options are CSS/DOM edits on that same render (`page.addStyleTag`, `page.evaluate`) |
   | An email, message, or send setting | The message as the recipient sees it | Render the real template the sender uses, filled per option, in a neutral mail-client frame |
   | A site, report, or listing row | That row/page after the change | The site's own build or HTML with the option's data |
   | A doc, ticket, or plan | The section that changes | Render the real Markdown/HTML before and after |

   Never draw a fake UI from scratch, and never imitate a third-party product's chrome
   (no fake Gmail/Slack screens): use a neutral frame around real content.
3. **Capture** with Playwright, `deviceScaleFactor: 2`, one PNG per card, all cropped to
   the **same region** so the cards line up. Measure, don't guess: log the numbers that
   matter (e.g. `scrollWidth` vs `clientWidth`) and put them in the note. Hide dev
   overlays (e.g. `nextjs-portal{display:none}`). Worked example:
   `examples/demo-capture.mjs` captures `examples/demo-page.html` at 390px with three
   CSS options (`node examples/demo-capture.mjs <out-dir>`).
4. **Write the spec** (`examples/demo.json`):
   ```json
   {"ref": "optional label", "date": "optional", "question": "...?",
    "source": "Where the shots came from · options are CSS edits on that render",
    "options": [
      {"name": "Today", "baseline": true, "image": "demo-today.png", "note": "...",
       "zoom": {"x": 190, "y": 50, "w": 200, "h": 44}},
      {"name": "Fit all five", "rec": true, "image": "demo-fit.png", "note": "..."}],
    "why": "One line for the Rec."}
   ```
   - `image` paths are relative to the spec or absolute; PNG only.
   - `baseline: true` marks Today (no letter, dimmed). Options get A, B, C.
   - `zoom` (optional, CSS px of the shot) adds a 2x close-up of the part that differs,
     so it reads on a phone. Use the same zoom on every card.
   - `dsf` (optional, default 2) is the shot's device scale factor.
   - `note`: one line, ≤ 10 words, the visible difference plus any cost.
   - At most one `rec: true`. Calm wording, no red.
5. **Render:** `node <skill-dir>/render.mjs <spec.json>` prints one PNG path per line
   (default `$TMPDIR/visual/<session>/`, `--out <dir>` to change). Up to three cards per
   board; more split into balanced boards.
6. **Look at the board** with Read: zoom aimed at the right spot, nothing clipped, the
   difference visible at a glance. Fix and re-render.
7. **Show it:** `SendUserFile({files: [...], display: "render", status: "normal", caption: "<question>"})`,
   then one line: the Rec and the pick needed. Do not repeat the board as text.

## How images reach the chat

- **`SendUserFile` with `display: "render"`** puts the PNG in the chat as an inline file
  card in the Claude desktop app and on claude.ai/code. Send all boards for one decision
  in one call.
- **Read of a PNG** shows it to the model only. Use it to check the render.
- **Markdown images** of local files (`![](file:///…)`) do not render. Do not use them.
- **Terminal-only session** (no `SendUserFile`): print the PNG paths; opening a window
  on the user's desktop needs their OK in the same turn.

## Rules

- Real renders only. Mock content (new copy, a value) is placeholder; say so in the note
  or `source`.
- No paid APIs, no live browser, no Computer Use. Headless Chromium only.
- Board chrome is a neutral dark palette in Helvetica Neue; edit the `:root` tokens in
  `render.mjs` to match your own brand.
- Keep scratch in a temp dir; stop dev servers and remove any worktree you made when done.
