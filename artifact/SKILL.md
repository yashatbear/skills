---
name: artifact
description: Build a self-contained claude.ai-style HTML page — inline CSS/JS, light and dark, no CDNs — written to a local file and opened in your browser. For mockups, dashboards, UX previews, explainers. Not the hosted Artifact tool.
---

# artifact — self-contained HTML pages, opened locally

Build a single `.html` file (all CSS/JS inline), write it to disk, and open it in a
browser. The file IS the delivery — a real page you can open, keep, and re-open offline —
not a screenshot.

> **This is not the hosted `Artifact` tool.** This skill is the local-HTML-file workflow:
> a self-contained file rendered straight from disk, with no server and no network.

## When to use

Reach for this whenever communicating something **visually** beats terminal text:
- UI / product **mockups** (a screen, a component, a proposed change)
- **Dashboards** or data snapshots
- **Message / UX previews** (what an iMessage, email, or notification will look like)
- **Visual explainers** (a flow, a before/after, a set of states laid out as cards)

If the answer is a paragraph or a table, just say it in chat. Use a page when layout,
color, or fidelity carry the meaning.

## Hard design rules — treat as requirements

1. **Apple-clean, light by default. No serif fonts.** Use the SF system stack:
   `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif`.
   Rounded cards, generous whitespace, subtle hairlines, `letter-spacing: -0.02em` on headings.
2. **Header is the title and a date line. Nothing else.** One `<h1>`, then one `.meta`
   line carrying provenance and the date — and that is the whole header. **No lede, no
   subtitle, no tagline, no handling note stacked underneath.** A one-line summary of what
   the page shows is what the exec summary is for; provenance goes in the date line or the
   footer; internal handling instructions go in the `#agents-md` block, never rendered —
   especially on a page an external reader will see. The failure mode is additive: each
   edit adds one more "helpful" line under the `<h1>` until the reader has to scan four
   near-titles before reaching content.
3. **Theme-aware.** Support light AND dark via `@media (prefers-color-scheme: dark)`.
   Drive colors through CSS variables so dark mode is a small `:root` override block.
4. **Fully self-contained.** Inline all CSS/JS. **No external fonts, CDNs, or network
   requests of any kind.** Embed images as `data:` URIs. It must render correctly opened
   straight from disk as a `file://` with no internet.
   *You don't have to hand-embed the bytes* — author with references to **local** files
   (a linked stylesheet, `<img src="assets/x.png">`) and run `finalize.sh` to inline
   everything. See **Author small, finalize once** below. A `file://` with local relative
   refs already renders in a browser, so you can iterate on the small version and only
   inline at hand-off.
5. **Responsive.** Relative units; `max-width: 100%` on images/media; constrain content
   with a `max-width` wrapper (~720px). Wide content (code, tables, diagrams) scrolls
   **inside its own container** (`overflow-x: auto`) — the page body never scrolls sideways.
6. **Mirror the real thing.**
   - Chat/messages → real **iMessage** styling: incoming = **gray, left-aligned bubble with
     a bottom-left tail**; outgoing = **blue, right-aligned, tail on the right**.
   - Product UI → mirror the **actual components** (real colors, spacing, labels). Don't
     fabricate a look that isn't in the product.
7. **Modals shown in isolation sit on a plain background — no dim scrim.** When showing a
   modal/sheet on its own, render it on the page background, not over a darkened overlay.

## Standard structure — every artifact has three parts, in this order

Enforced, not suggested: `bash agents-block.sh --check <page>` **exits 4** if the page
doesn't hold the shape. Guidance without a gate erodes in about three edits.

> **This binds every operation on an artifact, not just a final check.** Generating a page,
> any edit, any in-place live update — each one runs `agents-block.sh --check` before you
> call it done. **A failing check means the work isn't finished**, the same way a failing
> test does.
>
> This applies to artifacts that already exist. One that predates the rule fails until its
> block gains a `## Structure` stanza — that is the intended migration, deliberately with
> no grandfather clause. Touching an old artifact means bringing it into shape.

### 1. Executive summary, at the top

Max **5 bullets**, each **one line** (≤100 characters — one line at the 720px wrapper in
15px text; the checker counts `<li>` in an element with id/class `exec-summary`).

- **5 is a ceiling, not a target.** Three strong bullets beat five padded ones. Write the
  ones you have and stop. A stated count otherwise becomes a quota agents always fill.
- **Derived conclusions only.** A bullet may state a comparison, ratio, trend, or verdict.
  It may **not** restate a figure that appears verbatim in a chart or table below.
  "Option A is 132× cheaper than Option B" is a summary. "$5.6118" is a duplicate.
