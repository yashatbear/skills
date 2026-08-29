#!/usr/bin/env bash
# verify.sh — render an artifact with the `browse` skill and print the PNGs, so the
# agent can Read them before handing the page over.
#
# Why this exists: an artifact is a *visual* deliverable, so "the HTML looks right"
# is not verification — you have to look at the rendered page. Two constraints shape
# how:
#
#   1. **Headless only.** The headless `browse` Chromium is what does the rendering;
#      a *GUI* browser window is for a human's eyes, not an agent's self-check. Never
#      `screencapture` or screen-record a window to check your own work — it grabs
#      whatever else is on screen and drives the GUI.
#   2. **`browse` blocks `file://`** (http/https only), so the page is finalized into
#      one self-contained file and served over loopback http.
#
# What it does:
#   finalize.sh -> temp self-contained copy  (assets inlined; one file, renders as shipped)
#   python3 -m http.server --bind 127.0.0.1 --directory <that dir>   (torn down on exit)
#   browse: viewport, goto, screenshot  (light; then dark via a CSSOM media flip)
#   measure the laid-out DOM -> one `verify: layout ...` line on stderr
#   run agents-block.sh --check -> one `verify: structure ...` line on stderr
#   print the PNG paths
#
# Dark mode: `browse` has no `prefers-color-scheme` emulation, so this flips every
# `@media (prefers-color-scheme: dark)` block to `all` via CSSOM — same rules, same
# cascade, no page edits. Skipped with a note if the page has no dark block.
#
# Usage:
#   bash verify.sh page.html                       # light + dark @ 1200x900
#   bash verify.sh page.html --viewport 390x844    # phone-width check
#   bash verify.sh page.html --light-only
#   bash verify.sh page.html --out ~/some/dir      # where the PNGs land (default: mktemp -d)
#   bash verify.sh page.html --host <hostname>     # render on a remote host over ssh
#
# Prints one PNG path per line on stdout. **Read every PNG it prints** — running it
# and not looking at the output is not verification.
#
# It also prints one `verify: layout ...` line on stderr — viewport, documentElement
# scrollWidth/clientWidth, the max-width container (or MISSING) and its computed width,
# and any element wider than the viewport. **Read that line too**, especially after a
# structural edit: a screenshot catches styling, measurement catches structure. A page
# that lost its wrapper looks like "slightly wide cards" in a downscaled PNG and like
# `container=MISSING` here.
#
# And one `verify: structure ...` line — the result of `agents-block.sh --check`, which
# fires here because agents already run verify.sh after an edit. Every operation on an
# artifact has to hold the standard structure (see the `artifact` skill), so this is the
# automatic reminder. It is REPORTING ONLY: verify.sh is a rendering tool and callers
# depend on its exit status, so a shape failure never changes it. `agents-block.sh
# --check` is the gate that exits 4 — run it directly before you hand the page over.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIEWPORT="1200x900"; OUTDIR=""; FILE=""; DARK=1
HOST="${ARTIFACT_VERIFY_HOST:-}"      # empty = render locally

while [ $# -gt 0 ]; do
  case "$1" in
    --viewport) VIEWPORT="${2:?--viewport needs WxH}"; shift 2 ;;
    --out)      OUTDIR="${2:?--out needs a dir}"; shift 2 ;;
    --host)     HOST="${2:?--host needs a hostname}"; shift 2 ;;
    --light-only) DARK=0; shift ;;
    -h|--help)  sed -n '2,50p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *)  FILE="$1"; shift ;;
  esac
done
[ -n "$FILE" ] || { echo "usage: verify.sh <page.html> [--viewport WxH] [--light-only] [--out dir] [--host h]" >&2; exit 1; }
[ -f "$FILE" ] || { echo "verify: no such file: $FILE" >&2; exit 1; }
[[ "$VIEWPORT" =~ ^[0-9]+x[0-9]+$ ]] || { echo "verify: --viewport must be WxH, got: $VIEWPORT" >&2; exit 1; }

