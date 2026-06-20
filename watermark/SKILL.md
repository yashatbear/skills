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
- **Color / opacity / fill** — sensible defaults (cream, 20% opacity, SF Pro Bold, wide-tracked ALL CAPS, dynamically sized to span the page). Override with `--color`, `--opacity`, `--fill`.
- **`--no-caps`** — keep the recipient/text exactly as typed (disables the wide ALL-CAPS tracking) for cases where caps don't suit the document.

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
  --fill 0.88
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

The default house style is SF Pro Bold, wide-tracked ALL CAPS, sized to span the page corner-to-corner.

- **Text:** wide-tracked ALL CAPS — `R E C I P I E N T   ·   <date>   ·   C O N F I D E N T I A L`. Pass `--no-caps` to keep typed case with no tracking.
- **Font:** SF Pro Display Bold (see **Font requirement** below). Falls back to Helvetica-Bold with an install hint if SF Pro isn't installed.
- **Position:** dead-center of each page.
- **Diagonal:** follows the page's **true corner-to-corner angle** (≈29° on 16:9 slides), running bottom-left → top-right, so it spans the whole page regardless of aspect ratio. Override with `--angle <deg>`.
- **Size:** dynamic — the text is auto-sized to span `--fill` (default 0.90) of the page diagonal. No fixed fontsize; it adapts per page, so it never clips and always reaches the corners.
- **Color:** cream (#EDDBC3) by default — readable on dark slide backgrounds, subtle on cream surfaces.
- **Opacity:** 20% — visible without fighting content.

### Font requirement

The house style needs **SF Pro Display Bold**. Apple's license forbids redistributing the font, so it is **not** committed to this repo — install it on each machine that runs the skill (laptops, CI):

1. Download **SF Pro** from https://developer.apple.com/fonts/ (free).
2. Open the `.dmg` and run the installer `.pkg`, or copy the `.otf` files into `~/Library/Fonts/`.
3. The script auto-detects `SF-Pro-Display-Bold.otf` in `~/Library/Fonts/` or `/Library/Fonts/`.

If SF Pro is missing, the script still produces a watermark but falls back to **Helvetica-Bold** and prints the install hint to stderr. **When you see that hint, install SF Pro and re-run** so the output matches the house style — don't ship the Helvetica fallback for anything client-facing. (A local, untracked `watermark/fonts/SF-Pro-Display-Bold.otf` is also picked up if present.)

### Color presets

| `--color` | Value | When to use |
|---|---|---|
| `cream` (default) | #EDDBC3 | Dark-background decks (dark brown, black) |
| `grey` | 50% grey | Mixed backgrounds — universal safe choice |
| `brown` | #332011 | Light-background docs (cream, white) |
| `white` / `black` | — | Escape hatches |

## Gotchas

- **Sizing is dynamic — no fontsize knob.** The text auto-sizes to span the page diagonal, so it fits any aspect ratio (16:9 slides, US Letter memos, A4) without clipping. To make it less dominant, lower `--fill` (e.g. `--fill 0.80`); to make it bolder, raise it toward `1.0`. The legacy `--fontsize` and `--rotation` flags are **deprecated and ignored** — the script accepts them (so old callers don't hard-error) but prints a warning. Use `--fill` instead of `--fontsize`, and `--angle <deg>` instead of `--rotation`.
- **Light-background docs need `--color brown`.** The default cream is invisible on tan/cream/white body pages — it only reads on dark backgrounds. For light-background memos and documents, pass `--color brown`. Match the color to the document background; don't default to cream just because it's the skill default.
- **Long labels just get smaller.** Because sizing is dynamic, a long recipient/label no longer overflows — it shrinks to fit. If that makes it too small, shorten the label rather than fighting the size.
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
