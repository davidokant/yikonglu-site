import sys, pickle, re, glob, os; sys.path.insert(0,'.')
from common import *
from geo3 import cell_box
from geo4 import geom4 as geom3
from pix import cellvec
import numpy as np
idx=png_index()
pages=sorted(set(list(idx))|set(os.path.basename(f)[:-4] for f in glob.glob("/home/user/yikonglu-site/tools/yuanye/p*.jpg")))
pages=[p for p in pages if re.fullmatch(r"p\d{3}",p)]
C=[]; V=[]; G={}
for p in pages:
    im=load(p,idx)
    g=geom3(im)
    if not g: print("nogeo",p); continue
    G[p]={k:v for k,v in g.items()}
    b=im<150
    for col in range(1,11):
        for k in range(20):
            x0,y0,x1,y1=cell_box(g,col,k)
            r=dict(p=p,col=col,k=k,x0=x0,y0=y0,x1=x1,y1=y1)
            C.append(r); V.append(cellvec(b,r))
V=np.array(V,np.float32)
np.save("VA.npy",V); pickle.dump((C,G),open("cells.pkl","wb"))
print(len(pages),len(C))
