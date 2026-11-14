#!/usr/bin/env python3
"""原页图角标（11-14 定“让抄袭帮我们扩散”第一项）：每张原页右下角印“一孔录 yikonglu.com · 书 卷 · 第 N 页”＋一孔印。
印只许用工坊 assets/一孔印.png 原件（sha256 4d0d4d02…6378），脚本先核 sha，不对就停。
三本同一版式：论语按版框切边，道德经、三字经底下补到同一留白；一行小字在底边白里，镂空印一半压进版框右下角。
论语：建站时 build.py yuanye_wm_out() 每次从 tools/yuanye/ 干净图现出，不用手跑。
道德经、三字经：11-14 已一次性加好、直接改了图片仓库，tools/ddj_pages.json、szj_julie.json 的页高随之改大；
要重出，先从图片仓库 4e6e004（加角标前）取干净图，别对已加角标的图再跑一遍。
用法：python3 wm.py <一孔印.png> <原图目录> <出图目录> <书 lunyu|ddj|szj> [页 p013 ...]"""
import sys, os, json, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageStat
from frame import mb  # 底边留白，与 frame.py 一致
CROP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yuanye_crop_lunyu.json'), encoding='utf-8'))['pages']
SEAL_SHA = "4d0d4d02"
FONT = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_字体/NotoSerifSC.ttf"
CN = "〇一二三四五六七八九十"
def cn(n): return CN[n] if n <= 10 else ("十" + (CN[n-10] if n > 10 else "")) if n < 20 else CN[n//10] + "十" + (CN[n%10] if n % 10 else "")
PIAN = ["学而", "为政", "八佾", "里仁", "公冶长", "雍也", "述而", "泰伯", "子罕", "乡党", "先进", "颜渊", "子路", "宪问", "卫灵公", "季氏", "阳货", "微子", "子张", "尧曰"]
LY = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_原文/论语原文-集注分章-v1.json"
_F = {}
def _first():  # 各篇起页
    if not _F:
        for c, v in json.load(open(LY, encoding="utf-8")).items(): _F.setdefault(int(c.split(".")[0]), v["pdf_page"])
    return _F
def label(book, p):
    """三本同一写法（11-14 主人：书名排版要一致）：书名 注家 卷次 篇名 · 第 N 页。"""
    n = int(p[1:])
    if book == "lunyu":
        first = _first()
        pn = max([k for k, v in first.items() if v <= n] or [0])
        if not pn: return f"论语集注 朱熹 · 第 {n} 页"
        return f"论语集注 朱熹 卷{cn((pn + 1) // 2)} {PIAN[pn-1]} · 第 {n} 页"
    if book == "ddj": return f"老子道德经注 王弼 {'卷上 道经' if n < 95 else '卷下 德经'} · 第 {n} 页"
    return f"三字经训诂 王相 · 第 {n} 页"
def hollow(seal):
    """镂空（11-14 主人：“你把它镂空，这样哪怕覆盖在书页上也不太碍事”）：去掉原件白底，只留朱色笔画；朱色取原件笔画的中位色，不改形。"""
    from PIL import ImageChops
    rgb = seal.convert("RGB"); a0 = seal.getchannel("A") if seal.mode == "RGBA" else Image.new("L", seal.size, 255)
    g = rgb.getchannel("G")  # 白底 G≈255，朱色 G 低
    a = g.point(lambda v: max(0, min(255, int((235 - v) * 255 / 150))))
    a = ImageChops.multiply(a, a0)
    ink = [int(x) for x in ImageStat.Stat(rgb, mask=a.point(lambda v: 255 if v > 200 else 0)).median]
    out = Image.new("RGBA", seal.size, tuple(ink) + (0,)); out.putalpha(a)
    return out
_SL = {}
def _seal(seal, s):
    if (id(seal), s) not in _SL: _SL[(id(seal), s)] = hollow(seal).resize((s, s), Image.LANCZOS)
    return _SL[(id(seal), s)]
def mark(im, seal, text):
    """三本同一版式（11-14 主人：角标、小字、书名排版都要一致）：大小都按图宽同一比例；
    底边留白（frame.mb）里一行小字“一孔录 yikonglu.com · 书名…”，与镂空印下沿齐平；印一半压进版框右下角以内。"""
    W, H = im.size
    s = round(W * 0.045); fs = round(W * 0.018); pad = round(s * 0.3); m = mb(W)
    f = ImageFont.truetype(FONT, fs)
    t1 = "一孔录 yikonglu.com"; t = t1 + " · " + text
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sl = _seal(seal, s); x_seal = W - pad - s; ys = H - m - s // 2  # 截掉印就得截掉书页
    lay.paste(sl, (x_seal, ys), sl)
    sb = sl.getchannel("A").point(lambda v: 255 if v > 60 else 0).getbbox()  # 印笔画的实际外框
    tx = x_seal + sb[0] - round(pad * 0.6) - f.getlength(t)
    ty = ys + sb[3] - f.getbbox(t)[3]  # 一行小字下沿与印下沿齐平（11-14 主人：小字和印要对齐）
    hw = max(2, fs // 8); halo = (246, 243, 234, 170)  # 纸色细描边：压到扫描边的暗纹上也认得出
    d.text((tx, ty), t, font=f, fill=(90, 86, 78, 235), stroke_width=hw, stroke_fill=halo)
    d.text((tx, ty), t1, font=f, fill=(35, 80, 63, 235), stroke_width=hw, stroke_fill=halo)
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
def crop_box(path, p=None):
    """论语原页切框：yuanye_crop_lunyu.json 里有、且图尺寸对得上就用；否则（新页、换了校平图）现找版框。"""
    from PIL import Image as _I
    from frame import box
    W, H = _I.open(path).size; c = CROP.get(p or os.path.basename(path)[:-4])
    return c["box"] if c and (c["W"], c["H"]) == (W, H) else box(path)[0]
def prep(book, im, p, path=None):
    """论语按 yuanye_crop_lunyu.json 切边；道德经、三字经已切（11-13，框外 24／30 像素），底下补纸色到同一留白。"""
    if book == "lunyu": return im.crop(crop_box(path, p) if path else CROP[p]["box"])
    W, H = im.size; have = 24 if book == "ddj" else 30; add = max(0, mb(W) - have)
    paper = tuple(int(v) for v in ImageStat.Stat(im.convert("RGB").crop((0, H - 6, W, H))).median)
    out = Image.new("RGB", (W, H + add), paper); out.paste(im.convert("RGB"), (0, 0)); return out
if __name__ == "__main__":
    sp, src, dst, book = sys.argv[1:5]
    if not hashlib.sha256(open(sp, "rb").read()).hexdigest().startswith(SEAL_SHA): sys.exit("一孔印不是工坊原件（sha 不对），停。")
    seal = Image.open(sp); os.makedirs(dst, exist_ok=True)
    pages = sys.argv[5:] or sorted(f[:-4] for f in os.listdir(src) if f.endswith(".jpg"))
    for p in pages:
        im = Image.open(os.path.join(src, p + ".jpg"))
        mark(prep(book, im, p, os.path.join(src, p + ".jpg")), seal, label(book, p)).save(os.path.join(dst, p + ".jpg"), quality=88, optimize=True)
        print(p, label(book, p))
