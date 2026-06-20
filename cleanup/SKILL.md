---
name: cleanup
description: Reclaim disk and clear stale clutter (git worktrees, merged branches, Docker images, DerivedData, idle tunnels). Reclaim RAM/CPU only when a pre-flight pressure check shows actual constraint — on a healthy Mac, "memory used" looks high by design and stopping idle processes won't lower it. Always inventory first, then ask before deleting anything.
---

# System Cleanup

Reclaims **disk** (the usual win on a Mac) and clears stale **clutter** that slows you down — worktrees on merged PRs, branches with shipped PRs, idle tunnels, dangling Docker images, stopped VMs. Reclaims **RAM/CPU only when the Step 0 pre-flight shows actual constraint** — on a healthy system, "memory used" looks high by design (file cache + compressor + inactive pages) and stopping idle processes won't change it. **This skill is destructive** — always inventory first, present what you found, and get confirmation before deleting anything.

**Why disk-first, not RAM-first:** a full sweep that reclaims tens of GB of disk can show RAM going *up* during the cleanup window — stopped VMs and removed images held no RAM, while whatever apps you have open drift up in the same window. Targeting "Memory Used" creates a false sense of progress. Target disk and clutter; only target RAM when the pressure sysctl (Step 0) actually shows pressure.

## Safety Rules

- **Never kill blindly.** Always list what's running before acting.
- **Always show the kill list and ask before stopping anything.** One confirmation per category is fine; don't ask per-process.
- **Never kill processes the user is actively using.** If a process is attached to a TTY, has a recent file modification under it, or is the user's shell, leave it alone.
- **Never touch system processes** (`launchd`, `WindowServer`, `kernel_task`, anything owned by root unless explicitly asked).
- **NEVER kill MCP server processes.** They look like duplicates (e.g. `linear-mcp`, `gmail-mcp`, various `mcp-server-*`) spawned once per Claude session, but the Claude Code harness pools/shares them across sessions. Killing any one of them — even an apparently "stale" set from an old session — will disconnect MCP tools from the **current** session. Always mark MCP processes `[KEEP]`.
- **Never delete data.** Stopping containers is OK; `docker system prune -a --volumes` is NOT OK without explicit volume confirmation.
- **Never remove git worktrees with uncommitted changes.** Check `git status` first.
- **Never delete the current branch, a worktree-checked-out branch, or a base/env branch** (`main`/`develop`/`master`/`staging`). For a branch whose PR is closed or absent, check its tracking issue before deleting — a closed PR on a still-active ticket is live work, not a dead branch.

## Step 0: Pre-flight — is RAM actually constrained?

Run this first. It decides whether the **[RAM-gated]** sections in Step 1 are worth running at all.

```bash
pressure=$(sysctl -n kern.memorystatus_vm_pressure_level)
swapouts=$(vm_stat | awk '/Swapouts/ {print $2}' | tr -d '.')
swap=$(sysctl -n vm.swapusage | awk '{print $3}')
echo "pressure=$pressure  swapouts=$swapouts  swap=$swap"
```

| Reading                                          | Decision                                                       |
|--------------------------------------------------|----------------------------------------------------------------|
| `pressure=1` AND `swapouts=0` AND `swap=0.00M`   | **GREEN** — skip every `[RAM-gated]` section in Step 1.        |
| `pressure≥2` OR `swapouts>0` OR `swap` non-zero  | **YELLOW/RED** — run `[RAM-gated]` sections; RAM is a target.  |

Do NOT use "Memory Used" from `top` or Activity Monitor for this decision — on a healthy Mac it sits at 80–95% by design (file cache + compressor + inactive pages) and stopping idle processes does not lower it. The kernel's pressure sysctl and swap-out counter are the only honest signals.

## Step 1: Inventory

Run categories in this order. Always run the un-tagged ones. Only run the `[RAM-gated]` ones if Step 0 returned YELLOW/RED.

