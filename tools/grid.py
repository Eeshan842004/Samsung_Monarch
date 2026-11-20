import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys, json, itertools, io, contextlib; 
import suite
grid=json.loads(sys.argv[1]); imu=sys.argv[2]; base=json.loads(sys.argv[3]) if len(sys.argv)>3 else {}
keys=list(grid)
for vals in itertools.product(*[grid[k] for k in keys]):
    cfg=dict(base); cfg.update(zip(keys,vals))
    with contextlib.redirect_stdout(io.StringIO()):
        rows,m=suite.suite(cfg,"data/euroc/*",imu,verbose=False)
    print(imu, " ".join(f"{k}={v}" for k,v in zip(keys,vals)), "| ATE %.3f blindATE %.3f DR5end %.3f DR5rmse %.3f RPE %.3f m %.3f deg rot %.1f blindrot %.1f | worst ATE %.2f"%(m["ate_rmse"],m["ate_blind"],m["blind_dr_end"],m["blind_dr_rmse"],m["rpe_trans_1s"],m["rpe_rot_1s_deg"],m["rot_rmse_deg"],sum(r["blind_rot_end_deg"] for r in rows)/len(rows),max(r["ate_rmse"] for r in rows)))
