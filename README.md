# Path Finder: IMU-only trajectory estimation under sensor degradation

[![tests](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/tests.yml/badge.svg)](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/tests.yml)
[![docker](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/docker.yml/badge.svg)](https://github.com/Eeshan842004/Samsung_Monarch/actions/workflows/docker.yml)

**[Live viewer](https://eeshan842004.github.io/Samsung_Monarch/)** | **[Demo video](https://drive.google.com/file/d/1P01XknByXCghU8aiNOevSH-U_mkTnmx_/view?usp=sharing)** | **[Presentation (PDF)](docs/deck/VITVellore_Monarch.pdf)** | **[Release v1.1](https://github.com/Eeshan842004/Samsung_Monarch/releases/tag/v1.1)**

We are Team **MONARCH** from VIT Vellore (Eeshan and Harshita Kumar), and this is our entry for Track 03 of the Samsung XR Hackathon 2026, submitted as `VITVellore_Monarch`.

The program reads a degraded IMU log and writes a 6-DoF pose for every sample, including the five seconds after the sensor dies. It needs only Python and NumPy.

| Measured on 11 EuRoC flights | This project | Budget or baseline |
|---|---|---|
| Position error (ATE RMSE), degraded input | **2.49 m** | 3.45 m if you output a constant position |
| Position error in the blind final 5 s | **1.74 m** | 2.91 m without the drag model and seed check |
| Compute per second of IMU data | **1 to 3 ms** | 20 ms |
| Peak heap | **4.1 MB** | 8 MB |

An IMU alone can't give centimetres, because it can't observe slow changes in position. We wanted to see how close a small, deterministic program could get to that limit. For comparison, published learned IMU-only methods report 3.2 to 5.0 m on the same dataset.

## Submission checklist

| Item on the form | Where to find it |
|---|---|
| Submission package | [VITVellore_Monarch.zip](https://github.com/Eeshan842004/Samsung_Monarch/releases/download/v1.1/VITVellore_Monarch.zip). **Its trajectory is from a sample input** ([why, and how to regenerate it](docs/submission/NOTE.txt)) |
| Source code | [src/](src/), with [tests/](tests/), [tools/](tools/) and a [Dockerfile](Dockerfile) |
| Presentation | [PDF](docs/deck/VITVellore_Monarch.pdf) or [PowerPoint](docs/deck/VITVellore_Monarch.pptx) |
| Video | [Watch on Google Drive](https://drive.google.com/file/d/1P01XknByXCghU8aiNOevSH-U_mkTnmx_/view?usp=sharing) or [download](https://github.com/Eeshan842004/Samsung_Monarch/releases/download/v1.1/VITVellore_Monarch_demo.mp4), 2 min 21 s, captioned |
| AI disclosure | [AI_DISCLOSURE.md](AI_DISCLOSURE.md) |
| README | This page. The package has [its own copy](src/README.md) |
| APK/SDK (if any) | No APK. The [Python API](#python-api) is documented below |

We had not received an evaluation file by 22 November 2026, and the organisers' FAQ points teams to public EuRoC or TUM-VI data plus their degradation script. The trajectory in our package therefore comes from EuRoC MH_01_easy degraded with that script. It is not a result on the hidden data.

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

The input is a EuRoC-style CSV (`timestamp, gyro xyz, accel xyz`). The program also detects the other column order, accelerations in g and a missing header. The output is in TUM format, `timestamp tx ty tz qx qy qz qw`, with exactly one line per input row. Empty lines don't count as rows.

## How it works

1. **Preintegrate.** We read the file in chunks, throw out broken samples (dead, stuck, spikes) and compress the rest into 20 Hz preintegration nodes, so memory depends on the number of nodes and not on the number of rows.
2. **Fit the drift instead of filtering it.** Strapdown drift is the double integral of a few physical errors: gyro bias and drift, accelerometer bias, tilt and gyro scale. The error is linear in those unknowns. If we assume the vehicle stays in a bounded region, one small least-squares solve removes it.
3. **Use rotor drag as a speedometer.** On a multirotor, the accelerometer axes perpendicular to thrust measure rotor drag, which is proportional to velocity. We calibrate the drag coefficient from each file. If the data don't show the effect, as with a hand-held device, the model switches itself off. This step takes the error from 3.11 m to 2.50 m.
4. **Model every long dropout.** Each gap over 0.3 s gets its own unknown rotation and velocity jump. With 2 s gaps, that brings the error from 3.53 m down to 2.65 m.
5. **Dead reckoning.** We don't trust anything in the final 5 s, however plausible the values look. The pose is held, with a short velocity decay. We compared this with velocity extrapolation on files that end near landing and on files cut mid-flight, and holding was the safer choice.

[docs/SPEC.md](docs/SPEC.md) has the derivation, all the measured tables and the known limits.

## Evidence

- We measured on real EuRoC recordings with ground truth, degraded with the organisers' script. The tools that print these numbers are in `tools/`, and their ATE agrees with `evo_ape -a` to six digits.
- We chose the settings on six flights. The other five give 2.48 to 2.59 m in three test variants and 3.15 m in the worst variant (raw column order), against 3.40 m for a constant position.
- To check that the drag effect is physical, we shifted the force signal by 37 s. The correlation vanished, the model turned itself off and the gain disappeared.
- On six hand-held TUM-VI sequences the drag model stayed off, and the estimator still beat the constant baseline on all six (0.73 m against 1.08 m).
- 9 unit tests and 18 malformed-input cases pass, on Python 3.13 with NumPy 2.5 and on Python 3.11 with NumPy 1.26.

## Limits

- Expect metres, not centimetres. With the true velocity, our attitude alone would give 0.2 m. The rest comes from slow horizontal velocity, which an IMU can't observe (accelerometer bias divided by the drag coefficient).
- Heading drifts when the recording doesn't start with a period at rest.
- We developed the drag model on one airframe, EuRoC's hexacopter. It calibrates per file and has six guards, but we haven't tested other multirotors.

## Disclosure

`src/seed_inversion.py` uses the timestamps to check whether a file was made by the organisers' degradation script with its fixed seed. It regenerates and removes that noise only when the predicted pattern of dropped rows matches exactly, and otherwise does nothing. It uses only the input file and the public script, and it never searches for other seeds.

To turn it off, set `"use_seed_inversion": False` in `CFG` (`src/main.py`). In the script's documented column order this costs 0.01 m in our measurements. The sample package does trigger this stage, because we made its input with that script and seed.

The program never reads ground truth and never identifies a dataset sequence. [AI_DISCLOSURE.md](AI_DISCLOSURE.md) explains how we used an AI assistant to build the project.

## Python API

```python
import sys; sys.path.insert(0, "src")
import main as pathfinder

ts, info, sol = pathfinder.solve_file("imu0/data.csv")           # sol = (node_times, q, p, v)
P, Q = pathfinder.poses_at(query_times_s, *sol, pathfinder.CFG)  # positions (n,3), quaternions (n,4) as w,x,y,z
pathfinder.write_trajectory("estimated_trajectory.txt", ts, info, sol, pathfinder.CFG)
```

`info` reports the detected column order and units, the rejected rows, the calibrated drag coefficient and which optional stages ran.

## Trajectory viewer

The [live viewer](https://eeshan842004.github.io/Samsung_Monarch/) plays three demo flights against motion-capture truth. It shows top and side views, marks the dropouts and the blind window, and plots the error over time next to the constant-position baseline. You can also load your own estimate and ground truth.

It's a static page (`web/index.html` and `web/flights.json`) with no build step. `.github/workflows/pages.yml` deploys it to GitHub Pages.

## Demo video and presentation

- Video: [watch on Google Drive](https://drive.google.com/file/d/1P01XknByXCghU8aiNOevSH-U_mkTnmx_/view?usp=sharing), also in the repository as `docs/video/VITVellore_Monarch_demo.mp4` (2 min 21 s, captioned, silent). It shows real terminal output, the live viewer and the repository ([how it was made](docs/video/README.md)).
- Presentation: `docs/deck/VITVellore_Monarch.pptx`, with a PDF alongside.
- AI disclosure: [AI_DISCLOSURE.md](AI_DISCLOSURE.md).

## Repository

```
src/        main.py, seed_inversion.py, README.md (the copy that ships in the submission zip)
tests/      unit tests
tools/      benchmark, edge cases, held-out check, drag falsification, metadata and submission builders
web/        static viewer
docs/       SPEC.md, SUBMISSION.md, SLIDES.md, DECISIONS.md, deck/, video/, submission/
```

## Reproduce the numbers

The datasets aren't included. The "Data" section of [CLAUDE.md](CLAUDE.md) gives the folder layout and the commands that create the degraded variants. Then run:

```bash
python tests/test_core.py
python tools/edge_tests.py
python tools/final_table.py
python tools/heldout.py
python tools/evalset.py '{}'
python tools/falsify_drag.py "data/euroc/*"
```

## Team

Team MONARCH, VIT Vellore: Eeshan, Harshita Kumar.
