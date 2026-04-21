---
name: watermark-video
description: Add a per-recipient diagonal watermark to a video file (.mov, .mp4, etc.). Takes a source file and a person's name, burns "<recipient> · <date> · confidential" diagonally onto every frame, and saves the output alongside the source in a "watermarked copies/" folder. Use when asked to watermark a video, create a tracked copy for someone, or prep a share-safe version of a recording.
---

# Watermark Video — per-recipient video watermarking

## When to use

- User asks to watermark a video, create a "tracked copy," or prep a recording for a specific recipient
- User invokes `/wmv` with or without arguments, or says "watermark this video for <name>"
- Before sending a confidential video (product demo, walkthrough, internal recording) to an external reviewer where you want a visible trail of who received which copy

For PDFs, use the `watermark` skill (`/wm`) instead.

## Inputs

Two pieces of information are required:
1. **Source video** — the file to watermark (.mov, .mp4, .m4v, .mkv, etc.)
2. **Recipient name** — the person the copy is for

Both should be inferred from chat context when possible:
- If the conversation just discussed a specific video file, use that as the source.
- If the conversation just discussed or drafted correspondence to a specific person, use them as the recipient.
- If only one is in context, ask the user to confirm the missing one. Do not guess recipients or files.
- If neither is in context, ask for both.

Optional inputs:
- **Date** — defaults to today (ISO format). Override with `--date`.
- **Output directory** — defaults to `<src_dir>/watermarked copies/`. Override with `--out`.
- **Color / opacity / fontsize** — sensible defaults mirror the PDF skill (cream, 22% opacity, 48pt at 1080p, auto-scaled for other resolutions).
- **Quality** — `--crf` (default 18, visually lossless-ish) and `--preset` (default `medium`) control H.264 encoding.

## Usage

```bash
python3 /path/to/skills/watermark-video/watermark_video.py \
  "/path/to/source.mov" \
  "Recipient Full Name"
```

With overrides:

```bash
python3 /path/to/skills/watermark-video/watermark_video.py \
  "/path/to/source.mov" \
  "Recipient Full Name" \
  --date 2026-04-10 \
  --color grey \
  --opacity 0.30 \
  --fontsize 56 \
  --crf 20
```

The script prints the output path on success. Show it to the user.

## Output

Default output location: `<source_dir>/watermarked copies/<slug>-<date>.<ext>`

Example:
```
Source:  /Users/you/demos/20260415 product demo.mov
Output:  /Users/you/demos/watermarked copies/jane-doe-2026-04-21.mov
```

Slug is the recipient name lowercased with non-alphanumeric characters replaced by hyphens. The output keeps the source's extension (.mov stays .mov).

## Watermark design

- **Text:** `<recipient>  ·  <date>  ·  confidential`
- **Position:** dead-center of every frame
- **Rotation:** 45° diagonal (counterclockwise)
- **Color:** cream (#EDDBC3) by default
- **Opacity:** 22%
- **Fontsize:** 48pt at 1080p, scaled linearly with height (e.g. ~96pt at 4K, ~32pt at 720p)

### Color presets

Same as the PDF skill:

| `--color` | Value | When to use |
|---|---|---|
| `cream` (default) | #EDDBC3 | Dark-background videos (UIs on brown/black) |
| `grey` | 50% grey | Mixed or unpredictable backgrounds — universal safe choice |
| `brown` | #332011 | Light-background videos (cream/white UIs) |
| `white` / `black` | — | Escape hatches |

## How it works

1. `ffprobe` reads the video's native width and height.
2. Pillow renders a transparent PNG at that resolution with the text rotated 45° and centered.
3. FFmpeg overlays the PNG on every frame with `libx264 -crf 18 -preset medium`, copies the audio track untouched, and writes `-movflags +faststart` for streaming.

Re-encoding is unavoidable (the frames are being modified), but CRF 18 is visually close to the source for most UI/demo content.

## Gotchas

- **Screen recordings need higher opacity.** The 22% default is tuned for decks (solid backgrounds) and gets absorbed by UI detail in screen recordings. For product demos and other UI captures, use `--opacity 0.40` to `0.50` — it still reads as a transparent overlay but survives the busy background. On dark UI palettes, `--color cream --opacity 0.45` is a good pair.
- **Always verify a frame before iterating.** After any run, extract a frame with `ffmpeg -ss 5 -i <out.mov> -frames:v 1 /tmp/frame.png` and Read it. Don't guess at whether the watermark is visible — re-encodes cost 30-60s each.
- **Re-encode, not a remux.** Audio is copied, but video is re-encoded to H.264. Output file size usually shrinks; quality matches the source for screen-recording content at CRF 18. Bump `--crf` lower (e.g. 15) for high-motion or HDR material; raise it (e.g. 22) for smaller files.
- **Dimensions preferred over duration.** For a 4K recording, the default fontsize auto-scales to ~96pt so it reads at a glance. If the watermark looks too big or too small, pass `--fontsize` explicitly — the override skips auto-scaling.
- **Pixel format.** The script forces `yuv420p` for compatibility with QuickTime, Preview, browsers, and most chat apps. If you need a different pixel format (e.g. ProRes for editorial handoff), edit the `watermark_video` function or drop `-pix_fmt yuv420p` and specify a different `-c:v`.
- **No HDR preservation.** Re-encoding an HDR source through libx264 flattens it to SDR. Don't use this for HDR masters — watermark a separate SDR export instead.
- **Dependencies.** Requires `ffmpeg` on PATH (`brew install ffmpeg`) and `pillow` (`pip install pillow`).
- **Preserves source.** The script never modifies the source video — it reads, overlays, and writes a new file.
- **Not a security boundary.** This is a visible-trail watermark, not DRM. A determined adversary can crop, re-encode, or AI-inpaint it away. Use your cloud-storage share-link controls for actual access control.

## Chat-context heuristics

When the user says "watermark this video for Jane" or "/wmv Jane":
1. Look back in the conversation for the most recently referenced video file. Prefer the one most recently generated, exported, or read.
2. Look back for the most recently named person. If multiple, ask the user.
3. Confirm both choices with the user before running if there's any ambiguity — videos take longer to re-encode than PDFs, so it's costlier to redo.

When the user says "/wmv" with no arguments:
1. If there's an obvious source and recipient in the last few turns, propose them and run.
2. Otherwise ask which file and which person.
