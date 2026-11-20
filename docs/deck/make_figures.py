"""Figures for the deck, from the final build and real data."""
import sys; sys.path.insert(0,"src"); sys.path.insert(0,"scripts")
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import main as M, bench as Bn
BG="#0A0E1A"; INK="#E8EDF5"; MUTE="#9AA7B4"; GRID="#1E2A3E"; OURS="#0E9CC2"; AMBER="#D07E08"; TRUTH="#8A94A0"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,"axes.facecolor":BG,"figure.facecolor":BG,"text.color":INK,
    "axes.labelcolor":MUTE,"xtick.color":MUTE,"ytick.color":MUTE,"axes.edgecolor":GRID})
def clean(ax):
    for s in ax.spines.values(): s.set_visible(False)
    ax.grid(color=GRID,lw=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)

# F1: trajectory, near-median flight, degraded input, default pipeline
seq="MH_03_medium"; d=f"data/euroc/{seq}"
ts,P,Q,info=M.estimate(f"{d}/deg_af.csv")
gt=np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=range(1,4)); tg=np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=0,dtype=np.int64)
t=(ts-ts[0])*1e-9; ie,ig=Bn.associate(t,(tg-ts[0])*1e-9)
R,tr=Bn.umeyama(P[ie],gt[ig]); A=P@R.T+tr
e=np.linalg.norm(A[ie]-gt[ig],axis=1); ate=np.sqrt((e**2).mean())
blind=t>=t[-1]-5.0
fig,ax=plt.subplots(figsize=(6.4,5.0),dpi=200)
ax.plot(gt[:,0],gt[:,1],color=TRUTH,lw=2.0,label="Ground truth")
ax.plot(A[~blind,0],A[~blind,1],color=OURS,lw=2.0,label="Our estimate")
ax.plot(A[blind,0],A[blind,1],color=AMBER,lw=3.2,label="Blind final 5 s")
ax.scatter([A[blind][-1,0]],[A[blind][-1,1]],s=60,color=AMBER,zorder=5,edgecolor=BG,linewidth=2)
ax.set_aspect("equal"); clean(ax); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
leg=ax.legend(loc="lower center",bbox_to_anchor=(0.5,1.0),ncol=3,frameon=False,fontsize=12,labelcolor=INK,handlelength=1.6,columnspacing=1.2)
fig.tight_layout(); fig.savefig("docs/deck/fig/trajectory.png"); plt.close(fig)
print("trajectory ATE", ate)

# F2: rotor drag physics, one flight, 1 s means, ground truth used only to show the effect
seq="V1_02_medium"; d=f"data/euroc/{seq}"
m=np.loadtxt(f"{d}/imu.csv",delimiter=",",skiprows=1,usecols=range(1,7)); ti=np.loadtxt(f"{d}/imu.csv",delimiter=",",skiprows=1,usecols=0,dtype=np.int64)
G=np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=range(1,11)); tg=np.loadtxt(f"{d}/gt.csv",delimiter=",",skiprows=1,usecols=0,dtype=np.int64)
ie,ig=Bn.associate((ti-ti[0])*1e-9,(tg-ti[0])*1e-9)
q=G[ig,3:7]/np.linalg.norm(G[ig,3:7],axis=1)[:,None]; vb=M.quat_rotate(q*np.array([1,-1,-1,-1]),G[ig,7:10]); f=m[ie,3:]
W=200; n=len(f)//W
fb=f[:n*W].reshape(n,W,3).mean(1); vbb=vb[:n*W].reshape(n,W,3).mean(1)
ax_t=fb.mean(0); ax_t/=np.linalg.norm(ax_t); e1=np.cross(ax_t,[0,0,1.0]); e1/=np.linalg.norm(e1); e2=np.cross(ax_t,e1)
X=np.concatenate([vbb@e1,vbb@e2]); Y=np.concatenate([fb@e1,fb@e2])
Y=Y-np.concatenate([np.full(n,np.median(fb@e1)),np.full(n,np.median(fb@e2))])
k=np.polyfit(X,Y,1); r=np.corrcoef(X,Y)[0,1]
fig,ax=plt.subplots(figsize=(6.0,4.6),dpi=200)
ax.scatter(X,Y,s=14,color=OURS,alpha=0.55,linewidths=0)
xx=np.linspace(X.min(),X.max(),10); ax.plot(xx,np.polyval(k,xx),color=AMBER,lw=2.4)
ax.text(0.97,0.92,f"slope = {k[0]:.2f} 1/s\ncorrelation {r:.2f}",transform=ax.transAxes,ha="right",va="top",color=INK,fontsize=13)
clean(ax); ax.set_xlabel("in-plane body velocity [m/s]"); ax.set_ylabel("in-plane specific force [m/s²]")
fig.tight_layout(); fig.savefig("docs/deck/fig/drag.png"); plt.close(fig)
print("drag slope", k[0], "corr", r)
