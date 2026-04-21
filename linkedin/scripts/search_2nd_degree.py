"""Search 2nd-degree connections in a location with keyword filters.

Searches your 2nd-degree LinkedIn network (not scoped to a specific person's
connections) with keyword and location filters. Useful for finding people
when you've exhausted direct connection mining.

Usage:
    uv run python search_2nd_degree.py --keywords "product manager" --geo 105080838 --pages 3
    uv run python search_2nd_degree.py --keywords "strategy operations startup" --geo 105080838
    uv run python search_2nd_degree.py --keywords "GTM analyst" --geo 105080838 --pages 2

Run from the linkedin-mcp directory:
    cd /path/to/linkedin-mcp

Common geoUrns:
    105080838 = New York
    102095887 = San Francisco Bay Area
    90000049  = Greater Los Angeles
"""

import argparse
import asyncio
import json
import sys
import urllib.parse

# Parse our args BEFORE importing the MCP server (which adds its own argparse args)
_parser = argparse.ArgumentParser(description="Search 2nd-degree connections by keyword and location")
_parser.add_argument("--keywords", required=True, help="Search keywords")
_parser.add_argument("--geo", default="105080838", help="LinkedIn geoUrn (default: NYC)")
_parser.add_argument("--pages", type=int, default=2, help="Number of pages (default: 2)")
_parser.add_argument("--network", default="S", help="Network: S=2nd, F=1st (default: S)")
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


async def main():
    args = _args

    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page

    all_people = []
    for pg in range(1, args.pages + 1):
        try:
            params = (
                f'?keywords={urllib.parse.quote(args.keywords)}'
                f'&network=%5B%22{args.network}%22%5D'
                f'&origin=FACETED_SEARCH&page={pg}'
                f'&geoUrn=%5B%22{args.geo}%22%5D'
            )
            url = f'https://www.linkedin.com/search/results/people/{params}'
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await asyncio.sleep(3)
            await scroll_to_bottom(page)
            await asyncio.sleep(2)
            people = await page.evaluate(JS_EXTRACT)
            degree = '2nd' if args.network == 'S' else '1st' if args.network == 'F' else '3rd'
            people = [p for p in people if degree in p.get('context', '')]
            for p in people:
                p['search'] = args.keywords
            all_people.extend(people)
            print(f'Page {pg}: {len(people)} results', file=sys.stderr)
            if len(people) == 0:
                break
            await asyncio.sleep(3)
        except Exception as e:
            print(f'Page {pg} error: {e}', file=sys.stderr)
            break

    print(json.dumps(all_people, indent=2))
    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
