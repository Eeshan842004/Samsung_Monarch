"""Falsification tests for the rotor-drag model (run on clean files with ground truth).
1. self-calibrated mu per file and on each half of the file
2. NULL test: the in-plane force is shifted by 37 s, which keeps its statistics but breaks the
   physics; the model must switch itself off and the gain must disappear
3. leave-one-out: mu fixed to the mean of the OTHER sequences
Usage: python tools/falsify_drag.py "data/euroc/*" ["data/tumvi/room*"]"""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import glob
import numpy as np, bench as Bn
R = {}
pats = sys.argv[1:] or ["data/euroc/*"]
for d in [x for p in pats for x in sorted(glob.glob(p))]:
    m = Bn.run(f"{d}/imu.csv", f"{d}/gt.csv", {"use_seed_inversion": False}); dr = m["info"]["drag"]
    mn = Bn.run(f"{d}/imu.csv", f"{d}/gt.csv", {"use_seed_inversion": False, "_drag_null_shift_rows": 37}); dn = mn["info"]["drag"]
    R[d] = (m, dr)
    print("%-16s mu %.3f halves (%.2f, %.2f) corr %+.2f used %-5s ATE %.2f | NULL: corr %+.2f used %-5s ATE %.2f" % (
        os.path.basename(d), dr["mu"], *dr.get("mu_halves", (0, 0)), dr["corr"], dr["used"], m["ate_rmse"], dn["corr"], dn["used"], mn["ate_rmse"]))
used = [k for k in R if R[k][1]["used"]]
if len(used) > 2:
    loso = []
    for k in used:
        mu = float(np.mean([R[kk][1]["mu"] for kk in used if kk != k]))
        loso.append(Bn.run(f"{k}/imu.csv", f"{k}/gt.csv", {"use_seed_inversion": False, "drag_mu": mu})["ate_rmse"])
    print("mean ATE where the model is used: self-calibrated %.3f | leave-one-out mu %.3f" % (np.mean([R[k][0]["ate_rmse"] for k in used]), np.mean(loso)))
