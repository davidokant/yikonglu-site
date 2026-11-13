import json, glob, re, pickle
Q=json.load(open(sorted(glob.glob('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_道德经/_原文/道德经原文-v*.json'))[-1]))
PUN=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》·…—]")
S=pickle.load(open("scan.pkl","rb"))
cols=[]
for p in sorted(S):
    for ci,c in enumerate(S[p]["cols"]):
        k=re.sub(r"(?<=#)s(?=#)","#",c["cls"]); k=re.sub(r"^s(?=#)","#",k); k=re.sub(r"(?<=#)s(?=\.|$)","#",k)
        kind="h" if (1.8<c["fy"]<3.2 or re.match(r"^\.\.#{2,4}s",c["cls"])) else ("m" if c["cls"][0]!="." and c["fy"]<1.3 else "c")
        cols.append(dict(p=p,ci=ci,kind=kind,n=k.count("#") if kind=="m" else 0,k=k,fy=c["fy"]))
H=[i for i,c in enumerate(cols) if c["kind"]=="h"]
print("headings",len(H))
print([(cols[i]["p"],cols[i]["ci"],round(cols[i]["fy"],2)) for i in H][:100])
pickle.dump(cols,open("cols.pkl","wb"))
CH=sorted([k for k in Q if k.isdigit()],key=int)
hd={}
for c in CH:
    p=f"p{Q[c]['pdf_page']:03d}"
    cand=[i for i in H if cols[i]["p"]==p and re.search(r"#{1,4}s",S[p]["cols"][cols[i]["ci"]]["cls"])]
    same=[x for x in CH if Q[x]["pdf_page"]==Q[c]["pdf_page"]]
    if len(cand)<len(same): print("no heading",c,p,len(cand),len(same)); continue
    if len(same)>1: hd[c]=sorted(cand)[same.index(c)] if len(cand)==len(same) else None
    else: hd[c]=max(cand,key=lambda i: S[p]["cols"][cols[i]["ci"]]["cls"].count("s"))
    if hd[c] is None: del hd[c]; print("ambig",c)
res={}
for j,c in enumerate(CH):
    if c not in hd: continue
    a=hd[c]; b=hd.get(CH[j+1]) if j+1<len(CH) else len(cols)
    if b is None: continue
    mc=[i for i in range(a+1,b) if cols[i]["kind"]=="m"]
    L=len(PUN.sub("",Q[c]["text"])); tot=sum(cols[i]["n"] for i in mc)
    res[c]=(L,tot,mc)
ok=[c for c in res if res[c][0]==res[c][1]]
print("exact",len(ok),"/",len(res))
print("diff",[(c,res[c][1]-res[c][0]) for c in res if res[c][0]!=res[c][1]])
pickle.dump((hd,res),open("seg.pkl","wb"))
