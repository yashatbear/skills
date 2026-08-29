#!/usr/bin/env python3
"""Tests for the `## Derivations` gate in agents-block.sh.

The gate exists because the checker cannot do an artifact's arithmetic, so it
gates the next best thing: that the author wrote the derivation down. Two ways
it can go wrong, and both are load-bearing —

  · too loose  → a summary figure that doesn't close ships again (a real case:
    "19 of 20 … from 7 distinct senders" over a table summing to 18 of 19
    across 8; every other check passed)
  · too tight  → ticket ids, versions, years and dates read as "figures", the
    gate cries wolf on ordinary bullets, and someone waives it to get work done

So the identifier/date exclusions are pinned here just as hard as the catches.

Run: python3 test_derivations.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

CHECK = Path(__file__).parent / "agents-block.sh"

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8" />
<script type="text/markdown" id="agents-md">
# AGENTS.md — for agents editing this artifact

## What this page is
A fixture exercising the derivations gate.

## Structure
- type: reference
- bottom: open-questions
{der}
## Data sources
Fixture; no live data.
</script></head><body>
<section id="exec-summary"><ul>{lis}</ul></section>
<section id="open-questions"><ul><li>Does the gate hold?</li></ul></section>
<footer>Updated Aug 4, 2026 · Sources: fixture</footer>
</body></html>
"""

OK, VIOLATION, UNFILLED = 0, 4, 3

# (label, expected exit, summary bullets, derivations body or None)
CASES = [
    # --- must NOT trip: nothing in the bullet is a claim about an asset ---------
    ("plain verdict, no digits", OK,
     ["The mailer never receives inbound mail — that account is send-only."], None),
    ("ticket id is not a figure", OK,
     ["ISSUE-482 drops the extra relay hop and is the real fix here."], None),
    ("bare year is not a figure", OK,
     ["The setup doc still describes a chain that was replaced in 2026."], None),
    ("month + day is not a figure", OK,
     ["The forwarding chain was replaced on Jul 14, not in August."], None),
    ("compound like 30-day is not a figure", OK,
     ["Retention is 30-day, so old records age out on their own."], None),

    # --- must trip: a real figure with nothing covering it ----------------------
    ("count with no Derivations", VIOLATION,
     ["19 of 20 messages arrived via the relay, from 7 senders."], None),
    ("multiplier with no Derivations", VIOLATION,
     ["Option A is 132× cheaper than Option B."], None),
    ("percentage with no Derivations", VIOLATION,
     ["Lane B carries 5% of inbound and is the rarer path."], None),

    # --- Derivations present: the quality of the line decides -------------------
    ("a real derivation closes it", OK,
     ["19 of 20 messages arrived via the relay, from 7 senders."],
     '- "19 of 20" = 18 message-table rows + 1 unresolved, of 20 fetched; 7 = Lane-A rows.'),
    ("a gesture without arithmetic does not", VIOLATION,
     ["19 of 20 messages arrived via the relay, from 7 senders."],
     "- Computed from the message table below."),
    ("scaffold TODO is unfilled, not a derivation", UNFILLED,
     ["19 of 20 messages arrived via the relay, from 7 senders."],
     '- TODO: `"<figure>" = <asset> <arithmetic>`.'),

    # --- one line per figure-bearing bullet, not per page -----------------------
    ("two figure bullets, one line", VIOLATION,
     ["19 of 20 arrived via the relay.", "Lane B carries 5% of inbound."],
     '- "19 of 20" = 18 rows + 1 unresolved, of 20 fetched.'),
    ("two figure bullets, two lines", OK,
     ["19 of 20 arrived via the relay.", "Lane B carries 5% of inbound."],
     '- "19 of 20" = 18 rows + 1 unresolved, of 20 fetched.\n'
     '- "5%" = 1 Lane-B row of 19 resolved recipients.'),
    ("a plain bullet alongside needs nothing", OK,
     ["19 of 20 arrived via the relay.", "The mailer is send-only."],
     '- "19 of 20" = 18 rows + 1 unresolved, of 20 fetched.'),
]


def run_case(tmp, bullets, der):
    page = tmp / "p.html"
    page.write_text(PAGE.format(
        lis="".join("<li>%s</li>" % b for b in bullets),
        der="" if der is None else "\n## Derivations\n%s\n" % der,
    ), encoding="utf-8")
    return subprocess.run(
        ["bash", str(CHECK), "--check", str(page)],
        capture_output=True, text=True,
    ).returncode


def main() -> int:
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for label, want, bullets, der in CASES:
            got = run_case(tmp, bullets, der)
            if got == want:
                print("  ok    %s" % label)
            else:
                failed += 1
                print("  FAIL  %s (want exit %d, got %d)" % (label, want, got))
    print("\n%d/%d passed" % (len(CASES) - failed, len(CASES)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
