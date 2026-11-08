import numpy as np
def init(d,h,o,seed=0):
    rng=np.random.default_rng(seed)
    return dict(W1=rng.normal(0,np.sqrt(2/d),(d,h)).astype(np.float32),b1=np.zeros(h,np.float32),
                W2=rng.normal(0,np.sqrt(1/h),(h,o)).astype(np.float32),b2=np.zeros(o,np.float32))
def fwd(P,X):
    H=np.maximum(X@P["W1"]+P["b1"],0); z=H@P["W2"]+P["b2"]; return H,z
def predict(P,X):
    z=fwd(P,X)[1]; z=z-z.max(1,keepdims=True); e=np.exp(z); return e/e.sum(1,keepdims=True)
def fit(X,y,o=3,h=96,ep=40,bs=128,lr=2e-3,l2=1e-4,seed=0,cw=None):
    P=init(X.shape[1],h,o,seed); M={k:np.zeros_like(v) for k,v in P.items()}; S={k:np.zeros_like(v) for k,v in P.items()}
    rng=np.random.default_rng(seed); t=0; Y=np.eye(o,dtype=np.float32)[y]
    w=np.ones(len(y),np.float32) if cw is None else np.array(cw,np.float32)[y]
    for e in range(ep):
        perm=rng.permutation(len(y))
        for i in range(0,len(y),bs):
            j=perm[i:i+bs]; x=X[j]
            H,z=fwd(P,x); z=z-z.max(1,keepdims=True); p=np.exp(z); p/=p.sum(1,keepdims=True)
            dz=(p-Y[j])*w[j][:,None]/len(j)
            G={"W2":H.T@dz+l2*P["W2"],"b2":dz.sum(0)}
            dH=(dz@P["W2"].T)*(H>0)
            G["W1"]=x.T@dH+l2*P["W1"]; G["b1"]=dH.sum(0)
            t+=1
            for k in P:
                M[k]=0.9*M[k]+0.1*G[k]; S[k]=0.999*S[k]+0.001*G[k]**2
                P[k]-=lr*(M[k]/(1-0.9**t))/(np.sqrt(S[k]/(1-0.999**t))+1e-8)
    return P
