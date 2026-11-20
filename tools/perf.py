import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys, time, tracemalloc, subprocess, resource; 
import numpy as np, main as M
path=sys.argv[1]; inv = len(sys.argv)<3 or sys.argv[2]!="noinv"
cfg=dict(M.CFG); cfg["use_seed_inversion"]=inv
t0=time.perf_counter(); ts,info,sol=M.solve_file(path,cfg); M.write_trajectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_perf_est.txt"),ts,info,sol,cfg); wall=time.perf_counter()-t0
dur=(ts[-1]-ts[0])*info["ts_scale"]
del ts,sol
tracemalloc.start(); ts,info,sol=M.solve_file(path,cfg); M.write_trajectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_perf_est.txt"),ts,info,sol,cfg); cur,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
print("%s rows=%d dur=%.1fs | wall %.3f s = %.2f ms per s of IMU | tracemalloc peak %.2f MB | %s"%(path.split('/')[-2]+'/'+path.split('/')[-1],len(ts),dur,wall,1000*wall/dur,peak/2**20,str(info.get("seed_inversion",""))[:30]))
