from PIL import Image; import numpy as np, scipy.ndimage as nd, json
G=json.load(open("geom.json"))
def col_at(p,hint,it=3,thr=130,win=260):
    g=np.asarray(Image.open(f"raw/p-{p}.jpg").convert('L')); H,W=g.shape
    e=nd.binary_erosion(g<thr,iterations=it)
    prof=nd.uniform_filter1d(e.sum(0).astype(float),120)
    lo,hi=hint-win,hint+win; x=lo+int(prof[lo:hi].argmax())
    a=x;b=x
    while a>x-190 and prof[a]>prof[x]*0.3: a-=1
    while b<x+190 and prof[b]>prof[x]*0.3: b+=1
    rows=np.where(nd.uniform_filter1d(e[:,a:b].sum(1).astype(float),15)>2)[0]
    rows=rows[(rows>H*0.08)&(rows<H*0.97)]
    print(p,hint,'->',x,a,b,b-a,round(float(prof[x]),1))
    return [a-15,int(rows[0])-10,b+15,int(rows[-1])+10,round(float(prof[x]),1)]
fixes={'008':{2:1560},'031':{0:1120,1:720},'035':{1:1600},'027':{0:3600}}
for p,d in fixes.items():
    for i,h in d.items(): G[p]['cols'][i]=col_at(p,h)
    G[p]['cols'].sort(key=lambda c:-c[0])
json.dump(G,open("geom.json","w"))
