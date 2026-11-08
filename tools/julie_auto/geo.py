import numpy as np
def runs(a):
    if len(a)==0: return []
    out=[];s=a[0];prev=a[0]
    for v in a[1:]:
        if v!=prev+1: out.append((int(s),int(prev))); s=v
        prev=v
    out.append((int(s),int(prev))); return out
def geom(im):
    b=(im<140); H,W=b.shape
    # 竖粗线：中段行里的暗列，宽 ≥ 8
    mid=b[int(H*0.3):int(H*0.7),:].mean(axis=0)
    vr=[r for r in runs(np.where(mid>0.6)[0]) if r[1]-r[0]>=6]
    R=[r for r in vr if r[0]>W*0.75]; Lf=[r for r in vr if r[1]<W*0.25]
    if not R and not Lf: return None
    if R and Lf: xr=R[-1][0]; xl=Lf[-1][1]  # 右框内沿、左框内沿
    elif Lf: xl=Lf[-1][1]; xr=xl+1234   # 缺一边框（如 p264）：按常见版框宽推
    else: xr=R[-1][0]; xl=xr-1234
    # 横粗线：在框内的行
    rows=b[:, xl+5:xr-5].mean(axis=1)
    hr=[r for r in runs(np.where(rows>0.6)[0]) if r[1]-r[0]>=6]
    T=[r for r in hr if r[1]<H*0.4]; B=[r for r in hr if r[0]>H*0.6]
    if not T and not B: return None
    if T and B: yt=T[-1][1]; yb=B[0][0]
    elif B: yb=B[0][0]; yt=yb-1765   # 缺顶线（如 p264）：按常见版框高推
    else: yt=T[-1][1]; yb=yt+1765
    return dict(xl=xl, xr=xr, yt=yt, yb=yb, cw=(xr-xl)/10)

def geom2(im):
    g=geom(im)
    if not g: return None
    b=(im<170)
    prof=b[g["yt"]+30:g["yb"]-30,:].mean(axis=0)
    W=len(prof)
    # 线性分：把框内高度切 40 段，每段里这一竖条（±1 像素取最暗）几乎全黑才算一段；界栏能连成几十段，字的竖笔最多一两段
    body=b[g["yt"]+30:g["yb"]-30,:]
    bb=body[:, :]
    bb=np.maximum(np.maximum(bb[:, :-2], bb[:, 1:-1]), bb[:, 2:]); bb=np.pad(bb,((0,0),(1,1)))
    hh=bb.shape[0]//40
    seg=bb[:hh*40].reshape(40,hh,W).mean(axis=1)
    ls=(seg>0.85).sum(axis=0)/40.0
    mx=np.array([ls[max(0,x-2):x+3].max() for x in range(W)])
    thick=[r for r in runs(np.where(prof>0.6)[0]) if r[1]-r[0]>=5]
    anchors=[("L",r[1]+1) for r in thick if r[1]<W*0.3]+[("R",r[0]) for r in thick if r[0]>W*0.7]
    best=None
    for side,a in anchors:
        for off in range(0,72,2):
            for per in np.arange(119,124.5,0.1):
                x0=a+off if side=="L" else a-off-10*per
                if x0<0 or x0+10*per>=W-2: continue
                pos=(x0+np.arange(11)*per).astype(int)
                s=mx[pos].sum()
                if best is None or s>best[0]: best=(s,per,x0,side)
    if not best: return None
    s,per,x0,side=best
    g.update(cw=per, x10=x0, xr=x0+10*per, side=side, score=s)
    return g

def cells(im, g, pitch=None):
    """返回 [(col, k, x0,y0,x1,y1, feats)]，col 1 起自右向左，k 0 起自上而下"""
    b=(im<140)
    if pitch is None: pitch=(g["yb"]-g["yt"]-34)/20
    m=(g["yb"]-g["yt"]-20*pitch)/2
    out=[]
    for col in range(1,11):
        x1=g["xr"]-(col-1)*g["cw"]; x0=x1-g["cw"]
        for k in range(20):
            y0=g["yt"]+m+k*pitch; y1=y0+pitch
            cx0,cx1=int(x0+7),int(x1-7); cy0,cy1=int(y0+4),int(y1-4)
            c=b[cy0:cy1,cx0:cx1]
            w=c.shape[1]; mid=w//2
            band=c[:, mid-int(w*0.07):mid+int(w*0.07)+1]
            f=dict(ink=c.mean(), band=band.mean(), bandrows=(band.sum(axis=1)>0).mean(),
                   L=c[:, :mid-int(w*0.07)].mean(), R=c[:, mid+int(w*0.07)+1:].mean())
            out.append((col,k,x0,y0,x1,y1,f))
    return out
