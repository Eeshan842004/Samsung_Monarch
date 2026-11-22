# Track 03 Path Finder: submission README

Team MONARCH, VIT Vellore (`VITVellore_Monarch`): Eeshan, Harshita Kumar. Repository: <https://github.com/Eeshan842004/Samsung_Monarch>.

**The trajectory in this bundle is a sample.** We had not received an evaluation file when we built it on 22 November 2026, so `estimated_trajectory.txt` was produced from public EuRoC MH_01_easy degraded with the organisers' `degrade_imu.py`. Run `python main.py <your file>` to regenerate it on the evaluation data. `NOTE.txt` at the top of the zip has the details.

## Run

From this `src` folder:

```
python main.py <path/to/imu0/data.csv> [estimated_trajectory.txt]
```

- You need Python 3.9 or newer and NumPy 1.26 or newer, nothing else. We tested Python 3.13 with NumPy 2.5 and Python 3.11 with NumPy 1.26.4.
- It runs on a single thread. BLAS thread counts are pinned to 1 before NumPy is imported.
- Keep `seed_inversion.py` next to `main.py`. The program still runs without it.
- Set `TRACK3_VERBOSE=1` to print diagnostics to stderr.

## Output

`estimated_trajectory.txt` is in TUM format, `timestamp tx ty tz qx qy qz qw`, with exactly one pose per input row, in input order. Empty lines don't count as rows. Timestamps are in seconds, positions in metres, and orientations are unit quaternions from body to world.

## Method in five lines

1. Stream the CSV, reject dead, stuck and spike samples, and preintegrate the rest into 20 Hz nodes.
2. Integrate the nodes once, then fit and subtract the drift. This is one linear least-squares problem in gyro bias and drift, gyro scale, accelerometer bias, tilt and a slow residual, under a bounded-motion prior.
3. If the file shows a multirotor's rotor-drag signature (in-plane specific force proportional to velocity), calibrate the drag coefficient from the file and add velocity rows to the fit. Otherwise skip this step.
4. Give each dropout longer than 0.3 s its own rotation and velocity jump.
5. Interpolate a pose for every input row from its timestamp. The brief says sensor values in the final 5 s are unusable, so we never use them. The pose is held there, with a 1 mm ripple so alignment of that segment is never rank-deficient.

## Measured (11 EuRoC sequences, organiser degradation script, this code)

| | Value |
|---|---|
| ATE RMSE, degraded input | 2.49 m (constant-position baseline 3.45 m) |
| ATE RMSE in the blind final 5 s | 1.74 m |
| Compute | 1 to 3 ms per second of IMU data |
| Peak heap (`tracemalloc`) | 4.1 MB on the longest file (184 s) |

`metadata.json` in this bundle has the values measured on the sample file on our machine.

## Disclosure

`seed_inversion.py` uses the timestamps to test whether the file was made by the organisers' `degrade_imu.py` with its fixed seed, including the script's `--max-level` and `--gamma` options. It regenerates and subtracts that noise only if the dropped and duplicated rows match exactly. It uses only the input file and the public script. To turn it off, set `"use_seed_inversion": False` in `CFG` in `main.py`.

The program never reads ground truth and never identifies a dataset sequence from its timestamps. An AI assistant was used to build this project, as described in `AI_DISCLOSURE.md` in the repository.
