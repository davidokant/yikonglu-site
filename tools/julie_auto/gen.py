import pickle, json, re, os, sys
sys.path.insert(0,'.')
from common import *
C,G=pickle.load(open("cells.pkl","rb"))
out,PR=pickle.load(open("align.pkl","rb"))
virt,_=pickle.load(open("lowc.pkl","rb"))
J=julie()
Q=json.load(open(G_:='/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_原文/论语原文-集注分章-v1.json',encoding='utf-8'))
PUNCT=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》〈〉·…—,.;:?!()\[\]]")
def split_ju(text):
    return [x for x in re.findall(r"[^。？！]+[。？！]+[”’」』]*|[^。？！]+$", text) if x.strip()]
outdir=sys.argv[1]; os.makedirs(outdir,exist_ok=True)
n=0; skipped=[]
for pn,(toks,asg,dels) in out.items():
    per={}
    for j,(ch,c,m) in enumerate(toks):
        if m>=0: per.setdefault(c,[]).append((m,ch,asg.get(j)))
    for c,lst in per.items():
        if c in J: continue
        if c in virt or any(i is None or i<0 for _,_,i in lst): skipped.append(c); continue
        text=Q[c]["text"]
        if PUNCT.sub("",text)!="".join(ch for _,ch,_ in lst): skipped.append(c+"(字)"); continue
        chars=[]; pages={}
        for m,ch,i in lst:
            r=C[i]; p=r["p"]
            chars.append([ch,p,r["col"],int(round(r["x0"])),int(round(r["y0"])),int(round(r["x1"])),int(round(r["y1"]))])
            pages[p]={"pdf_page":int(p[1:]),"image":p+".png","w":1369,"h":2400,"deskew":{"angle":0.0,"src_w":1369,"src_h":2400,"canvas":"same","note":"未校平，坐标在原图上"}}
        sents=[]; k=0
        for s_i,s in enumerate(split_ju(text),1):
            need=len(PUNCT.sub("",s)); got=chars[k:k+need]; k+=need
            spans=[]
            for ch,p,col,x0,y0,x1,y1 in got:
                if spans and spans[-1]["page"]==p and spans[-1]["col"]==col:
                    sp=spans[-1]; sp["x0"]=min(sp["x0"],x0); sp["x1"]=max(sp["x1"],x1); sp["y0"]=min(sp["y0"],y0); sp["y1"]=max(sp["y1"],y1)
                else: spans.append({"page":p,"col":col,"x0":x0,"x1":x1,"y0":y0,"y1":y1})
            sents.append({"n":s_i,"text":PUNCT.sub("",s),"spans":spans})
        d={"format":"一孔录 句列对照 v1","book":"论语","chapter":c,"title":"","zhu":"朱注","source":"四部备要-四书集注-论语.pdf",
           "pages":dict(sorted(pages.items())),
           "coord":"像素，左上为原点；未校平，坐标在原 PDF 页图上；col＝本页版框内自右向左第几列（1 起）；x 取两侧界栏之间，y 取字格",
           "auto":"11-08 网站线程从原页图自动找经文大字、与原文逐字对齐生成（已用 236 章旧坐标对过答案）；字用网站原文简体",
           "chars":chars,"sentences":sents}
        json.dump(d,open(os.path.join(outdir,c+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        n+=1
print("written",n,"skipped",len(skipped),skipped)
