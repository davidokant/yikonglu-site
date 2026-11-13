import pickle, sys, json, glob, re
from PIL import Image, ImageDraw
Q=json.load(open(sorted(glob.glob('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_道德经/_原文/道德经原文-v*.json'))[-1]))
PUN=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》·…—]")
S=pickle.load(open("scan.pkl","rb")); cols=pickle.load(open("cols.pkl","rb")); out,costs=pickle.load(open("local.pkl","rb"))
for c0 in sys.argv[1:]:
    T=PUN.sub("",Q[c0]["text"]); pages={}
    for i,t,m in out[c0]:
        col=cols[i]; p=col["p"]; X=S[p]["X"]; y0=S[p]["y0"]; rh=S[p]["rh"]; ci=col["ci"]
        rows=[r for r,ch in enumerate(col["k"]) if ch=="#"]
        rows=(rows+list(range(rows[-1]+1,30)))[:m] if rows else list(range(m))
        pages.setdefault(p,[]).append((X[7-ci],int(y0+rows[0]*rh),X[8-ci],int(y0+(rows[-1]+1)*rh),T[t:t+m]))
    ims=[]
    for p,bx in sorted(pages.items()):
        im=Image.open(f"/home/user/yikonglu-img/ddj/{p}.jpg").convert("RGB"); d=ImageDraw.Draw(im)
        for x0,y0,x1,y1,t in bx: d.rectangle((x0+4,y0,x1-4,y1),outline=(220,0,0),width=7)
        ims.append(im.resize((im.width//4,im.height//4)))
    W=sum(i.width for i in ims); H=max(i.height for i in ims); sheet=Image.new("RGB",(W,H),"white"); x=0
    for i in ims[::-1]: sheet.paste(i,(x,0)); x+=i.width
    sheet.save(f"v_{c0}.png"); print(c0,costs[c0],[t for *_,t in sum(pages.values(),[])])
