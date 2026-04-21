"""Batch-lookup profile + experience + education for a list of LinkedIn usernames.

Usage:
    uv run python batch_profile_lookup.py username1 username2 ...

Prints each person's main profile, experience, and education sections.
"""

import asyncio
import json
import sys

from linkedin_mcp_server.drivers.browser import get_or_create_browser, ensure_authenticated
from linkedin_mcp_server.core.utils import scroll_to_bottom


async def scrape_section(page, url, label):
    """Navigate to a URL and return the main element's text."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        await scroll_to_bottom(page)
        await asyncio.sleep(1)
        main_el = await page.query_selector("main")
        if main_el:
            return await main_el.inner_text()
        return "(empty)"
    except Exception as e:
        return f"ERROR: {e}"


async def main():
    usernames = sys.argv[1:]
    if not usernames:
        print("Usage: batch_profile_lookup.py username1 username2 ...")
        sys.exit(1)

    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page

    for username in usernames:
        print(f"\n{'='*60}")
        print(f"=== PROFILE: {username} ===")
        print(f"{'='*60}")

        # Main profile page
        profile_text = await scrape_section(
            page,
            f"https://www.linkedin.com/in/{username}/",
            "profile"
        )
        print("\n--- MAIN PROFILE ---")
        print(profile_text[:2000])

        await asyncio.sleep(1.5)

        # Experience section
        exp_text = await scrape_section(
            page,
            f"https://www.linkedin.com/in/{username}/details/experience/",
            "experience"
        )
        print("\n--- EXPERIENCE ---")
        print(exp_text[:2000])

        await asyncio.sleep(1.5)

        # Education section
        edu_text = await scrape_section(
            page,
            f"https://www.linkedin.com/in/{username}/details/education/",
            "education"
        )
        print("\n--- EDUCATION ---")
        print(edu_text[:2000])

        await asyncio.sleep(1.5)

    await browser.page.context.browser.close()


if __name__ == "__main__":
    asyncio.run(main())
