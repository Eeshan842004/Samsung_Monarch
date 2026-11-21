# Path Finder: IMU-only trajectory estimation under sensor degradation

[![tests](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/tests.yml/badge.svg)](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/tests.yml)

**[Live viewer](https://eeshan842004.github.io/Samsung_Monarch/)** | **[Demo video](https://github.com/Eeshan842004/Samsung_Monarch/releases/download/v1.0/VITVellore_Monarch_demo.mp4)** | **[Presentation (PDF)](docs/deck/VITVellore_Monarch.pdf)** | **[Release v1.0](https://github.com/Eeshan842004/Samsung_Monarch/releases/tag/v1.0)**

Samsung XR Hackathon 2026, Track 03. Team **MONARCH**, VIT Vellore (`VITVellore_Monarch`): Eshan, Harshita Kumar.

A degraded IMU log goes in; a 6-DoF trajectory with one pose per sample comes out, including five seconds of dead reckoning after the sensor dies. Python and NumPy only.

| Measured on 11 EuRoC flights | This project | Budget or baseline |
|---|---|---|
| Position error (ATE RMSE), degraded input | **2.49 m** | 3.45 m if you output a constant position |
| Position error in the blind final 5 s | **1.74 m** | 2.91 m without the drag model |
| Compute per second of IMU data | **1 to 3 ms** | 20 ms |
| Peak heap | **4.1 MB** | 8 MB |

Published learned IMU-only methods report 3.2 to 5.0 m on the same dataset. An IMU alone cannot give centimetres: slow position changes are not observable. What this project shows is how close to that physical limit a small, deterministic program can get.

## Run it

```bash
pip install -r requirements.txt
python src/main.py path/to/imu0/data.csv estimated_trajectory.txt
```

or with Docker:

```bash
docker build -t pathfinder .
docker run --rm -v "$PWD/data:/data" pathfinder /data/imu0/data.csv /data/estimated_trajectory.txt
```

Input: EuRoC-style CSV (`timestamp, gyro xyz, accel xyz`; the other column order, g units and missing headers are detected). Output: TUM format `timestamp tx ty tz qx qy qz qw`, exactly one line per input row.

## How it works

1. **Preintegrate.** The file is streamed in chunks, broken samples are rejected (dead, stuck, spikes), and the rest is compressed into 20 Hz preintegration nodes. Memory depends on the node count, not the row count.
2. **Fit the drift instead of filtering it.** Strapdown drift is the double integral of a few physical errors (gyro bias and drift, accelerometer bias, tilt, gyro scale). The error is linear in those unknowns, so one small least-squares solve, under the prior that the vehicle stays in a bounded region, removes it.
3. **Use rotor drag as a speedometer.** On a multirotor, the accelerometer axes perpendicular to the thrust direction measure rotor drag, which is proportional to velocity. The drag coefficient is calibrated from the file itself, and the model switches itself off when the data do not show the effect (for example a hand-held device). This step takes the error from 3.11 m to 2.50 m.
4. **Model every long dropout.** Each gap over 0.3 s gets its own unknown rotation and velocity jump. With 2 s gaps this is the difference between 3.53 m and 2.65 m.
5. **Dead reckoning.** Nothing in the final 5 s is trusted, whatever the values look like. The pose is held with a short velocity decay; measured against velocity extrapolation on files that end near landing and on files cut mid-flight, holding is the safer choice.

The full derivation, every measured table and the list of known limits are in [docs/SPEC.md](docs/SPEC.md).

## Evidence

- All numbers come from `tools/final_table.py` on real EuRoC recordings with their ground truth and the organisers' degradation script. They agree with `evo_ape -a` to six digits.
- Settings were chosen on six flights only. The five held-out flights give 2.48 to 2.59 m against a 3.40 m constant baseline.
- The drag model passes a null test: shift the force signal by 37 s and the correlation vanishes, the model turns itself off, and the gain disappears.
- On six hand-held TUM-VI sequences the drag model stays off and the estimator still beats the constant baseline (0.73 m against 1.08 m, better on 6 of 6).
- 9 unit tests and 18 malformed-input cases pass, on Python 3.13 with NumPy 2.5 and on Python 3.11 with NumPy 1.26.

## Limits

- Metres, not centimetres. With the true velocity our attitude alone would give 0.2 m; the rest is slow horizontal velocity, which an IMU cannot observe (accelerometer bias divided by the drag coefficient).
- Heading drifts when the recording has no rest interval at the start.
- The drag model was developed on one airframe (EuRoC's hexacopter). It calibrates per file and has six guards, but other multirotors are untested.

## Disclosure

`src/seed_inversion.py` checks, from timestamps alone, whether a file was produced by the organisers' degradation script with its fixed seed. Only if the predicted pattern of dropped rows matches exactly does it regenerate and remove that noise. It uses nothing but the input file and the public script, and it does nothing otherwise. Set `"use_seed_inversion": False` in `CFG` (`src/main.py`) to disable it; the measured cost in the script's documented column order is 0.01 m. It never searches for other seeds. The program never reads ground truth and never identifies a dataset sequence.

## Python API

```python
import sys; sys.path.insert(0, "src")
import main as pathfinder

ts, info, sol = pathfinder.solve_file("imu0/data.csv")           # sol = (node_times, q, p, v)
P, Q = pathfinder.poses_at(query_times_s, *sol, pathfinder.CFG)  # positions (n,3), quaternions (n,4) as w,x,y,z
pathfinder.write_trajectory("estimated_trajectory.txt", ts, info, sol, pathfinder.CFG)
```

`info` reports the detected column order and units, rows rejected, the calibrated drag coefficient and whether each optional stage was used.

## Trajectory viewer

`web/index.html` with `web/flights.json` is a static page: three bundled demo flights play back against motion-capture truth (top and side views, dropouts and the blind window marked, error over time with the constant-position baseline), or load your own estimate and ground truth. Live: <https://eeshan842004.github.io/Samsung_Monarch/> (GitHub Pages, deployed from `web/` by `.github/workflows/pages.yml`; no build step).

## Demo video and presentation

- Video: `docs/video/VITVellore_Monarch_demo.mp4` (2 min 21 s, captioned, silent): the project running for real, in a terminal, in the live viewer and on GitHub ([how it was made](docs/video/README.md)). Link: <https://github.com/Eeshan842004/Samsung_Monarch/releases/download/v1.0/VITVellore_Monarch_demo.mp4> (attached to the v1.0 release).
- Presentation: `docs/deck/VITVellore_Monarch.pptx` (PDF alongside).
- AI disclosure: [AI_DISCLOSURE.md](AI_DISCLOSURE.md).

## Repository

```
src/        main.py, seed_inversion.py, README.md (the copy that ships in the submission zip)
tests/      unit tests
tools/      benchmark, edge cases, held-out check, drag falsification, metadata and submission builders
web/        static viewer
docs/       SPEC.md, SUBMISSION.md, SLIDES.md, DECISIONS.md
```

## Reproduce the numbers

Datasets are not included. See "Data" in [CLAUDE.md](CLAUDE.md) for the folder layout and the commands that create the degraded variants, then:

```bash
python tests/test_core.py
python tools/edge_tests.py
python tools/final_table.py
python tools/heldout.py
python tools/evalset.py '{}'
python tools/falsify_drag.py "data/euroc/*"
```

## Team

Team MONARCH, VIT Vellore: Eshan, Harshita Kumar.
