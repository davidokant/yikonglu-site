import pickle, numpy as np, sys, json, re
sys.path.insert(0,'.')
from mlp3 import *
C,G=pickle.load(open("cells.pkl","rb")); V=np.load("VA.npy")
lab,who,jp=pickle.load(open("labels.pkl","rb"))
try: P=pickle.load(open("m3_all.pkl","rb"))
except FileNotFoundError:
    use=np.array([r["p"] in jp for r in C])
    P=fit(V[use],lab[use],cw=[1,1,5]); pickle.dump(P,open("m3_all.pkl","wb"))
PR=predict(P,V)
Q=json.load(open('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_原文/论语原文-集注分章-v1.json',encoding='utf-8'))
Q["1.6"]["text"]=Q["1.6"]["text"].replace("泛爱众","汎爱众")
key=lambda c: tuple(int(x) for x in c.split("."))
chs=sorted(Q,key=key)
han=lambda t: re.sub(r"[^㐀-鿿\U00020000-\U0002ffff]","",t)
pages=sorted(G); pidx={p:i for i,p in enumerate(pages)}
order={}  # 阅读序
seq=sorted(range(len(C)), key=lambda i:(pidx[C[i]["p"]],C[i]["col"],C[i]["k"]))
PD=12.0
GAP=0.15
HB=np.load('HB.npy')
def align_pian(pn):
    cs=[c for c in chs if c.split(".")[0]==str(pn)]
    toks=[]
    for n,c in enumerate(cs):
        if n>0: toks.append(("○",c,-1))
        for m,ch in enumerate(han(Q[c]["text"])): toks.append((ch,c,m))
    p0=f'p{Q[cs[0]]["pdf_page"]:03d}'
    nxt=[c for c in chs if c.split(".")[0]==str(pn+1)]
    p1=f'p{Q[nxt[0]]["pdf_page"]:03d}' if nxt else pages[-1]
    cells=[]
    allp=[f"p{n:03d}" for n in range(int(p0[1:]),int(p1[1:])+1)]
    byp={}
    for i in seq:
        if p0<=C[i]["p"]<=p1: byp.setdefault(C[i]["p"],[]).append(i)
    for p in allp:
        if p in byp: cells+=byp[p]
        else: cells+=[-1]*200   # 缺页：中性虚格
    
    M=len(toks); N=len(cells)
    isring=np.array([t[0]=="○" for t in toks])
    isyi=np.array([t[0]=="一" for t in toks])
    mid=np.zeros(M+1); 
    for j in range(1,M): mid[j]=GAP if toks[j][2]>=0 else 0.0
    eps=1e-6
    D=np.arange(M+1)*PD
    back=np.zeros((N,M+1),np.int8)
    jj=np.arange(M+1)
    for a,i in enumerate(cells):
        pr=PR[i] if i>=0 else np.array([1/3,1/3,1/3])
        po,pb,prr=np.log(pr+eps)
        S=D+(-po)+mid; S[0]=D[0]; S[M]=D[M]
        pby=np.log(max(PR[i][1],0.95)+eps) if (i>=0 and HB[i]) else pb
        mc=np.where(isring,-prr,np.where(isyi,-pby,-pb))
        Mt=np.full(M+1,np.inf); Mt[1:]=D[:-1]+mc
        Dn=np.minimum(S,Mt); b=np.where(Mt<S,1,0).astype(np.int8)
        E=Dn-jj*PD; cm=np.minimum.accumulate(E); imp=cm<E-1e-9
        Dn=np.where(imp,cm+jj*PD,Dn); b[imp]=2
        back[a]=b; D=Dn
    # 回溯
    asg={}; a=N-1; j=M; dels=[]
    while j>0 and a>=0:
        b=back[a,j]
        if b==1: asg[j-1]=cells[a]; a-=1; j-=1
        elif b==2: dels.append(j-1); j-=1
        else: a-=1
    while j>0: dels.append(j-1); j-=1
    return toks,asg,set(dels),float(D[M])
if __name__=="__main__":
    out={}
    for pn in range(1,21):
        toks,asg,dels,cost=align_pian(pn)
        out[pn]=(toks,asg,dels)
        print(pn,len(toks),"dels",len(dels),"cost",round(cost,1))
    pickle.dump((out,PR),open("align.pkl","wb"))
