import numpy as np
from geo import geom2
import geo3
def geom4(im):
    g=geom2(im)
    if not g: return None
    b=(im<170); H,W=b.shape
    bm=np.maximum(np.maximum(b[:, :-2], b[:, 1:-1]), b[:, 2:]); bm=np.pad(bm,((0,0),(1,1)))
    yt,yb=int(g["yt"]),int(g["yb"])
    offs=np.arange(-30,31); pers=np.arange(g["cw"]-2,g["cw"]+2.01,0.1)
    I=np.arange(11)
    rows=[]
    for y in range(yt+15,yb-115,50):
        ls=bm[y:y+100].mean(axis=0)
        X=(g["x10"]+offs[:,None,None]+pers[None,:,None]*I[None,None,:]).round().astype(int)
        X=np.clip(X,0,W-1)
        S=ls[X].sum(axis=2)
        a,bq=np.unravel_index(S.argmax(),S.shape)
        rows.append((y+50,offs[a],pers[bq],S[a,bq]))
    R=np.array(rows)
    w=R[:,3]; ok=w>w.max()*0.5
    co_o=np.polyfit(R[ok,0],R[ok,1],2); co_p=np.polyfit(R[ok,0],R[ok,2],2)
    for _ in range(2):
        res=np.abs(R[:,1]-np.polyval(co_o,R[:,0]))+np.abs(R[:,2]-np.polyval(co_p,R[:,0]))*5
        ok2=ok&(res<4)
        if ok2.sum()>=6: co_o=np.polyfit(R[ok2,0],R[ok2,1],2); co_p=np.polyfit(R[ok2,0],R[ok2,2],2)
    ys=np.linspace(yt,yb,40)
    lines=[]
    for i in range(11):
        xs=g["x10"]+np.polyval(co_o,ys)+np.polyval(co_p,ys)*i
        lines.append(np.polyfit(ys,xs,2))
    g["lines"]=lines; g["bands"]=R
    # 栏顶栏底沿用 geom3 的做法
    g3=geo3.geom3(im); g["cols"]=g3["cols"] if g3 else [(yt,yb)]*10
    return g
