# 导出道德经逐句原页框：tools/ddj_julie.json {章: [[ [页, x0, y0, x1, y1], ... ] 每句一组]}
import pickle, json, glob, re, sys
sys.path.insert(0, "/home/user/yikonglu-site/tools")
Q=json.load(open(sorted(glob.glob('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_道德经/_原文/道德经原文-v*.json'))[-1]))
PUN=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》·…—]")
def split_ju(text):
    out = re.findall(r"[^。？！]+[。？！]+[”’」』]*|[^。？！]+$", text)
    return [x for x in out if x.strip()]
S=pickle.load(open("scan.pkl","rb")); cols=pickle.load(open("cols.pkl","rb")); out,costs=pickle.load(open("local.pkl","rb"))
PG=json.load(open("/home/user/yikonglu-site/tools/ddj_pages.json"))
R={}; bad=[]
for c,asg in out.items():
    T=PUN.sub("",Q[c]["text"]); sl=[len(PUN.sub("",x)) for x in split_ju(Q[c]["text"])]
    if sum(sl)!=len(T): bad.append((c,"len")); continue
    # 每个字 → (页, 列 x0, x1, 行 y0, y1)
    pos=[None]*len(T)
    for i,t,m in asg:
        col=cols[i]; p=col["p"]; X=S[p]["X"]; y0=S[p]["y0"]; rh=S[p]["rh"]; ci=col["ci"]
        rows=[r for r,ch in enumerate(col["k"]) if ch=="#"]
        rows=(rows+list(range(rows[-1]+1,40)))[:m] if rows else list(range(m))
        for k in range(m): pos[t+k]=(p,int(X[7-ci]),int(X[8-ci]),int(y0+rows[k]*rh),int(y0+(rows[k]+1)*rh))
    per=[]; a=0
    for n in sl:
        bx={}
        for q in pos[a:a+n]:
            if q is None: continue
            key=(q[0],q[1]); b=bx.get(key)
            bx[key]=[q[0],q[1]+4,q[3]-2,q[2]-4,q[4]+2] if not b else [b[0],b[1],min(b[2],q[3]-2),b[3],max(b[4],q[4]+2)]
        per.append(sorted(bx.values(),key=lambda b:(b[0],-b[1])))
        a+=n
    R[c]=per
json.dump({k:R[k] for k in sorted(R,key=int)},open("/home/user/yikonglu-site/tools/ddj_julie.json","w"),ensure_ascii=False,separators=(",",":"))
print(len(R),"chapters; bad",bad)
miss=[(c,b[0]) for c,per in R.items() for bb in per for b in bb if int(b[0][1:]) not in (Q[c].get("pages") or [])]
print("box pages outside chapter pages:",sorted(set(miss)))
