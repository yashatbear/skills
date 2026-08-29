#!/usr/bin/env bash
# finalize.sh — turn an artifact authored with *external* references into a single
# fully self-contained HTML file, without the giant asset bytes ever passing through
# an agent's token stream.
#
# The `artifact` skill requires a fully self-contained deliverable (all CSS/JS inline,
# images as data: URIs). But *authoring* that way is slow and token-heavy: a 400 KB
# base64 image or a 150-line re-typed stylesheet is expensive for the model to emit
# and pathological to Edit (line-addressing a 160 000-char line). So author small —
# reference assets by path — then run this once to inline everything for the handoff:
#
#   <link rel="stylesheet" href="artifact.css">   ->  <style> …file contents… </style>
#   @import "base.css"  (inside CSS, recursive)   ->  imported CSS spliced in place
#   <img  src="assets/chart.png">                 ->  <img src="data:image/png;base64,…">
#   <img srcset="a.png 1x, b.png 2x"> / <source>  ->  each candidate URL -> data: URI
#   <script src="app.js"></script>                ->  <script> …file contents… </script>
#   url(assets/bg.png)  (inside CSS)              ->  url(data:image/png;base64,…)
#
# Paths resolve relative to the HTML file's own directory. Anything already inline or
# remote (data:, http(s)://, //, protocol-relative) is left untouched, so it's safe to
# run repeatedly (idempotent) and safe on an already-self-contained file (a no-op).
#
# Usage:
#   bash finalize.sh page.html                 # rewrite page.html in place (self-contained)
#   bash finalize.sh page.html -o out.html     # write a new file, leave the source alone
#   bash finalize.sh page.html --stdout        # print to stdout, touch nothing
#   bash finalize.sh --check page.html         # report external refs, change nothing (exit 3 if any)
#
# Call it by hand to produce a portable single file (to email or archive) or to
# preview the inlined result before hand-off.
set -euo pipefail

MODE="inplace"; OUT=""; FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o|--out) OUT="${2:?-o needs a path}"; MODE="out"; shift 2 ;;
    --stdout) MODE="stdout"; shift ;;
    --check)  MODE="check"; shift ;;
    -h|--help) sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *)  FILE="$1"; shift ;;
  esac
done
[ -n "$FILE" ] || { echo "usage: finalize.sh <file.html> [-o out.html | --stdout | --check]" >&2; exit 1; }
[ -f "$FILE" ] || { echo "no such file: $FILE" >&2; exit 1; }

FIN_DIR="$(cd "$(dirname "$FILE")" && pwd)" \
FIN_BASE="$(basename "$FILE")" \
FIN_MODE="$MODE" \
FIN_OUT="$OUT" \
python3 <<'PY'
import base64, os, re, sys

d    = os.environ["FIN_DIR"]
base = os.environ["FIN_BASE"]
mode = os.environ["FIN_MODE"]
out  = os.environ.get("FIN_OUT") or ""
src_path = os.path.join(d, base)
html = open(src_path, "r", encoding="utf-8").read()

MIME = {
    # images
    ".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".gif":"image/gif",
    ".webp":"image/webp", ".svg":"image/svg+xml", ".ico":"image/x-icon",
    ".avif":"image/avif", ".bmp":"image/bmp",
    # fonts (CSP allows font-src data:)
    ".woff2":"font/woff2", ".woff":"font/woff", ".ttf":"font/ttf", ".otf":"font/otf",
    ".eot":"application/vnd.ms-fontobject",
    # audio / video (CSP allows media-src data:)
    ".mp4":"video/mp4", ".webm":"video/webm", ".ogg":"video/ogg",
    ".mp3":"audio/mpeg", ".m4a":"audio/mp4", ".wav":"audio/wav",
}

def is_remote(u):
    u = u.strip()
    return (u.startswith("data:") or u.startswith("http://") or u.startswith("https://")
            or u.startswith("//") or u.startswith("#") or u.startswith("mailto:")
            or u.startswith("blob:"))

# Everything inlined must live inside the artifact's own directory tree. Reject
# absolute paths (/etc/…, /Users/…) and any ref that escapes the root via ../, so
# finalize can't be tricked into embedding an arbitrary local file into a shared
# artifact.
_ROOT = os.path.realpath(d)