- **Every figure must close, and the derivation goes in the block.** A figure in the
  summary is a claim *about* an asset below it. Walk it back to that asset, confirm the
  arithmetic, and record it under `## Derivations` — one line per figure-bearing bullet,
  naming the asset and showing the sum. `--check` exits 4 on a bullet that states a figure
  with nothing covering it. Identifiers, years and calendar dates aren't figures, so a
  bullet citing a ticket ID or "replaced in July" needs no derivation.

Why this is gated and prose in the block isn't enough: a summary once read *"19 of 20
recent messages arrived via the relay, from 7 distinct senders"* above a table that
actually summed to 18 of 19, across 8 recipients rather than 7. Every mechanical check
passed — bullet count, caps, footer, filled-in block. The rule that would have caught it,
*"keep the views in sync,"* was prose in the block, and prose in the block is what nobody
re-reads at handover. Writing the derivation out is the step at which a number that
doesn't close stops being invisible.

The failure it protects against is regeneration: summary tiles that merely restated chart
data were once deleted from a page by hand — and without this rule the skill regenerates
exactly what was just removed. It is also the one sanctioned exception to MECE below — a
summary duplicates by construction, so "derived only" is what keeps it honest.

### 2. The middle — MECE facts, as visual as possible

Mutually exclusive, collectively exhaustive. With one carve-out that matters:

- **The rule is "no fact appears twice FOR THE SAME PURPOSE", not "no fact appears
  twice."** A chart and a table may legitimately carry the same numbers — the chart gives
  shape, ordering, magnitude; the table gives precision, metadata, outcome. That split is
  correct and deliberate. The failure mode is a **third** home with no distinct job.
- **Visual, but not gratuitously.** Pick the simplest form that shows the comparison. A
  chart earns its place when *shape* matters — ordering, magnitude, trend. For three data
  points a table is more honest than a bar chart. "As visual as possible" on its own
  produces slop; the test is whether the form carries meaning the text can't.

### 3. Bottom — conditional, and omitted when it's empty

- Decision / recommendation artifacts → **Next steps** (id `next-steps`).
- Reference / measurement artifacts → **Open questions / what would change this**
  (id `open-questions`).
- Same caps as the summary: max 5 bullets, one line each, ceiling not target.
- **If there are no next steps, omit the section entirely.** A forced section produces
  filler, and filler is the bloat this whole rule fights. Record the omission as
  `bottom: none — <reason>` in the embedded block so the next agent knows it was a
  decision, not an oversight.

### 4. Footer — one line: staleness and provenance

Every artifact ends in a single `<footer>`, at most **160 characters**, shaped:

```
Updated <date> · Sources: <where the numbers came from>
```

- **Bump the date on every edit.** The stamp is what lets a reader judge whether the page
  is still true; a stale one is worse than none, because it asserts freshness that isn't
  there.
- **The sources are what let a reader check the numbers.** Name the systems, not the
  people — where someone would go looking to verify the figures.
- **Nothing else earns a place there.** No caveats, no commentary, no "generated by", no
  second line. Anything that qualifies the *data* belongs in a legend chip, a table row's
  `.sub`, or the table's basis note — not the footer.

Enforced: a missing `<footer>`, a missing `Updated <date>` stamp, or one over the cap
exits 4. Exempt types (mockup, preview, explainer) skip it with the rest of the shape.

### Declaring the shape (and the two exemptions)

The embedded `#agents-md` block carries a `## Structure` section. It is what
`agents-block.sh --check` reads:

```markdown
## Structure
- type: decision            # decision | reference | mockup | preview | explainer
- bottom: next-steps        # next-steps | open-questions | none — <why there are none>
```

- **Type exemption.** `mockup`, `preview` and `explainer` have nothing to summarise — a
  screen mockup or an iMessage preview is the artifact. Those types skip the exec-summary
  and bottom checks entirely. `decision` and `reference` must hold the shape.
- **Waiver.** When a page genuinely can't take the standard shape, add a `waiver:` line to
  `## Structure` stating why, and the check passes:

  ```markdown
  - waiver: three interleaved timelines; any summary bullet would misstate the sequencing
  ```

  **A waiver is opt-in, and it is loud.** `template.html` deliberately ships *no* `waiver:`
  line — you add one on purpose rather than forgetting to delete one. Scaffold-ish text
  (`TODO`, `<reason>`, `(delete unless used)`, anything parenthetical, under 12 characters,
  or a single word) is **rejected as a violation**, not honoured: an escape hatch that its
  own placeholder satisfies is an off switch. When a waiver is in force, every `--check`
  run prints `*** STRUCTURE CHECKS WAIVED ***` and the stated reason to stderr — it is a
  **recorded, reviewable decision**, not a way to quiet the checker. Reach for it rarely;
  prefer fixing the page or declaring an honest `type:`.

