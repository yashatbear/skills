---
name: linkedin
description: Search LinkedIn profiles, companies, and jobs via a local MCP server with advanced faceted search filters. Use this when you need to look up people, search by company/school/connections, or find jobs.
---

# LinkedIn MCP (Local Fork)

> ⚠ **Use at your own risk.** This skill automates a real logged-in LinkedIn session via a browser driver. That's against LinkedIn's Terms of Service and can get your account rate-limited, flagged, or suspended. Don't run it against an account you can't afford to lose, don't run it at high volume, and don't use it for anything LinkedIn's ToS prohibits (bulk scraping, commercial data products, etc.). Published as-is, no warranty — see [LICENSE](../LICENSE).

## When to Use

When you need to search for people, look up profiles/companies, or find jobs on LinkedIn. Especially useful for:

- Finding people by company, school, title, location, or industry
- Searching within a specific person's connections (e.g., "someone's connections who worked at Apple")
- Looking up a person's profile with experience, education, contact info
- Researching companies and their recent posts
- Searching for job openings

## Architecture

Based on a local fork of [stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server).

- **Patchright** (Playwright fork) with persistent Chromium profile at `~/.linkedin-mcp/profile/`
- Session persists across runs (no re-login needed)
- Configured in `.mcp.json` as the `linkedin` server via `uv run`

## MCP Tools

All tools are prefixed with `mcp__linkedin__` when called.

### People

| Tool | Description |
|---|---|
| `search_people` | Search for people with advanced filters (see below) |
| `get_person_profile` | Get a person's profile by username |
| `get_shared_connections` | Mutual connections between the viewer and a target |
| `get_sidebar_profiles` | "People you may know" / recommended profiles on a page |

> **`get_shared_connections` only works for 2nd-degree targets.** Mutuals are
> people 1st-degree to *both* you and the target — that's exactly the 2nd-degree
> case. A **1st-degree** target returns nothing useful (the view is just *their*
> connections); a **3rd-degree** target has *no* mutual by definition. The tool
> reads the target's degree badge and refuses (returns `note`, empty `sections`)
> for anything but 2nd-degree, and echoes `target_name`/`target_degree` so you
> can confirm it resolved the right person. Always check `target_name` matches
> who you asked for before trusting the list — a 3rd-degree profile has no
> Message button, and the URN resolver can otherwise grab a stray recommendation
> card's identity and return a *stranger's* network.
>
> **If it refuses for a real 2nd-degree target (no Message button → `Could not
> resolve profile URN`), the mutuals are still reachable** — the profile renders
> a `"<A>, <B> and N other mutual connections"` link; navigate that href to a
> `/search/results/people/?facetConnectionOf=…` page listing every mutual with
> full name + slug. `scripts/mutual_connection_check.py` does exactly this
> click-through. Pace it (a delay around each `page.goto`) and abort on
> `/checkpoint`|`/authwall`. Don't conclude "no warm path" from the refusal.

### Companies

| Tool | Description |
|---|---|
| `get_company_profile` | Get a company's about page by slug |
| `get_company_posts` | Get recent posts from a company |

### Jobs

| Tool | Description |
|---|---|
| `search_jobs` | Search for jobs by keywords + location |
| `get_job_details` | Get full details for a job posting by ID |

### Session

| Tool | Description |
|---|---|
| `close_session` | Clean up the browser session |

## Advanced People Search

`search_people` supports the following filters. Company names and usernames are automatically resolved to LinkedIn internal IDs for accurate faceted results.

| Parameter | Description | Example |
|---|---|---|
| `keywords` | Free-text search (required, can be empty `""`) | `"software engineer"` |
| `location` | Location filter | `"New York"` |
| `company` | Current company (resolved to company ID) | `"Apple"` |
| `past_company` | Past company (resolved to company ID) | `"Google"` |
| `school` | School/university | `"Stanford University"` |
| `industry` | Industry filter | `"Technology"` |
| `title` | Job title filter | `"VP of Sales"` |
| `network` | Connection degree: `"F"` (1st), `"S"` (2nd), `"O"` (3rd+) | `"F"` |
| `connection_of` | LinkedIn username to scope to their connections | `"someuser"` |

### How ID Resolution Works

- **`company` / `past_company`**: Navigates to `linkedin.com/company/{slug}/`, extracts numeric company ID from `urn:li:fsd_company:{id}` in the page HTML.
- **`connection_of`**: Navigates to the user's profile, extracts their internal profile ID from the connections link URL (the `connectionOf` parameter LinkedIn embeds in the "N connections" href).
- All facet params use LinkedIn's native JSON-array URL encoding (`%5B%22{id}%22%5D`).
- When `connection_of` is set, `network` defaults to `["F","S"]` (1st + 2nd degree) to match LinkedIn's UI behavior.

