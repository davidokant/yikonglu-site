# 为政起已公开各章的逐句表：白话按定版白话逐句切（句数对得上才自动）；朱注按字面重合挂到句上（只收有底本页、非转述的条目；引某氏与“愚谓”的总论挂末句）
import json,re,sys,os
from opencc import OpenCC
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from man import M
t2s=OpenCC("t2s").convert
S=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(S+"/pub.json"))
STOP=set("之也者而其以曰子不所于为则矣乎人此言谓故有则亦是与无一")
P=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》〈〉·…—]")
def split(bh): return [x for x in re.split(r'(?<=[。？！])(?![”’])',bh) if x.strip()]
out={};bad=[]
for c in sorted(d,key=lambda c:tuple(map(int,c.split('.')))):
    if c.startswith("1."): continue
    ju=d[c]["ju"]; bh=M.get(c) or split(d[c]["bh"] or "")
    if len(bh)!=len(ju): bad.append((c,len(ju),len(bh))); continue
    ss=[{"bh":b,"zhu":[],"jj":[],"yk":""} for b in bh]
    cur=0
    for t,src,pg,para in d[c]["cites"]:
        if not pg or para: continue
        p="—".join(pg) if len(pg)>1 else pg[0]
        t2=t+("" if t.endswith(("。","！","？","”","……")) else "。")
        if len(ju)==1: k=0
        elif src!="朱注": k=len(ju)-1
        elif (h:=re.split(r"[，。；]",t2s(t))[0]) and len(h)<=4 and any(h in j for j in ju):
            k=next((i for i in range(cur,len(ju)) if h in ju[i]),None)
            if k is None: k=next(i for i in range(len(ju)) if h in ju[i])
            cur=k
        else:
            cs=set(P.sub("",t2s(t)))-STOP
            sc=[len(cs&(set(P.sub("",j))-STOP)) for j in ju]
            k=max(range(cur,len(ju)),key=lambda i:(sc[i],-i)); 
            if sc[k]==0: k=cur
            cur=k
        ss[k]["zhu"].append([t2,f"{src}，底本第 {p} 页",""])
    out[c]=ss
json.dump(out,open(S+"/gen.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(len(out),"bad",bad)
