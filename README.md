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
- **linkedin** — Searches LinkedIn profiles/companies/jobs via a local MCP server with faceted filters.
- **p** — "Proceed" — execute the recommended action from the previous response.
- **s** — "Simplify" — re-explain the previous response in plain language.
- **r** — "Recommend" — gather context on an open decision and deliver a reasoned recommendation.

## Status

These skills are published as snapshots from a private repo I use for my own work. They work for me — they may or may not work for you without tweaks. Issues and PRs welcome but responses may be slow.

## License

MIT. See [LICENSE](LICENSE).
