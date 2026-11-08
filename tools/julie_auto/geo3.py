import numpy as np
from geo import geom2
def geom3(im):
    g=geom2(im)
    if not g: return None
    b=(im<170); H,W=b.shape
    bm=np.maximum(np.maximum(b[:, :-2], b[:, 1:-1]), b[:, 2:]); bm=np.pad(bm,((0,0),(1,1)))
    yt,yb=g["yt"],g["yb"]
    lines=[]
    for i in range(11):
        xp=g["x10"]+i*g["cw"]
        pts=[]
        # 从中间往上、往下追
        ys=list(range(int(yt)+10,int(yb)-90,60))
        mid=len(ys)//2
        order=[ys[mid:], ys[:mid][::-1]]
        for seq in order:
            cur=xp
            for y in seq:
                lo=int(round(cur))-10; hi=int(round(cur))+11
                lo=max(lo,0); hi=min(hi,W)
                band=bm[y:y+80, lo:hi].mean(axis=0)
                j=int(np.argmax(band)); s=band[j]
                if s>0.8:
                    x=lo+j
                    # 粗线取中
                    jj=np.where(band>s-0.05)[0]; x=lo+(jj.min()+jj.max())/2
                    pts.append((y+40,x,s)); cur=x
        if len(pts)>=4:
            P=np.array(pts)
            deg=2 if len(pts)>=8 else 1
            co=np.polyfit(P[:,0],P[:,1],deg)
            res=P[:,1]-np.polyval(co,P[:,0])
            ok=np.abs(res)<4
            if ok.sum()>=4: co=np.polyfit(P[ok,0],P[ok,1],deg)
        else:
            co=np.array([0,0,xp])
        if len(co)==2: co=np.r_[0,co]
        lines.append(co)
    g["lines"]=lines
    # 每栏顶底：在栏中部找粗横线
    cols=[]
    for c in range(1,11):
        li=10-(c-1); ri=li  # 第 c 栏右线 index 10-(c-1)，左线 9-(c-1)
        xr=np.polyval(lines[10-(c-1)],(yt+yb)/2); xl=np.polyval(lines[9-(c-1)],(yt+yb)/2)
        a,bx=int(xl+15),int(xr-15)
        def edge(y0,y1,top):
            rows=b[max(0,y0):y1, a:bx].mean(axis=1)
            idx=np.where(rows>0.6)[0]
            if len(idx)==0: return None
            return max(0,y0)+(idx.max()+1 if top else idx.min())
        t=edge(int(yt)-30,int(yt)+30,True); bo=edge(int(yb)-30,int(yb)+30,False)
        cols.append((t if t is not None else yt, bo if bo is not None else yb))
    T=np.array([c[0] for c in cols],float); B=np.array([c[1] for c in cols],float); x=np.arange(10)
    def robust(v):
        ok=np.ones(10,bool)
        for _ in range(3):
            co=np.polyfit(x[ok],v[ok],1); r=np.abs(v-np.polyval(co,x))
            ok=r<=max(3,np.median(r)*3)
            if ok.sum()<5: ok=r<=np.sort(r)[5]
        return np.where(ok,v,np.polyval(co,x))
    T=robust(T); B=robust(B)
    g["cols"]=list(zip(T.tolist(),B.tolist()))
    return g
def cell_box(g,col,k):
    t,bo=g["cols"][col-1]; pitch=(bo-t-34)/20
    y0=t+17+k*pitch; y1=y0+pitch; ym=(y0+y1)/2
    xr=np.polyval(g["lines"][10-(col-1)],ym); xl=np.polyval(g["lines"][9-(col-1)],ym)
    return xl,y0,xr,y1
