"""一孔印压版框右下角（主人 11-16 定“压版框不压字”）。
找版框最下一道横粗线、最右一道竖粗线，印心对准两线交点；印落进框内那一角若有正文墨迹，就沿对角线往外挪，直到不压字。
页底来源行改为右对齐，止于印左 0.8% 页宽处，免得和印相碰。"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def runs(b):
    out=[];s=None
    for i,v in enumerate(b):
        if v and s is None: s=i
        if not v and s is not None: out.append((s,i-1)); s=None
    if s is not None: out.append((s,len(b)-1))
    return out

def frame_corner(gray, thr=140):
    h,w=gray.shape; d=gray<thr
    rr=[r for r in runs(d.mean(1)>0.35) if r[0]>h*0.6]
    y0,y1=rr[-1]
    cc=[r for r in runs(d[int(h*0.3):y0].mean(0)>0.35) if r[0]>w*0.6]
    x0,x1=cc[-1]
    return x0,x1,y0,y1

def seal_pos(gray, S, thr=110, pad=8):
    """找不到版框角（底边没框线、角不在右下四分之一以内）或挪到底仍压字，返回 None：照旧放回原位置（版框外右下）。"""
    h,w=gray.shape
    try: x0,x1,y0,y1=frame_corner(gray)
    except IndexError: return None
    if not (x1>w*0.85 and y1>h*0.85): return None
    d=(gray<thr).copy()
    # 版框线（长横线、长竖线）不算正文：整行/整列黑的比例高的先抹掉
    lr=d.mean(1)>0.30; d[lr]=False
    lc=d[int(h*0.3):y0].mean(0)>0.30; d[:,lc]=False
    # 腐蚀一次：抹掉一两像素宽的细线和噪点，正文笔画粗，留得下
    from PIL import ImageFilter
    d=np.array(Image.fromarray((d*255).astype('uint8')).filter(ImageFilter.MinFilter(5)))>0
    cx,cy=(x0+x1)/2,(y0+y1)/2
    for step in range(0,S):
        L,T=int(cx-S/2+step),int(cy-S/2+step)
        inner=d[T:y0-pad, L:x0-pad]
        if inner.size==0 or inner.mean()<0.01: break
    else: return None
    return L,T,step,(x0,x1,y0,y1)

def stamp(img, seal, footer, font_path, color, S=None):
    w,h=img.size; S=S or round(w*0.041)
    g=np.array(img.convert('L'))
    r=seal_pos(g,S)
    if r is None: return None,None   # 交回原角标流程
    L,T,step,(x0,x1,y0,y1)=r
    out=img.convert('RGBA')
    fs=round(w*0.0195); f=ImageFont.truetype(font_path,fs); d=ImageDraw.Draw(out)
    tw=d.textlength(footer,font=f); gap=round(w*0.008)
    ty=(y1+h)/2
    d.text((L-gap-tw,ty),footer,font=f,fill=color,anchor='lm')
    out.alpha_composite(seal.resize((S,S),Image.LANCZOS),(L,T))
    return out.convert('RGB'),dict(seal=(L,T,S),moved=step,frame=(x0,x1,y0,y1))
