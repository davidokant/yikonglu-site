"""开放下载 PDF 加一孔录署名（11-08 主人定，防扩散后被冒名）：每页页脚居中小印＋“一孔录 · yikonglu.com · 免费读本，转载请署名”，元数据作者填一孔录。
用法：python3 tools/duben_mark.py 原.pdf 出.pdf [标题]。重复跑会叠两层，须从未加过的原件出。"""
import io, sys, os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
SEAL = os.path.join(HERE, "..", "docs", "assets", "seal-180.png")
pdfmetrics.registerFont(TTFont("ZH", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))
TXT = "一孔录 · yikonglu.com · 免费读本，转载请署名"
TXT_HANT = "一孔錄 · yikonglu.com · 免費讀本，轉載請署名"

def stamp(w, h, TXT=TXT):
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(w, h)); fs = 6.5
    tw = pdfmetrics.stringWidth(TXT, "ZH", fs); sz = 9; gap = 3; x0 = (w - (sz + gap + tw)) / 2; y = 16
    c.drawImage(SEAL, x0, y - 2, sz, sz, mask="auto")
    c.setFont("ZH", fs); c.setFillColorRGB(0.45, 0.45, 0.42); c.drawString(x0 + sz + gap, y, TXT)
    c.save(); b.seek(0); return PdfReader(b).pages[0]

def main(src, dst, title=None):
    r = PdfReader(src); wtr = PdfWriter(); cache = {}
    for p in r.pages:
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        k = (round(w), round(h))
        if k not in cache: cache[k] = stamp(w, h, TXT_HANT if "hant" in os.path.basename(dst) else TXT)
        p.merge_page(cache[k]); wtr.add_page(p)
    md = {k: v for k, v in (r.metadata or {}).items()}
    md.update({"/Author": "一孔录 Yikonglu", "/Creator": "一孔录 yikonglu.com", "/Producer": "一孔录 yikonglu.com",
               "/Subject": "一孔录免费读本 · https://yikonglu.com · 转载请署名“一孔录 yikonglu.com”", "/Keywords": "一孔录, Yikonglu, yikonglu.com"})
    if title: md["/Title"] = title
    wtr.add_metadata(md); wtr.compress_identical_objects()
    with open(dst, "wb") as f: wtr.write(f)

if __name__ == "__main__": main(*sys.argv[1:])
