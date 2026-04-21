"""Batch-lookup experience sections for a list of LinkedIn usernames.

Usage:
    echo '["username1","username2"]' | uv run python batch_experience_lookup.py

Or pass usernames as arguments:
    uv run python batch_experience_lookup.py username1 username2 ...

Prints each person's experience section (truncated to 1200 chars) to stdout.
Useful for checking whether people have engineering backgrounds.
"""

import asyncio
import json
import sys

from linkedin_mcp_server.drivers.browser import get_or_create_browser, ensure_authenticated
from linkedin_mcp_server.core.utils import scroll_to_bottom


async def main():
    # Accept usernames as args or from stdin JSON array
    if len(sys.argv) > 1:
        usernames = sys.argv[1:]
    else:
        usernames = json.load(sys.stdin)

    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page

    for username in usernames:
        url = f"https://www.linkedin.com/in/{username}/details/experience/"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)
            await scroll_to_bottom(page)
            await asyncio.sleep(1)
            main_el = await page.query_selector("main")
            if main_el:
                text = await main_el.inner_text()
                print(f"=== {username} ===")
                print(text[:1200])
                print()
        except Exception as e:
            print(f"=== {username} === ERROR: {e}")
        await asyncio.sleep(1.5)

    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
