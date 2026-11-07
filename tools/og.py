"""每章分享图（og:image）：本章原文＋章号＋一孔录印。1200×630，缓存在 tools/og/<变体>/<章号>.jpg。
字体：思源宋体可变字重（共享盘 数据/网站素材/_字体/NotoSerifSC.ttf，不进公开仓库）。没有字体就跳过，页面回落到全站横幅。"""
import os, hashlib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_字体/NotoSerifSC.ttf"
W, H = 1200, 630
BG, INK, MUTE, RED, LINE = (246, 241, 230), (42, 36, 29), (123, 111, 95), (163, 48, 31), (228, 217, 195)

def _font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > width and cur:
            if ch in "，。；：？！、”’」』）":  # 标点不出现在行首
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

def available():
    return os.path.exists(FONT)

def make(variant, c, head, text, foot):
    """返回相对路径 og/<variant>/<c>.jpg；内容变了才重画。"""
    sig = hashlib.md5(f"{head}|{text}|{foot}|v1".encode()).hexdigest()[:10]
    d = os.path.join(HERE, "og", variant); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"{c}.jpg"); sigf = out + ".sig"
    if os.path.exists(out) and os.path.exists(sigf) and open(sigf).read() == sig:
        return f"og/{variant}/{c}.jpg"
    im = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(im)
    dr.rectangle([28, 28, W - 29, H - 29], outline=LINE, width=2)
    dr.rectangle([28, 28, 40, H - 29], fill=RED)
    hf = _font(30, 600); dr.text((84, 66), head, font=hf, fill=RED)
    # 原文：字号从大往小试，最多 5 行；还放不下就截断加省略号
    box_w, box_h = W - 84 - 90, 380
    for size in (64, 58, 52, 46, 42, 38):
        f = _font(size, 600); lines = _wrap(dr, text, f, box_w); lh = int(size * 1.55)
        if len(lines) * lh <= box_h: break
    maxl = box_h // lh
    if len(lines) > maxl:
        lines = lines[:maxl]; lines[-1] = lines[-1][:-1] + "……"
    y = 130 + (box_h - len(lines) * lh) // 2
    for ln in lines:
        dr.text((84, y), ln, font=f, fill=INK); y += lh
    dr.line([84, H - 104, W - 90, H - 104], fill=LINE, width=2)
    seal = Image.open(os.path.join(HERE, "assets", "seal-180.png")).convert("RGBA").resize((60, 60))
    im.paste(seal, (84, H - 88), seal)
    dr.text((160, H - 86), "一孔录", font=_font(34, 900), fill=INK)
    dr.text((278, H - 78), foot, font=_font(24, 400), fill=MUTE)
    uf = _font(24, 400); dr.text((W - 90 - dr.textlength("yikonglu.com", font=uf), H - 78), "yikonglu.com", font=uf, fill=MUTE)
    im.save(out, quality=86, optimize=True, progressive=True); open(sigf, "w").write(sig)
    return f"og/{variant}/{c}.jpg"


def _wrap_words(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur: lines.append(cur)
    return lines

def _clip(lines, n, ell):
    if len(lines) <= n: return lines
    lines = lines[:n]; lines[-1] = lines[-1].rstrip("，,;；:： ") + ell
    return lines

def make3(c, head, text, en, ja, foot):
    """三语分享图：原文＋英译＋日译，一张图给所有语种。返回 og/tri/<c>.jpg。"""
    sig = hashlib.md5(f"{head}|{text}|{en}|{ja}|{foot}|t4".encode()).hexdigest()[:10]
    d = os.path.join(HERE, "og", "tri"); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"{c}.jpg"); sigf = out + ".sig"
    if os.path.exists(out) and os.path.exists(sigf) and open(sigf).read() == sig:
        return f"og/tri/{c}.jpg"
    im = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(im)
    dr.rectangle([28, 28, W - 29, H - 29], outline=LINE, width=2)
    dr.rectangle([28, 28, 40, H - 29], fill=RED)
    dr.text((84, 58), head, font=_font(28, 600), fill=RED)
    bw = W - 84 - 90; top, bottom = 108, H - 122
    for size, yl, el, jl, sf in ((52, 3, 3, 2, 24), (48, 3, 3, 2, 24), (46, 3, 2, 2, 24), (42, 3, 2, 2, 22), (40, 3, 2, 1, 22), (38, 3, 2, 1, 22), (36, 3, 1, 1, 22), (34, 3, 1, 1, 20)):
        f = _font(size, 600); lh = int(size * 1.45); ff = _font(sf, 400); slh = int(sf * 1.5)
        L1 = _clip(_wrap(dr, text, f, bw), yl, "……")
        L2 = _clip(_wrap_words(dr, en, ff, bw), el, "…") if en else []
        L3 = _clip(_wrap(dr, ja, ff, bw), jl, "…") if ja else []
        need = len(L1) * lh + 36 + (len(L2) * slh + 10 if L2 else 0) + (len(L3) * slh if L3 else 0)
        if need <= bottom - top: break
    y = top
    for ln in L1: dr.text((84, y), ln, font=f, fill=INK); y += lh
    y += 12; dr.line([84, y, 150, y], fill=RED, width=3); y += 24
    for ls in (L2, L3):
        for ln in ls: dr.text((84, y), ln, font=ff, fill=(74, 72, 64)); y += slh
        if ls: y += 10
    dr.line([84, H - 104, W - 90, H - 104], fill=LINE, width=2)
    seal = Image.open(os.path.join(HERE, "assets", "seal-180.png")).convert("RGBA").resize((60, 60))
    im.paste(seal, (84, H - 88), seal)
    dr.text((160, H - 86), "一孔录", font=_font(34, 900), fill=INK)
    dr.text((278, H - 78), foot, font=_font(24, 400), fill=MUTE)
    uf = _font(24, 400); dr.text((W - 90 - dr.textlength("yikonglu.com", font=uf), H - 78), "yikonglu.com", font=uf, fill=MUTE)
    im.save(out, quality=86, optimize=True, progressive=True); open(sigf, "w").write(sig)
    return f"og/tri/{c}.jpg"