### When it doesn't fit — soften, don't refuse

If the content can't be conveyed within the envelope: **build it anyway**, then say plainly
that it exceeded the envelope and propose how to split it into multiple artifacts.

Refuse outright **only** when a decision artifact was explicitly requested and it can't be
made into one. Agents judge "can this be conveyed in five bullets" badly, and a hard
refusal leaves the reader with nothing — a page plus an honest caveat is always better.

## Workflow

1. **Start from the template.** Copy `template.html` (in this skill dir) and adapt it —
   it has the light/dark CSS-variable scaffold, SF font stack, card, pill tags, and code
   block. It's the **lean core**; chat mockups add the iMessage bubbles snippet
   (`snippets/imessage-bubbles.css`). It also carries the **embedded AGENTS block** — fill
   in its TODOs as you build the page, and if you're editing an artifact you didn't write,
   **read that block first** (`bash agents-block.sh page.html`). See **The embedded AGENTS
   block** below.
2. **Save it somewhere durable — never `/tmp`.** Every artifact is a saved record; there is
   no throwaway tier. Write it next to what it's *about* — a synced folder or a git repo,
   so the context that explains it travels with it and it survives the session. Don't
   invent a central `artifacts/` bin — colocate with the subject. Say where you wrote it.
3. **Check the shape — before you show anything.** A required step, not a
   final-checklist nicety:
   ```bash
   bash agents-block.sh --check /absolute/path/to/page.html   # must exit 0
   ```
   Exit 3 = the embedded block is missing or still has TODOs. Exit 4 = the page doesn't
   hold the standard structure (see **Standard structure** above). Either way the artifact
   is **not finished** — fix it and re-run. Do not hand it over on a non-zero exit.
4. **Open it in a browser:**
   ```bash
   open -a "Safari" /absolute/path/to/page.html   # macOS; substitute your own browser
   ```
5. **Iterate live.** The reviewer opens it in the browser; edit the file and they
   hard-refresh (Cmd+Shift+R). A high-res 2× screenshot is fine as evidence, but it is not
   the deliverable — the live page is. **Re-run step 3 after every edit** — an edit that
   breaks the shape is an unfinished edit.
6. **Verify with `verify.sh` when you need to see it yourself** — `bash verify.sh page.html`,
   then Read the PNGs. See **Verifying a page** below. `verify.sh` re-runs the structure
   check for you and reports it beside its `verify: layout …` diagnostics, but it will not
   fail the render over it — `agents-block.sh --check` stays the gate.
7. **Keep it live for the rest of the chat** — see **Live by default** below. Creating
   the file is not the end of the job; the page tracks the conversation until it's frozen.

## Author small, finalize once (don't emit base64 through your tokens)

The deliverable must be self-contained — but *authoring* it that way is the single
biggest time sink: a 400 KB base64 image or a 150-line re-typed stylesheet is expensive
to emit and pathological to `Edit` (line-addressing a 160 000-char line). So keep the
asset bytes **out of your token stream**:

