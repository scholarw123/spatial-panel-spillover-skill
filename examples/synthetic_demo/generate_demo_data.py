"""Generate deterministic artificial data; no source study is used or reproduced."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
RNG=np.random.default_rng(20260401)
UNITS=[f'R{i:02d}' for i in range(1,13)]
lat=[];lon=[]
for j in range(12):
    lat.append(32.0+(j//4)*2.0+(j%3)*.07)
    lon.append(105.0+(j%4)*2.0+(j//4)*.09)
coords=pd.DataFrame({'unit':UNITS,'lat':lat,'lon':lon})
coords.to_csv(ROOT/'coordinates.csv',index=False)
# Fixed artificial geographical weights for data generation only.
d=np.hypot((np.array(lat)[:,None]-np.array(lat)[None,:]),(np.array(lon)[:,None]-np.array(lon)[None,:]))
np.fill_diagonal(d,np.inf)
A=(np.argsort(np.argsort(d,axis=1),axis=1)<3).astype(float)
A=((A+A.T)>0).astype(float);np.fill_diagonal(A,0)
W=A/A.sum(axis=1,keepdims=True)
u=RNG.normal(0,.35,12);g=RNG.normal(0,.25,12)
I=np.eye(12); rows=[]
for t in range(2018,2024):
    X=.7+g+.08*(t-2018)+RNG.normal(0,.25,12)
    C1=1.1+.45*g+.04*(t-2018)+RNG.normal(0,.2,12)
    C2=RNG.normal(0,.5,12)
    b=u+.13*(t-2018)+.8*X+.22*C1-.12*C2+.14*(W@X)+RNG.normal(0,.24,12)
    Y=np.linalg.solve(I-.22*W,b)
    for k, unit in enumerate(UNITS): rows.append({'unit':unit,'year':t,'Y':Y[k],'X':X[k],'C1':C1[k],'C2':C2[k]})
pd.DataFrame(rows).to_csv(ROOT/'panel.csv',index=False)
print('Synthetic demo generated: 12 fictional regions x 6 years = 72 records')
