import json, re, difflib, opencc
cc=opencc.OpenCC('t2s')
S=json.load(open('/home/user/yikonglu-site/tools/szj.json'))
G=json.load(open('geom.json'))
W=[];  # (spread,col,ci,char)
for p in sorted(G):
    for k,t in enumerate(G[p]['txt']):
        for i,ch in enumerate(t): W.append((p,k,i,ch))
wt=''.join(cc.convert(x[3]) for x in W)
J=[]
for s in S:
    for gid,yw,bh in s['groups']:
        for ch in re.sub(r'[，。、；：！？]','',yw): J.append((s['n'],gid,ch))
jt=''.join(x[2] for x in J)
# normalize variants
norm=str.maketrans({'弟':'悌','元':'玄','故':'诂','詁':'诂','碁':'棋','颕':'颖','頴':'颖','籯':'籝','遊':'游'})
sm=difflib.SequenceMatcher(None,jt.translate(norm),wt.translate(norm),autojunk=False)
M={}  # J index -> W index
for op,a0,a1,b0,b1 in sm.get_opcodes():
    if op=='equal' or (op=='replace' and a1-a0==b1-b0):
        for k in range(a1-a0): M[a0+k]=b0+k
    if op!='equal': print(op,jt[a0:a1],'|',wt[b0:b1], J[a0][:2] if a0<len(J) else '', W[b0][:2] if b0<len(W) else '')
grp={}
for ji,(n,gid,ch) in enumerate(J):
    grp.setdefault((n,gid),[]).append(M.get(ji))
out={}
for (n,gid),ws in grp.items():
    hit=[W[w] for w in ws if w is not None]
    out.setdefault(n,[]).append([gid,len(hit),len(ws),[[h[0],h[1],h[2]] for h in hit]])
json.dump(out,open('gmap.json','w'))
print('groups',len(grp),'partial',[(k,len([w for w in v if w is not None]),len(v)) for k,v in grp.items() if None in v])
