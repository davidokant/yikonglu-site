import numpy as np, sys
from geo import geo
def cols9(L,w):
    d=np.diff(L); pitch=float(np.median(d))
    best=None
    for i in range(len(L)):
        seq=[L[i]]
        for x in L[i+1:]:
            if abs(x-seq[-1]-pitch)<pitch*.12: seq.append(x)
            elif abs(x-seq[-1]-2*pitch)<pitch*.15: seq+= [seq[-1]+round(pitch), x]
        if best is None or len(seq)>len(best): best=seq
    seq=best
    while len(seq)<9:
        l=seq[0]-pitch; r=seq[-1]+pitch
        if abs((l+seq[-1])/2-685) < abs((seq[0]+r)/2-685): seq=[int(l)]+seq
        else: seq=seq+[int(r)]
    if len(seq)>9:
        bs=min(range(len(seq)-8), key=lambda i: abs((seq[i]+seq[i+8])/2-685)); seq=seq[bs:bs+9]
    return seq, pitch
def grid(p):
    im,b,y0,y1,L=geo(p); h,w=b.shape
    X,pitch=cols9(L,w)
    # 每行字数：多数页 21 字，下篇有些页 20 字；用各列竖向墨量的自相关周期定
    ac=np.zeros(140)
    for ci in range(8):
        pr=b[y0:y1, X[7-ci]+12:X[8-ci]-12].sum(1).astype(float); pr-=pr.mean()
        for lag in range(55,95): ac[lag]+=(pr[:-lag]*pr[lag:]).sum()
    per=55+int(np.argmax(ac[55:95]))
    R=min((20,21), key=lambda r: abs((y1-y0)/r-per))
    rh=(y1-y0)/R
    fys=[]
    for ci in range(8):
        xr=X[8-ci]; xl=X[7-ci]
        prof=b[y0+3:y1-3, xl+12:xr-12].sum(1)
        on=(prof>=5).astype(int); run=np.convolve(on,np.ones(14,int),"valid")
        nz=np.where(run>=12)[0]
        fys.append((int(nz[0])+3)/rh if len(nz) else 99)
    mf=[f for f in fys if f<0.7]
    org=y0+((float(np.median(mf)) if mf else 0.1)-0.1)*rh
    G=[]
    for ci in range(8):
        xr=X[8-ci]; xl=X[7-ci]
        col=[]
        for k in range(R):
            ya=int(org+k*rh); yb=int(org+(k+1)*rh)
            cell=b[ya+12:min(yb,y1-6)-12, xl+10:xr-10]
            ink=cell.mean() if cell.size else 0
            cw2=cell.shape[1]; ctr=cell[:, int(cw2*.42):int(cw2*.58)].mean() if cell.size else 0
            col.append((ink,ctr,(xl,ya,xr,yb)))
        G.append((col,(fys[ci]*rh+y0-org)/rh))
    return G,X,org,y1,rh,R
def cls(ink,ctr):
    if ink<0.035: return "."
    if ctr<ink*0.35: return "s"
    return "#"
if __name__=="__main__":
    for p in sys.argv[1:]:
        G,X,y0,y1,rh,R=grid(p); print(p,X,round(rh,1),R)
        for k in range(R):
            print("  "+" ".join(cls(G[ci][0][k][0],G[ci][0][k][1]) for ci in range(8)[::-1]))
        print("  fy",[round(G[ci][1],2) for ci in range(8)[::-1]])
