import json, glob, re, pickle
Q=json.load(open(sorted(glob.glob('/mnt/project-files/一孔学-内-自媒体/数据/网站素材/_道德经/_原文/道德经原文-v*.json'))[-1]))
PUN=re.compile(r"[\s，。；：？！、“”‘’「」『』（）《》·…—]")
S=pickle.load(open("scan.pkl","rb")); cols=pickle.load(open("cols.pkl","rb")); hd,res=pickle.load(open("seg.pkl","rb"))
out={}; costs={}
for c,(L,tot,mc) in res.items():
    INF=10**9; n=len(mc)
    dp=[[INF]*(L+1) for _ in range(n+1)]; bk={}
    dp[0][0]=0
    for i in range(n):
        ni=cols[mc[i]]["n"]; R=S[cols[mc[i]]["p"]]["R"]
        for t in range(L+1):
            v=dp[i][t]
            if v>=INF: continue
            if v+1<dp[i+1][t]: dp[i+1][t]=v+1; bk[(i+1,t)]=(t,0)
            for m in range(max(1,ni-2),min(R,ni+2)+1):
                if t+m>L: break
                c2=v+3*abs(m-ni)
                if c2<dp[i+1][t+m]: dp[i+1][t+m]=c2; bk[(i+1,t+m)]=(t,m)
    cost=dp[n][L]; costs[c]=cost
    if cost>=INF: continue
    asg=[]; t=L
    for i in range(n,0,-1):
        pt,m=bk[(i,t)]
        if m: asg.append((mc[i-1],pt,m))
        t=pt
    out[c]=asg[::-1]
print(sorted(costs.items(),key=lambda x:-x[1])[:30])
print("cost<=4:",sum(1 for v in costs.values() if v<=4),"/",len(costs))
pickle.dump((out,costs),open("local.pkl","wb"))
