import pickle, numpy as np, sys
sys.path.insert(0,'.')
from common import *
from scipy import ndimage as ndi
C,G=pickle.load(open("cells.pkl","rb")); idx=png_index()
HB=np.zeros(len(C),bool); cur=None
for i,r in enumerate(C):
    if r["p"]!=cur: cur=r["p"]; b=load(cur,idx)<150
    c=b[int(r["y0"])+2:int(r["y1"])-2, int(r["x0"])+10:int(r["x1"])-10]
    lab,n=ndi.label(c,structure=np.ones((3,3),bool))
    big=[]
    for k,sl in enumerate(ndi.find_objects(lab)):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if (lab[sl]==k+1).sum()>=40: big.append((h,w))
    HB[i]= len(big)>=1 and any(w>=55 and h<=26 for h,w in big) and all(h<=26 or (h<=14 and w<=14) for h,w in big)
np.save("HB.npy",HB); print(HB.sum())
