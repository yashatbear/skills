#!/usr/bin/env bash
# agents-block.sh — read the embedded AGENTS.md block out of an artifact, and
# (with --check) enforce the standard artifact structure.
#
# Every artifact carries per-page guidance for agents in a non-rendering
#   <script type="text/markdown" id="agents-md">…</script>
# block in its <head>. Read it BEFORE editing the page. See the `artifact` skill.
#
#   bash agents-block.sh page.html          # print the block
#   curl -s "$URL" | bash agents-block.sh - # print it from a fetched artifact
#   bash agents-block.sh --check page.html  # block filled in AND structure valid
#
# --check enforces, on top of "block present and no TODOs left":
#   · the block has a `## Structure` section declaring `type:` and `bottom:`
#   · type mockup|preview|explainer       -> shape checks skipped (nothing to summarise)
#   · type decision|reference             -> the page must carry an exec summary
#     (an element with id/class `exec-summary`) of 1-5 <li> bullets, each <=100 chars
#   · any exec-summary bullet stating a FIGURE needs a `## Derivations` line showing
#     where that figure computes from — the checker can't do the arithmetic, so it
#     gates writing it down, which is where a number that doesn't close shows up
#   · bottom: next-steps | open-questions  -> that element must exist, same caps
#   · bottom: none - <reason>              -> no bottom section, reason on the record
#   · every shaped artifact ends in ONE <footer> line, <=160 chars, carrying an
#     "Updated <date>" stamp: "Updated <date> - Sources: <where the numbers came from>"
#   · waiver: <reason> in `## Structure`   -> skips the shape checks entirely. OPT-IN:
#     the template ships no such line, and scaffold-looking text is rejected, so a
#     waiver only ever exists because an author deliberately wrote a real reason.
#
# Exit: 0 ok · 2 bad usage / unreadable · 3 block missing or unfilled (TODOs)
#       4 structure violation (with --check)
set -euo pipefail

CHECK=0
SRC=""
for a in "$@"; do
  case "$a" in
    --check) CHECK=1 ;;
    -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) SRC="$a" ;;
  esac
done