def resolve(u, base_dir=None):
    """(abs_path|None, reason). reason: ok|absolute|escape|missing|bare."""
    base_dir = d if base_dir is None else base_dir
    p = u.split("?", 1)[0].split("#", 1)[0].strip()
    if not p:
        return None, "bare"
    if os.path.isabs(p):
        return None, "absolute"
    fp = os.path.realpath(os.path.join(base_dir, p))
    if fp != _ROOT and not fp.startswith(_ROOT + os.sep):
        return None, "escape"
    if not os.path.isfile(fp):
        return None, "missing"
    return fp, "ok"

changed = []
missing = []
unsafe = []

def _note_bad(u, reason):
    (unsafe if reason in ("absolute", "escape") else missing).append(u)

def read_bytes(u, base_dir=None):
    fp, reason = resolve(u, base_dir)
    if fp is None:
        _note_bad(u, reason); return None
    with open(fp, "rb") as f:
        return f.read()

def read_text(u, base_dir=None):
    b = read_bytes(u, base_dir)
    return None if b is None else b.decode("utf-8", "replace")

# process_css fully inlines a stylesheet's text: it expands @imports AND resolves
# url() — each relative to the directory of the file it appears in (CSS semantics),
# so a linked sheet or import in a subdir pulls its own assets correctly. Remote/data
# refs are left alone; an @import cycle drops the re-import; a media-qualified
# "@import 'x.css' screen" is wrapped in the matching @media block. Without this an
# @import (and any url() it carries) survives inlining and then fails offline
# (the artifact makes no network requests).
_IMPORT_RE = re.compile(
    r'@import\s+(?:url\(\s*)?["\']?([^"\')\s;]+)["\']?\s*\)?\s*([^;]*);', re.I)
_URL_RE = re.compile(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', re.I)
_import_seen = set()

def _resolve_css_urls(css, css_dir):
    def repl(m):
        quote, url = m.group(1) or "", m.group(2)
        if is_remote(url):
            return m.group(0)
        ext = os.path.splitext(url.split("?",1)[0].split("#",1)[0])[1].lower()
        mime = MIME.get(ext)
        if not mime:
            return m.group(0)
        raw = read_bytes(url, css_dir)
        if raw is None:
            return m.group(0)
        b64 = base64.b64encode(raw).decode("ascii")
        changed.append(("css-url", url))
        return "url(%sdata:%s;base64,%s%s)" % (quote, mime, b64, quote)
    return _URL_RE.sub(repl, css)

def expand_imports(css, css_dir):
    def repl(m):
        target, media = m.group(1), (m.group(2) or "").strip()
        if is_remote(target):
            return m.group(0)
        fp, reason = resolve(target, css_dir)
        if fp is None:
            _note_bad(target, reason)
            return m.group(0)
        if fp in _import_seen:      # cycle → drop the re-import
            return ""
        _import_seen.add(fp)
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            inner = process_css(f.read(), os.path.dirname(fp))
        changed.append(("css-import", target))
        return "@media %s {\n%s\n}" % (media, inner) if media else inner
    return _IMPORT_RE.sub(repl, css)

def process_css(css, css_dir):
    return _resolve_css_urls(expand_imports(css, css_dir), css_dir)

# 1) <link rel="stylesheet" href="local.css"> -> inline <style>
def repl_link(m):
    tag = m.group(0)
    rel = re.search(r'rel\s*=\s*["\']([^"\']*)["\']', tag, re.I)
    if not rel or "stylesheet" not in rel.group(1).lower():
        return tag
    href = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
    if not href or is_remote(href.group(1)):
        return tag
    css = read_text(href.group(1))
    if css is None:
        return tag
    # Fully inline (imports + url()) relative to the stylesheet's own directory.
    fp, _ = resolve(href.group(1))
    css = process_css(css, os.path.dirname(fp))
    changed.append(("css", href.group(1)))
    media = re.search(r'media\s*=\s*["\']([^"\']+)["\']', tag, re.I)
    open_tag = '<style media="%s">' % media.group(1) if media else "<style>"
    return "%s\n%s\n</style>" % (open_tag, css)

html = re.sub(r'<link\b[^>]*>', repl_link, html, flags=re.I)

# 1b) authored <style> block -> expand @import + inline url() (relative to page dir).
def repl_style_imports(m):
    return "%s%s%s" % (m.group(1), process_css(m.group(2), d), m.group(3))

html = re.sub(r'(<style\b[^>]*>)(.*?)(</style>)', repl_style_imports, html, flags=re.I | re.S)

# 2) <script src="local.js"></script> -> inline <script>
def repl_script(m):
    open_tag, close = m.group(1), m.group(2)
    s = re.search(r'src\s*=\s*["\']([^"\']+)["\']', open_tag, re.I)
    if not s or is_remote(s.group(1)):
        return m.group(0)
    js = read_text(s.group(1))
    if js is None:
        return m.group(0)
    changed.append(("js", s.group(1)))
    cleaned = re.sub(r'\s+src\s*=\s*["\'][^"\']+["\']', "", open_tag, flags=re.I)
    return "%s\n%s\n%s" % (cleaned, js, close)

html = re.sub(r'(<script\b[^>]*>)\s*(</script>)', repl_script, html, flags=re.I)

# 3) src="local.img" -> data: URI
def repl_src(m):
    whole, attr, url = m.group(0), m.group(1), m.group(2)
    if is_remote(url):
        return whole
    ext = os.path.splitext(url.split("?",1)[0].split("#",1)[0])[1].lower()
    mime = MIME.get(ext)
    if not mime:
        return whole
    raw = read_bytes(url)
    if raw is None:
        return whole
    b64 = base64.b64encode(raw).decode("ascii")
    changed.append(("img", url))
    return '%s="data:%s;base64,%s"' % (attr, mime, b64)

html = re.sub(r'\b(src)\s*=\s*["\']([^"\']+)["\']', repl_src, html, flags=re.I)

# 3b) srcset="a.png 1x, b.png 2x" (on <img> and <picture><source>) -> data: URIs.
# Each comma-separated candidate is "URL [descriptor]"; inline the URL, keep the
# descriptor. Without this a responsive image leaks external refs under the CSP.
def _inline_one(url):
    if is_remote(url):
        return None
    ext = os.path.splitext(url.split("?",1)[0].split("#",1)[0])[1].lower()
    mime = MIME.get(ext)
    if not mime:
        return None
    raw = read_bytes(url)
    if raw is None:
        return None
    changed.append(("srcset", url))
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))

