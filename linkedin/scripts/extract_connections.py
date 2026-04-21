"""Search within a LinkedIn user's connections.

Resolves a LinkedIn username to an internal profile ID, then searches
their connections with optional keyword and location filters.

Usage:
    uv run python extract_connections.py --user someuser --keywords Jane
    uv run python extract_connections.py --user someuser --keywords "software engineer" --geo 105080838
    uv run python extract_connections.py --profile-id ACoAAB97Gc0... --keywords Jane --pages 2

The script extracts actual LinkedIn usernames and profile URLs from search results,
unlike the innerText-only approach which loses link targets.
"""

import argparse
import asyncio
import json
import re
import sys
import urllib.parse

_parser = argparse.ArgumentParser(description="Search a LinkedIn user's connections")
_parser.add_argument("--user", help="LinkedIn username to search connections of")
_parser.add_argument("--profile-id", help="Internal LinkedIn profile ID (ACoAA...) — skips resolution")
_parser.add_argument("--keywords", default="", help="Search keywords (e.g. 'Jane', 'software engineer')")
_parser.add_argument("--geo", default=None, help="LinkedIn geoUrn for location filter (e.g. 105080838 = New York)")
_parser.add_argument("--pages", type=int, default=3, help="Number of result pages to scrape (default: 3)")
_args, _remaining = _parser.parse_known_args()
sys.argv = [sys.argv[0]] + _remaining

from linkedin_mcp_server.drivers.browser import get_or_create_browser, ensure_authenticated
from linkedin_mcp_server.core.utils import scroll_to_bottom

JS_EXTRACT = r"""() => {
    const results = [];
    const links = document.querySelectorAll('a[href*="/in/"]');
    const seen = new Set();
    for (const a of links) {
        const href = (a.href || '').split('?')[0].replace(/\/+$/, '');
        if (!href.includes('/in/')) continue;
        const parts = href.split('/in/');
        const username = parts[parts.length - 1];
        if (!username || seen.has(username)) continue;
        seen.add(username);
        let container = a.closest('li');
        const text = container ? container.innerText.trim().substring(0, 400) : a.innerText.trim().substring(0, 400);
        results.push({username: username, url: href, context: text});
    }
    return results;
}"""


async def resolve_profile_id(page, username):
    """Navigate to a user's profile and extract their internal ACoAA profile ID."""
    await page.goto(
        f"https://www.linkedin.com/in/{username}/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(3)
    profile_id = await page.evaluate(r"""() => {
        const html = document.documentElement.innerHTML;
        const match = html.match(/connectionOf=%5B%22(ACoAA[^%"]+)%22%5D/);
        if (match) return match[1];
        const match2 = html.match(/ACoAA[A-Za-z0-9_-]+/);
        return match2 ? match2[0] : null;
    }""")
    if not profile_id:
        raise RuntimeError(f"Could not resolve profile ID for {username}")
    return profile_id


async def main():
    args = _args

    if not args.user and not args.profile_id:
        _parser.error("Provide either --user or --profile-id")

    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page

    # Resolve profile ID if needed
    if args.profile_id:
        profile_id = args.profile_id
    else:
        print(f"Resolving profile ID for {args.user}...", file=__import__("sys").stderr)
        profile_id = await resolve_profile_id(page, args.user)
        print(f"Profile ID: {profile_id}", file=__import__("sys").stderr)

    # Build search URL
    all_people = []
    for pg in range(1, args.pages + 1):
        params = (
            f"?connectionOf=%5B%22{profile_id}%22%5D"
            f"&network=%5B%22F%22%2C%22S%22%5D"
            f"&origin=FACETED_SEARCH&page={pg}"
        )
        if args.keywords:
            params += f"&keywords={urllib.parse.quote(args.keywords)}"
        if args.geo:
            params += f"&geoUrn=%5B%22{args.geo}%22%5D"

        url = f"https://www.linkedin.com/search/results/people/{params}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        await scroll_to_bottom(page)
        await asyncio.sleep(2)

        people = await page.evaluate(JS_EXTRACT)
        # Filter out the target person
        if args.user:
            people = [p for p in people if p["username"] != args.user]
        all_people.extend(people)
        print(f"Page {pg}: {len(people)} results", file=__import__("sys").stderr)
        if len(people) == 0:
            break
        await asyncio.sleep(2)

    print(json.dumps(all_people, indent=2))
    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
