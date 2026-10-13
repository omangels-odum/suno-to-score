"""MusicXML -> PDF met Verovio (betrouwbaarder dan musicxml2ly bij meerdere stemmen per notenbalk).
Gebruik: python3 -I engrave_verovio.py <in.musicxml> <uit.pdf> [schaal]"""
import sys, verovio, tempfile, os
from playwright.sync_api import sync_playwright
src, dst = sys.argv[1], sys.argv[2]; scale = int(sys.argv[3]) if len(sys.argv) > 3 else 40
tk = verovio.toolkit()
tk.setOptions({"pageWidth": 2100, "pageHeight": 2970, "pageMarginLeft": 80, "pageMarginRight": 80, "pageMarginTop": 60,
               "scale": scale, "adjustPageHeight": False, "breaks": "auto", "footer": "none", "lyricSize": 4.0})
tk.loadFile(src)
pages = [tk.renderToSVG(i) for i in range(1, tk.getPageCount() + 1)]
html = "<html><head><style>@page{size:A4;margin:0} body{margin:0} div{page-break-after:always;width:210mm;height:297mm} svg{width:210mm;height:297mm}</style></head><body>" + "".join(f"<div>{p}</div>" for p in pages) + "</body></html>"
tmp = tempfile.mktemp(suffix='.html', dir=os.path.dirname(os.path.abspath(dst))); open(tmp, 'w').write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + tmp); pg.pdf(path=dst, format='A4', print_background=True); b.close()
os.remove(tmp); print('ok', dst, len(pages), "pagina's")
