from PIL import Image; import numpy as np, scipy.ndimage as nd, json, math
G=json.load(open('geom.json')); OUTW=1200
def clusters(xs):
    cl=[]
    for x in xs:
        if cl and x-cl[-1][-1]<=3: cl[-1].append(int(x))
        else: cl.append([int(x)])
    return cl
def linex(g,x,a,b):
    sub=(g[int(a):int(b),x-30:x+31]<120).sum(0).astype(float)
    sub[sub<sub.max()*0.5]=0
    return x-30+(sub*np.arange(61)).sum()/sub.sum()
P={}; CH={}
for p in sorted(G):
    im=Image.open(f'raw/p-{p}.jpg').convert('RGB'); g=np.asarray(im.convert('L')).astype(np.int16); H,W=g.shape
    cnt=(g<120).sum(0); xs=np.where(cnt>0.4*H)[0]; xs=xs[(xs>1500)&(xs<2500)]
    cl=clusters(xs)
    if len(cl)>=2: lf=int(np.mean(cl[0])); rf=int(np.mean(cl[-1])); gut=(lf+rf)//2
    else:
        x=int(np.mean(cl[0])); gut=x-200 if x>2000 else x+200; lf=rf=x
        lf,rf=(None,x) if x>2000 else (x,None)
    e=nd.binary_erosion(g<130,iterations=3)
    for side in ('R','L'):
        cols=[(k,c) for k,c in enumerate(G[p]['cols']) if ((c[0]+c[2])/2>gut)==(side=='R')]
        if not cols: continue
        x0,x1=(gut,W) if side=='R' else (0,gut)
        fx=rf if side=='R' else lf
        if fx is None: fx=None
        if fx is not None:
            xt=linex(g,fx,0.2*H,0.35*H); xb=linex(g,fx,0.65*H,0.8*H)
            ang=math.degrees(math.atan2(xb-xt,0.45*H))
        else: ang=0.0
        pn=int(p)*2+(0 if side=='R' else 1)
        crop=im.crop((x0,0,x1,H)); cw=x1-x0; cx,cy=cw/2,H/2
        bg=tuple(int(v) for v in np.median(np.asarray(crop)[:40].reshape(-1,3),0))
        rot=crop.rotate(-ang,resample=Image.BICUBIC,center=(cx,cy),fillcolor=bg)
        s=OUTW/cw; oh=round(H*s)
        rot.resize((OUTW,oh),Image.LANCZOS).save(f'out/p{pn:03d}.jpg',quality=80,optimize=True,progressive=True)
        a=math.radians(-ang)
        def tr(x,y):
            x-=x0; X=cx+(x-cx)*math.cos(a)+(y-cy)*math.sin(a); Y=cy-(x-cx)*math.sin(a)+(y-cy)*math.cos(a); return X*s,Y*s
        P[f'p{pn:03d}']=[OUTW,oh,round(ang,3)]
        for k,(c0,r0,c1,r1,_) in cols:
            prof=nd.uniform_filter1d(e[r0:r1,c0+20:c1-20].sum(1).astype(float),5)>1
            rows=np.where(prof)[0]; top,bot=rows[0],rows[-1]
            # largest internal gap
            ink=prof[top:bot+1]; best=(0,0,0); i=0
            while i<len(ink):
                if not ink[i]:
                    j=i
                    while j<len(ink) and not ink[j]: j+=1
                    if j-i>best[0]: best=(j-i,i,j)
                    i=j
                else: i+=1
            g0,g1=top+best[1],top+best[2]
            cells=[]
            for a_,b_ in ((top,g0),(g1,bot)):
                h=(b_-a_)/3
                for q in range(3): cells.append((a_+q*h,a_+(q+1)*h))
            boxes=[]
            for ya,yb in cells:
                pts=[tr(xx,r0+yy) for xx in (c0,c1) for yy in (ya,yb)]
                boxes.append([round(min(q[0] for q in pts)),round(min(q[1] for q in pts)),round(max(q[0] for q in pts)),round(max(q[1] for q in pts))])
            CH[f'{p}.{k}']=[f'p{pn:03d}',boxes,int(best[0])]
    print(p,gut,len(cl),P.get(f'p{int(p)*2:03d}'),P.get(f'p{int(p)*2+1:03d}'))
json.dump(dict(P=P,CH=CH),open('pages.json','w'))
