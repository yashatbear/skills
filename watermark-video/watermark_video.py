#!/usr/bin/env python3
"""
Per-recipient video watermarking.

Mirrors watermark.py for video files (.mov, .mp4, .m4v, etc.):
    <recipient>  ·  <date>  ·  confidential

Pillow renders a transparent, rotated PNG at the video's native resolution.
FFmpeg overlays it on every frame and copies the audio.

Output defaults to "<source_dir>/watermarked copies/<slug>-<date>.<ext>".

Usage:
    python3 watermark_video.py <source.mov> "Jane Doe"
    python3 watermark_video.py <source.mov> "Jane Doe" --date 2026-04-09
    python3 watermark_video.py <source.mov> "Jane Doe" --color cream|grey|brown
    python3 watermark_video.py <source.mov> "Jane Doe" --fontsize 70 --opacity 0.25

Dependencies: Pillow (pip install pillow), FFmpeg on PATH.
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "cream": (237, 219, 195),   # #EDDBC3
    "grey": (128, 128, 128),
    "brown": (51, 32, 17),       # #332011
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}

DEFAULT_COLOR = "cream"
DEFAULT_OPACITY = 0.22
DEFAULT_FONTSIZE = 48   # Sized for 1080p; auto-scales with video height.
DEFAULT_ROTATION = 45
DEFAULT_CRF = 18
DEFAULT_PRESET = "medium"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def find_font() -> str:
    for c in FONT_CANDIDATES:
        if Path(c).exists():
            return c
    raise RuntimeError(
        "No suitable font found. Install Helvetica or Arial, or edit FONT_CANDIDATES."
    )


def probe_dimensions(src: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(src),
        ],
        check=True, capture_output=True, text=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def render_watermark_png(
    width: int,
    height: int,
    text: str,
    color: tuple,
    opacity: float,
    fontsize: int,
    rotation: int,
    font_path: str,
) -> Image.Image:
    """Transparent RGBA canvas the size of the video, with rotated text centered."""
    font = ImageFont.truetype(font_path, fontsize)

    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = measure.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Pad so rotated corners don't get clipped on the tight canvas.
    pad = max(20, fontsize // 2)
    tight = Image.new("RGBA", (text_w + 2 * pad, text_h + 2 * pad), (0, 0, 0, 0))
    alpha = int(round(opacity * 255))
    ImageDraw.Draw(tight).text(
        (pad - bbox[0], pad - bbox[1]),
        text,
        font=font,
        fill=color + (alpha,),
    )

    rotated = tight.rotate(rotation, expand=True, resample=Image.BICUBIC)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rx, ry = rotated.size
    canvas.paste(rotated, ((width - rx) // 2, (height - ry) // 2), rotated)
    return canvas


def watermark_video(src: Path, dest: Path, png_path: Path, crf: int, preset: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-i", str(png_path),
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto",
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(dest),
    ]
    subprocess.run(cmd, check=True)


def scale_fontsize(fontsize: int, height: int, user_override: bool) -> int:
    """Scale the default fontsize relative to 1080p; leave user overrides alone."""
    if user_override:
        return fontsize
    return max(24, round(fontsize * height / 1080))


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("src", help="Source video path (.mov, .mp4, etc.)")
    p.add_argument("recipient", help='Recipient name, e.g. "Jane Doe"')
    p.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date (default: today)")
    p.add_argument("--out", help="Output directory (default: <src_dir>/watermarked copies/)")
    p.add_argument("--color", default=DEFAULT_COLOR, choices=list(COLORS.keys()),
                   help=f"Watermark color (default: {DEFAULT_COLOR})")
    p.add_argument("--opacity", type=float, default=DEFAULT_OPACITY,
                   help=f"Fill opacity 0-1 (default: {DEFAULT_OPACITY})")
    p.add_argument("--fontsize", type=int, default=None,
                   help=f"Font size in points at 1080p; auto-scales otherwise (default: {DEFAULT_FONTSIZE})")
    p.add_argument("--rotation", type=int, default=DEFAULT_ROTATION,
                   help=f"Rotation in degrees (default: {DEFAULT_ROTATION})")
    p.add_argument("--crf", type=int, default=DEFAULT_CRF,
                   help=f"H.264 CRF quality, lower=higher quality (default: {DEFAULT_CRF})")
    p.add_argument("--preset", default=DEFAULT_PRESET,
                   help=f"H.264 encoding preset (default: {DEFAULT_PRESET})")
    args = p.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.exists():
        print(f"Source video not found: {src}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out).expanduser().resolve() if args.out else src.parent / "watermarked copies"
    dest = out_dir / f"{slugify(args.recipient)}-{args.date}{src.suffix}"

    width, height = probe_dimensions(src)
    user_override = args.fontsize is not None
    fontsize = scale_fontsize(args.fontsize or DEFAULT_FONTSIZE, height, user_override)
    text = f"{args.recipient}  ·  {args.date}  ·  confidential"

    png = render_watermark_png(
        width=width,
        height=height,
        text=text,
        color=COLORS[args.color],
        opacity=args.opacity,
        fontsize=fontsize,
        rotation=args.rotation,
        font_path=find_font(),
    )

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        png_path = Path(tmp.name)
    png.save(png_path)

    try:
        watermark_video(src, dest, png_path, crf=args.crf, preset=args.preset)
    finally:
        png_path.unlink(missing_ok=True)

    print(dest)


if __name__ == "__main__":
    main()
