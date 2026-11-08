import numpy as np
from scipy import ndimage as ndi
GW,GH=24,20
def cellvec(b, r):
    cx0,cx1=int(r["x0"]+4),int(r["x1"]-4); cy0,cy1=int(r["y0"]),int(r["y1"])
    c=b[cy0:cy1,cx0:cx1].copy()
    H,W=c.shape
    # 去掉边上的界栏竖线
    colf=c.mean(axis=0)
    for x in list(range(0,14))+list(range(W-14,W)):
        if 0<=x<W and colf[x]>0.55: c[:,max(0,x-1):x+2]=False
    c=c.astype(float)
    # 面积平均缩到 GW×GH
    ys=np.linspace(0,H,GH+1).astype(int); xs=np.linspace(0,W,GW+1).astype(int)
    v=np.add.reduceat(np.add.reduceat(c,ys[:-1],axis=0),xs[:-1],axis=1)
    v=v/np.outer(np.diff(ys),np.diff(xs))
    return v.ravel()