- **Reference local assets by path while authoring.** Put images in an `assets/` dir next
  to the page and use `<img src="assets/chart.png">`; link shared CSS with
  `<link rel="stylesheet" href="…">`. Save a screenshot to a file (don't paste it inline).
  A `file://` with local relative refs renders fine, so iteration is unaffected.
- **Inline everything with one command at hand-off:**
  ```bash
  bash finalize.sh page.html            # rewrite in place → fully self-contained
  bash finalize.sh page.html --stdout   # or preview; -o out.html to keep the source
  bash finalize.sh --check page.html    # list any external local refs (exit 3 if any)
  ```
  It inlines linked stylesheets (recursively expanding `@import`), `<img src>`/`srcset`/
  `<picture><source>` and `url()` assets (images, fonts, audio/video as `data:` URIs), and
  `<script src>`, resolving paths against the file's dir. Remote/`data:` refs are left
  alone, so it's **idempotent** and a **no-op** on an already-self-contained file.
- **Assets must live under the page's own directory.** finalize **refuses** absolute paths
  (`/Users/…`, `/etc/…`) and any ref that escapes the dir via `../` — it leaves them as-is,
  warns, and `--check` flags them (so a broken or leaky page fails fast). Keep assets in an
  `assets/` dir beside the page. If `--check` fails, look for an absolute/`../` ref or a
  missing file.
- **Icons are already external-by-default:** `sf-icons.sh > icons.css`, `<link>` it, and
  finalize inlines it — the icon base64 never touches your context.

## Verifying a page — render it, never a screen recording

An artifact is a visual deliverable, so "the HTML looks right" isn't verification — you
have to look at the rendered page. Do that with the `browse` skill (a sibling skill in
this repo; a headless-Chromium CLI), driven by `verify.sh`:

```bash
bash verify.sh page.html                     # light + dark @ 1200x900 → prints PNG paths
bash verify.sh page.html --viewport 390x844  # phone-width check
bash verify.sh page.html --light-only
```

**Then `Read` every PNG it prints.** Running it and not looking is not verification.

It finalizes a temp self-contained copy, serves it on loopback http, drives `browse`
(`viewport` → `goto` → `screenshot`), and prints the PNG paths. Two constraints shaped
that path, so don't "simplify" around them:

- **Headless only.** The headless `browse` Chromium is what does the rendering — no GUI
  window. A GUI browser window is for a human's eyes, not an agent's self-check.
- **`browse` blocks `file://`** (http/https only), which is why the page gets served
  rather than opened off disk. It also refuses to write screenshots outside `/tmp` or the
  cwd, so `verify.sh` shoots into `/tmp` and copies out.

**Never screen-record or `screencapture` a browser window** to check your own work. That
captures whatever else is on screen; `verify.sh` renders the page alone at a known
viewport, which is what you actually want to inspect.

**Dark mode:** `browse` has no `prefers-color-scheme` emulation, so `verify.sh` flips every
`@media (prefers-color-scheme: dark)` block to `all` through CSSOM — same rules, same
cascade, no edit to the page. If the page has no dark block it says so and skips the shot
(which is itself a finding — rule 3 says every artifact supports dark).

**When to verify:** before hand-off, whenever you built or restructured the page without
anyone watching, and whenever you're about to claim it renders correctly. **When not to:**
don't screenshot-loop a mockup someone is actively reviewing in their own browser — they're
already looking at it; just edit the file and let them hard-refresh.

### After a structural edit, MEASURE — a screenshot won't catch it

A screenshot catches *styling*. It does not reliably catch *structure*. A downscaled
full-page render of a page that lost its `max-width` wrapper looks like "slightly wide
cards", not like a break — so reading the PNG feels like verification while the page is
actually broken. Two cheap checks close that gap. Run both after any **structural** edit
(reordering / removing / re-assembling `<section>`s, slicing the file by line ranges,
scripted rewrites) — not after copy tweaks:

1. **Tag balance, immediately after the surgery.** Before rendering anything, count the
   open vs close tags of the containers you moved across. Dropping a boundary line is the
   single most common way a slice-and-reassemble goes wrong, and it is silent — the page
   still parses, because the browser just re-parents the orphans.
   ```bash
   for t in main div section article header footer; do
     printf '%s open=%s close=%s\n' "$t" \
       "$(grep -o "<$t[ >]" page.html | wc -l)" "$(grep -o "</$t>" page.html | wc -l)"
   done
   ```
2. **Measure the live DOM, don't eyeball it.** `verify.sh` prints a `verify: layout …`
   line per render — read it. It reports the viewport, `documentElement`
   `scrollWidth`/`clientWidth`, whether the page's `max-width` container is present and
   how wide it computes, and any element wider than the viewport. A container that came
   back **missing**, or a width that scales with the window, is the bug — unambiguous and
   instant, where three screenshot rounds were not.

   Same measurement by hand, for anything `verify.sh` doesn't cover (an element's box, a
   specific selector, a served URL):
   ```bash
   B=path/to/browse/dist/browse   # the browse skill's built CLI
   $B goto "$URL"
   $B js 'document.querySelector(".wrap") ? getComputedStyle(document.querySelector(".wrap")).maxWidth : "MISSING"'
   ```

The invariants worth asserting: the `max-width` wrapper exists and computes to its
authored value; `document.documentElement.scrollWidth <= clientWidth` (no sideways
scroll); charts/tables render at their intended pixel size rather than scaling with the
window. (A real case: a section reorder dropped the `<main class="wrap">` open tag — only
`</main>` survived — so the page rendered at full window width and every chart scaled with
it. Three `verify.sh` runs plus three PNG reads missed it; one
`document.querySelector('.wrap')` returning `null` found it.)