### Disk-heavy items (always run)
The dominant cleanup target on a Mac. Each of these can hold tens of GB.
```bash
# Docker images and volumes (if docker installed) — old image layers pile up
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -20
docker system df 2>/dev/null

# Xcode DerivedData — regenerates on next build, often 10+ GB
du -sh ~/Library/Developer/Xcode/DerivedData 2>/dev/null

# iOS Simulator runtime caches (the disk image, not booted sims) — GBs each
du -sh ~/Library/Developer/CoreSimulator/Caches 2>/dev/null

# Homebrew download cache — regenerates on next install
du -sh "$(brew --cache 2>/dev/null)" 2>/dev/null

# Local VM images (tart, UTM, etc.) — ~50–100 GB each, often forgotten
tart list 2>/dev/null
```

Stopped VMs are **disk** decisions, not RAM: only suggest deleting them if the user explicitly wants to reclaim disk; never as a routine sweep.

### Memory pressure baseline [RAM-gated]
```bash
vm_stat | head -5
top -l 1 -n 0 -s 0 | grep -E "PhysMem|CPU usage"
ps -A -o pid,rss,comm | sort -k2 -rn | head -20
```

### Docker containers [RAM-gated]
(Docker *images* live in the Disk-heavy section above and are always inventoried.)
```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}" 2>/dev/null
```

### Dev servers / language runtimes [RAM-gated]
```bash
# Node, Python, Ruby, Go dev processes
ps -A -o pid,rss,etime,command | grep -E "(node|next|vite|webpack|python|uvicorn|gunicorn|celery|rails|puma|sidekiq|go run)" | grep -v grep
# Listening ports (common dev ports) — also surface even when GREEN if blocking a port the user needs
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

### Simulators / emulators / VMs (running ones — always run)
Catches booted simulators and running VMs that *are* burning CPU/RAM. The disk side of VM images is already inventoried under Disk-heavy items above.
```bash
xcrun simctl list devices booted 2>/dev/null
pgrep -lf "Simulator|qemu|VirtualBox|VMware|UTM|tart" 2>/dev/null
```

### Tunnels — ngrok / cloudflared / ssh -L (always run — easy clutter)
Tunnels left open after a demo are a common forgotten item. Tiny RAM cost but they expose ports and confuse later sessions.
```bash
pgrep -lf "ngrok|cloudflared|ssh.*-L" 2>/dev/null
```

### Virtualenvs / sandboxes [RAM-gated]
```bash
# Active python virtualenvs (process-level)
ps -A -o command | grep -E "venv/bin/python|\.venv/bin/python" | grep -v grep
# Orphaned __pycache__ / node_modules size (informational, don't delete)
```

### Browser automation leftovers [RAM-gated]
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

Lead with **disk reclaimed** and **clutter cleared**. Only quote a RAM delta if Step 0 was YELLOW/RED and you actually targeted RAM — otherwise it's noise from unrelated app drift and reporting it implies progress that didn't happen.

```
CLEANUP COMPLETE
================
Disk reclaimed:    150 GB (VM images, 1 worktree, Docker images)
Clutter cleared:   14 stale branches (12 local, 6 remote), 1 ngrok tunnel
Processes stopped: 2 docker containers, 2 dev servers   ← only if Step 0 was YELLOW/RED

[Memory section — include ONLY if Step 0 was YELLOW/RED]
Pressure before: 2 (warn), swapouts climbing
Pressure after:  1 (normal), swapouts flat
```

If Step 0 was GREEN, do **not** print a "Memory before / Memory after" line. The number will look bad (it often goes up during a cleanup window from unrelated app drift) and creates the wrong impression about what the skill is for.

## Things this skill does NOT do

- Does not run `docker system prune` (data loss risk)
- Does not delete `node_modules` or `__pycache__` (the user can rerun `npm install` but it's slow)
- Does not uninstall packages or clear Homebrew caches
- Does not log out of services or revoke tokens
- Does not touch anything under `/System`, `/Library`, or root-owned processes
- Does not restart the machine

If the user wants any of the above, they should ask explicitly.
