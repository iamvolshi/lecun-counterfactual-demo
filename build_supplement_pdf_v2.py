"""Build the LeCun supplement v2 PDF from the Markdown draft via WeasyPrint."""
import markdown
from pathlib import Path

SRC = Path("/home/hatch/workspace/lecun-counterfactual-repo/lecun-counterfactual-supplement-draft.md")
OUT_HTML = Path("/home/hatch/workspace/lecun-counterfactual-repo/lecun-counterfactual-supplement-v2.html")
OUT_PDF = Path("/home/hatch/workspace/lecun-counterfactual-repo/lecun-counterfactual-supplement-v2.pdf")

md = SRC.read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["fenced_code", "tables"])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Keeping the What-If: A Record for Counterfactual World Models</title>
<style>
@page {{
  size: Letter;
  margin: 2.5cm 2.5cm 2.5cm 2.5cm;
  @bottom-center {{ content: counter(page); font-size: 9pt; color: #666; }}
}}
body {{
  font-family: "Liberation Serif", "DejaVu Serif", Georgia, serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #111;
}}
h1 {{ font-size: 17pt; line-height: 1.3; margin: 0 0 6pt 0; }}
h2 {{ font-size: 13pt; margin: 18pt 0 6pt 0; page-break-after: avoid; }}
p {{ margin: 0 0 8pt 0; text-align: justify; }}
ul {{ margin: 0 0 8pt 0; }}
li {{ margin: 0 0 4pt 0; }}
pre {{
  font-family: "Liberation Mono", "DejaVu Sans Mono", monospace;
  font-size: 9pt;
  line-height: 1.4;
  background: #f6f6f6;
  border: 1px solid #ddd;
  padding: 8pt 10pt;
  white-space: pre-wrap;
  word-wrap: break-word;
  page-break-inside: avoid;
}}
code {{ font-family: "Liberation Mono", "DejaVu Sans Mono", monospace; font-size: 9.5pt; }}
a {{ color: #111; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

OUT_HTML.write_text(html, encoding="utf-8")
print("wrote", OUT_HTML)

from weasyprint import HTML
HTML(filename=str(OUT_HTML)).write_pdf(str(OUT_PDF))
print("wrote", OUT_PDF, OUT_PDF.stat().st_size, "bytes")
