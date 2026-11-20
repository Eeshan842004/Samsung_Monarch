"""Run a config over many recordings; print per-sequence and mean metrics."""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sys, json, glob, os; 
import numpy as np, bench as Bn
def suite(cfg, pattern="data/euroc/*", imu="imu.csv", verbose=True, mod="main"):
    rows=[]
    for d in sorted(glob.glob(pattern)):
        if not os.path.exists(f"{d}/{imu}"): continue
        m = Bn.run(f"{d}/{imu}", f"{d}/gt.csv", cfg, mod=mod); m["seq"]=os.path.basename(d); rows.append(m)
        if verbose:
            print("%-16s ATE %5.2f (static %4.2f) blind %5.2f | DR5s end %5.2f rmse %5.2f (travel %4.2f) | RPE1s %.3f m %5.2f deg | rot %5.1f | %.1f ms/s" % (
              m["seq"], m["ate_rmse"], m["static_rmse"], m["ate_blind"], m["blind_dr_end"], m["blind_dr_rmse"], m["blind_gt_travel"], m["rpe_trans_1s"], m["rpe_rot_1s_deg"], m["rot_rmse_deg"], m["ms_per_s"]))
    keys=["ate_rmse","static_rmse","ate_blind","blind_dr_end","blind_dr_rmse","rpe_trans_1s","rpe_rot_1s_deg","rot_rmse_deg","ms_per_s"]
    mean={k: float(np.mean([r[k] for r in rows])) for k in keys}
    print("MEAN  ATE %.3f (static %.3f) blindATE %.3f DR5 end %.3f rmse %.3f | RPE %.3f m %.3f deg | rot %.2f | %.2f ms/s  n=%d" % tuple([mean[k] for k in keys]+[len(rows)]))
    return rows, mean
if __name__=="__main__":
    cfg = json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
    suite(cfg, *(sys.argv[2:4]))
