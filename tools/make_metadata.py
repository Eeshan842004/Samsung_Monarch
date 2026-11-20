"""Runs the estimator on one file and writes metadata.json (runtime and memory statistics).
Usage: python tools/make_metadata.py <imu.csv> <estimated_trajectory.txt> [metadata.json]"""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json, platform, statistics, time, tracemalloc
import numpy as np
import main as M
src = sys.argv[1]; out = sys.argv[2]; meta = sys.argv[3] if len(sys.argv) > 3 else "metadata.json"
times = []
for _ in range(5):
    t0 = time.perf_counter(); ts, info, sol = M.solve_file(src); M.write_trajectory(out, ts, info, sol, M.CFG); times.append(time.perf_counter() - t0)
dur = float((ts[-1] - ts[0]) * info["ts_scale"])
del ts, sol
tracemalloc.start(); ts, info, sol = M.solve_file(src); M.write_trajectory(out, ts, info, sol, M.CFG)
peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
rec = {"input_rows": info["rows"], "imu_duration_s": round(dur, 3),
       "runtime_s_median_of_5": round(statistics.median(times), 4),
       "runtime_ms_per_s_of_imu": round(1000 * statistics.median(times) / dur, 3),
       "peak_heap_mb_tracemalloc": round(peak / 2 ** 20, 3),
       "measurement": "time.perf_counter around solve_file+write_trajectory; tracemalloc peak (traces NumPy buffers); single thread",
       "python": platform.python_version(), "numpy": np.__version__, "machine": platform.processor() or platform.machine(),
       "diagnostics": {k: (v if isinstance(v, (int, float, str, bool, dict)) else str(v)) for k, v in info.items()}}
json.dump(rec, open(meta, "w"), indent=2, default=str)
print(json.dumps({k: rec[k] for k in list(rec)[:6]}, indent=1))
