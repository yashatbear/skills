# icons-cache — local SF Symbol render cache

Local cache of SF Symbols rendered to alpha PNGs, for the `artifact` skill's
`sf-icons.sh`. It exists so you don't re-render the same glyphs via AppKit/`swift`
on every artifact build — a symbol is rendered **once**, cached here, and reused by
every future run.

> **This cache is not committed, and ships empty.** Apple's SF Symbols license
> restricts redistributing the glyph artwork, so this repo does not include
> pre-rendered PNGs — you generate your own locally, on macOS. The cache is
> gitignored (`icons-cache/*/`). Do not push rendered SF Symbols to a public repo.

## Layout

```
icons-cache/
  <weight>-<pt>/          # render config, e.g. regular-160, semibold-200
    <name>.png            # one alpha PNG per symbol; dots in the SF name -> hyphens
                          #   lock            -> lock.png
                          #   paperplane.fill -> paperplane-fill.png
```

`<weight>` is one of `ultralight thin light regular medium semibold bold heavy black`;
`<pt>` is the render point size. `regular-160` is the default.

## How it's populated (automatic)

You don't edit this folder by hand. `sf-icons.sh` manages it:

1. It checks here first — a cached symbol emits instantly, with **no `swift` render**.
2. Anything not cached is rendered via AppKit and **written back here**.

So just call the script normally with whatever symbols your page needs:

```bash
bash ../sf-icons.sh lock bolt airplane creditcard.fill > icons.css
```

Any new symbol you use lands here as a new `.png`. The first run that needs a given
glyph is the only one that touches `swift`; every later run for that symbol is a cache
hit — so once your common set is cached, `sf-icons.sh` runs even on a Mac without the
Xcode Command Line Tools.

## Prerequisites (macOS, one-time)

Rendering an uncached symbol needs:

- the [SF Symbols app](https://developer.apple.com/sf-symbols/), and
- the Xcode Command Line Tools — `xcode-select --install` (provides `swift`).

Notes
- These are alpha PNGs (glyph coverage only); the page tints them via `currentColor`,
  so one file serves both light and dark. Do not hand-edit the PNGs.
- A genuinely missing/renamed symbol produces no file (it's reported on stderr and left
  as a `/* MISSING */` comment) — nothing to cache in that case.
- `bash ../sf-icons.sh --no-cache <name>` renders fresh without reading or writing here
  (for one-off exotic weights/sizes you don't want to persist).
- The rendered bytes are inlined as `data:` URIs into each artifact, so pages stay fully
  self-contained; this folder only removes the *repeated render cost*.
</content>
