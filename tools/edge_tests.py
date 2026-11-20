"""Edge-case smoke tests: every case must produce exactly one finite pose per input row."""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sys, os, subprocess, numpy as np

src="data/euroc/V1_02_medium/imu.csv"; os.makedirs("_edge",exist_ok=True)
L=open(src).read().splitlines(); hdr, rows = L[0], L[1:6001]
def w(name, lines, header=hdr):
    p=f"_edge/{name}.csv"; open(p,"w").write(("" if header is None else header+"\n")+"\n".join(lines)+"\n"); return p
def cols(r): return r.split(",")
cases={}
cases["no_header"]=w("no_header",rows,None)
cases["accel_first"]=w("accel_first",[",".join([c[0]]+c[4:7]+c[1:4]) for c in map(cols,rows)],"t,ax,ay,az,gx,gy,gz")
cases["accel_in_g"]=w("accel_in_g",[",".join(c[:4]+["%.9f"%(float(x)/9.80665) for x in c[4:7]]) for c in map(cols,rows)])
cases["gyro_deg"]=w("gyro_deg",[",".join([c[0]]+["%.9f"%np.degrees(float(x)) for x in c[1:4]]+c[4:7]) for c in map(cols,rows)])
cases["seconds_ts"]=w("seconds_ts",[",".join(["%.6f"%(int(c[0])*1e-9)]+c[1:]) for c in map(cols,rows)])
cases["two_rows"]=w("two_rows",rows[:2])
cases["short_50"]=w("short_50",rows[:50])
cases["zeros_tail"]=w("zeros_tail",rows[:5000]+[c[0]+",0,0,0,0,0,0" for c in map(cols,rows[5000:])])
cases["nan_tail"]=w("nan_tail",rows[:5000]+[c[0]+",nan,nan,nan,nan,nan,nan" for c in map(cols,rows[5000:])])
cases["const_tail"]=w("const_tail",rows[:5000]+[c[0]+","+",".join(cols(rows[4999])[1:]) for c in map(cols,rows[5000:])])
cases["garbage_tail"]=w("garbage_tail",rows[:5000]+[c[0]+",1e6,-1e6,1e6,-1e6,1e6,-1e6" for c in map(cols,rows[5000:])])
_r=np.random.default_rng(0)
cases["noise_tail"]=w("noise_tail",rows[:5000]+[c[0]+","+",".join("%.6f"%v for v in np.concatenate([_r.normal(0,1,3),_r.normal(0,3,3)+[9.8,0,0]])) for c in map(cols,rows[5000:])])
cases["all_zero"]=w("all_zero",[c[0]+",0,0,0,0,0,0" for c in map(cols,rows[:500])])
cases["gap_2s"]=w("gap_2s",rows[:2500]+rows[2900:])
cases["dup_rows"]=w("dup_rows",[r for i,r in enumerate(rows) for _ in range(2 if i%97==0 else 1)])
cases["swapped_rows"]=w("swapped_rows",rows[:1000]+[rows[1001],rows[1000]]+rows[1002:])
cases["moving_start"]=w("moving_start",L[4001:10001])
cases["crlf"]=w("crlf",[r+"\r" for r in rows],hdr+"\r")
ok=True
for name,p in cases.items():
    out=f"_edge/{name}.txt"
    r=subprocess.run([sys.executable,os.path.join(_ROOT, "src", "main.py"),p,out],capture_output=True,text=True,env={**os.environ,"TRACK3_VERBOSE":"1"})
    n_in=sum(1 for l in open(p) if l.strip() and l[0] not in "#t")
    try:
        m=np.loadtxt(out,ndmin=2); good = r.returncode==0 and m.shape==(n_in,8) and np.isfinite(m).all() and np.allclose(np.linalg.norm(m[:,4:8],axis=1),1,atol=1e-6)
        extent=np.ptp(m[:,1:4],axis=0).max()
    except Exception as e: good=False; extent=float("nan"); m=None
    note = ("fallback" if "fallback" in r.stderr else "")
    print("%-14s %s rows_in=%d rows_out=%s max_extent=%.3f m %s %s"%(name,"PASS" if good else "FAIL",n_in,None if m is None else m.shape[0],extent,note,r.stderr.strip()[-120:] if not good else ""))
    ok&=good
print("ALL PASS" if ok else "SOME FAILED")
