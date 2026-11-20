import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys, json, io, contextlib; 
import numpy as np, suite
scen=[("clean","imu.csv",{}),
      ("clean, drag model OFF","imu.csv",{"drag_mu":-1.0}),
      ("degraded accel-first, inversion ON","deg_af.csv",{"use_seed_inversion":True}),
      ("degraded accel-first, inversion OFF","deg_af.csv",{"use_seed_inversion":False}),
      ("degraded accel-first, inv OFF, drag OFF","deg_af.csv",{"use_seed_inversion":False,"drag_mu":-1.0}),
      ("degraded raw-EuRoC order, inversion ON","deg_raw.csv",{"use_seed_inversion":True}),
      ("degraded raw-EuRoC order, inversion OFF","deg_raw.csv",{"use_seed_inversion":False}),
      ("seed 1 (no inversion possible)","deg_seed1.csv",{}),
      ("seed 2","deg_seed2.csv",{}),
      ("seed 3","deg_seed3.csv",{}),
      ("seed 7 + long gaps (<=2 s), gap model ON","deg_s7.csv",{}),
      ("seed 7 + long gaps (<=2 s), gap model OFF","deg_s7.csv",{"gap_s":99.0})]
out={}
for name,f,cfg in scen:
    with contextlib.redirect_stdout(io.StringIO()):
        rows,mean=suite.suite(cfg,"data/euroc/*",f,verbose=False)
    out[name]={"mean":mean,"rows":[{k:(v if not isinstance(v,(np.floating,)) else float(v)) for k,v in r.items() if k!="info"} for r in rows]}
    print("%-44s ATE %.2f | static %.2f | blindATE %.2f | DR5 rmse %.2f | RPE1s %.3f m %.2f deg | rot %.1f | %.2f ms/s | worst ATE %.2f | beats constant %d/%d"%(name,mean["ate_rmse"],mean["static_rmse"],mean["ate_blind"],mean["blind_dr_rmse"],mean["rpe_trans_1s"],mean["rpe_rot_1s_deg"],mean["rot_rmse_deg"],mean["ms_per_s"],max(r["ate_rmse"] for r in rows),sum(r["ate_rmse"]<r["static_rmse"] for r in rows),len(rows)))
json.dump(out,open("final_table.json","w"),indent=1,default=float)
print("\nper-sequence, clean / degraded(af, inv ON):")
for a,b in zip(out[scen[0][0]]["rows"],out[scen[2][0]]["rows"]):
    print("%-16s dur %5.1f s | clean ATE %.2f (static %.2f) RPE %.3f rot %4.1f | degraded ATE %.2f blindATE %.2f DR5 %.2f (travel %.2f) rot %4.1f"%(a["seq"],a["duration_s"],a["ate_rmse"],a["static_rmse"],a["rpe_trans_1s"],a["rot_rmse_deg"],b["ate_rmse"],b["ate_blind"],b["blind_dr_rmse"],b["blind_gt_travel"],b["rot_rmse_deg"]))
