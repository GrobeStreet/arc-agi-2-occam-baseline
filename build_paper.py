#!/usr/bin/env python3
"""Build the canonical ARC Measurement Audit v2 PDF from PAPER_V2.md.

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
PAPER = ROOT / "PAPER_V2.md"
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
    markers = ["\n---\n\n## 8. What is established", "\n---\n\n## 9. Reporting standard", "\n---\n\n## 10. Limitations"]
    for marker in markers:
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
    p { margin: 5pt 0 8pt; orphans: 3; widows: 3; }
    ul, ol { margin: 5pt 0 8pt 18pt; padding-left: 8pt; }
    li { margin: 1.8pt 0; }
    blockquote {
      border-left: 3px solid #0b6d59;
      color: #374151;
      margin: 8pt 0;
      padding: 2pt 0 2pt 10pt;
    }
    table {
      border-collapse: collapse;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 8.5pt;
      margin: 8pt 0 12pt;
      page-break-inside: avoid;
      width: 100%;
    }
    th, td { border: 1px solid #9ca3af; padding: 4pt 5pt; vertical-align: top; }
    th { background: #e8ecef; font-weight: 700; }
    tr:nth-child(even) td { background: #f8fafc; }
    code {
      background: #f1f5f9;
      border-radius: 2px;
      font-family: 'Courier New', monospace;
      font-size: 8.8pt;
      padding: 0.4pt 2pt;
    }
    pre {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      font-size: 8pt;
      overflow-wrap: anywhere;
      padding: 7pt;
      white-space: pre-wrap;
    }
    img {
      display: block;
      height: auto;
      margin: 10pt auto 4pt;
      max-height: 190mm;
      max-width: 100%;
      object-fit: contain;
      page-break-inside: avoid;
    }
    hr { border: 0; border-top: 1px solid #cbd5e1; margin: 14pt 0; }
    a { color: #0b5f92; text-decoration: none; }
    strong { color: #111827; }
    """
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
    HTML_OUTPUT.write_text(html, encoding="utf-8")

    executable = os.environ.get("CHROMIUM_EXECUTABLE")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=executable if executable else None,
        )
        page = browser.new_page(viewport={"width": 1200, "height": 1600})
        page.goto(HTML_OUTPUT.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
