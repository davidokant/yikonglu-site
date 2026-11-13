from PIL import Image; import numpy as np, scipy.ndimage as nd, json
L=[l.split() for l in open("wx_lines.txt")]
G={}
def find(g,N,it,thr):
    H,W=g.shape
    e=nd.binary_erosion(g<thr,iterations=it)
    prof=nd.uniform_filter1d(e.sum(0).astype(float),120); prof[:150]=0; prof[W-150:]=0
    def ext(x):
        a=x; b=x
        while a>x-190 and prof[a]>prof[x]*0.3: a-=1
        while b<x+190 and prof[b]>prof[x]*0.3: b+=1
        return a,b
    peaks=[]; pr=prof.copy(); tries=0
    while len(peaks)<N and tries<40:
        tries+=1; x=int(pr.argmax()); a,b=ext(x)
        if b-a>=215: peaks.append(x)
        pr[max(0,x-280):x+280]=0
    peaks.sort(reverse=True); cols=[]
    for x in peaks:
        a,b=ext(x)
        rows=np.where(nd.uniform_filter1d(e[:,a:b].sum(1).astype(float),15)>2)[0]
        rows=rows[(rows>H*0.08)&(rows<H*0.97)]
        cols.append([a-15,int(rows[0])-10,b+15,int(rows[-1])+10,round(float(prof[x]),1)])
    return cols
for p,*ts in L:
    g=np.asarray(Image.open(f"raw/p-{p}.jpg").convert('L')); H,W=g.shape
    for it,thr in ((6,110),(4,120),(3,130),(2,140)):
        cols=find(g,len(ts),it,thr)
        rel=[c[4]/max(x[4] for x in cols) for c in cols]
        if len(cols)==len(ts) and all(r>0.45 and c[2]-c[0]<400 for r,c in zip(rel,cols)): break
    G[p]=dict(W=W,H=H,cols=cols,txt=ts)
    print(p,it,[(c[0],c[2]-c[0],c[4]) for c in cols])
json.dump(G,open("geom.json","w"))
