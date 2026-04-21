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
```bash
# For each repo the user works in, list worktrees
for repo in ~/projects/*/; do
  [ -d "$repo/.git" ] || continue
  echo "=== $repo ==="
  git -C "$repo" worktree list 2>/dev/null
done
```

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
  [KEEP]   project/.worktrees/feature-1   has uncommitted changes
  [KILL]   project/.worktrees/feature-2   merged + clean

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
5. **Git worktrees** — `git -C <repo> worktree remove <path>`; refuse if dirty
6. **Simulators** — `xcrun simctl shutdown <udid>`

After each category, re-check it's actually gone (`pgrep` / `docker ps`) and report.

## Step 4: Report

Print a final summary:
```
CLEANUP COMPLETE
================
Stopped: 2 docker containers, 2 dev servers, 1 ngrok tunnel, 1 worktree
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
