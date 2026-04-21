"""Search a specific person's connections in a location.

Resolves a LinkedIn username to a profile ID, then searches their connections
with optional geo filter. Works for 1st+2nd degree connections of the target person.

Usage:
    uv run python search_person_connections.py --user someuser --geo 105080838 --pages 3
    uv run python search_person_connections.py --profile-id ACoAAB97Gc0... --geo 105080838
    uv run python search_person_connections.py --user someuser  # no geo = worldwide

Run from the linkedin-mcp directory:
    cd /path/to/linkedin-mcp

Tip: If a target user has "Who can see your connections" set to "Only you", LinkedIn
redirects the connectionOf search back to *your own* profile ID. You can detect this
by passing --self-profile-id <your-ACoAA-id> — the script will skip the search when
the resolved ID matches.

Common geoUrns:
    105080838 = New York
    102095887 = San Francisco Bay Area
"""

import argparse
import asyncio
import json
import sys
import urllib.parse

# Parse our args BEFORE importing the MCP server (which adds its own argparse args)
_parser = argparse.ArgumentParser(description="Search a person's connections by location")
_parser.add_argument("--user", help="LinkedIn username (resolves to profile ID)")
_parser.add_argument("--profile-id", help="Internal LinkedIn profile ID (ACoAA...) — skips resolution")
_parser.add_argument("--geo", default=None, help="LinkedIn geoUrn (e.g. 105080838 = New York)")
_parser.add_argument("--pages", type=int, default=3, help="Number of result pages (default: 3)")
_parser.add_argument("--network", default="F,S", help="Network filter: comma-separated F,S,O (default: F,S)")
_parser.add_argument("--self-profile-id", default=None,
                     help="Your own ACoAA profile ID — if target resolves to this, skip (privacy block)")
_args, _remaining = _parser.parse_known_args()
sys.argv = [sys.argv[0]] + _remaining  # pass remaining to MCP base class

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
    """Navigate to a user's profile and extract their internal profile ID."""
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

    if args.profile_id:
        profile_id = args.profile_id
    else:
        print(f"Resolving profile ID for {args.user}...", file=sys.stderr)
        profile_id = await resolve_profile_id(page, args.user)
        if args.self_profile_id and profile_id == args.self_profile_id:
            print(f"WARNING: {args.user} resolved to your own profile ID (privacy block). Skipping.", file=sys.stderr)
            await browser.page.context.browser.close()
            print("[]")
            return
        print(f"Profile ID: {profile_id}", file=sys.stderr)

    network_encoded = urllib.parse.quote(json.dumps(args.network.split(","), separators=(",", ":")))
    all_people = []

    for pg in range(1, args.pages + 1):
        try:
            params = (
                f'?connectionOf=%5B%22{profile_id}%22%5D'
                f'&network={network_encoded}'
                f'&origin=FACETED_SEARCH&page={pg}'
            )
            if args.geo:
                params += f'&geoUrn=%5B%22{args.geo}%22%5D'

            url = f'https://www.linkedin.com/search/results/people/{params}'
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await asyncio.sleep(3)
            await scroll_to_bottom(page)
            await asyncio.sleep(2)
            people = await page.evaluate(JS_EXTRACT)
            # Filter out the target person
            if args.user:
                people = [p for p in people if p["username"] != args.user]
            all_people.extend(people)
            print(f"Page {pg}: {len(people)} results", file=sys.stderr)
            if len(people) == 0:
                break
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Page {pg} error: {e}", file=sys.stderr)
            break

    print(json.dumps(all_people, indent=2))
    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
