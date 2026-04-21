---
name: ghostty
description: Configure and manage the Ghostty terminal emulator. Use this when modifying terminal appearance, keybindings, or behavior.
---

# Ghostty Terminal

Ghostty is a fast, native macOS terminal emulator. It uses Apple's Metal graphics API natively, avoiding the OpenGL rendering issues that affect some other terminals on macOS (Apple suspended active OpenGL development in favor of Metal starting with macOS Mojave).

## Config locations

- **Main config:** `~/.config/ghostty/config`
- **Custom themes:** `~/.config/ghostty/themes/<theme-name>` (no file extension)

If you version-control your dotfiles, a common setup is to keep the real files in a git checkout and symlink `~/.config/ghostty/config` (and `~/.config/ghostty/themes`) into that checkout. Ghostty follows the symlinks transparently.

## Theme

Ghostty supports light/dark auto-switching via the `theme` directive in the main config:

```
theme = light:<light-theme-name>,dark:<dark-theme-name>
```

This reads `~/.config/ghostty/themes/<theme-name>` for each mode. You can use built-in themes (run `ghostty +list-themes` for the full list) or drop your own into `~/.config/ghostty/themes/`.

A warm-dark aesthetic works well:
- A monospace font like SF Mono at 13pt, with a small line-height boost
- Background opacity around 0.75 with a blur radius (e.g. 20px) for a frosted-glass look
- Hidden titlebar, generous padding

Pick any palette you like — Ghostty's theme file format is small and well-documented.

## Key bindings

Examples of custom bindings you can set in the main config:

- **Cmd+D** — split right
- **Cmd+Shift+D** — split down
- **Cmd+Shift+Enter** — toggle split zoom
- **Opt+Tab** — cycle to next split
- **Cmd+T** — new tab
- **Cmd+W** — close surface

Ghostty defaults (not overridden by the above):

- **Cmd+[** / **Cmd+]** — previous / next split
- **Cmd+Opt+Arrow** — focus split in direction
- **Cmd+Ctrl+Arrow** — resize active split by 10
- **Cmd+Ctrl+=** — equalize splits

Run `ghostty +list-keybinds` for the full list.

## Troubleshooting

### Symlinks missing or broken

If you're using the symlinked-dotfiles setup, confirm with `ls -la ~/.config/ghostty/` — both `config` and `themes` should be symlinks pointing into your dotfiles checkout. If either is a regular file or missing, recreate:

```bash
rm -f ~/.config/ghostty/config
rm -rf ~/.config/ghostty/themes
ln -s /path/to/your/dotfiles/ghostty/config ~/.config/ghostty/config
ln -s /path/to/your/dotfiles/ghostty/themes ~/.config/ghostty/themes
```

### Dark mode not working

When the config uses `theme = light:<light>,dark:<dark>`, Ghostty requires matching theme files in `~/.config/ghostty/themes/`. If those files are missing, Ghostty silently falls back to whatever `foreground`/`background` values are in the main config (or its defaults). First check the themes directory, then confirm the main config uses the `theme` directive and does **not** have hardcoded `foreground`, `background`, or `palette` lines — those override the theme.

## Editing the config

Ghostty reads `~/.config/ghostty/config` on launch. Changes take effect on restart (no hot-reload — quit and reopen, or use `ghostty +show-config` to validate before restarting). Custom themes live in `~/.config/ghostty/themes/` (no file extension).
