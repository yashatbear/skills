#!/usr/bin/env bash
# sf-icons.sh — emit self-contained CSS for genuine SF Symbols as recolorable
# mask-image icons, for `artifact` skill HTML pages.
#
# Renders each named SF Symbol (via macOS AppKit / SF Symbols.app) to a high-res
# alpha PNG, then prints `.sf-<name>{ mask-image:url(data:image/png;base64,…) }`
# plus a base `.sf` rule. The icon is painted with `background: currentColor`, so
# it recolors to the element's text color — theme-aware (light/dark) for free and
# no external assets. This keeps the page fully self-contained (no fonts/CDNs),
# which the hand-drawn-SVG or emoji alternatives can't match with real Apple glyphs.
#
# Caching: rendered PNGs are memoized under `icons-cache/<weight>-<pt>/<name>.png`
# (in this skill dir). The common set is committed, so the usual symbols emit
# instantly with no `swift`/AppKit render at all — `swift` is only invoked for
# symbols not already in the cache, and each freshly rendered symbol is written
# back into the cache (and can be committed to grow the shared set). Because
# cached symbols need no render, the script also runs on machines without Xcode
# CLT `swift` as long as every requested symbol is already cached.
#
# Usage:
#   bash sf-icons.sh lock bolt paperplane.fill eye link            > icons.css
#   bash sf-icons.sh --weight semibold --pt 200 gearshape          >> icons.css
#   bash sf-icons.sh --no-base trash                               # skip base .sf rule
#   bash sf-icons.sh --no-cache lock                               # ignore + don't write cache
#
# Then paste icons.css into the page's <style> and use:
#   <span class="sf sf-lock" style="width:20px;height:20px"></span>
#   /* color inherits from the element or a parent: set `color:` to tint it */
#
# Notes
# - Names are exact SF Symbols identifiers (browse them in SF Symbols.app). Dots are
#   kept on input; the CSS class replaces them with hyphens
#   (paperplane.fill -> .sf-paperplane-fill). Prefer outline names for a light look,
#   `.fill` variants where a solid glyph reads better (e.g. paperplane.fill, pin.fill).
# - Missing/renamed symbols are reported on stderr and left as a `/* MISSING */`
#   comment rather than failing the whole run.
# - macOS only; needs the SF Symbols app installed + Xcode CLT `swift`
#   — but only when a requested symbol isn't already cached.
# - Weight is the symbol weight, one of: ultralight thin light regular medium
#   semibold bold heavy black (default regular). --pt is the render size in points
#   (default 160 — plenty crisp for icons shown at <=32px via mask-size:contain).
set -euo pipefail

WEIGHT="regular"; PT="160"; BASE=1; CACHE=1; NAMES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --weight)  WEIGHT="${2:?--weight needs a value}"; shift 2 ;;
    --pt)      PT="${2:?--pt needs a value}"
               [[ "$PT" =~ ^[0-9]+$ ]] || { echo "--pt must be an integer" >&2; exit 1; }; shift 2 ;;
    --no-base) BASE=0; shift ;;
    --no-cache) CACHE=0; shift ;;
    -h|--help) sed -n '2,45p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *)  # SF Symbol names are [a-z0-9.] only; reject anything else so a name
        # can't carry a path separator (`/`, `..`) into the PNG filename below.
        [[ "$1" =~ ^[A-Za-z0-9.]+$ ]] || { echo "invalid symbol name: '$1' (allowed: letters, digits, dots)" >&2; exit 1; }
        NAMES+=("$1"); shift ;;
  esac
done
[ "${#NAMES[@]}" -gt 0 ] || { echo "no symbol names given (see --help)" >&2; exit 1; }
# WEIGHT is interpolated into the cache path below, so restrict it to the known set
# (this is also exactly the set the swift renderer understands) — a stray value like
# `../x` must never let the cache dir escape icons-cache/.
case " ultralight thin light regular medium semibold bold heavy black " in
  *" $WEIGHT "*) ;;
  *) echo "invalid --weight: '$WEIGHT' (one of: ultralight thin light regular medium semibold bold heavy black)" >&2; exit 1 ;;
esac

# Resolve the skill dir even when invoked through the ~/.claude/skills symlink, so
# the on-disk cache is always the committed one in the repo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Cache is keyed by (weight, pt) — the render config that changes the pixels — then name.
CACHE_SUB="$SCRIPT_DIR/icons-cache/$WEIGHT-$PT"
[ "$CACHE" = 1 ] && mkdir -p "$CACHE_SUB"

# safe_name: SF name -> filename/class-safe token (dots -> hyphens). The CLI already
# restricts names to [A-Za-z0-9.], so this can't produce a path separator.
safe_name() { printf '%s' "${1//./-}"; }

