import markdown, base64, re, os
from playwright.sync_api import sync_playwright
md = open("PAPER.md").read()
# embed figures as base64
for fn in ["fig1_calibration.png", "fig_leaderboard_ci.png"]:
    uri = "data:image/png;base64," + base64.b64encode(open(fn, "rb").read()).decode()
    md = md.replace(f"]({fn})", f"]({uri})")
body = markdown.markdown(md, extensions=["tables", "sane_lists"])
css = """
@page{size:A4;margin:20mm 18mm}
*{box-sizing:border-box}
body{font-family:Georgia,'Times New Roman',serif;font-size:10.3pt;line-height:1.5;color:#1a1a1a}
h1{font-size:18pt;line-height:1.25;margin:0 0 2pt;font-weight:700}
h2{font-size:12.5pt;font-weight:700;margin:16pt 0 5pt;padding-bottom:2pt;border-bottom:1.3px solid #333;page-break-after:avoid}
h1+h2{font-size:12pt;font-weight:400;font-style:italic;color:#444;border:none;margin-top:2pt}
h3{font-size:10.8pt;font-weight:700;margin:12pt 0 4pt;page-break-after:avoid}
p{margin:0 0 7pt;text-align:justify}
strong{font-weight:700}
hr{border:none;border-top:1px solid #ccc;margin:12pt 0}
ul,ol{margin:0 0 7pt;padding-left:18pt}
li{margin:0 0 3pt;text-align:justify}
code{font-family:Menlo,Consolas,monospace;font-size:8.8pt;background:#f4f4f4;padding:1px 3px;border-radius:2px}
table{border-collapse:collapse;width:100%;margin:6pt 0 10pt;font-size:9.2pt;font-family:Helvetica,Arial,sans-serif;page-break-inside:avoid}
th{background:#222;color:#fff;text-align:left;padding:5pt 8pt;font-weight:600;font-size:8.8pt}
td{border-bottom:1px solid #ddd;padding:4pt 8pt}
tr:nth-child(even) td{background:#fafafa}
img{display:block;width:82%;margin:8pt auto 2pt;border:1px solid #e5e5e5;border-radius:3px}
em{color:#333}
p>em:only-child{display:block;font-size:8.8pt;color:#555;text-align:center;margin:-2pt auto 10pt;max-width:92%}
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
open("_paper.html", "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    pg = b.new_page(); pg.goto("file://" + os.path.abspath("_paper.html"))
    pg.pdf(path="ARC_Paper_Draft.pdf", format="A4", print_background=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    b.close()
print("built ARC_Paper_Draft.pdf", os.path.getsize("ARC_Paper_Draft.pdf"))
