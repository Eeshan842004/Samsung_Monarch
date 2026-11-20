"""Held-out report for the shipped configuration. The settings in CFG were selected with tools/tune.py
on the TRAIN flights only; this prints both splits so the gap is visible. (Split of AirIMU / AirIO.)"""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np, bench as Bn
TRAIN=["MH_01_easy","MH_03_medium","MH_05_difficult","V1_02_medium","V2_01_easy","V2_03_difficult"]
TEST=["MH_02_easy","MH_04_difficult","V1_01_easy","V1_03_difficult","V2_02_medium"]
FILES=[("clean","imu.csv"),("degraded seed 42, no inversion","deg_af.csv"),("degraded seed 1","deg_seed1.csv"),("raw column order, no inversion","deg_raw.csv")]
for name,seqs in (("TRAIN",TRAIN),("TEST",TEST)):
    tot=[]
    for lab,f in FILES:
        r=[Bn.run(f"data/euroc/{s}/{f}",f"data/euroc/{s}/gt.csv",{"use_seed_inversion":False}) for s in seqs]
        a=float(np.mean([m["ate_rmse"] for m in r])); c=float(np.mean([m["static_rmse"] for m in r])); tot.append(a)
        print("%-5s %-32s ATE %.2f m | constant %.2f m | blind-window ATE %.2f m"%(name,lab,a,c,float(np.mean([m["ate_blind"] for m in r]))))
    print("%-5s mean over the four variants: %.3f m"%(name,np.mean(tot)))
