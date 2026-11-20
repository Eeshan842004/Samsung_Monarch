"""Bundle demo flights for the web viewer: subsampled estimate + ground truth + dropout list + metrics."""
import os, sys, json
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, main as M, bench as Bn
FLIGHTS=[("MH_03_medium","Machine Hall 03","medium"),("V1_02_medium","Vicon Room 1-02","medium"),("MH_05_difficult","Machine Hall 05","difficult")]
out=[]
for seq,label,diff in FLIGHTS:
    d=f"data/euroc/{seq}"; f=f"{d}/deg_af.csv"
    ts,info,sol=M.solve_file(f,dict(M.CFG)); t=(ts-ts[0]).astype(float)*info["ts_scale"]
    P,Q=M.poses_at(t,*sol,M.CFG)
    m=Bn.run(f,f"{d}/gt.csv",{})
    dt=np.diff(t); med=np.median(dt); gi=np.flatnonzero(dt>2.5*med)
    gaps=[[round(float(t[i]),3),round(float(t[i+1]),3)] for i in gi]
    g=np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=(1,2,3)); tg=(np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=0,dtype=np.int64)-ts[0])*1e-9
    step=max(1,len(t)//2500); sg=max(1,len(tg)//2500)
    rec={"id":seq,"label":label,"difficulty":diff,"rows":int(len(t)),"duration":round(float(t[-1]),2),
         "est":[[round(float(a),3),round(float(x),3),round(float(y),3),round(float(z),3)] for a,(x,y,z) in zip(t[::step],P[::step])],
         "gt":[[round(float(a),3),round(float(x),3),round(float(y),3),round(float(z),3)] for a,(x,y,z) in zip(tg[::sg],g[::sg])],
         "gaps":gaps,"blind_from":round(float(t[-1]-5.0),3),
         "metrics":{"ate":round(m["ate_rmse"],3),"constant":round(m["static_rmse"],3),"ate_blind":round(m["ate_blind"],3),
                    "ms_per_s":round(m["ms_per_s"],2),"rpe":round(m["rpe_trans_1s"],3),"mu":round(float(info.get("drag",{}).get("mu",0)),3),
                    "drag_used":bool(info.get("drag",{}).get("used",False)),"rejected":int(info.get("dead",0)+info.get("stuck",0)+info.get("spike",0)),
                    "seed":str(info.get("seed_inversion",""))[:7]}}
    out.append(rec); print(seq, rec["metrics"], len(gaps),"gaps", "longest %.3f"%max([b-a for a,b in gaps] or [0]))
json.dump({"flights":out,"summary":{"ate":2.49,"constant":3.45,"blind":1.74,"heap_mb":4.1,"ms":"1-3"}},open(os.path.join(_ROOT,"web","flights.json"),"w"),separators=(",",":"))
print("wrote web/flights.json")
