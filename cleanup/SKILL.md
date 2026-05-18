---
name: cleanup
description: Reclaim memory and CPU by stopping background processes the user no longer needs — Docker containers, dev servers, idle Python/Node processes, git worktrees, simulators, and stale virtualenvs. Always inventory first, then ask before killing anything.
---

# System Cleanup

Reclaims memory by shutting down background processes, containers, sandboxes, and dev environments that are no longer in use. **This skill is destructive** — always inventory first, present what you found, and get confirmation before stopping anything.

## Safety Rules

- **Never kill blindly.** Always list what's running before acting.
- **Always show the kill list and ask before stopping anything.** One confirmation per category is fine; don't ask per-process.
- **Never kill processes the user is actively using.** If a process is attached to a TTY, has a recent file modification under it, or is the user's shell, leave it alone.
- **Never touch system processes** (`launchd`, `WindowServer`, `kernel_task`, anything owned by root unless explicitly asked).
- **NEVER kill MCP server processes.** They look like duplicates (e.g. `linear-mcp`, `gmail-mcp`, various `mcp-server-*`) spawned once per Claude session, but the Claude Code harness pools/shares them across sessions. Killing any one of them — even an apparently "stale" set from an old session — will disconnect MCP tools from the **current** session. Always mark MCP processes `[KEEP]`.
- **Never delete data.** Stopping containers is OK; `docker system prune -a --volumes` is NOT OK without explicit volume confirmation.
- **Never remove git worktrees with uncommitted changes.** Check `git status` first.
- **Never delete the current branch, a worktree-checked-out branch, or a base/env branch** (`main`/`develop`/`master`/`staging`). For a branch whose PR is closed or absent, check its tracking issue before deleting — a closed PR on a still-active ticket is live work, not a dead branch.

## Step 1: Inventory

Run these in parallel and collect output. Skip categories that error (tool not installed).

### Memory pressure baseline
```bash
vm_stat | head -5
top -l 1 -n 0 -s 0 | grep -E "PhysMem|CPU usage"
ps -A -o pid,rss,comm | sort -k2 -rn | head -20
```

### Docker
```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}" 2>/dev/null
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -20
docker system df 2>/dev/null
```

### Dev servers / language runtimes
```bash
# Node, Python, Ruby, Go dev processes
ps -A -o pid,rss,etime,command | grep -E "(node|next|vite|webpack|python|uvicorn|gunicorn|celery|rails|puma|sidekiq|go run)" | grep -v grep
# Listening ports (common dev ports)
lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | grep -E ":(3000|3001|4000|5000|5173|5432|6379|8000|8080|8888|9000)"
```

### Background bash shells started by Claude Code
Check for any long-running background commands you (Claude) started in this session via `run_in_background: true`. These may still be holding memory.

### MCP servers — DO NOT KILL, inventory only
List them so the user sees them, but always mark `[KEEP]`. Do not include them in the kill list under any circumstances. See Safety Rules above.
```bash
ps -A -o pid,rss,etime,command | grep -E "mcp" | grep -v grep
```

### Git worktrees
Capture each worktree's branch, uncommitted-file count, lock status, and — if `gh` (the GitHub CLI) is available — its **PR merge state**, so removal decisions are merge-aware. A clean worktree on a merged-PR branch is the safest possible delete; a dirty or no-PR worktree must always be kept.

```bash
# For each repo the user works in, list worktrees with branch/dirty/PR-state.
for repo in ~/projects/*/; do
  [ -d "$repo/.git" ] || [ -f "$repo/.git" ] || continue
  echo "=== $repo ==="
  git -C "$repo" worktree list 2>/dev/null
  for wt in $(git -C "$repo" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}'); do
    [ "$wt" = "${repo%/}" ] && continue  # skip the main checkout
    b=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
    d=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    pr=$(cd "$wt" && gh pr list --state all --head "$b" --json number,state,mergedAt --limit 1 2>/dev/null)
    echo "  $wt | branch=$b | dirty=$d | pr=$pr"
  done
done
```

Categorize each worktree from the output:

| Signal                                      | Decision  | Reason                                              |
|----------------------------------------------|-----------|-----------------------------------------------------|
| `dirty > 0`                                  | **KEEP**  | uncommitted work — never remove                     |
| branch in `main`/`master`/`develop`          | **KEEP**  | base-branch checkout, not a feature worktree        |
| `pr=[]` (no PR found, or `gh` unavailable)   | **KEEP**  | can't verify safety; may be unpushed work           |
| PR `state=OPEN`                              | **KEEP?** | flag — usually keep, ask the user if disk-pressed   |
| PR `state=MERGED` and `dirty=0`              | **KILL**  | shipped + clean — safe delete                       |
| PR `state=CLOSED` (not merged) and `dirty=0` | **KILL?** | abandoned branch — confirm with the user            |

Locked worktrees (`locked` in `worktree list` output) follow the same rules — if their PR is merged and the tree is clean, they're safe to remove with `unlock` + `--force` (Step 3).

### Stale branches

Local and remote branches whose PRs already shipped pile up invisibly — a busy repo can reach 100+ local branches before anyone notices. If `gh` is available, classify every local branch by its PR state:

```bash
for repo in ~/projects/*/; do
  [ -d "$repo/.git" ] || continue
  echo "=== $repo ==="
  git -C "$repo" fetch --prune origin 2>/dev/null   # updates remote-tracking refs; deletes nothing local
  for b in $(git -C "$repo" for-each-ref --format='%(refname:short)' refs/heads/); do
    pr=$(cd "$repo" && gh pr list --state all --head "$b" --json number,state --limit 1 2>/dev/null)
    echo "  $b | pr=$pr"
  done
done
```