### Examples

```
# A user's connections in New York who worked at Apple
search_people(keywords="", location="New York", past_company="Apple", connection_of="someuser")

# Software engineers at Google in SF
search_people(keywords="software engineer", location="San Francisco", company="Google")

# 1st-degree connections who are VPs
search_people(keywords="", title="VP", network="F")

# People from Stanford in the finance industry
search_people(keywords="", school="Stanford University", industry="Finance")
```

### Profile Sections

`get_person_profile` accepts an optional `sections` parameter (comma-separated):

| Section | What it scrapes |
|---|---|
| `experience` | Work history |
| `education` | Education history |
| `interests` | Followed topics/influencers |
| `honors` | Awards and honors |
| `languages` | Languages spoken |
| `contact_info` | Email, phone, websites (overlay) |

The main profile page is always included. Example: `sections="experience,education,contact_info"`

## Rate Limiting

- 2-second delay between page navigations
- Automatic detection of LinkedIn rate limits, CAPTCHAs, and auth walls
- Single retry with 5-second backoff on soft rate limits
- Filters requiring ID resolution add extra page visits (1 per company, 1 for connection_of)
- **Bulk scraping can get the account temporarily restricted.** Fanning out thousands of faceted searches back-to-back (e.g. a whole audience × dozens of companies) can trigger a multi-day account restriction and invalidate the logged-in profile (a fresh `--login` is then required to recover). For large jobs: pace **30–45s between subjects, ~10–15 subjects/day spread across days**, and smoke-test ONE scan after any re-login before resuming. Treat an all-zero result that coincides with a navigation / "execution context destroyed" error as a **throttle (retry), not a genuine zero**.
- **`connection_of` counts are a floor, and the subject is excluded.** The faceted `connectionOf` + `network=["F","S"]` search only surfaces that person's connections that ALSO fall in *your* 1st/2nd-degree network, so it undercounts (you miss their connections outside your network even when their list is public). The script drops the subject from their own results.

## Reusable Scripts

Helper scripts live in `scripts/` next to this SKILL.md. Run them from the linkedin-mcp fork directory:

```bash
uv run --directory /path/to/linkedin-mcp-server-fork python /path/to/skills/linkedin/scripts/<script>.py
```

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract_connections.py` | Search a person's connections by keyword, location, etc. Auto-resolves username → profile ID. | `python script.py --user someuser --keywords Jane` |
| `search_person_connections.py` | Search a person's connections by location. Resolves username → ID, detects privacy blocks. | `python script.py --user someuser --geo 105080838 --pages 3` |
| `search_2nd_degree.py` | Search your 2nd-degree network by keywords + location. Not scoped to a specific person. | `python script.py --keywords "product manager" --geo 105080838 --pages 3` |
| `batch_experience_lookup.py` | Batch-lookup experience sections for a list of usernames to check backgrounds | `python script.py username1 username2 ...` |

#### extract_connections.py flags

| Flag | Description | Example |
|------|-------------|---------|
| `--user` | LinkedIn username (resolves to profile ID automatically) | `--user someuser` |
| `--profile-id` | Internal profile ID (ACoAA...) — skips resolution | `--profile-id ACoAAB97Gc0...` |
| `--keywords` | Search keywords within connections | `--keywords "Jane"` |
| `--geo` | LinkedIn geoUrn for location filter | `--geo 105080838` (New York) |
| `--pages` | Number of result pages (default: 3) | `--pages 5` |

These scripts bypass the MCP tool interface and use the fork's Python API directly with the shared browser profile. Useful when:
- The MCP tool schema doesn't expose a needed parameter
- You need to extract raw HTML/link data (not just innerText)
- You need to batch-process many profiles efficiently

**Important:** When you create new LinkedIn automation scripts during a session, save them to this `scripts/` directory for future agents to reuse.

## Resolving usernames

- **WebSearch for the LinkedIn slug, don't guess.** Given a name, use a web search like `"<full name>" linkedin.com/in` to find the actual `linkedin.com/in/<slug>` URL. Guessed slugs (lowercase first-last, etc.) often don't exist or hit the wrong person.

## Troubleshooting

- **Session expired**: Run `uvx linkedin-scraper-mcp --login` to re-authenticate
- **CAPTCHA**: May need `--no-headless` flag to solve manually
- **Rate limited**: Wait and retry; reduce filter count to minimize page visits
