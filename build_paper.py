#!/usr/bin/env python3
"""Build the canonical ARC Measurement Audit v2 PDF from PAPER.md.

The builder injects figures generated from committed machine-readable results,
embeds them as data URIs, and uses Playwright's installed Chromium. Set
CHROMIUM_EXECUTABLE only when a non-default browser binary is required.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
PAPER = ROOT / "PAPER.md"
OUTPUT = ROOT / "ARC_Measurement_Audit_v2.pdf"
HTML_OUTPUT = ROOT / "_paper_v2.html"

FIGURES = [
    (
        "fig_v2_task_weighting.png",
        "Figure 1. The original candidate-program-weighted curve and the corrected equal-task estimates. The marginal rise remains descriptive because task composition and held-out targets change with k.",
    ),
    (
        "fig_v2_coverage_reliability.png",
        "Figure 2. Added demonstrations increase conditional candidate reliability while reducing the diagnostic DSL's coverage and leaving end-to-end consensus yield near three percent.",
    ),
    (
        "fig_v2_same_target_delta.png",
        "Figure 3. Same-task, same-target effects of fitting two rather than one demonstration. Every end-to-end quantity moves downward in this representation-limited DSL.",
    ),
    (
        "fig_v2_selection.png",
        "Figure 4. Selection on ambiguous candidate sets. Description length improves over random selection but does not attain the candidate-set oracle.",
    ),
    (
        "fig_v2_consensus_calibration.png",
        "Figure 5. Modal candidate agreement is severely overconfident. Unanimity within a restricted grammar does not imply correctness.",
    ),
]


def inject_figures(source: str) -> str:
    available = [(filename, caption) for filename, caption in FIGURES if (ROOT / filename).exists()]
    if not available:
        return source
    gallery = ["", "---", "", "## Evidence Figures", ""]
    for filename, caption in available:
        gallery.extend([f"![{caption}]({filename})", f"*{caption}*", ""])
    marker = "\n---\n\n## 6. Discussion"
    if marker in source:
        return source.replace(marker, "\n".join(gallery) + marker, 1)
    return source + "\n" + "\n".join(gallery)


def embed_images(source: str) -> str:
    for filename, _ in FIGURES:
        path = ROOT / filename
        if not path.exists():
            continue
        uri = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        source = source.replace(f"]({filename})", f"]({uri})")
    return source


def main() -> None:
    source = PAPER.read_text(encoding="utf-8")
    source = inject_figures(source)
    source = embed_images(source)
    body = markdown.markdown(
        source,
        extensions=["tables", "sane_lists", "fenced_code", "toc"],
    )

    css = """
    @page { size: A4; margin: 19mm 17mm 20mm; }
    * { box-sizing: border-box; }
    html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    body {
      margin: 0;
      color: #17202a;
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 10.2pt;
      line-height: 1.48;
    }
    h1, h2, h3 { page-break-after: avoid; color: #111827; }
    h1 {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 25pt;
      line-height: 1.08;
      letter-spacing: -0.5pt;
      margin: 0 0 5pt;
      padding-top: 7mm;
    }
    h1 + h2 {
      border: 0;
      color: #4b5563;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14pt;
      font-style: normal;
      font-weight: 400;
      line-height: 1.25;
      margin: 0 0 11pt;
      padding: 0;
    }
    h2 {
      border-bottom: 1.4px solid #1f2937;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 13.5pt;
      letter-spacing: -0.15pt;
      margin: 17pt 0 7pt;
      padding-bottom: 3pt;
    }
    h3 {
      font-family: Arial, Helvetica, sans-serif;
      font-size: 11.2pt;
      margin: 12pt 0 4pt;
    }
    p { margin: 0 0 7pt; text-align: justify; }
    strong { color: #111827; }
    em { color: #374151; }
    hr { border: 0; border-top: 1px solid #cbd5e1; margin: 13pt 0; }
    ul, ol { margin: 0 0 8pt; padding-left: 19pt; }
    li { margin: 0 0 3pt; }
    code {
      background: #f1f5f9;
      border-radius: 3px;
      font-family: Menlo, Consolas, monospace;
      font-size: 8.7pt;
      padding: 1px 3px;
    }
    pre {
      background: #f8fafc;
      border: 1px solid #dbe3ec;
      border-radius: 6px;
      line-height: 1.35;
      overflow-wrap: anywhere;
      padding: 9pt;
      page-break-inside: avoid;
      white-space: pre-wrap;
    }
    pre code { background: transparent; padding: 0; }
    table {
      border-collapse: separate;
      border-spacing: 0;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 8.7pt;
      margin: 7pt auto 11pt;
      max-width: 100%;
      page-break-inside: avoid;
      width: 100%;
    }
    thead { display: table-header-group; }
    th {
      background: #1f2937;
      color: white;
      font-size: 8.3pt;
      font-weight: 600;
      line-height: 1.25;
      padding: 6pt 6pt;
      text-align: left;
      vertical-align: middle;
    }
    td {
      border-bottom: 1px solid #dbe3ec;
      line-height: 1.3;
      padding: 5pt 6pt;
      vertical-align: middle;
    }
    tbody tr:nth-child(even) td { background: #f8fafc; }
    img {
      border: 1px solid #dbe3ec;
      border-radius: 5px;
      display: block;
      height: auto;
      margin: 9pt auto 3pt;
      max-height: 178mm;
      max-width: 93%;
      object-fit: contain;
      page-break-inside: avoid;
    }
    p > em:only-child {
      color: #4b5563;
      display: block;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 8.3pt;
      line-height: 1.35;
      margin: 2pt auto 11pt;
      max-width: 90%;
      text-align: center;
    }
    blockquote {
      background: #f8fafc;
      border-left: 4px solid #64748b;
      margin: 9pt 0;
      padding: 8pt 11pt;
    }
    blockquote p { margin: 0; }
    a { color: #1d4ed8; text-decoration: none; }
    """

    html = f"""<!doctype html>
    <html><head><meta charset="utf-8"><title>ARC Measurement Audit v2</title>
    <style>{css}</style></head><body>{body}</body></html>"""
    HTML_OUTPUT.write_text(html, encoding="utf-8")

    with sync_playwright() as playwright:
        executable = os.environ.get("CHROMIUM_EXECUTABLE")
        launch_args = {"executable_path": executable} if executable else {}
        browser = playwright.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1240, "height": 1754})
        page.goto(HTML_OUTPUT.as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template='<div style="font-size:8px;color:#6b7280;width:100%;padding:0 17mm;text-align:right;">ARC Measurement Audit v2</div>',
            footer_template='<div style="font-size:8px;color:#6b7280;width:100%;padding:0 17mm;display:flex;justify-content:space-between;"><span>Robert Morong · July 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
            margin={"top": "19mm", "bottom": "20mm", "left": "17mm", "right": "17mm"},
        )
        browser.close()

    print(f"built {OUTPUT.name}: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