[ -n "$SRC" ] || { echo "usage: agents-block.sh [--check] <page.html|->" >&2; exit 2; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if [ "$SRC" = "-" ]; then
  cat > "$WORK/page.html"
  SRC="$WORK/page.html"
elif [ ! -r "$SRC" ]; then
  echo "agents-block.sh: cannot read $SRC" >&2
  exit 2
fi

cat > "$WORK/extract.py" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
m = re.search(
    r'<script\b[^>]*\bid=["\']agents-md["\'][^>]*>(.*?)</script\s*>',
    src, re.I | re.S)
if not m:
    sys.exit(3)
# <script> is a raw-text element: the HTML parser does NOT decode entities in it,
# so `&amp;` in the block is literally `&amp;` to a browser. Emit it verbatim to
# match what document.getElementById('agents-md').textContent would return —
# unescaping here would silently rewrite the author's text.
sys.stdout.write(m.group(1).strip() + "\n")
PY

set +e
python3 "$WORK/extract.py" "$SRC" > "$WORK/block.md"
rc=$?
set -e

if [ "$rc" -eq 3 ]; then
  echo "agents-block.sh: no #agents-md block in $SRC" >&2
  exit 3
elif [ "$rc" -ne 0 ]; then
  exit "$rc"
fi

cat "$WORK/block.md"

[ "$CHECK" -eq 1 ] || exit 0

if grep -q 'TODO' "$WORK/block.md"; then
  echo "agents-block.sh: block still has TODO placeholders — fill them in" >&2
  exit 3
fi

# ── Structure check (exit 4) ──────────────────────────────────────────────────
# Guidance without a gate erodes in about three edits, so the shape of the page is
# validated here rather than merely described in the skill. Both escape hatches are
# explicit and on the record — an artifact `type:` with nothing to summarise, or a
# stated `waiver:` — so neither is silent: they live in the block the next agent reads.
cat > "$WORK/shape.py" <<'PY'
import re, sys
from html.parser import HTMLParser

CAP = 100          # chars per bullet — a bullet is ONE line, and ~100 chars is one
                   # line at the artifact's 720px wrapper in 15px text.
MAX_BULLETS = 5    # a CEILING, not a target
FOOTER_CAP = 160   # the footer is ONE line: "Updated <date> · Sources: <what the
                   # numbers came from". Provenance and staleness, nothing else.
EXEMPT = {"mockup", "preview", "explainer"}
SHAPED = {"decision", "reference"}
BOTTOMS = {"next-steps", "open-questions", "none"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

page_path, block_path = sys.argv[1], sys.argv[2]
block = open(block_path, encoding="utf-8", errors="replace").read()
errs = []


def field(name, text):
    m = re.search(r'^[ \t]*(?:[-*+][ \t]*)?\**[ \t]*%s[ \t]*\**[ \t]*:[ \t]*(.*)$'
                  % re.escape(name), text, re.M | re.I)
    return m.group(1).strip().strip('`') if m else None


sec = re.search(r'^#{2,4}[ \t]+Structure\b[^\n]*\n(.*?)(?=^#{1,4}[ \t]|\Z)',
                block, re.M | re.S | re.I)
if not sec:
    print("agents-block.sh: block has no `## Structure` section. Add one:\n"
          "\n  ## Structure\n"
          "  - type: decision      "
          "# decision | reference | mockup | preview | explainer\n"
          "  - bottom: next-steps  "
          "# next-steps | open-questions | none — <why there are none>\n",
          file=sys.stderr)
    sys.exit(4)
sec = sec.group(1)

def report():
    """Print the accumulated violations and exit 4."""
    print("agents-block.sh: artifact structure violations in %s" % page_path, file=sys.stderr)
    for e in errs:
        print("  - %s" % e, file=sys.stderr)
    print("\nFix the page, or record an exemption in the block's `## Structure`:\n"
          "  - type: mockup     # mockups/previews/explainers have nothing to summarise\n"
          "  - waiver: <why this page cannot take the standard shape>  "
          "# add deliberately; never shipped by default",
          file=sys.stderr)
    sys.exit(4)


# A waiver is OPT-IN: `template.html` ships no `waiver:` line, so the line only exists
# because an author wrote it. Scaffold-looking text is rejected outright — an escape
# hatch that is satisfied by its own placeholder is an off switch, not an escape hatch,
# and it would silently disable the gate the first time someone filled in the TODOs
# without deleting the line.
WAIVER_SCAFFOLD = ("delete unless used", "todo", "<why", "<reason", "<the reason",
                   "a stated reason the standard shape cannot apply", "xxx", "n/a")
waiver = field("waiver", sec)
if waiver is not None:
    low = waiver.lower()
    hit = [p for p in WAIVER_SCAFFOLD if p in low]
    if hit or waiver.startswith("(") or len(waiver) < 12 or " " not in waiver:
        errs.append("`waiver:` is placeholder text, not a stated reason (%r). A waiver is "
                    "a recorded decision — write the actual reason this page cannot take "
                    "the standard shape, or delete the line." % waiver[:60])
    else:
        print("agents-block.sh: *** STRUCTURE CHECKS WAIVED *** — %s\n"
              "  (a recorded, reviewable decision, not a way to quiet the checker)"
              % waiver, file=sys.stderr)
        sys.exit(0)

raw_type = (field("type", sec) or "").split("#")[0].strip().lower()
if not raw_type:
    errs.append("`## Structure` declares no `type:` "
                "(decision | reference | mockup | preview | explainer)")
elif raw_type not in EXEMPT | SHAPED:
    errs.append("unknown `type: %s` — use decision | reference | mockup | preview | explainer"
                % raw_type)

if raw_type in EXEMPT:
    # Nothing to summarise — but a malformed waiver line is still a violation, and the
    # shape checks below would only produce noise for a mockup.
    if errs:
        report()
    print("agents-block.sh: type=%s — exec-summary/bottom checks skipped" % raw_type,
          file=sys.stderr)
    sys.exit(0)


class Collector(HTMLParser):
    """Collect the <li> text of every element whose id/class names a target section."""

    def __init__(self, targets):
        super().__init__(convert_charrefs=True)
        self.targets, self.found = targets, {}
        self.depth, self.active, self.li_depth, self.buf = 0, None, None, []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        self.depth += 1
        if self.active is None:
            toks = set((a.get("id") or "").split()) | set((a.get("class") or "").split())
            hit = self.targets & toks
            if hit:
                key = sorted(hit)[0]
                self.active = (key, tag, self.depth)
                self.found.setdefault(key, [])
                return
        if self.active and tag == "li" and self.li_depth is None:
            self.li_depth, self.buf = self.depth, []

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.active and self.li_depth is not None and tag == "li" \
                and self.depth == self.li_depth:
            self.found[self.active[0]].append(" ".join("".join(self.buf).split()))
            self.li_depth, self.buf = None, []
        if self.active and tag == self.active[1] and self.depth == self.active[2]:
            self.active = None
        self.depth -= 1

    def handle_data(self, data):
        if self.li_depth is not None:
            self.buf.append(data)


SRC = open(page_path, encoding="utf-8", errors="replace").read()

class FooterText(HTMLParser):
    """Collect the visible text of the page's <footer>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth, self.active, self.buf = 0, None, []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.depth += 1
        if tag == "footer" and self.active is None:
            self.active = self.depth

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.active is not None and tag == "footer" and self.depth == self.active:
            self.active = None
        self.depth -= 1

    def handle_data(self, data):
        if self.active is not None:
            self.buf.append(data)

    @property
    def text(self):
        return " ".join("".join(self.buf).split())


TARGETS = {"exec-summary", "next-steps", "open-questions"}
c = Collector(TARGETS)
c.feed(SRC)
found = c.found


def check_list(key, label):
    items = found.get(key)
    if items is None:
        errs.append('no element with id/class "%s" on the page — %s' % (key, label))
        return
    if not items:
        errs.append('"%s" carries no <li> bullets (the checker counts <li>)' % key)
        return
    if len(items) > MAX_BULLETS:
        errs.append('"%s" has %d bullets — the ceiling is %d, and %d is a ceiling, '
                    'not a target' % (key, len(items), MAX_BULLETS, MAX_BULLETS))
    for b in items:
        if len(b) > CAP:
            errs.append('"%s" bullet is %d chars, cap is %d (one line): "%s…"'
                        % (key, len(b), CAP, b[:60]))


check_list("exec-summary",
           "a decision/reference artifact opens with one: <=5 derived one-line bullets, "
           "no figure restated verbatim from a chart or table below")

# ── derivations: every figure in the summary has to close ────────────────────
# A summary figure is a claim ABOUT an asset further down the page. The checker cannot
# do the arithmetic, so it gates the one thing it can: that the author wrote the
# derivation down. Spelling out "19 of 20 = 18 table rows + 1 unresolved, of 20 fetched"
# is the step at which a number that does not close becomes visible.
#
# A real case: an artifact shipped claiming "19 of 20 recent messages arrived via the
# relay, from 7 distinct senders" above a table summing to 18 of 19 across 8. Every
# other check passed. "Keep the views in sync" was prose in the block, and prose in the
# block is read by nobody at handover — which is the argument for every gate here.
IDENT = re.compile(r'\b[A-Za-z]+[-_]?\d+[\w-]*\b|\b\d+[-_]?[A-Za-z]+\b')
YEAR = re.compile(r'\b(?:19|20)\d{2}\b')
MONTHDAY = re.compile(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?'
                      r'[ \t]+\d{1,2}\b', re.I)
DER_SCAFFOLD = ("todo", "<figure", "<where", "delete if", "xxx", "n/a")


def figures(text):
    """Digit runs that are claims — not ticket ids, versions, years or calendar dates."""
    t = MONTHDAY.sub(" ", text)
    t = YEAR.sub(" ", IDENT.sub(" ", t))
    return re.findall(r'\d[\d,]*(?:\.\d+)?', t)


der = re.search(r'^#{2,4}[ \t]+Derivations\b[^\n]*\n(.*?)(?=^#{1,4}[ \t]|\Z)',
                block, re.M | re.S | re.I)
der_lines = []
if der:
    for ln in der.group(1).splitlines():
        s = ln.strip()
        if s[:1] in ("-", "*", "+"):
            s = s.lstrip("-*+ \t")
            low = s.lower()
            # A derivation names its asset AND shows the arithmetic, so it carries
            # digits. "computed from the table below" is a gesture, not a derivation.
            if len(s) >= 12 and re.search(r"\d", s) \
                    and not any(p in low for p in DER_SCAFFOLD):
                der_lines.append(s)

numeric = [b for b in (found.get("exec-summary") or []) if figures(b)]
if numeric:
    quoted = "; ".join('"%s…"' % b[:52] for b in numeric)
    if der is None:
        errs.append("exec-summary states figures but the block has no `## Derivations` "
                    "section — %s. Add one line per figure-bearing bullet showing where "
                    "it computes from, or restate the bullet as a verdict without figures."
                    % quoted)
    elif len(der_lines) < len(numeric):
        errs.append("%d exec-summary bullet(s) state figures but `## Derivations` carries "
                    "only %d usable line(s) — %s. A derivation names its asset and shows "
                    "the arithmetic (so it contains digits); placeholder text does not "
                    "count." % (len(numeric), len(der_lines), quoted))

bottom = re.split(r'\s+#', field("bottom", sec) or "", 1)[0].strip()   # drop ` # comment`
bkind = re.split(r'[^a-z-]', bottom.lower(), 1)[0]
if not bottom:
    errs.append("`## Structure` declares no `bottom:` "
                "(next-steps | open-questions | none — <why there are none>)")
elif bkind not in BOTTOMS:
    errs.append("unknown `bottom: %s` — use next-steps | open-questions | none — <reason>"
                % bottom)
elif bkind == "none":
    reason = bottom[len(bkind):].strip(" —–-:().")
    if len(reason) < 8:
        errs.append("`bottom: none` needs a stated reason, e.g. `none — nothing "
                    "actionable; this is a record of what was measured`")
    for k in ("next-steps", "open-questions"):
        if found.get(k):
            errs.append('`bottom: none` but the page has a "%s" section — '
                        'the block and the page disagree' % k)
else:
    check_list(bkind, "declared as this artifact's bottom section")
    other = "open-questions" if bkind == "next-steps" else "next-steps"
    if found.get(other):
        errs.append('page has both "%s" and "%s" — declare one bottom section'
                    % (bkind, other))

# ── footer: one line, provenance + staleness, nothing else ───────────────────
ft = FooterText()
ft.feed(SRC)
footer = ft.text

if not footer:
    errs.append('no <footer> on the page — every artifact ends in ONE line: '
                '"Updated <date> · Sources: <what the numbers came from>"')
else:
    if len(footer) > FOOTER_CAP:
        errs.append('footer is %d chars, cap is %d (one line): "%s…"'
                    % (len(footer), FOOTER_CAP, footer[:60]))
    if not re.search(r"updated\s+\S+\s+\d{1,2},?\s+\d{4}", footer, re.I):
        errs.append('footer carries no "Updated <date>" stamp — a reader cannot tell '
                    'how stale the page is. e.g. "Updated Aug 3, 2026 · Sources: …"')

if errs:
    report()
PY

set +e
python3 "$WORK/shape.py" "$SRC" "$WORK/block.md"
rc=$?
set -e
exit "$rc"
