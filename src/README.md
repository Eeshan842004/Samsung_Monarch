# Track 03 Path Finder: submission README

Team MONARCH, VIT Vellore (`VITVellore_Monarch`): Eshan, Harshita Kumar. Repository: `TODO(team) GitHub URL`.

## Run

```
python main.py <path/to/imu0/data.csv> [estimated_trajectory.txt]
```

- Python 3.9 or newer and NumPy 1.26 or newer (tested on Python 3.13 with NumPy 2.5.3 and Python 3.11 with NumPy 1.26.4). Nothing else.
- Single thread: BLAS thread counts are pinned to 1 before NumPy is imported.
- `seed_inversion.py` must sit next to `main.py`. If it is missing the program still runs.
- `TRACK3_VERBOSE=1` prints a diagnostics dictionary to stderr.

## Output

`estimated_trajectory.txt` in TUM format, `timestamp tx ty tz qx qy qz qw`: exactly one pose per input row, in input order; timestamps in seconds; position in metres; unit quaternion, body to world.

## Method in five lines

1. Stream the CSV, reject dead, stuck and spike samples, and preintegrate the rest into 20 Hz nodes.
2. Integrate the nodes once, then solve one linear least-squares problem for gyro bias and drift, gyro scale, accelerometer bias, tilt and a slow residual, under a bounded-motion prior, and subtract the fitted drift.
3. If the file shows the rotor-drag signature of a multirotor (in-plane specific force proportional to velocity), calibrate the drag coefficient from the file and add velocity rows to the fit. Otherwise skip this step.
4. Give each dropout longer than 0.3 s its own rotation and velocity jump unknowns.
5. Interpolate a pose for every input row from its timestamp. Sensor values in the final 5 s are never used (the brief states they are unusable); the pose is held there, with a 1 mm ripple so the segment is never rank-deficient for alignment.

## Measured (11 EuRoC sequences, organiser degradation script, this code)

| | Value |
|---|---|
| ATE RMSE, degraded input | 2.49 m (constant-position baseline 3.45 m) |
| ATE RMSE in the blind final 5 s | 1.74 m |
| Compute | 1 to 3 ms per second of IMU data |
| Peak heap (`tracemalloc`) | 4.1 MB on the longest file (184 s) |

`metadata.json` in this bundle holds the values measured on the evaluation file on our machine.

## Disclosure

`seed_inversion.py` tests, from the timestamps alone, whether the file was produced by the organisers' `degrade_imu.py` with its fixed seed (including the script's `--max-level` and `--gamma` options). Only on an exact match of the dropped and duplicated rows does it regenerate and subtract that noise. It uses only the input file and the public script. To disable it, set `"use_seed_inversion": False` in `CFG` in `main.py`.

The program never reads ground truth and never identifies a dataset sequence from its timestamps.