# Split requested names into cache hits vs. those we still need to render.
TO_RENDER=()
for name in "${NAMES[@]}"; do
  safe="$(safe_name "$name")"
  if [ "$CACHE" = 1 ] && [ -f "$CACHE_SUB/$safe.png" ]; then continue; fi
  TO_RENDER+=("$name")
done

TMP=""
# Only pay for swift/AppKit when something isn't cached.
if [ "${#TO_RENDER[@]}" -gt 0 ]; then
  command -v swift >/dev/null 2>&1 || {
    echo "swift (Xcode Command Line Tools) not found — needed to render: ${TO_RENDER[*]}" >&2
    exit 1
  }
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  printf '%s\n' "${TO_RENDER[@]}" > "$TMP/names.txt"

  # Render each uncached symbol to a black-on-transparent alpha PNG (alpha = glyph
  # coverage, which is all a CSS mask needs).
  SFDIR="$TMP" SFWEIGHT="$WEIGHT" SFPT="$PT" swift - <<'SWIFT'
import AppKit
let env = ProcessInfo.processInfo.environment
let dir = env["SFDIR"]!
let weights: [String: NSFont.Weight] = [
  "ultralight":.ultraLight,"thin":.thin,"light":.light,"regular":.regular,
  "medium":.medium,"semibold":.semibold,"bold":.bold,"heavy":.heavy,"black":.black]
let weight = weights[env["SFWEIGHT"] ?? "regular"] ?? .regular
let pt = CGFloat(Double(env["SFPT"] ?? "160") ?? 160)
let names = (try! String(contentsOfFile: dir + "/names.txt", encoding: .utf8))
  .split(separator: "\n").map(String.init)
func warn(_ s: String) { FileHandle.standardError.write((s + "\n").data(using: .utf8)!) }
for name in names {
  guard let base = NSImage(systemSymbolName: name, accessibilityDescription: nil) else {
    warn("MISSING SF Symbol: \(name)"); continue
  }
  let cfg = NSImage.SymbolConfiguration(pointSize: pt, weight: weight)
  guard let img = base.withSymbolConfiguration(cfg) else { warn("no config: \(name)"); continue }
  let s = img.size
  let w = Int(ceil(s.width)), h = Int(ceil(s.height))
  guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0) else { continue }
  rep.size = s
  NSGraphicsContext.saveGraphicsState()
  NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
  NSColor.black.set()
  img.draw(at: .zero, from: NSRect(origin: .zero, size: s), operation: .sourceOver, fraction: 1.0)
  NSGraphicsContext.restoreGraphicsState()
  guard let png = rep.representation(using: .png, properties: [:]) else { continue }
  // Defence in depth: the CLI already restricts names to [A-Za-z0-9.], but keep the
  // filename to a safe charset so it can never escape `dir` even if that changes.
  let allowed = Set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
  let safe = String(name.replacingOccurrences(of: ".", with: "-").map { allowed.contains($0) ? $0 : "-" })
  try! png.write(to: URL(fileURLWithPath: dir).appendingPathComponent(safe + ".png"))
}
SWIFT

  # Move freshly rendered PNGs into the cache (or, with --no-cache, keep them in TMP
  # and emit straight from there). A genuinely missing symbol produced no file.
  if [ "$CACHE" = 1 ]; then
    for name in "${TO_RENDER[@]}"; do
      safe="$(safe_name "$name")"
      [ -f "$TMP/$safe.png" ] && mv -f "$TMP/$safe.png" "$CACHE_SUB/$safe.png"
    done
  fi
fi

if [ "$BASE" = 1 ]; then
  cat <<'CSS'
.sf{display:inline-block;vertical-align:middle;background-color:currentColor;
    -webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;
    -webkit-mask-position:center;mask-position:center;
    -webkit-mask-size:contain;mask-size:contain}
CSS
fi

# Emit CSS for every requested name, reading bytes from the cache (or, under
# --no-cache, from the just-rendered TMP dir).
if [ "$CACHE" = 1 ]; then SRC="$CACHE_SUB"; else SRC="$TMP"; fi
missing=0
for name in "${NAMES[@]}"; do
  safe="$(safe_name "$name")"
  f="$SRC/$safe.png"
  if [ ! -f "$f" ]; then echo "/* MISSING SF Symbol: $name */"; missing=1; continue; fi
  b64="$(base64 < "$f" | tr -d '\n')"
  printf '.sf-%s{-webkit-mask-image:url(data:image/png;base64,%s);mask-image:url(data:image/png;base64,%s)}\n' \
    "$safe" "$b64" "$b64"
done
[ "$missing" = 0 ] || echo "sf-icons.sh: some symbols were missing — see comments above" >&2
