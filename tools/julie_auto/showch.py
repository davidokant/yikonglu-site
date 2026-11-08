import pickle, numpy as np, sys
sys.path.insert(0,'.')
from common import *
from PIL import Image, ImageDraw
C,G=pickle.load(open("cells.pkl","rb"))
out,PR=pickle.load(open("align.pkl","rb"))
J=julie(); idx=png_index()
def show(c, fn, scale=0.5):
    pn=int(c.split(".")[0]); toks,asg,dels=out[pn]
    mine=[(m,C[asg[j]]) for j,(ch,cc,m) in enumerate(toks) if cc==c and m>=0 and j in asg]
    ring=[C[asg[j]] for j,(ch,cc,m) in enumerate(toks) if cc==c and m<0 and j in asg]
    pages=sorted(set(r["p"] for _,r in mine)|set(r["p"] for r in ring))
    ims=[]
    for p in pages:
        im=load(p,idx); I=Image.fromarray(im).convert("RGB"); d=ImageDraw.Draw(I)
        if c in J:
            for ch in J[c][1]:
                if ch[1]==p: d.rectangle(ch[3:7],outline=(0,170,0),width=4)
        for m,r in mine:
            if r["p"]==p: d.rectangle((r["x0"]+4,r["y0"]+3,r["x1"]-4,r["y1"]-3),outline=(220,0,0),width=3)
        for r in ring:
            if r["p"]==p: d.rectangle((r["x0"]+4,r["y0"]+3,r["x1"]-4,r["y1"]-3),outline=(0,0,255),width=3)
        ims.append(I.resize((int(I.width*scale),int(I.height*scale))))
    W=sum(i.width for i in ims); H=max(i.height for i in ims)
    O=Image.new("RGB",(W,H),"white"); x=0
    for i in ims[::-1]: O.paste(i,(x,0)); x+=i.width
    O.save(fn); return pages
if __name__=="__main__":
    for c in sys.argv[1:]: print(c, show(c, f"ch_{c}.png", 0.33))