OUTDIR="${OUTDIR:-$(mktemp -d)}"; mkdir -p "$OUTDIR"
# Drop shots from a previous run into the same --out dir: a page that lost its dark
# block would otherwise print a stale dark.png as if it were current.
rm -f "$OUTDIR/light.png" "$OUTDIR/dark.png"
BASE="$(basename "${FILE%.html}" | tr -c 'A-Za-z0-9._-' '-')"
RUN="$BASE-$$"

# Self-contained copy — one file to serve, and it renders exactly as the deliverable.
LOCAL_TMP="$(mktemp -d)"
trap 'rm -rf "$LOCAL_TMP"' EXIT
bash "$HERE/finalize.sh" "$FILE" -o "$LOCAL_TMP/page.html" >/dev/null

# The render step, run identically whether it executes here or over ssh. Takes the
# serve dir + shot dir as $1/$2 so the remote copy can use the host's own paths.
RENDER_SCRIPT=$(cat <<'RENDER'
set -euo pipefail
SERVE_DIR="$1"; SHOT_DIR="$2"; VIEWPORT="$3"; DARK="$4"; RUN="$5"
export PATH="$HOME/.bun/bin:$PATH"          # dist/browse shells out to bun

# The browse runtime lives in different places per host (see the browse skill).
for c in "${BROWSE_BIN:-}" \
         ".claude/skills/browse/dist/browse" \
         "$HOME/.claude/skills/browse/dist/browse"; do
  [ -n "$c" ] && [ -x "$c" ] && [ -d "$(dirname "$c")/../node_modules" ] && { B="$c"; break; }
done
[ -n "${B:-}" ] || { echo "verify: browse runtime not found — see Setup in the browse skill" >&2; exit 1; }

DARK_JS='[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}}).filter(r=>r.media&&r.conditionText&&r.conditionText.includes("prefers-color-scheme: dark")).map(r=>{r.media.mediaText="all";return 1}).length'
export BROWSE_STATE_FILE="/tmp/browse-artifact-$RUN/browse.json"   # own server, no crosstalk

# browse refuses to write a screenshot outside /tmp or its cwd, so shoot into /tmp
# and copy out afterwards.
SHOT_TMP="/tmp/artifact-verify-$RUN"; mkdir -p "$SHOT_TMP"

PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
# --directory is explicit: a backgrounded server does not reliably inherit the cwd
# of the shell that spawned it.
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$SERVE_DIR" >/dev/null 2>&1 &
SRV=$!
disown $SRV 2>/dev/null || true              # keeps teardown from printing "Terminated"
trap 'kill $SRV 2>/dev/null || true; "$B" stop >/dev/null 2>&1 || true; rm -rf "$SHOT_TMP"' EXIT
for _ in $(seq 20); do curl -sf -o /dev/null "http://127.0.0.1:$PORT/page.html" && break; sleep 0.2; done

"$B" viewport "$VIEWPORT" >/dev/null
"$B" goto "http://127.0.0.1:$PORT/page.html" >/dev/null
"$B" screenshot "$SHOT_TMP/light.png" >/dev/null

# Layout measurement — a screenshot catches styling, not structure. A page that lost
# its max-width wrapper (e.g. a section reorder that dropped the container's open tag)
# renders as "slightly wide cards" in a downscaled PNG but is obvious here.
MEASURE_JS='(()=>{const d=document.documentElement,vw=d.clientWidth;
const w=document.querySelector("main,.wrap,.container,.page,body>div");
const wid=w?Math.round(w.getBoundingClientRect().width):null;
const mx=w?getComputedStyle(w).maxWidth:null;
const over=[...document.body.querySelectorAll("*")].filter(e=>e.getBoundingClientRect().width>vw+1)
  .slice(0,5).map(e=>e.tagName.toLowerCase()+(e.className&&typeof e.className==="string"?"."+e.className.trim().split(/\s+/)[0]:"")+"@"+Math.round(e.getBoundingClientRect().width));
return `vw=${vw} scrollW=${d.scrollWidth} clientW=${d.clientWidth} container=${w?w.tagName.toLowerCase()+(w.className&&typeof w.className==="string"?"."+w.className.trim().split(/\s+/)[0]:""):"MISSING"} width=${wid} max-width=${mx} overflowing=[${over.join(", ")}]`})()'
echo "verify: layout $("$B" js "$MEASURE_JS" 2>/dev/null | tr -d '\r')" >&2

