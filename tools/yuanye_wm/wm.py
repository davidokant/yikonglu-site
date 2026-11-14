#!/usr/bin/env python3
"""原页图角标（11-14 定“让抄袭帮我们扩散”第一项）：每张原页右下角印“一孔录 yikonglu.com · 书 卷 · 第 N 页”＋一孔印。
印只许用工坊 assets/一孔印.png 原件（sha256 4d0d4d02…6378），脚本先核 sha，不对就停。
印镂空（只留朱色笔画），连同两行小字直接压在书页右下角，三本书都不改图尺寸。
用法：python3 wm.py <一孔印.png> <原图目录> <出图目录> <书 lunyu|ddj|szj> [页 p013 ...]"""
import sys, os, json, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageStat
SEAL_SHA = "4d0d4d02"
FONT = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_字体/NotoSerifSC.ttf"
CN = "〇一二三四五六七八九十"
def cn(n): return CN[n] if n <= 10 else ("十" + (CN[n-10] if n > 10 else "")) if n < 20 else CN[n//10] + "十" + (CN[n%10] if n % 10 else "")
PIAN = ["学而", "为政", "八佾", "里仁", "公冶长", "雍也", "述而", "泰伯", "子罕", "乡党", "先进", "颜渊", "子路", "宪问", "卫灵公", "季氏", "阳货", "微子", "子张", "尧曰"]
LY = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_原文/论语原文-集注分章-v1.json"
def label(book, p):
    n = int(p[1:])
    if book == "lunyu":
        first = {}
        for c, v in json.load(open(LY, encoding="utf-8")).items(): first.setdefault(int(c.split(".")[0]), v["pdf_page"])
        pn = max([k for k, v in first.items() if v <= n] or [0])
        if not pn: return f"论语集注 · 第 {n} 页"
        return f"论语集注 卷{cn((pn + 1) // 2)} {PIAN[pn-1]} · 第 {n} 页"
    if book == "ddj": return f"老子道德经 王弼注 卷{'上' if n < 95 else '下'} · 第 {n} 页"
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
def mark(im, seal, text, book):
    W, H = im.size
    s = max(44, int(W * 0.045))  # 印边长
    fs = max(20, int(W * 0.018))
    f = ImageFont.truetype(FONT, fs); f.set_variation_by_axes([500]) if hasattr(f, "set_variation_by_axes") else None
    t1 = "一孔录 yikonglu.com"; t2 = text
    tw = max(f.getlength(t1), f.getlength(t2)); pad = int(s * 0.3)
    out = im.convert("RGBA"); y0 = H - s - pad
    sl = hollow(seal).resize((s, s), Image.LANCZOS)
    x_seal = W - pad - s
    lay = Image.new("RGBA", out.size, (0, 0, 0, 0)); lay.paste(sl, (x_seal, y0), sl)
    d = ImageDraw.Draw(lay)
    tx = x_seal - int(pad * 0.6) - tw
    halo = (246, 243, 234, 200)  # 字周一圈纸色描边，压在字上也认得出，又不整块盖住
    d.text((tx + tw - f.getlength(t1), y0 + s * 0.02), t1, font=f, fill=(35, 80, 63, 230), stroke_width=max(2, fs // 8), stroke_fill=halo)
    d.text((tx + tw - f.getlength(t2), y0 + s * 0.98 - fs * 1.15), t2, font=f, fill=(90, 86, 78, 230), stroke_width=max(2, fs // 8), stroke_fill=halo)
    return Image.alpha_composite(out, lay).convert("RGB")
if __name__ == "__main__":
    sp, src, dst, book = sys.argv[1:5]
    if not hashlib.sha256(open(sp, "rb").read()).hexdigest().startswith(SEAL_SHA): sys.exit("一孔印不是工坊原件（sha 不对），停。")
    seal = Image.open(sp); os.makedirs(dst, exist_ok=True)
    pages = sys.argv[5:] or sorted(f[:-4] for f in os.listdir(src) if f.endswith(".jpg"))
    for p in pages:
        im = Image.open(os.path.join(src, p + ".jpg"))
        mark(im, seal, label(book, p), book).save(os.path.join(dst, p + ".jpg"), quality=88, optimize=True)
        print(p, label(book, p))
