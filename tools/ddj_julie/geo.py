import numpy as np
from PIL import Image
IMG="/home/user/yikonglu-img/ddj/"
def geo(p):
    im=np.array(Image.open(IMG+p+".jpg").convert("L")); h,w=im.shape; b=im<70; br=im<170
    # horizontal rules: rows with long dark runs in middle 60% width
    mid=br[:, int(w*.2):int(w*.8)]
    rf=mid.mean(1)
    rows=np.where(rf>0.4)[0]
    top=rows[rows<h*.25]; bot=rows[rows>h*.75]
    y0=int(top.max())+1 if len(top) else None; y1=int(bot.min())-1 if len(bot) else None
    if y0 is None and y1 is not None: y0=y1-1460
    if y1 is None and y0 is not None: y1=y0+1460
    if y0 is None: y0=int(h*.5-730); y1=y0+1460
    # vertical rules between y0,y1
    band=br[y0+20:y1-20] if y0 and y1 else br[int(h*.15):int(h*.85)]
    cf=band.mean(0)
    xs=np.where(cf>0.5)[0]
    # group
    lines=[]
    for x in xs:
        if lines and x-lines[-1][-1]<=6: lines[-1].append(x)
        else: lines.append([x])
    lines=[int(np.mean(l)) for l in lines]
    from scipy import ndimage
    lab,n=ndimage.label(b); sz=np.bincount(lab.ravel()); keep=sz>=60; keep[0]=False
    b=keep[lab]
    b=strip_long(b,150,1)
    return im,b,y0,y1,lines
def strip_long(b, maxlen, axis):
    """去掉沿 axis 方向长于 maxlen 的连续墨线（界栏、版框、底纹框），字的笔画短于一格。"""
    a=b if axis==0 else b.T
    a=a.copy(); n=a.shape[0]
    pad=np.zeros((1,a.shape[1]),bool)
    d=np.diff(np.vstack([pad,a,pad]).astype(np.int8),axis=0)
    for x in range(a.shape[1]):
        st=np.where(d[:,x]==1)[0]; en=np.where(d[:,x]==-1)[0]
        for s0,e0 in zip(st,en):
            if e0-s0>maxlen: a[s0:e0,x]=False
    return a if axis==0 else a.T
if __name__=="__main__":
    import sys
    for p in sys.argv[1:]:
        im,b,y0,y1,L=geo(p); print(p,im.shape,y0,y1,L,[L[i+1]-L[i] for i in range(len(L)-1)])
