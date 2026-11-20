"""Evaluation harness. Own implementation of evo-style metrics (cross-checked against evo):
ATE RMSE after SE(3) Umeyama (no scale), RPE over fixed time deltas, blind-window error."""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sys, time, json, importlib, tracemalloc
import numpy as np


def load_gt(path):
    """EuRoC state_groundtruth_estimate0/data.csv -> t_ns, p (n,3), q wxyz (n,4)"""
    with open(path) as fh:
        first = fh.readline()
    skip = 0 if first[0].isdigit() else 1
    ts = np.loadtxt(path, delimiter=",", skiprows=skip, usecols=0, dtype=np.int64, comments=None)
    m = np.loadtxt(path, delimiter=",", skiprows=skip, usecols=range(1, 8), comments=None)
    return ts, m[:, :3], m[:, 3:7]


def umeyama(x, y):
    """R, t minimising sum |R x_i + t - y_i|^2 (no scale)."""
    mx, my = x.mean(0), y.mean(0)
    S = (y - my).T @ (x - mx) / len(x)
    U, d, Vt = np.linalg.svd(S)
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    return R, my - R @ mx


def qrot_mat(q):
    w, x, y, z = q.T
    return np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
                     2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
                     2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], 1).reshape(-1, 3, 3)


def associate(t_est, t_gt, max_diff=0.01):
    """nearest GT sample for every estimate row (same idea as evo.core.sync)"""
    j = np.clip(np.searchsorted(t_gt, t_est), 1, len(t_gt) - 1)
    j = np.where(np.abs(t_gt[j - 1] - t_est) < np.abs(t_gt[j] - t_est), j - 1, j)
    ok = np.abs(t_gt[j] - t_est) <= max_diff
    return np.flatnonzero(ok), j[ok]


def metrics(t_est, p_est, q_est, t_gt, p_gt, q_gt, blind_s=5.0):
    ie, ig = associate(t_est, t_gt)
    te, pe, qe = t_est[ie], p_est[ie], q_est[ie]
    pg, qg = p_gt[ig], q_gt[ig]
    R, tr = umeyama(pe, pg)
    pa = pe @ R.T + tr
    err = np.linalg.norm(pa - pg, axis=1)
    out = {"ate_rmse": float(np.sqrt((err ** 2).mean())), "ate_max": float(err.max()), "matched": int(len(ie))}
    # static baseline: best constant position
    out["static_rmse"] = float(np.sqrt(((pg - pg.mean(0)) ** 2).sum(1).mean()))
    # ATE split: sensed part vs blind tail (same global alignment)
    blind = te >= te[-1] - blind_s
    out["ate_sensed"] = float(np.sqrt((err[~blind] ** 2).mean()))
    out["ate_blind"] = float(np.sqrt((err[blind] ** 2).mean()))
    # blind-only dead-reckoning error: align on the sensed part's last pose instead (drift from hand-over)
    k = np.flatnonzero(blind)[0]
    d_est = (pa[blind] - pa[k]); d_gt = (pg[blind] - pg[k])
    out["blind_dr_end"] = float(np.linalg.norm(d_est[-1] - d_gt[-1]))
    out["blind_dr_rmse"] = float(np.sqrt(((d_est - d_gt) ** 2).sum(1).mean()))
    out["blind_gt_travel"] = float(np.linalg.norm(d_gt[-1]))
    # blind segment aligned on its own (what a per-segment evo run would report); may be degenerate
    try:
        Rb, tb = umeyama(pe[blind], pg[blind])
        eb = pe[blind] @ Rb.T + tb - pg[blind]
        out["blind_seg_ate"] = float(np.sqrt((eb ** 2).sum(1).mean()))
        cov = (pg[blind] - pg[blind].mean(0)).T @ (pe[blind] - pe[blind].mean(0)) / blind.sum()
        out["blind_seg_rank"] = int(np.count_nonzero(np.linalg.svd(cov, compute_uv=False) > np.finfo(float).eps))
    except Exception:
        out["blind_seg_ate"] = float("nan"); out["blind_seg_rank"] = 0
    # RPE over 1 s (translation, m) and rotation (deg), computed on aligned poses
    Re = np.einsum("ij,njk->nik", R, qrot_mat(qe)); Rg = qrot_mat(qg)
    step = max(1, int(round(1.0 / np.median(np.diff(te)[np.diff(te) > 0]))))
    i0 = np.arange(0, len(te) - step, step // 4 or 1); i1 = i0 + step
    de = np.einsum("nji,nj->ni", Re[i0], pa[i1] - pa[i0]); dg = np.einsum("nji,nj->ni", Rg[i0], pg[i1] - pg[i0])
    out["rpe_trans_1s"] = float(np.sqrt(((de - dg) ** 2).sum(1).mean()))
    dRe = np.einsum("nji,njk->nik", Re[i0], Re[i1]); dRg = np.einsum("nji,njk->nik", Rg[i0], Rg[i1])
    E = np.einsum("nji,njk->nik", dRg, dRe)
    ang = np.degrees(np.arccos(np.clip((np.trace(E, axis1=1, axis2=2) - 1) / 2, -1, 1)))
    out["rpe_rot_1s_deg"] = float(np.sqrt((ang ** 2).mean()))
    Eb = np.einsum("nji,njk->nik", Rg, Re)[blind]; Eb = np.einsum("ji,njk->nik", Eb[0], Eb)
    out["blind_rot_end_deg"] = float(np.degrees(np.arccos(np.clip((np.trace(Eb[-1]) - 1) / 2, -1, 1))))
    # absolute orientation error after alignment
    Ea = np.einsum("nji,njk->nik", Rg, Re)
    Ea = np.einsum("nij,jk->nik", Ea, Ea[0].T)   # remove constant body-frame offset
    aa = np.degrees(np.arccos(np.clip((np.trace(Ea, axis1=1, axis2=2) - 1) / 2, -1, 1)))
    out["rot_rmse_deg"] = float(np.sqrt((aa ** 2).mean()))
    return out


def run(imu_path, gt_path, cfg_over=None, measure=False, mod="main"):
    M = importlib.import_module(mod)
    cfg = dict(M.CFG); cfg.update(cfg_over or {})
    if measure:
        tracemalloc.start()
    t0 = time.perf_counter()
    ts, p, q, info = M.estimate(imu_path, cfg)
    dt = time.perf_counter() - t0
    peak = None
    if measure:
        peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    tg, pg, qg = load_gt(gt_path)
    scale = info["ts_scale"]
    t_est = (ts - ts[0]).astype(float) * scale
    t_gt = (tg - ts[0]).astype(float) * 1e-9
    m = metrics(t_est, p, q, t_gt, pg, qg)
    dur = t_est[-1]
    m.update({"runtime_s": dt, "ms_per_s": 1000 * dt / dur, "duration_s": float(dur), "info": info})
    if peak is not None:
        m["peak_mb"] = peak / 2 ** 20
    return m


if __name__ == "__main__":
    m = run(sys.argv[1], sys.argv[2], measure=False)
    print({k:(round(v,3) if isinstance(v,float) else v) for k,v in m.items() if k!="info"})
