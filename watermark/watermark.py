#!/usr/bin/env python3
"""
Per-recipient PDF watermarking.

Overlays a diagonal watermark on every page of a PDF:
    <recipient>  ·  <date>  ·  confidential

Output defaults to "<source_dir>/watermarked copies/<slug>-<date>.pdf".

Usage:
    python3 watermark.py <source.pdf> "Jane Doe"
    python3 watermark.py <source.pdf> "Jane Doe" --date 2026-04-09
    python3 watermark.py <source.pdf> "Jane Doe" --out /path/to/dir
    python3 watermark.py <source.pdf> "Jane Doe" --color cream|grey|brown
    python3 watermark.py <source.pdf> "Jane Doe" --fontsize 70 --opacity 0.25

Dependencies: PyMuPDF (pip install pymupdf)
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF


# Preset colors. Cream reads well on dark-background decks; grey is the safe
# universal choice for mixed-background PDFs; brown for light-background decks.
COLORS = {
    "cream": (237 / 255, 219 / 255, 195 / 255),   # #EDDBC3
    "grey": (0.5, 0.5, 0.5),
    "brown": (51 / 255, 32 / 255, 17 / 255),       # #332011
    "white": (1.0, 1.0, 1.0),
    "black": (0.0, 0.0, 0.0),
}

DEFAULT_COLOR = "cream"
DEFAULT_OPACITY = 0.22
DEFAULT_FONTSIZE = 65
DEFAULT_ROTATION = 45
DEFAULT_FONTNAME = "helv"


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def compute_box(rect: fitz.Rect, text: str, fontsize: float, fontname: str) -> fitz.Rect:
    """Size a textbox that fits the text and — after 45° rotation around the
    page center — stays within the page bounds so nothing gets clipped."""
    text_width = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
    box_w = text_width + 40
    # Generous vertical room so PyMuPDF's layout never decides the line
    # doesn't fit (it needs more than just fontsize).
    box_h = fontsize * 3
    return fitz.Rect(
        (rect.width - box_w) / 2,
        (rect.height - box_h) / 2,
        (rect.width + box_w) / 2,
        (rect.height + box_h) / 2,
    )


def watermark_pdf(
    src: Path,
    dest: Path,
    recipient: str,
    date: str,
    color: tuple,
    opacity: float,
    fontsize: int,
    rotation: int,
) -> None:
    text = f"{recipient}  ·  {date}  ·  confidential"
    doc = fitz.open(src)

    for page in doc:
        rect = page.rect
        box = compute_box(rect, text, fontsize, DEFAULT_FONTNAME)
        center = fitz.Point(rect.width / 2, rect.height / 2)
        matrix = fitz.Matrix(1, 1).prerotate(rotation)

        ret = page.insert_textbox(
            box,
            text,
            fontsize=fontsize,
            fontname=DEFAULT_FONTNAME,
            color=color,
            fill_opacity=opacity,
            stroke_opacity=opacity,
            align=fitz.TEXT_ALIGN_CENTER,
            morph=(center, matrix),
            overlay=True,
        )
        if ret < 0:
            raise RuntimeError(
                f"insert_textbox failed on page {page.number}: returned {ret}. "
                f"Try a smaller --fontsize or shorter recipient/date string."
            )

    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dest, garbage=4, deflate=True)
    doc.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src", help="Source PDF path")
    p.add_argument("recipient", help='Recipient name, e.g. "Jane Doe"')
    p.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date (default: today)")
    p.add_argument("--out", help="Output directory (default: <src_dir>/watermarked copies/)")
    p.add_argument("--color", default=DEFAULT_COLOR, choices=list(COLORS.keys()), help=f"Watermark color (default: {DEFAULT_COLOR})")
    p.add_argument("--opacity", type=float, default=DEFAULT_OPACITY, help=f"Fill opacity 0-1 (default: {DEFAULT_OPACITY})")
    p.add_argument("--fontsize", type=int, default=DEFAULT_FONTSIZE, help=f"Font size in points (default: {DEFAULT_FONTSIZE})")
    p.add_argument("--rotation", type=int, default=DEFAULT_ROTATION, help=f"Rotation in degrees (default: {DEFAULT_ROTATION})")
    args = p.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.exists():
        print(f"Source PDF not found: {src}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out).expanduser().resolve() if args.out else src.parent / "watermarked copies"
    dest = out_dir / f"{slugify(args.recipient)}-{args.date}.pdf"

    watermark_pdf(
        src=src,
        dest=dest,
        recipient=args.recipient,
        date=args.date,
        color=COLORS[args.color],
        opacity=args.opacity,
        fontsize=args.fontsize,
        rotation=args.rotation,
    )
    print(dest)


if __name__ == "__main__":
    main()
