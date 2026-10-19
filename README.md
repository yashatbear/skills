# skills

A small collection of [Claude Code](https://claude.com/claude-code) skills I use day-to-day. Each directory is a self-contained skill — a `SKILL.md` (documentation Claude reads to know when and how to use it) and any helper scripts the skill invokes.

## Installation

Claude Code loads skills from `~/.claude/skills/` (user-wide) or `.claude/skills/` (repo-local). Symlink whichever skills you want:

```bash
git clone https://github.com/yashatbear/skills.git ~/skills
mkdir -p ~/.claude/skills
ln -s ~/skills/watermark ~/.claude/skills/watermark
# ...repeat for whichever skills you want
```

Or copy the directories in directly. Most skills have a `Dependencies` section in their `SKILL.md` — install those before using the skill.

A couple of skills need a build or setup step, documented in their own `SKILL.md`:

- **browse** ships source, not a binary — `npm install`, then `bun build --compile src/cli.ts --outfile dist/browse`, then `npx playwright install chromium`.
- **artifact**'s icon helper (`sf-icons.sh`) renders SF Symbols locally on first use (macOS + the SF Symbols app + Xcode CLT `swift`); the render cache ships empty and is gitignored, because Apple's SF Symbols license restricts redistributing the glyph artwork.

## What's here

- **artifact** — Builds a single self-contained `.html` page (inline CSS/JS, light + dark, no CDNs) you open straight from disk. For UI mockups, dashboards, message previews, and visual explainers. Ships a template, a structure checker, an asset-inliner, and an SF-Symbol icon helper (macOS).
- **browse** — A persistent headless-Chromium CLI for QA and dogfooding: navigate, click, fill, screenshot, accessibility snapshots, before/after diffs, console/network inspection. Built on Bun + Playwright; build from source (see its SKILL.md).
- **watermark** — Adds a per-recipient diagonal watermark to a PDF ("Name · Date · confidential") for tracked document sharing. Built on PyMuPDF.
- **watermark-video** — Same idea for videos (.mov, .mp4). Built on FFmpeg + Pillow.
- **md-to-pdf** — Converts Markdown to a cleanly styled PDF via WeasyPrint.
- **rename-files** — Inspects files in a directory (images, PDFs) and proposes descriptive renames.
- **cleanup** — Inventories background processes and asks before killing them.
- **ghostty** — Configures and manages the Ghostty terminal emulator.
- **learn** — Captures corrections and preferences into a persistent memory system so the same mistake doesn't recur across sessions.
- **d** — "Document" — captures the conversation's decisions, findings, and referenced resources into your project's docs folder. Sibling of `learn`.
- **linkedin** — Searches LinkedIn profiles/companies/jobs via a local MCP server with faceted filters.
- **telephony** — Runs outbound AI phone calls through several call-capable texting assistants (Tab, Pally, Fo, ...): load-balanced and parallel, retried every couple of hours inside each business's opening hours. Ships a dispatcher, a reply watcher, a small Messages helper (macOS) and a lessons file on phone menus, voicemail, voice-bot receptionists and caller-ID rejection.
- **opens** — Lists what's waiting on you in a multi-agent session (decisions, approvals, opt-ins, worker questions), skipping anything an agent or worker is still working on. Read-only, one line per item with a recommended pick.
- **p** — "Proceed" — execute the recommended action from the previous response.
- **s** — "Simplify" — re-explain the previous response in plain language.
- **r** — "Recommend" — gather context on an open decision and deliver a reasoned recommendation.

## Status

These skills are published as snapshots from a private repo I use for my own work. They work for me — they may or may not work for you without tweaks. Issues and PRs welcome but responses may be slow.

## Credits

Each skill wraps one or more open-source projects. The skills' own code is MIT-licensed, but the runtime dependencies each carry their own license — install and use accordingly:

- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)** (used by `watermark`) — **AGPL-3.0** or commercial. AGPL is copyleft and can affect how you redistribute software that links against it. Artifex sells a commercial license if AGPL doesn't fit your use case.
- **[MuPDF](https://mupdf.com)** (underlies PyMuPDF) — **AGPL-3.0-or-later** or commercial
- **[Pillow](https://github.com/python-pillow/Pillow)** (used by `watermark-video`) — MIT-CMU (HPND)
- **[FFmpeg](https://ffmpeg.org)** (used by `watermark-video`) — LGPL-2.1-or-later by default; GPL-2.0-or-later for builds with `--enable-gpl` (e.g. libx264 support). Homebrew's default build is GPL.
- **[Python-Markdown](https://github.com/Python-Markdown/markdown)** (used by `md-to-pdf`) — BSD-3-Clause
- **[WeasyPrint](https://github.com/Kozea/WeasyPrint)** (used by `md-to-pdf`) — BSD-3-Clause
- **[Pygments](https://pygments.org)** (used by `md-to-pdf`) — BSD-2-Clause
- **[Pango](https://pango.gnome.org)** (used by `md-to-pdf` via WeasyPrint) — LGPL-2.0-or-later
- **[Ghostty](https://github.com/ghostty-org/ghostty)** (configured by `ghostty`) — MIT
- **[stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server)** (drives `linkedin`) — Apache-2.0
- **[Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)** (Playwright fork, used by linkedin-mcp-server) — Apache-2.0
- **[Playwright](https://github.com/microsoft/playwright)** (drives `browse`) — Apache-2.0
- **[Chromium](https://www.chromium.org)** (downloaded by `browse` via `playwright install chromium`, not bundled) — BSD-3-Clause + others
- **[Bun](https://bun.sh)** (builds/runs `browse`) — MIT
- **[jsdiff](https://github.com/kpdecker/jsdiff)** (`diff`, used by `browse`) — BSD-3-Clause
- **[SF Symbols](https://developer.apple.com/sf-symbols/)** (rendered on demand by `artifact`'s `sf-icons.sh`) — **Apple license**. The glyphs are Apple's; their license restricts redistribution and reproduction, so this repo ships **no** rendered SF Symbol artwork — `sf-icons.sh` renders them locally on your Mac and the cache is gitignored. Using the icon helper means agreeing to Apple's SF Symbols license.
- **gstack** — the `browse` skill is a public extraction of **gstack**, the headless-browser CLI it grew out of. Credit and thanks to gstack for the foundation.

Thanks to the maintainers of all of the above.

## License

The skills in this repo are MIT-licensed — see [LICENSE](LICENSE). That applies to the code I wrote. It does **not** override the licenses of any dependencies listed under Credits — in particular, if you use the `watermark` skill, you're also using PyMuPDF, which is AGPL-3.0.
