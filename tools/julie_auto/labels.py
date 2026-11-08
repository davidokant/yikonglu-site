import sys, pickle; sys.path.insert(0,'.')
from common import *
import numpy as np
C,G=pickle.load(open("cells.pkl","rb"))
J=julie()
pos={(r["p"],r["col"],r["k"]):i for i,r in enumerate(C)}
pages=sorted(G)
def prev(p,col,k):
    if k>0: return (p,col,k-1)
    if col>1: return (p,col-1,19)
    i=pages.index(p)
    return (pages[i-1],10,19) if i>0 else None
def find(ch):
    p=ch[1]; cx=(ch[3]+ch[5])/2; cy=(ch[4]+ch[6])/2
    best=None
    for col in range(1,11):
        for k in range(20):
            i=pos.get((p,col,k))
            if i is None: continue
            r=C[i]
            ix=max(0,min(r["x1"],ch[5])-max(r["x0"],ch[3])); iy=max(0,min(r["y1"],ch[6])-max(r["y0"],ch[4]))
            ov=ix*iy/((r["x1"]-r["x0"])*(r["y1"]-r["y0"]))
            if best is None or ov>best[0]: best=(ov,i)
    return best
lab=np.zeros(len(C),int)  # 0 其他 1 大字 2 圈
who={}
low=0
for c,(d,chs) in J.items():
    for n,ch in enumerate(chs):
        b=find(ch)
        if not b or b[0]<0.45: low+=1; continue
        lab[b[1]]=1; who[b[1]]=(c,n,ch[0])
for c,(d,chs) in J.items():
    if c.endswith(".1") or not chs: continue
    b=find(chs[0])
    if not b or b[0]<0.45: continue
    r=C[b[1]]; q=prev(r["p"],r["col"],r["k"])
    if q and q in pos and lab[pos[q]]==0: lab[pos[q]]=2
print("low-overlap",low, "big",(lab==1).sum(),"ring",(lab==2).sum())
jp=set(ch[1] for c,(d,chs) in J.items() for ch in chs)
pickle.dump((lab,who,jp),open("labels.pkl","wb"))
