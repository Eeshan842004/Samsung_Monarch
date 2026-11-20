"""Choose settings on the TRAIN split only (three degraded variants, no inversion); report TEST."""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json, itertools
import numpy as np, bench as Bn
TRAIN=["MH_01_easy","MH_03_medium","MH_05_difficult","V1_02_medium","V2_01_easy","V2_03_difficult"]
TEST=["MH_02_easy","MH_04_difficult","V1_01_easy","V1_03_difficult","V2_02_medium"]
FILES=["deg_seed1.csv","deg_af.csv","deg_raw.csv","imu.csv"]
def score(cfg, seqs):
    c=dict(cfg,use_seed_inversion=False); out={}
    for f in FILES:
        r=[Bn.run(f"data/euroc/{s}/{f}",f"data/euroc/{s}/gt.csv",c) for s in seqs]
        out[f]=(float(np.mean([m["ate_rmse"] for m in r])),float(np.mean([m["rot_rmse_deg"] for m in r])),float(np.mean([m["ate_blind"] for m in r])))
    return out
grid=json.loads(sys.argv[1]); keys=list(grid); res=[]
for vals in itertools.product(*grid.values()):
    cfg=dict(zip(keys,vals)); s=score(cfg,TRAIN); res.append((np.mean([s[f][0] for f in FILES]),cfg,s))
res.sort(key=lambda x:x[0])
fmt=lambda s: " ".join("%s %.2f/%.0fdeg"%(f.replace(".csv","").replace("deg_",""),s[f][0],s[f][1]) for f in FILES)
print("TRAIN ranking (mean ATE over 4 variants):")
for a,cfg,s in res[:5]+res[-1:]: print("  %.3f %s | %s"%(a,cfg,fmt(s)))
d=score({},TRAIN); print("  default: %.3f | %s"%(np.mean([d[f][0] for f in FILES]),fmt(d)))
print("TEST split:")
for name,cfg in (("default",{}),("train-best",res[0][1])):
    s=score(cfg,TEST); print("  %-10s %.3f | %s | blind %s"%(name,np.mean([s[f][0] for f in FILES]),fmt(s)," ".join("%.2f"%s[f][2] for f in FILES)))
