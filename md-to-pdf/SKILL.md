---
name: md-to-pdf
description: Convert Markdown files to beautifully formatted PDFs using WeasyPrint. Use this skill whenever the user asks to convert .md files to .pdf, export markdown as PDF, or create a PDF from markdown content.
---

# Markdown to PDF Conversion

## Setup

Dependencies are already installed under Homebrew Python 3.14. If they need reinstalling:
```bash
/opt/homebrew/bin/python3.14 -m pip install --break-system-packages markdown weasyprint pygments
```

Also requires `pango` via Homebrew (`brew install pango`).

For Mermaid diagram support (optional), install the Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
```

## Usage

**IMPORTANT**: Always use `/opt/homebrew/bin/python3.14` to run the script (system Python cannot find the Homebrew libraries).

```bash
/opt/homebrew/bin/python3.14 .claude/skills/md-to-pdf/md_to_pdf.py input.md output.pdf
```

Or with a custom title:

```bash
/opt/homebrew/bin/python3.14 .claude/skills/md-to-pdf/md_to_pdf.py input.md output.pdf "My Document Title"
```

After generating the PDF, open it for the user:
```bash
open output.pdf
```

## Style Variants

- **Sans-serif / modern**: Change body font-family to `'Helvetica Neue', 'Arial', sans-serif`
- **Wider margins**: Increase `@page margin` to `1.25in 1.5in`
- **Tighter**: Use `font-size: 10pt` and `line-height: 1.45`

## Notes

- WeasyPrint handles page breaks, headers/footers, and print CSS natively
- For syntax highlighting in code blocks, the script includes Pygments CSS
- Images referenced in markdown must use absolute paths or be co-located with the markdown file
- The script auto-derives the PDF filename from the input if not specified
- ` ```mermaid ` fenced blocks are rendered to SVG via `mmdc` and embedded as images. If `mmdc` isn't on PATH, those blocks fall through and render as plain code (with a warning).