**When someone reports the page looks wrong, measure before you fix.** A theory that is
merely self-consistent is not a diagnosis — publishing off one costs a second report and
burns the trust in the first fix. Measure first, and start from *what you changed* (your
recent edits to that file) rather than *what looks suspicious*.

## Live by default — the artifact tracks the chat until frozen

An artifact created mid-chat is a **living page**, not a one-shot render. From the moment
you write it, keeping it consistent with the conversation is part of your job:

- **Track what it depicts.** Remember the file path and what the page shows. Whenever a
  later turn changes or extends that content — new data arrives, a decision is revised,
  copy gets edited, the direction shifts — the **same file gets updated in place**,
  unprompted, and you note it in your reply ("updated `<path>` — refresh with ⌘R"). A
  stale artifact that contradicts the chat is a bug.
- **Re-check the shape after every in-place edit — before you say it's updated.** These
  unprompted live updates are where the structure actually drifts: a new row, a new
  finding, one more bullet "while I'm here", and the summary is at seven. So the loop is
  **edit → `bash agents-block.sh --check <path>` → report**, every time, not just on
  first write. The usual failure is the exec summary growing past five, or a new figure
  being restated there when it already appears in a chart or table below; the fix is to
  tighten the summary, not to raise the ceiling.

### Delegating live updates to a sub-agent (optional)

Live upkeep is well-specified mechanical work; if your setup supports sub-agents (e.g. the
`Agent` tool), applying new data to existing views is a good thing to dispatch rather than
doing inline — it keeps the main context clear of HTML. If you do:

- **The prompt is the whole handoff — make it self-contained.** The sub-agent has none of
  the chat's context. Give it: the **absolute file path**; one line on what the page
  currently shows; **exactly what changed this turn** (the new rows / figures / revised
  conclusion, verbatim — never "update per the conversation"); the standing tailoring
  constraints on this artifact; and the marching orders — *read the embedded `#agents-md`
  block first (`bash agents-block.sh <path>`), edit the same file in place, extend the
  views already on the page rather than bolting on new assets, never regenerate from the
  template, update the block (Derivations / exclusions) alongside the page, then run
  `bash agents-block.sh --check <path>` and don't finish until it exits 0.*
- **One agent per file, never two.** Concurrent edits to the same page clobber each other.
  Updates to *different* artifacts are independent and can run together.
- **Relay only past a passing check.** A failing or unreported check means the update is
  NOT done — re-dispatch with the failure detail, or fix that one thing yourself.
- **Creation is not an update.** Building the page — and the iterative design loop while
  someone is actively reviewing it with you — stays with the main agent, where the design
  conversation lives. Delegation covers the unprompted keep-it-current edits.
