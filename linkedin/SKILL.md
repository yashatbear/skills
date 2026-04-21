---
name: linkedin
description: Search LinkedIn profiles, companies, and jobs via a local MCP server with advanced faceted search filters. Use this when you need to look up people, search by company/school/connections, or find jobs.
---

# LinkedIn MCP (Local Fork)

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

## Troubleshooting

- **Session expired**: Run `uvx linkedin-scraper-mcp --login` to re-authenticate
- **CAPTCHA**: May need `--no-headless` flag to solve manually
- **Rate limited**: Wait and retry; reduce filter count to minimize page visits