if [ "$DARK" = "1" ]; then
  n="$("$B" js "$DARK_JS" | tr -dc '0-9')"
  if [ "${n:-0}" -gt 0 ]; then
    "$B" screenshot "$SHOT_TMP/dark.png" >/dev/null
  else
    echo "verify: no @media (prefers-color-scheme: dark) block found — dark shot skipped" >&2
  fi
fi

mkdir -p "$SHOT_DIR"
cp "$SHOT_TMP"/*.png "$SHOT_DIR"/
RENDER
)

if [ -z "$HOST" ]; then
  bash -c "$RENDER_SCRIPT" _ "$LOCAL_TMP" "$OUTDIR" "$VIEWPORT" "$DARK" "$RUN"
else
  # Remote: ship the one file, render there, pull the PNGs back. The remote login
  # shell is zsh, so the whole render script goes over stdin and only simple scalars
  # ride on the command line.
  REMOTE_DIR="tmp/artifact-verify/$RUN"
  ssh "$HOST" "mkdir -p ~/$REMOTE_DIR" >/dev/null
  scp -q "$LOCAL_TMP/page.html" "$HOST:~/$REMOTE_DIR/page.html"
  # Double quotes so the remote shell expands $HOME (single quotes would pass it literal).
  ssh "$HOST" "bash -s -- \"\$HOME/$REMOTE_DIR\" \"\$HOME/$REMOTE_DIR\" '$VIEWPORT' '$DARK' '$RUN'" <<<"$RENDER_SCRIPT"
  scp -q "$HOST:~/$REMOTE_DIR/*.png" "$OUTDIR/" 2>/dev/null || true
  ssh "$HOST" "rm -rf ~/$REMOTE_DIR /tmp/browse-artifact-$RUN" >/dev/null 2>&1 || true
fi

# ── Structure check — reported, never fatal ───────────────────────────────────
# Fires here because agents already run verify.sh after an edit, and the standard
# structure binds every operation on an artifact, not just publishing. Checked against
# the AUTHORED file (not the finalized copy) — that's the one you'd fix.
#
# This never changes verify.sh's exit status: it renders pages, and callers depend on
# that status meaning "the render worked". `agents-block.sh --check` is the gate.
if [ -r "$HERE/agents-block.sh" ]; then
  set +e
  SHAPE_OUT="$(bash "$HERE/agents-block.sh" --check "$FILE" 2>&1 >/dev/null)"
  SHAPE_RC=$?
  set -e
  if [ "$SHAPE_RC" -eq 0 ]; then
    echo "verify: structure ok (agents-block.sh --check -> 0)" >&2
    # An exempt `type:` or a live waiver comes back on stderr with rc 0 — surface it,
    # so "ok" never quietly means "the checks were skipped".
    if [ -n "$SHAPE_OUT" ]; then
      printf '%s\n' "$SHAPE_OUT" | sed 's/^/verify:   /' >&2
    fi
  else
    echo "verify: structure FAIL (agents-block.sh --check -> $SHAPE_RC) *** THIS ARTIFACT IS NOT FINISHED ***" >&2
    printf '%s\n' "$SHAPE_OUT" | sed 's/^/verify:   /' >&2
    echo "verify:   ^ fix the page and re-run. verify.sh does not fail on this — it only renders;" >&2
    echo "verify:     \`bash agents-block.sh --check '$FILE'\` is the gate, and it exits $SHAPE_RC." >&2
  fi
fi

SHOTS=()
for s in "$OUTDIR/light.png" "$OUTDIR/dark.png"; do [ -f "$s" ] && SHOTS+=("$s"); done
[ ${#SHOTS[@]} -gt 0 ] || { echo "verify: no screenshots came back" >&2; exit 1; }
printf '%s\n' "${SHOTS[@]}"
