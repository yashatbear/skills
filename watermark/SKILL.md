---
name: watermark
description: Add a per-recipient diagonal watermark to a PDF. Takes a source file and a person's name, overlays "<recipient> · <date> · confidential" diagonally on every page, and saves the output alongside the source in a "watermarked copies/" folder. Use when asked to watermark a PDF, create a tracked copy for someone, or prep a share-safe version of a deck.
---

# Watermark — per-recipient PDF watermarking

## When to use

- User asks to watermark a PDF, create a "tracked copy," or prep a deck for a specific recipient
- User invokes `/wm` with or without arguments
- Before sending a confidential PDF to an external reviewer where you want a visible trail of who received which copy

## Inputs

Two pieces of information are required:
1. **Source PDF** — the file to watermark
2. **Recipient name** — the person the copy is for

Both should be inferred from chat context when possible:
- If the conversation just discussed a specific PDF (exported deck, memo, etc.), use that as the source.
- If the conversation just discussed or drafted correspondence to a specific person, use them as the recipient.
- If only one is in context, ask the user to confirm the missing one. Do not guess recipients or files.
- If neither is in context, ask for both.

Optional inputs:
- **Date** — defaults to today (ISO format). Override with `--date`.
- **Output directory** — defaults to `<src_dir>/watermarked copies/`. Override with `--out`.
- **Color / opacity / fontsize** — sensible defaults (cream, 22% opacity, 65pt Helvetica).

## Usage

```bash
python3 /path/to/skills/watermark/watermark.py \
  "/path/to/source.pdf" \
  "Recipient Full Name"
```

With overrides:

```bash
python3 /path/to/skills/watermark/watermark.py \
  "/path/to/source.pdf" \
  "Recipient Full Name" \
  --date 2026-04-10 \
  --color grey \
  --opacity 0.30 \
  --fontsize 70
```

The script prints the output path on success. Show it to the user.

## Output

Default output location: `<source_dir>/watermarked copies/<slug>-<date>.pdf`

Example:
```
Source:  /Users/you/decks/20260327 pitch deck.pdf
Output:  /Users/you/decks/watermarked copies/jane-doe-2026-04-10.pdf
```

Slug is the recipient name lowercased with non-alphanumeric characters replaced by hyphens.

## Watermark design

- **Text:** `<recipient>  ·  <date>  ·  confidential`
- **Position:** dead-center of each page
- **Rotation:** 45° diagonal (counterclockwise)
- **Color:** cream (#EDDBC3) by default — readable on dark slide backgrounds, subtle on cream surfaces
- **Opacity:** 22% — visible without fighting content
- **Fontsize:** 65pt — sized so the rotated text stays inside a standard 1920×1080 deck page

### Color presets

| `--color` | Value | When to use |
|---|---|---|
| `cream` (default) | #EDDBC3 | Dark-background decks (dark brown, black) |
| `grey` | 50% grey | Mixed backgrounds — universal safe choice |
| `brown` | #332011 | Light-background docs (cream, white) |
| `white` / `black` | — | Escape hatches |

## Gotchas

- **Fontsize ceiling.** The watermark must fit within the page after 45° rotation. For 1920×1080 slides, max fontsize is ~65pt with the default text. Larger sizes cause `insert_textbox` to return a negative value and render nothing. The script raises an error with a hint if this happens.
- **Default 65pt is sized for slides, not docs.** The default assumes a 1920×1080 deck page. On US Letter (8.5×11) pages, 65pt clips at both edges of the rotated text — use `--fontsize 40` for Letter/A4 documents. If you see the watermark cut off in preview, drop the fontsize.
- **Match color to background.** The default cream reads well on dark slide backgrounds but is invisible on cream/tan/white body pages — use `--color brown` (and likely a smaller `--fontsize`) for light-background documents. Don't default to cream just because it's the skill default.
- **Textbox won't fit.** If the error fires, drop `--fontsize` or shorten the recipient name / date string.
- **Dependency.** Requires `pymupdf` (`pip install pymupdf`). System Python on macOS typically has it; if not, `/opt/homebrew/bin/python3 -m pip install pymupdf`. PyMuPDF and the underlying MuPDF are licensed **AGPL-3.0** (or commercial) — consider the implications before redistributing a product that uses this skill.
- **Preserves source.** The script never modifies the source PDF — it opens, overlays, and saves to a new file.
- **Not a security boundary.** This is a visible-trail watermark, not a DRM system. A determined adversary can strip it. Use your cloud-storage share-link controls (download disabled, expiring links) for actual access control.

## Chat-context heuristics

When the user says "watermark this for Jane" or "/wm Jane":
1. Look back in the conversation for the most recently referenced PDF file. Prefer the one most recently generated, exported, or read.
2. Look back for the most recently named person. If multiple, ask the user.
3. Confirm both choices with the user before running if there's any ambiguity — it's better to ask once than produce a wrong watermark.

When the user says "/wm" with no arguments:
1. If there's an obvious source and recipient in the last few turns, propose them and run.
2. Otherwise ask which file and which person.
