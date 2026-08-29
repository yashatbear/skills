/**
 * find-browse — locate the browse binary.
 *
 * Compiled to browse/dist/find-browse (standalone binary, no bun runtime needed).
 * Outputs the absolute path to the browse binary on stdout, or exits 1 if not found.
 */

import { existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

// ─── Binary Discovery ───────────────────────────────────────────

function getGitRoot(): string | null {
  try {
    const proc = Bun.spawnSync(['git', 'rev-parse', '--show-toplevel'], {
      stdout: 'pipe',
      stderr: 'pipe',
    });
    if (proc.exitCode !== 0) return null;
    return proc.stdout.toString().trim();
  } catch {
    return null;
  }
}

export function locateBinary(): string | null {
  const root = getGitRoot();
  const home = homedir();
  const relPath = join('.claude', 'skills', 'browse', 'dist', 'browse');

  // Repo-local takes priority (for development)
  if (root) {
    const local = join(root, relPath);
    if (existsSync(local)) return local;
  }

  // Global fallback (~/.claude/skills/browse/dist/browse)
  const global = join(home, relPath);
  if (existsSync(global)) return global;

  return null;
}

// ─── Main ───────────────────────────────────────────────────────

function main() {
  const bin = locateBinary();
  if (!bin) {
    process.stderr.write('ERROR: browse binary not found. Build it: bun build --compile src/cli.ts --outfile dist/browse\n');
    process.exit(1);
  }

  console.log(bin);
}

main();
