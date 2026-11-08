import pickle, numpy as np
C,G=pickle.load(open("cells.pkl","rb"))
out,PR=pickle.load(open("align.pkl","rb"))
HB=np.load("HB.npy")
virt=set(); bad={}
for pn in range(1,21):
    toks,asg,dels=out[pn]
    for j,(ch,c,m) in enumerate(toks):
        i=asg.get(j)
        if i is None or i<0: virt.add(c); continue
        p=PR[i][2] if m<0 else (max(PR[i][1],0.95) if ch=="一" and HB[i] else PR[i][1])
        if p<0.5: bad.setdefault(c,[]).append(f"{m}{ch}@{C[i]['p']},{C[i]['col']},{C[i]['k']}:{p:.2f}")
print("virtual-touch",len(virt),sorted(virt,key=lambda c:tuple(map(int,c.split(".")))))
for c,v in bad.items():
    if c not in virt: print(c,v[:6])
pickle.dump((virt,bad),open("lowc.pkl","wb"))
