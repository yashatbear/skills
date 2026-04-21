"""Scrape all connections from the LinkedIn connections page.

Unlike search_person_connections.py (which uses the search API and caps at ~400),
this script scrolls through the connections management page to get ALL connections.

Usage:
    uv run python scrape_connections_page.py
    uv run python scrape_connections_page.py --output /tmp/connections.json

Run from the linkedin-mcp directory:
    cd /path/to/linkedin-mcp

Notes:
    - LinkedIn's connectionOf search API caps at ~400 results even for 1000+ connections
    - This script uses the /mynetwork/invite-connect/connections/ page with infinite scroll
    - Results are sorted by most recently connected
"""

import argparse
import asyncio
import json
import sys

_parser = argparse.ArgumentParser(description="Scrape all connections from connections page")
_parser.add_argument("--output", default="/tmp/connections.json", help="Output file path")
_args, _remaining = _parser.parse_known_args()
sys.argv = [sys.argv[0]] + _remaining

from linkedin_mcp_server.drivers.browser import get_or_create_browser, ensure_authenticated


JS_CLICK_LOAD_MORE = r"""() => {
    const btns = document.querySelectorAll("button");
    for (const b of btns) {
        if (b.innerText.includes("Load more") || b.innerText.includes("Show more")) {
            b.click();
            return true;
        }
    }
    return false;
}"""

JS_EXTRACT = r"""() => {
    const results = [];
    const seen = new Set();
    const selector = 'a[href*="' + '/in/' + '"]';
    const links = document.querySelectorAll(selector);
    for (const a of links) {
        const text = a.innerText.trim();
        if (!text || text.length < 3) continue;
        const href = (a.href || "").split("?")[0].replace(/\/+$/, "");
        const parts = href.split("/in/");
        const username = parts[parts.length - 1];
        if (!username || seen.has(username)) continue;
        seen.add(username);
        const lines = text.split("\n").map(l => l.trim()).filter(l => l);
        const name = lines[0] || "";
        const headline = lines.slice(1).join(" | ") || "";
        results.push({username: username, name: name, headline: headline, url: href});
    }
    return results;
}"""

JS_COUNT = r"""() => {
    const selector = 'a[href*="' + '/in/' + '"]';
    return document.querySelectorAll(selector).length;
}"""


async def main():
    args = _args

    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page

    await page.goto(
        "https://www.linkedin.com/mynetwork/invite-connect/connections/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(4)

    rounds = 0
    stale = 0
    prev_count = 0
    while rounds < 300 and stale < 5:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)
        clicked = await page.evaluate(JS_CLICK_LOAD_MORE)
        if not clicked:
            await asyncio.sleep(1)
            clicked = await page.evaluate(JS_CLICK_LOAD_MORE)
            if not clicked:
                stale += 1
                # Scroll up and back down to trigger lazy load
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight - 1000)")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                continue
        stale = 0
        await asyncio.sleep(1.5)
        rounds += 1
        if rounds % 20 == 0:
            count = await page.evaluate(JS_COUNT)
            unique = count // 2  # each person has 2 links (avatar + name)
            print(f"Round {rounds}: ~{unique} connections loaded", file=sys.stderr, flush=True)
            if unique == prev_count:
                stale += 1
            prev_count = unique

    people = await page.evaluate(JS_EXTRACT)
    print(f"Total extracted: {len(people)}", file=sys.stderr)

    with open(args.output, "w") as f:
        json.dump(people, f, indent=2)

    print(json.dumps(people, indent=2))
    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
