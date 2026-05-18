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

## What's here

- **watermark** — Adds a per-recipient diagonal watermark to a PDF ("Name · Date · confidential") for tracked document sharing. Built on PyMuPDF.
- **watermark-video** — Same idea for videos (.mov, .mp4). Built on FFmpeg + Pillow.
- **md-to-pdf** — Converts Markdown to a cleanly styled PDF via WeasyPrint.
- **rename-files** — Inspects files in a directory (images, PDFs) and proposes descriptive renames.
- **cleanup** — Inventories background processes and asks before killing them.
- **ghostty** — Configures and manages the Ghostty terminal emulator.
- **learn** — Captures corrections and preferences into a persistent memory system so the same mistake doesn't recur across sessions.
- **d** — "Document" — captures the conversation's decisions, findings, and referenced resources into your project's docs folder. Sibling of `learn`.
- **linkedin** — Searches LinkedIn profiles/companies/jobs via a local MCP server with faceted filters.
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

Thanks to the maintainers of all of the above.

## License

The skills in this repo are MIT-licensed — see [LICENSE](LICENSE). That applies to the code I wrote. It does **not** override the licenses of any dependencies listed under Credits — in particular, if you use the `watermark` skill, you're also using PyMuPDF, which is AGPL-3.0.