Categorize from the output:

| Signal                                       | Decision  | Reason                                              |
|-----------------------------------------------|-----------|-----------------------------------------------------|
| current branch / checked out in a worktree    | **KEEP**  | git refuses anyway — never list it for deletion     |
| base/env branch (`main`/`develop`/`staging`)  | **KEEP**  | long-lived, protected by name                       |
| PR `MERGED`                                   | **KILL**  | shipped                                             |
| PR `CLOSED` (not merged)                      | **KILL?** | cross-check the tracking issue before deleting      |
| PR `OPEN` / no PR / `gh` unavailable          | **KEEP**  | live work, or unpushed WIP                          |

For every `CLOSED`-PR branch, check its tracking issue first: a closed PR whose issue is still active is live work that lost its PR, not a dead branch — mark it `[KEEP]` and flag it. Local branch deletes are reflog-recoverable for ~90 days; remote deletes are not — list them explicitly.

### Simulators / emulators
```bash
xcrun simctl list devices booted 2>/dev/null
pgrep -lf "Simulator|qemu|VirtualBox|VMware|UTM" 2>/dev/null
```

### Virtualenvs / sandboxes
```bash
# Active python virtualenvs (process-level)
ps -A -o command | grep -E "venv/bin/python|\.venv/bin/python" | grep -v grep
# Orphaned __pycache__ / node_modules size (informational, don't delete)
```

### Tunnels (ngrok, cloudflared, ssh -L)
```bash
pgrep -lf "ngrok|cloudflared|ssh.*-L" 2>/dev/null
```

### Browser automation leftovers
```bash
pgrep -lf "chromedriver|playwright|puppeteer|selenium" 2>/dev/null
```

## Step 2: Categorize & Present

Group findings into a punch list. For each item show: what it is, memory/disk it's using, and whether you recommend killing it. Use this format:

```
CLEANUP CANDIDATES
==================

Docker (3 containers, ~2.1 GB)
  [KILL]   local-postgres       500 MB   running 4d (no recent connections)
  [KILL]   redis-test           120 MB   exited 2d ago
  [KEEP?]  api-dev              1.5 GB   running, port 8000 active

Dev servers (2 processes, ~1.8 GB)
  [KILL]   next-dev             900 MB   pid 41203, started 6h ago
  [KILL]   vite                 850 MB   pid 41892, started 6h ago

Background shells (1)
  [KILL]   bash_42              started by Claude this session, idle 2h

Git worktrees (4)
  [KEEP]   project/.worktrees/feature-1   DIRTY (12 files)
  [KEEP]   project/.worktrees/feature-2   no PR (unpushed?)
  [KILL]   project/.worktrees/feature-3   PR #540 MERGED, clean
  [KILL]   project/.worktrees/feature-4   PR #612 MERGED, clean, locked → unlock + force

Stale branches (project: 14 local, 6 remote)
  [KILL]   feature/old-cleanup        local + origin   PR #678 MERGED
  [KILL?]  feature/host-aware-tests   local            PR #274 CLOSED — check issue
  [KEEP]   feature/dark-mode          origin           PR closed BUT issue still active

Tunnels (1)
  [KILL]   ngrok http 8000      pid 38211

Total reclaimable: ~5.4 GB RAM, ~3 GB disk
```

Then ask: **"Proceed with the [KILL] items? (y / pick / no)"**
- `y` → kill everything marked KILL
- `pick` → let user toggle individual items
- `no` → abort

## Step 3: Execute

Once confirmed, run shutdowns in this order (least → most disruptive):

1. **Background shells (Claude session)** — use `KillShell` on the bash_id
2. **Tunnels & browser automation** — `kill <pid>` (SIGTERM, then SIGKILL after 3s if still alive)
3. **Dev servers** — `kill <pid>`; for processes with children (next, vite, celery), kill the process group: `kill -- -<pgid>`
4. **Docker containers** — `docker stop <id>` (graceful); never `docker rm -v` without confirmation
5. **Git worktrees** — only remove ones the inventory marked KILL (merged PR + clean). Unlocked: `git -C <repo> worktree remove <path>`. Locked: `git -C <repo> worktree unlock <path> && git -C <repo> worktree remove --force <path>`. Refuse to remove if dirty, no-PR, on a base branch, or PR is OPEN — even if the user says proceed, re-check with `git -C <wt> status --porcelain` first.
6. **Stale branches** — delete only the branches the user confirmed (the `pick` step may have dropped some). Local: `git -C <repo> branch -D <branch>`. Remote: `git -C <repo> push origin --delete <branch>` — one branch per push, since a batched delete aborts entirely if any ref is already gone. Never delete the current branch, a worktree-checked-out branch, or a protected branch.
7. **Simulators** — `xcrun simctl shutdown <udid>`

After each category, re-check it's actually gone (`pgrep` / `docker ps` / `git branch`) and report.

## Step 4: Report

Print a final summary:
```
CLEANUP COMPLETE
================
Stopped: 2 docker containers, 2 dev servers, 1 ngrok tunnel
Pruned:  1 worktree, 14 stale branches (12 local, 6 remote)
Memory before: 14.2 GB used / 16 GB
Memory after:   8.8 GB used / 16 GB
Reclaimed:      5.4 GB
```

## Things this skill does NOT do

- Does not run `docker system prune` (data loss risk)
- Does not delete `node_modules` or `__pycache__` (the user can rerun `npm install` but it's slow)
- Does not uninstall packages or clear Homebrew caches
- Does not log out of services or revoke tokens
- Does not touch anything under `/System`, `/Library`, or root-owned processes
- Does not restart the machine

If the user wants any of the above, they should ask explicitly.