def repl_srcset(m):
    attr, val = m.group(1), m.group(2)
    out = []
    for cand in val.split(","):
        parts = cand.strip().split(None, 1)
        if not parts:
            continue
        inlined = _inline_one(parts[0])
        url = inlined if inlined else parts[0]
        out.append(url + ((" " + parts[1]) if len(parts) > 1 else ""))
    return '%s="%s"' % (attr, ", ".join(out))

html = re.sub(r'\b(srcset)\s*=\s*["\']([^"\']+)["\']', repl_srcset, html, flags=re.I)

# 4) url(local.img) inside styles -> data: URI
def repl_cssurl(m):
    quote, url = m.group(1) or "", m.group(2)
    if is_remote(url):
        return m.group(0)
    ext = os.path.splitext(url.split("?",1)[0].split("#",1)[0])[1].lower()
    mime = MIME.get(ext)
    if not mime:
        return m.group(0)
    raw = read_bytes(url)
    if raw is None:
        return m.group(0)
    b64 = base64.b64encode(raw).decode("ascii")
    changed.append(("css-url", url))
    return "url(%sdata:%s;base64,%s%s)" % (quote, mime, b64, quote)

html = re.sub(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', repl_cssurl, html, flags=re.I)

def uniq(seq):
    seen=set(); out=[]
    for x in seq:
        if x not in seen: seen.add(x); out.append(x)
    return out
changed_refs = uniq([r for _, r in changed])
missing = uniq(missing)
unsafe = uniq(unsafe)

for r in missing:
    sys.stderr.write("finalize: local ref not found, left as-is: %s\n" % r)
for r in unsafe:
    sys.stderr.write("finalize: refusing unsafe ref (absolute path or outside the "
                     "artifact dir), left as-is: %s\n" % r)

if mode == "check":
    # A finalized file is publish-safe only if NOTHING external local remains:
    # inlinable-but-present refs (shouldn't happen post-finalize), missing refs
    # (would 404 offline / under the CSP), and unsafe refs (rejected by policy).
    leftover = changed_refs + [x for x in (missing + unsafe) if x not in changed_refs]
    if leftover:
        sys.stderr.write("finalize --check: %d external local ref(s) remain: %s\n"
                         % (len(leftover), ", ".join(leftover)))
        sys.exit(3)
    sys.exit(0)

sys.stderr.write("finalize: inlined %d reference(s)%s%s%s\n" % (
    len(changed),
    (" (%s)" % ", ".join(changed_refs)) if changed_refs else "",
    ("; %d missing" % len(missing)) if missing else "",
    ("; %d unsafe skipped" % len(unsafe)) if unsafe else "",
))

if mode == "stdout":
    sys.stdout.write(html)
elif mode == "out":
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    sys.stderr.write("finalize: wrote %s\n" % out)
else:  # inplace
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(html)
PY
