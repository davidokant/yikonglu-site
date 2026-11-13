import json, glob, re, pickle, numpy as np
from grid import grid, cls
Q=json.load(open(sorted(glob.glob('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_道德经/_原文/道德经原文-v*.json'))[-1]))
PUN=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》·…—]")
pages=sorted(set(p for c in Q if c.isdigit() for p in Q[c]["pages"]))
out={}
for n in pages:
    p=f"p{n:03d}"
    try: G,X,y0,y1,rh,R=grid(p)
    except Exception as e: print("fail",p,e); continue
    cols=[]
    for ci in range(8):
        cc,fy=G[ci]
        cs=[cls(a,b) for a,b,_ in cc]
        inks=[round(a,3) for a,b,_ in cc]
        cols.append(dict(cls="".join(cs), ink=inks, box=[bx for _,_,bx in cc], fy=fy))
    out[p]=dict(cols=cols,X=X,y0=y0,y1=y1,rh=rh,R=R)
pickle.dump(out,open("scan.pkl","wb"))
tot=sum(len(PUN.sub("",Q[c]["text"])) for c in Q if c.isdigit())
mains=sum(len(re.match(r"#*",c["cls"]).group(0)) for p in out.values() for c in p["cols"] if c["cls"][0]=="#")
print(len(out),"pages; text chars",tot,"; main-col big chars",mains)