- **Preserve tailoring.** Any adjustment asked for in-chat (layout, colors, wording,
  what's in/out) is a standing constraint on that artifact. Apply updates as incremental
  edits — **never regenerate from the template**, which would wipe it. Restate the
  tailoring in every update prompt, and keep the page's `#agents-md` tailoring section
  current — that's the copy that survives the session.
- **Replace superseded content; don't stack it.** When an update changes what the page
  *concludes* — status, diagnosis, recommendation — rewrite that section in place instead
  of adding a second block beside the old one. Dated facts and event history stay
  append-only.
- **Same path, always.** Updating in place is what makes a browser refresh sufficient. A
  new path is a new artifact, not an update — only fork when a variant or copy is asked for.
- **Freeze on request.** "Freeze / pin / lock this" ends the live behavior: the file is now
  a snapshot. If later conversation drifts from a frozen page, say so — but do **not** touch
  the file. "Unfreeze" resumes updates. If changes are wanted to a frozen page while keeping
  the snapshot, fork to a new file (`<name>-v2.html`) and that fork is live from birth.
- **Per-artifact state.** Multiple artifacts in one chat are tracked independently — each
  has its own live/frozen status and its own tailoring constraints.

## The embedded AGENTS block — every artifact carries its own instructions

An artifact outlives the chat that made it. Weeks later another agent — in another
session, often with only the file — is asked to add data to it, and knows nothing about
why the page is shaped the way it is. So **the guidance travels inside the file**: every
artifact carries a non-rendering `AGENTS.md` in its `<head>`.

```html
<script type="text/markdown" id="agents-md">
# AGENTS.md — for agents editing this artifact
…
</script>
```

**Read it before you touch the page. Update it when your edit changes what it says.**

```bash
bash agents-block.sh page.html            # print the block
curl -s "$URL" | bash agents-block.sh -   # ditto, from a served/hosted copy
bash agents-block.sh --check page.html    # exit 3 if missing or still full of TODOs
```

**Why a `<script type="text/markdown">` and not an HTML comment.** An HTML comment cannot
legally contain `--`, and these blocks routinely do (`--update`, `--origin`, `--private`,
any CLI flag). A script block with a non-JS `type` is never executed, never rendered, and
never parsed as markup, so it holds `--`, `<`, and `>` verbatim; the only forbidden
sequence is a literal `</script`. It also survives `finalize.sh` untouched (which only
rewrites `<script src>` tags) and is a real DOM node, so it's addressable by id.

### The rule that matters most: extend what's there, don't bolt on

Copy this into every artifact's block, because it's the failure mode that actually
happens. When new data arrives, **extend every view already on the page that can carry
it** — add the row, series, column, or tile to the chart or table that's already there —
before you consider adding a new asset. A new asset is only correct when the data has no
home in what exists (genuinely different unit, scope, or population), and then you record
why under **Deliberate exclusions**.

Adding a fresh card beside the existing ones for data those could have carried is drift:
the page ends up asserting the same fact in two shapes and no reader can tell which is
authoritative. Its sibling failure is the same fact landing in one view and silently not
the others, so a reader who scrolls to the chart and a reader who scrolls to the table
leave with different numbers.

So after any data edit, **walk every asset on the page** and confirm each new figure is
either present or deliberately excluded — then make sure the block's exclusion list still
matches reality.

### What goes in the block

Keep it short and specific to *this* page — it is not a copy of this skill.

- **What this page is** — subject, audience, what it's for. One line.
- **Structure** — `type:` and `bottom:` (and a `waiver:` if one was needed). This is the
  machine-read part: see **Standard structure** above. `--check` exits 4 without it.
- **Standing rules** — the extend-don't-bolt-on rule above, plus anything peculiar to
  this page.
- **Derivations** — one line per exec-summary bullet that states a figure, naming the
  asset it computes from and showing the arithmetic. Gated: `--check` exits 4 if a
  figure-bearing bullet has none. Delete the section when the summary states no figures.
- **Deliberate exclusions** — every "X is not in view Y, because Z". This is the highest
  value part: it's what stops the next agent from either "fixing" a considered decision or
  silently breaking it. If you exclude something, write down why, here, in the same edit.
- **Tailoring asked for** — standing in-chat constraints (layout, wording, what's in or
  out) that a later agent would otherwise undo.
- **Data sources** — where the numbers came from and how to refresh them. Include the
  folder or repo the page was saved to, so the durable original stays findable.

`template.html` ships with this block scaffolded; fill in the TODOs rather than deleting
them. A page whose block is missing or still says TODO is unfinished — `agents-block.sh
--check` is the gate.

**`--check` exit codes:** `0` ok · `2` bad usage or unreadable file · `3` block missing,
or TODOs still in it · `4` structure violation (no `## Structure`, missing/oversized exec
summary, >5 bullets, a bullet over 100 chars, a summary figure with no `## Derivations`
line, or a declared bottom section that isn't on the page). Every failure prints what to
fix and how to exempt the page legitimately.

## Icons — genuine SF Symbols (recolorable, still self-contained)

For an Apple-clean look, use the **real SF Symbols** rather than emoji or hand-drawn SVG
approximations. `sf-icons.sh` (in this skill dir) turns any SF Symbol into an inline,
recolorable icon with **no external assets**:

```bash
bash sf-icons.sh lock bolt paperplane.fill eye link > icons.css
```

It prints a base `.sf` rule plus one `.sf-<name>` rule per symbol — each the symbol's
alpha PNG (rendered via AppKit) embedded as a `data:` URI and applied as a CSS
`mask-image`. Paste the output into the page's `<style>` and drop icons in with:

```html
<span class="sf sf-lock" style="width:20px;height:20px"></span>
```

Because the glyph is painted with `background: currentColor`, each icon **inherits the
element's text color** — so it recolors to your accent, a muted gray, or the right
light/dark value automatically, with zero extra work (mask-based, so one asset serves
both themes). Dots in a symbol name become hyphens in the class
(`paperplane.fill` → `.sf-paperplane-fill`). Browse names in SF Symbols.app; prefer
outline names for a light look and `.fill` variants where a solid glyph reads better.
Missing/renamed names are reported on stderr and left as a `/* MISSING */` comment.

Flags: `--weight <ultralight…black>` (default `regular`), `--pt N` (render size, default
160 — crisp for any icon shown ≤ 32px), `--no-base` to skip re-emitting the `.sf` rule on
a second call, `--no-cache` to bypass the cache (render fresh, don't write it).

**Requirements:** macOS, SF Symbols.app, and the Xcode Command Line Tools (`swift`) — the
glyphs are rendered through AppKit. `swift` is only invoked for a symbol that isn't already
in the local cache. Emoji are multicolor/off-brand and can't be tinted; a licensed webfont
breaks the self-contained rule; hand-drawn SVGs aren't the real glyphs — hence real SF
Symbols, rendered once and cached.

### Setting up the icon cache

Rendered PNGs are memoized under `icons-cache/<weight>-<pt>/<name>.png` in this skill dir,
so the same symbol is never rendered twice. **The cache ships empty** and builds itself on
first use: Apple's SF Symbols license restricts redistributing the glyph artwork, so this
repo does not include pre-rendered PNGs — you generate your own locally.

- **One-time prerequisites (macOS):** install the [SF Symbols
  app](https://developer.apple.com/sf-symbols/) and the Xcode Command Line Tools
  (`xcode-select --install`, which provides `swift`).
- **How it fills:** just call `sf-icons.sh` with the symbols your page needs. Each name
  that isn't cached is rendered via AppKit and written to
  `icons-cache/<weight>-<pt>/<name>.png` (default `regular/160`); every subsequent call for
  that symbol is a near-instant cache hit. So the first run that needs a new glyph is the
  only one that touches `swift`.
- **Layout & contract:** see `icons-cache/README.md`. A weight+size pair is one subdir
  (`regular-160/`, `bold-88/`, …); the PNG is the symbol's alpha channel at that size.
- **The cache is gitignored** (`icons-cache/*/`) — the PNGs are Apple artwork and stay
  local. If you maintain a private fork you can commit your own cache there, but don't push
  rendered SF Symbols to a public repo.
- **Once a symbol is cached, no `swift` is needed** — a Mac without the Xcode CLT can emit
  any already-cached glyph. Only rendering a brand-new symbol requires the toolchain.

## Starter template (trimmed — full copy in `template.html`)

Lean core — no iMessage bubbles (add `snippets/imessage-bubbles.css` only for chat mockups):

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Title — short description</title>
<!-- Guidance for agents editing this page. Never rendered. Fill in the TODOs. -->
<script type="text/markdown" id="agents-md">
# AGENTS.md — for agents editing this artifact

## What this page is
TODO: one line — subject, audience, and what it is for.

## Structure
- type: TODO — decision | reference | mockup | preview | explainer
- bottom: TODO — next-steps | open-questions | none — <why there are none>

## Structural rules
- **Exec summary: max 5 one-line bullets, 5 is a ceiling not a target.** Derived
  conclusions only — a comparison, ratio, trend or verdict, never a figure restated
  verbatim from a chart or table below.
- **Middle is MECE, as visual as the comparison warrants.** No fact twice *for the same
  purpose*: chart = shape/ordering/magnitude, table = precision/metadata/outcome. A third
  home with no distinct job is the failure.
- **Bottom is conditional.** Next steps (decision) or Open questions (reference), same
  caps. No next steps → delete the section and say `bottom: none — <reason>` above.

## Standing rules
- **Represent new data in the assets that already exist.** Extend the charts/tables
  already here — add the row, series, column, or tile — before adding a new asset. A new
  asset is only correct when the data has no home in what exists; record why below.
- **Keep the views in sync.** A figure in one view belongs in every other view whose
  scope covers it. After any edit, walk each asset and confirm.
- **Deliberate exclusions are decisions, not gaps.** Do not "fix" one silently.
- **Edit in place; preserve tailoring.** Never regenerate from the template.

## Derivations
TODO: one line per summary bullet stating a figure — `"<figure>" = <asset> <arithmetic>`.
Delete if the summary states no figures.

## Deliberate exclusions
TODO: `<figure>` is not shown in `<view>` because `<reason>`. Delete if none.

## Tailoring asked for
TODO: standing constraints from chat. Delete if none.

## Data sources
TODO: where the numbers come from, and how to refresh them.
</script>
<style>
  :root {
    --bg:#f5f5f7; --card:#fff; --ink:#1d1d1f; --sub:#6e6e73; --line:#e6e6ea;
    --code-bg:#1d1d1f; --code-ink:#e6e6ea; --accent:#0b6bcb;
  }
  * { box-sizing:border-box; }
  html,body { margin:0; padding:0; }
  body {
    background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",Arial,sans-serif;
    -webkit-font-smoothing:antialiased; line-height:1.5; padding:48px 20px 72px;
  }
  .wrap { max-width:720px; margin:0 auto; }
  h1 { font-size:28px; font-weight:600; letter-spacing:-0.02em; margin:0 0 6px; }
  .meta { color:var(--sub); font-size:13px; margin:0 0 36px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:18px;
          padding:22px; margin:0 0 22px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
  pre { background:var(--code-bg); color:var(--code-ink);
        font-family:"SF Mono",ui-monospace,Menlo,monospace; font-size:12.5px;
        border-radius:10px; padding:12px 14px; overflow-x:auto; white-space:pre-wrap; }
  img,svg,video { max-width:100%; height:auto; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#000; --card:#1c1c1e; --ink:#f5f5f7; --sub:#98989d; --line:#2c2c2e;
            --code-bg:#0b0b0c; --accent:#6cb0ff; }
    .card { box-shadow:none; }
  }
</style>
<!-- chat mockup? <link rel="stylesheet" href="snippets/imessage-bubbles.css"> (finalize inlines it) -->
</head>
<body>
<div class="wrap">
  <h1>Page title</h1>
  <p class="meta">Provenance · Month D, YYYY</p>   <!-- header = title + date line ONLY -->
  <!-- 1 · summary: derived conclusions, max 5 one-line bullets. Drop for mockups. -->
  <section class="card" id="exec-summary">
    <ul><li>A comparison, ratio, trend or verdict — not a number copied from below.</li></ul>
  </section>
  <!-- 2 · the middle: MECE facts, simplest form that shows the comparison. -->
  <section class="card">
    <p>Card content. For a chat preview, add the bubbles snippet, then:</p>
    <!-- <div class="phone"><div class="bubble">Incoming — gray, left, tail.</div></div>
         <div class="phone out"><div class="bubble out">Outgoing — blue, right.</div></div> -->
  </section>
  <!-- 3 · bottom: id="next-steps" or id="open-questions". NO next steps → delete
       this card and record `bottom: none — <reason>` in the block. Never pad it. -->
  <section class="card" id="next-steps">
    <ul><li>One action, one line.</li></ul>
  </section>
</div>
</body>
</html>
```

## Dependencies

- **macOS + a browser** for the core workflow (the examples use Safari; any browser opens
  the file). `finalize.sh`, `agents-block.sh`, and the HTML itself are plain bash + a
  browser and are cross-platform.
- **`verify.sh`** shells out to the **`browse`** skill (a sibling in this repo) — build it
  per its own SKILL.md. Without `browse`, skip `verify.sh` and just open the file.
- **`sf-icons.sh`** needs macOS, SF Symbols.app, and Xcode CLT `swift` — only for icons,
  and only to render an uncached symbol. See **Setting up the icon cache**.
- **`test_derivations.py`** (unit tests for the checker's figure logic) needs Python 3.

## Checklist before you hand it over

- [ ] **Header is the `<h1>` plus one date line — nothing else.** No lede, subtitle, or
      handling note underneath it (rule 2). Count the lines: two, not four.
- [ ] Opens correctly as a bare `file://` with **no network** (no CDN/font/image URLs).
- [ ] Light AND dark both look right (toggle appearance, or check the dark block).
- [ ] Page body doesn't scroll horizontally on a narrow window; wide blocks scroll inside.
- [ ] Chat mockups use real iMessage bubble styling; product mockups mirror real components.
- [ ] If you needed to check it yourself: `bash verify.sh <path>` and **Read** the PNGs —
      headless render, never a screen recording of a browser window.
- [ ] If the edit was **structural** (sections reordered/removed, file sliced and
      reassembled): tag balance checked right after the surgery, and `verify.sh`'s
      `verify: layout` line read — wrapper present, no horizontal overflow.
- [ ] Still current with the conversation — if the chat moved past what the page shows,
      it's been updated in place (or explicitly frozen).
- [ ] Carries a filled-in `#agents-md` block — `bash agents-block.sh --check <path>` exits 0.
- [ ] Any new data appears in **every** existing view whose scope covers it; nothing was
      solved by adding a new chart/table beside one that could have carried it. New
      exclusions are written down in the block.
- [ ] **Every figure in the summary was walked back to its asset and still closes**, and
      the arithmetic is on the record under `## Derivations` — `--check` exits 4 otherwise.
- [ ] Holds the **standard structure**: exec summary of ≤5 derived one-line bullets, a MECE
      middle, and a bottom section only if there is one — `--check` exits 4 otherwise.
      Mockups/previews/explainers declare their `type:` instead.
- [ ] If the content overflowed the envelope: built anyway, and said so plainly, with a
      proposed split into multiple artifacts. Never a silent squeeze, never a flat refusal.
</content>
