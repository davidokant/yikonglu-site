import pickle, numpy as np, sys, re
sys.path.insert(0,'.')
from common import *
C,G=pickle.load(open("cells.pkl","rb"))
out,PR=pickle.load(open("align.pkl","rb"))
J=julie()
lab,who,jp=pickle.load(open("labels.pkl","rb"))
cellof={}  # (c,n)->cell
for i,(c,n,ch) in who.items(): cellof[(c,n)]=i
res={}
for pn,(toks,asg,dels) in out.items():
    per={}
    for j,(ch,c,m) in enumerate(toks):
        if m<0: continue
        d=per.setdefault(c,[0,0,0,0])  # 总字, 删, 与julie同格, julie有
        d[0]+=1
        if j in dels: d[1]+=1; continue
        if (c,m) in cellof:
            d[3]+=1
            if cellof[(c,m)]==asg[j]: d[2]+=1
    res.update(per)
ok=[c for c,d in res.items() if d[3] and d[2]==d[3]==d[0]]
part=[(c,d) for c,d in res.items() if d[3] and not (d[2]==d[3]==d[0])]
print("julie chapters fully agree:",len(ok),"disagree:",len(part))
for c,d in sorted(part,key=lambda x:tuple(map(int,x[0].split(".")))): print(c,d, len(J[c][1]))
nod=[c for c,d in res.items() if not d[3]]
print("new chapters:",len(nod),"with dels:",[ (c,res[c][1]) for c in nod if res[c][1]])
pickle.dump(res,open("val.pkl","wb"))
