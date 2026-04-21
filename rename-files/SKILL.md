---
name: rename-files
description: "Rename files in a directory to have descriptive names. Views images/PDFs to determine content, then proposes renames. Receipts get consistent YYYYMMDD naming."
---

# Rename Files

## When to Use

When the user asks to:
- Rename files on Desktop (or any directory) to have descriptive names
- Clean up generic filenames like `IMG_*.jpeg` or `Screenshot *.png`
- Standardize receipt naming

## iCloud Download Check

**Before doing anything**, check if files are fully downloaded from iCloud:

```bash
# Find iCloud stub files (not yet downloaded)
find <directory> -name '.*.icloud' 2>/dev/null
```

If stubs exist, download them first:
```bash
# Download all iCloud stubs in the directory
find <directory> -name '.*.icloud' -exec brctl download {} \;
```

Wait for downloads to complete before proceeding. Check periodically:
```bash
# Re-check — should return nothing when all downloaded
find <directory> -name '.*.icloud' 2>/dev/null
```

## Process

1. **List files** in the target directory
2. **Identify files needing renames** — files with generic/non-descriptive names:
   - `IMG_*.jpeg/HEIC/PNG` — camera roll photos
   - `Screenshot YYYY-MM-DD at *.png` — macOS screenshots
   - Any other file whose name doesn't describe its content
3. **Skip files that already have good names** — don't touch these:
   - Receipts already in `YYYYMMDD Vendor Amount.ext` format
   - Files with clear descriptive names (e.g., `Apple Form 1095-C...`)
   - Directories
   - Hidden files (`.DS_Store`, `.localized`, etc.)
4. **Read each file** using the Read tool to view its content (works for images and PDFs)
5. **Determine a descriptive name** based on what you see
6. **Present all proposed renames** to the user for approval before executing
7. **Execute renames** using `mv` commands

## Naming Conventions

### Receipts
Files that show a purchase, invoice, bill, or financial transaction:
```
YYYYMMDD Vendor Description Amount.ext
```
Examples:
- `20260202 Aspen Skiing Gold Tune 75.00.HEIC`
- `20260103 DPV Anthropic Claude Pro 21.78.pdf`
- `20260115 Apple AppleCare One 19.99.png`

Rules:
- Date is the transaction/purchase date from the receipt, format `YYYYMMDD`
- Vendor is the business name (short, recognizable)
- Description is a brief note about what was purchased
- Amount is the total with cents, no `$` sign
- Use the original file extension (preserve case)

### Tax / Legal / Government Documents
```
Issuer Document Type Year [details].ext
```
Examples:
- `Apple Form 1095-C Health Insurance 2025 p1.HEIC`
- `EFTPS Enrollment Letter 2026-01-28.HEIC`
- `NY State Dept of Labor Notice.HEIC`

### Screenshots
Rename based on what the screenshot shows:
```
Descriptive Name of Content.png
```
Examples:
- `Carta Equity Grants First 5 Engineers.PNG`
- `Linear Roadmap Sprint 14.png`

If a screenshot is of a receipt, use the receipt naming convention instead.

### General Photos
Rename based on what the photo shows:
```
Descriptive Name [optional date context].ext
```
Keep it concise but clear enough to find later.

### Business Documents
```
Company/Source Document Description [date if relevant].ext
```
Examples:
- `Withum Investment Response.pdf`
- `circit_evidence_provider_tos_31012025.pdf` (already fine)

## Important Rules

- **ALWAYS confirm renames with the user before executing.** Present a table of old → new names.
- **NEVER overwrite existing files.** If the proposed new name already exists, append a number suffix.
- **Preserve file extensions exactly** (including case: `.HEIC` stays `.HEIC`, `.png` stays `.png`).
- **Use `mv` to rename** — single atomic operation per file.
- **Quote all paths** — filenames may contain spaces, parentheses, dollar signs.
- If you can't determine what a file contains (blurry, unclear), ask the user.
- Process files in batches of ~5–8 to keep confirmation manageable.
- For the Desktop specifically, the path is `~/Desktop/`.
