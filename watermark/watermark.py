#!/usr/bin/env python3
"""
Per-recipient PDF watermarking.

Overlays a diagonal watermark on every page of a PDF. The default house style
is SF Pro Bold, wide-tracked ALL CAPS, cream, dynamically sized so the line
spans the page corner-to-corner along its true diagonal:

    R E C I P I E N T   ·   2 0 2 6 - 0 6 - 1 7   ·   C O N F I D E N T I A L

Requires the SF Pro Display fonts (free from https://developer.apple.com/fonts/).
If they're not installed the script still runs but falls back to Helvetica-Bold
and prints how to install SF Pro. See SKILL.md "Font requirement".

Output defaults to "<source_dir>/watermarked copies/<slug>-<date>.pdf".

Usage:
    python3 watermark.py <source.pdf> "Jane Doe"
    python3 watermark.py <source.pdf> "Acme Partners 2026" --date 2026-06-19
    python3 watermark.py <source.pdf> "Jane Doe" --out /path/to/dir
    python3 watermark.py <source.pdf> "Jane Doe" --color cream|grey|brown
    python3 watermark.py <source.pdf> "Jane Doe" --opacity 0.25 --fill 0.88
    python3 watermark.py <source.pdf> "Jane Doe" --no-caps   # keep typed case, no tracking

Dependencies: PyMuPDF (pip install pymupdf)
"""

import argparse
import datetime as dt
import math
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
DEFAULT_OPACITY = 0.20
DEFAULT_FILL = 0.90        # fraction of the page diagonal the watermark spans
DIAGONAL_DEG = None        # None => follow the page's true corner-to-corner angle

# SF Pro Bold, searched in priority order across the standard macOS font dirs.
# SF Pro is not redistributed with this repo (Apple license); install it from
# https://developer.apple.com/fonts/ if it's missing — see install_hint().
SCRIPT_DIR = Path(__file__).resolve().parent
FONT_CANDIDATES = [
    Path.home() / "Library" / "Fonts" / "SF-Pro-Display-Bold.otf",
    Path("/Library/Fonts/SF-Pro-Display-Bold.otf"),
    SCRIPT_DIR / "fonts" / "SF-Pro-Display-Bold.otf",  # optional local override, untracked
]

INSTALL_HINT = (
    "watermark: SF Pro Display Bold not found — falling back to Helvetica-Bold.\n"
    "  For the house style, install Apple's SF Pro fonts (free):\n"
    "    1. Download 'SF Pro' from https://developer.apple.com/fonts/\n"
    "    2. Open the .dmg and run the installer (.pkg), or copy the .otf files\n"
    "       into ~/Library/Fonts/.\n"
    "  The skill auto-detects SF-Pro-Display-Bold.otf once installed.\n"
)


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def resolve_font() -> fitz.Font:
    """Return the watermark font, preferring bundled SF Pro Bold and falling
    back to the built-in Helvetica-Bold if no SF Pro file is available."""
    for p in FONT_CANDIDATES:
        if p.exists():
            return fitz.Font(fontfile=str(p))
    sys.stderr.write(INSTALL_HINT)
    return fitz.Font("hebo")  # Helvetica-Bold builtin


def widen(text: str) -> str:
    """House style: ALL CAPS with wide letter-spacing. Every glyph is separated
    by a space and words are separated by a triple space, e.g.
    'Jane Doe' -> 'J A N E   D O E'."""
    return "   ".join(" ".join(token) for token in text.upper().split())


def stamp_page(
    page: fitz.Page,
    font: fitz.Font,
    text: str,
    color: tuple,
    opacity: float,
    fill: float,
    angle_deg,
) -> None:
    """Stamp one page: size the text so it spans `fill` of the page diagonal,
    center it, and rotate it along the page's true corner-to-corner angle
    (bottom-left -> top-right) unless an explicit angle is given."""
    r = page.rect
    cx, cy = r.width / 2, r.height / 2
    diag = math.hypot(r.width, r.height)
    theta = math.radians(angle_deg) if angle_deg is not None else math.atan2(r.height, r.width)

    unit = font.text_length(text, fontsize=1.0)
    fontsize = (diag * fill) / unit
    text_len = font.text_length(text, fontsize=fontsize)
    cap = font.ascender * fontsize * 0.72  # approx cap height, for vertical centering
    origin = fitz.Point(cx - text_len / 2, cy + cap / 2)

    tw = fitz.TextWriter(r, color=color)
    tw.append(origin, text, font=font, fontsize=fontsize)
    c, s = math.cos(theta), math.sin(theta)
    # (c, s, -s, c) rotates bottom-left -> top-right in PDF's y-down space.
    matrix = fitz.Matrix(c, s, -s, c, 0, 0)
    tw.write_text(page, opacity=opacity, morph=(fitz.Point(cx, cy), matrix))


def watermark_pdf(
    src: Path,
    dest: Path,
    recipient: str,
    date: str,
    color: tuple,
    opacity: float,
    fill: float,
    caps: bool,
    angle_deg,
) -> None:
    raw = f"{recipient} · {date} · confidential"
    text = widen(raw) if caps else raw
    font = resolve_font()
    doc = fitz.open(src)
    for page in doc:
        stamp_page(page, font, text, color, opacity, fill, angle_deg)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dest, garbage=4, deflate=True)
    doc.close()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src", help="Source PDF path")
    p.add_argument("recipient", help='Recipient name or label, e.g. "Jane Doe"')
    p.add_argument("--date", default=dt.date.today().isoformat(), help="ISO date (default: today)")
    p.add_argument("--out", help="Output directory (default: <src_dir>/watermarked copies/)")
    p.add_argument("--color", default=DEFAULT_COLOR, choices=list(COLORS.keys()), help=f"Watermark color (default: {DEFAULT_COLOR})")
    p.add_argument("--opacity", type=float, default=DEFAULT_OPACITY, help=f"Fill opacity 0-1 (default: {DEFAULT_OPACITY})")
    p.add_argument("--fill", type=float, default=DEFAULT_FILL, help=f"Fraction of page diagonal the text spans (default: {DEFAULT_FILL})")
    p.add_argument("--angle", type=float, default=DIAGONAL_DEG, help="Diagonal angle in degrees (default: page's true corner angle)")
    p.add_argument("--no-caps", dest="caps", action="store_false", help="Keep recipient/text as typed (disables wide ALL-CAPS tracking)")
    # Deprecated and IGNORED. Sizing is now dynamic (use --fill) and the angle
    # follows the page's true diagonal (use --angle). Accepted only so old
    # callers don't hard-error; a warning nudges them to migrate.
    p.add_argument("--fontsize", type=int, help=argparse.SUPPRESS)
    p.add_argument("--rotation", type=int, help=argparse.SUPPRESS)
    p.set_defaults(caps=True)
    args = p.parse_args()

    if args.fontsize is not None:
        sys.stderr.write(
            "watermark: --fontsize is deprecated and ignored; sizing is dynamic. "
            "Use --fill (fraction of the page diagonal, default 0.90) to scale.\n"
        )
    if args.rotation is not None:
        sys.stderr.write(
            "watermark: --rotation is deprecated and ignored; the watermark follows "
            "the page's true diagonal. Use --angle <deg> to force a specific angle.\n"
        )

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
        fill=args.fill,
        caps=args.caps,
        angle_deg=args.angle,
    )
    print(dest)


if __name__ == "__main__":
    main()
