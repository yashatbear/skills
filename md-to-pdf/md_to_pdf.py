#!/opt/homebrew/bin/python3.14
"""Convert Markdown files to beautifully formatted PDFs using WeasyPrint.

Mermaid fenced blocks (```mermaid ... ```) are rendered to SVG via mmdc and
embedded as images. Requires `mmdc` on PATH (npm i -g @mermaid-js/mermaid-cli).
If mmdc is missing, mermaid blocks fall through as code.
"""

import markdown
from weasyprint import HTML
import atexit
import sys
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


MERMAID_BLOCK = re.compile(r"^```mermaid\n(.*?)\n```", re.MULTILINE | re.DOTALL)


def _render_mermaid_blocks(md_content: str):
    """Replace ```mermaid blocks with <img> tags pointing at rendered SVGs.

    Returns (rendered_content, svg_dir). svg_dir is the temp directory holding the
    rendered SVGs (which WeasyPrint reads by absolute path during write_pdf) or
    None if nothing was rendered. The caller is responsible for removing svg_dir
    once the PDF has been written.
    """
    if not MERMAID_BLOCK.search(md_content):
        return md_content, None
    if not shutil.which("mmdc"):
        print(
            "Warning: mmdc not found on PATH; mermaid blocks will render as code. "
            "Install: npm i -g @mermaid-js/mermaid-cli",
            file=sys.stderr,
        )
        return md_content, None

    svg_dir = Path(tempfile.mkdtemp(prefix="md_to_pdf_mermaid_"))
    counter = {"i": 0}

    def replace(match: "re.Match[str]") -> str:
        idx = counter["i"]
        counter["i"] += 1
        diagram_src = match.group(1)
        mmd_file = svg_dir / f"diagram-{idx}.mmd"
        svg_file = svg_dir / f"diagram-{idx}.svg"
        mmd_file.write_text(diagram_src)
        result = subprocess.run(
            ["mmdc", "-i", str(mmd_file), "-o", str(svg_file), "-b", "transparent"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not svg_file.exists():
            print(
                f"mmdc failed for diagram {idx}: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return match.group(0)
        # Markdown image syntax with absolute path; surround with blank lines so
        # the markdown parser treats it as a block-level image, not inline text.
        return f"\n![mermaid diagram {idx}]({svg_file})\n"

    return MERMAID_BLOCK.sub(replace, md_content), svg_dir


def md_to_pdf(md_path, pdf_path=None, title=None):
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found")
        sys.exit(1)

    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"

    if title is None:
        title = os.path.splitext(os.path.basename(md_path))[0].replace("-", " ").replace("_", " ").title()

    with open(md_path, "r") as f:
        md_content = f.read()

    md_content, mermaid_dir = _render_mermaid_blocks(md_content)
    # WeasyPrint reads the rendered SVGs by absolute path during write_pdf below,
    # so the temp dir must outlive this call — clean it up at process exit.
    if mermaid_dir is not None:
        atexit.register(shutil.rmtree, mermaid_dir, ignore_errors=True)

    # Convert MD to HTML with useful extensions
    html_body = markdown.markdown(
        md_content,
        extensions=[
            "tables",
            "fenced_code",
            "codehilite",
            "toc",
            "smarty",
            "meta",
        ],
        extension_configs={
            "codehilite": {"css_class": "highlight", "linenums": False},
        },
    )

    # Wrap in full HTML with Apple-inspired styling
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    @page {{
        size: letter;
        margin: 0.45in 0.5in 0.5in 0.5in;
        @bottom-center {{
            content: counter(page);
            font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', Helvetica, sans-serif;
            font-size: 8pt;
            color: #86868b;
        }}
    }}
    body {{
        font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', Helvetica, sans-serif;
        font-size: 10.5pt;
        line-height: 1.35;
        color: #1d1d1f;
        max-width: 100%;
        -webkit-font-smoothing: antialiased;
    }}
    h1 {{
        font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Helvetica, sans-serif;
        font-size: 22pt;
        font-weight: 700;
        letter-spacing: -0.003em;
        margin-top: 0;
        margin-bottom: 0.3em;
        color: #1d1d1f;
    }}
    h2 {{
        font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Helvetica, sans-serif;
        font-size: 14pt;
        font-weight: 600;
        letter-spacing: -0.003em;
        margin-top: 1.0em;
        margin-bottom: 0.3em;
        color: #1d1d1f;
    }}
    h3 {{
        font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Helvetica, sans-serif;
        font-size: 12pt;
        font-weight: 600;
        letter-spacing: -0.003em;
        margin-top: 0.85em;
        margin-bottom: 0.25em;
        color: #1d1d1f;
    }}
    h4 {{
        font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Helvetica, sans-serif;
        font-size: 11pt;
        font-weight: 600;
        margin-top: 1.2em;
        margin-bottom: 0.3em;
        color: #1d1d1f;
    }}
    p {{
        margin-bottom: 0.45em;
        margin-top: 0;
    }}
    strong {{
        font-weight: 600;
        color: #1d1d1f;
    }}
    code {{
        font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
        font-size: 9pt;
        background: #f5f5f7;
        padding: 1.5px 5px;
        border-radius: 4px;
        color: #1d1d1f;
    }}
    pre {{
        background: #f5f5f7;
        border-radius: 10px;
        padding: 16px 20px;
        overflow-x: auto;
        font-size: 8.5pt;
        line-height: 1.52947;
        margin: 1.2em 0;
    }}
    pre code {{
        background: none;
        padding: 0;
        font-size: inherit;
    }}
    table {{
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        margin: 1.2em 0;
        font-size: 10pt;
        border-radius: 8px;
        overflow: hidden;
    }}
    th {{
        background: #f5f5f7;
        font-weight: 600;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 1px solid #d2d2d7;
        color: #1d1d1f;
    }}
    td {{
        padding: 10px 14px;
        border-bottom: 1px solid #e8e8ed;
        color: #1d1d1f;
    }}
    tr:last-child td {{
        border-bottom: none;
    }}
    blockquote {{
        border-left: 3px solid #d2d2d7;
        margin: 1.2em 0;
        padding: 0.4em 1.2em;
        color: #6e6e73;
    }}
    blockquote p {{
        margin-bottom: 0.4em;
    }}
    ul, ol {{
        margin-bottom: 0.7em;
        margin-top: 0;
        padding-left: 1.4em;
    }}
    li {{
        margin-bottom: 0.15em;
    }}
    li > ul, li > ol {{
        margin-top: 0.25em;
        margin-bottom: 0.1em;
    }}
    a {{
        color: #0066cc;
        text-decoration: none;
    }}
    hr {{
        border: none;
        border-top: 1px solid #d2d2d7;
        margin: 2em 0;
    }}
    img {{
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    # Use the markdown file's directory as base_url so relative images resolve
    base_url = os.path.dirname(os.path.abspath(md_path))
    HTML(string=html, base_url=base_url).write_pdf(pdf_path)
    print(f"Created {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <input.md> [output.pdf] [title]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    doc_title = sys.argv[3] if len(sys.argv) > 3 else None
    md_to_pdf(input_path, output_path, doc_title)
