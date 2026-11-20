"""Compact multi-set evaluation of one config (inversion off unless stated)."""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import glob, json
import numpy as np, bench as Bn
def ev(cfg, sets=None):
    out=[]
    S=sets or [("mid","data/mid/*","deg_af.csv"),("std","data/euroc/*","deg_af.csv"),("seed1","data/euroc/*","deg_seed1.csv"),("clean","data/euroc/*","imu.csv")]
    for name,pat,f in S:
        c=dict(cfg); c.setdefault("use_seed_inversion",False)
        r=[Bn.run(f"{d}/{f}",f"{d}/gt.csv",c) for d in sorted(glob.glob(pat))]
        g=lambda k: float(np.mean([m[k] for m in r]))
        out.append("%s: ATE %.3f blind[global %.3f DR %.3f seg %.3f rank>=2: %d/%d]"%(name,g("ate_rmse"),g("ate_blind"),g("blind_dr_rmse"),g("blind_seg_ate"),sum(m["blind_seg_rank"]>=2 for m in r),len(r)))
    return " | ".join(out)
if __name__=="__main__":
    for a in sys.argv[1:]:
        print(a, "\n    ", ev(json.loads(a)), flush=True)
