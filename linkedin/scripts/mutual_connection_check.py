"""Check mutual connections for a list of LinkedIn profiles.

Edit the `profiles` list to contain (username, label) tuples for the people
you want to check, then run the script. For each target, the script navigates
to their profile, follows the "N mutual connections" link, and lists who the
mutual connections are.

Usage:
    uv run python mutual_connection_check.py
"""
import asyncio
from linkedin_mcp_server.drivers.browser import get_or_create_browser, ensure_authenticated
from linkedin_mcp_server.core.utils import scroll_to_bottom

# (linkedin_username, label) — label is free-form (company, role, note)
profiles = [
    # ("someuser", "Example Co"),
]

JS = r"""() => {
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
        const text = container ? container.innerText.trim().substring(0, 200) : a.innerText.trim().substring(0, 200);
        results.push({username: username, context: text});
    }
    return results;
}"""

async def get_mutual(page, username, label):
    url = "https://www.linkedin.com/in/" + username + "/"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(3)
    mutual_link = await page.evaluate(r"""() => {
        const links = document.querySelectorAll('a');
        for (const a of links) {
            const t = a.innerText || '';
            if (t.includes('mutual')) return {text: t.trim(), href: a.href};
        }
        return null;
    }""")
    if not mutual_link or not mutual_link.get("href"):
        print("=== " + label + " (" + username + "): No mutual connections ===")
        return

    print("=== " + label + " (" + username + ") ===")
    print("  " + mutual_link["text"])
    await page.goto(mutual_link["href"], wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(4)
    await scroll_to_bottom(page)
    await asyncio.sleep(2)
    results = await page.evaluate(JS)
    for r in results:
        ctx = r["context"].replace("\n", " | ")[:150]
        print("  " + r["username"] + ": " + ctx)

async def main():
    await ensure_authenticated()
    browser = await get_or_create_browser()
    page = browser.page
    for username, label in profiles:
        await get_mutual(page, username, label)
        await asyncio.sleep(1)

asyncio.run(main())
