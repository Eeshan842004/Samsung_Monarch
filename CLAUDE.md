# CLAUDE.md: instructions for Claude Code in this repository

## What this repository is

The submission for Samsung XR Hackathon 2026, Track 03 "Path Finder": estimate a 6-DoF trajectory from a degraded IMU CSV, including 5 s of dead reckoning after the sensor fails. Deadline: **22 Nov 2026, 11:59 PM IST**.

**The estimator is already implemented, tested and measured.** Do not rewrite it. Your job is to keep it correct, finish the packaging, and help produce the submission.

Read in this order: `docs/SPEC.md` (authoritative: maths, functions, measured results), `docs/SUBMISSION.md` (what must be handed in), `docs/DECISIONS.md` (why things are the way they are).

## Layout

```
src/main.py              the estimator (NumPy only, ~915 lines). Entry point for the evaluator.
src/seed_inversion.py    optional stage; main.py runs without it
src/README.md            the README that goes inside the submission zip
tests/test_core.py       9 unit tests for the maths
tools/                   benchmark, edge cases, metadata, submission zip, organiser's degrade script
web/index.html           static trajectory viewer (no build step)
docs/                    SPEC, SUBMISSION, SLIDES, DECISIONS, deck/ (presentation), video/ (demo video), archive/
AI_DISCLOSURE.md         what the AI assistant was used for
Dockerfile, requirements.txt
```

## Commands

```bash
python src/main.py <imu0/data.csv> [estimated_trajectory.txt]      # run the estimator
TRACK3_VERBOSE=1 python src/main.py <csv> out.txt                  # print diagnostics to stderr
python tests/test_core.py                                          # must print "9 tests passed"
python tools/edge_tests.py                                         # must end with "ALL PASS", 18 cases (needs data/euroc/V1_02_medium/imu.csv)
python tools/final_table.py                                        # full benchmark (about 2 minutes)
python tools/perf.py <csv>                                         # time and peak heap
python tools/make_submission.py <CollegeName_TeamName> <organiser csv>
docker build -t pathfinder . && docker run --rm -v "$PWD/data:/data" pathfinder /data/imu0/data.csv /data/estimated_trajectory.txt
```

## Hard rules (breaking any of these can disqualify the submission)

1. **One pose per input row, in input order.** Never drop, merge, sort or append rows in the output. Duplicated timestamps get identical poses.
2. **`src/main.py` stays standalone**: Python standard library plus NumPy only. No pandas, SciPy, PyTorch, numba, multiprocessing or threads.
3. **Budgets**: peak traced heap under 8 MB and under 20 ms per second of IMU. Current values are 4.1 MB and under 3 ms; any change that raises heap above 5 MB or time above 5 ms on `MH_01_easy` needs a reason written in the commit message.
4. **Only the input file is used.** Never read ground truth in `src/`, never identify a dataset sequence from its timestamps, never embed dataset-specific constants (the drag coefficient is calibrated per file at run time and must stay that way).
5. **Output format**: `timestamp tx ty tz qx qy qz qw`, space separated, timestamps in seconds with nine decimals produced by integer arithmetic, unit quaternions, body-to-world.
6. **Never emit an exactly constant trajectory** (evo's alignment fails on it); `fallback_solution` exists for this.
7. **The run must not crash.** Everything after `scan_timestamps` is wrapped by the fallback in `solve_file`; keep it that way.

## Rules for changing the estimator

- Do not change maths or defaults in `CFG` without running `tools/final_table.py`, `tools/heldout.py`, `tools/edge_tests.py` and `tests/test_core.py` before and after, and pasting the before/after table in the commit message.
- Select settings with `tools/tune.py` (train flights only). Accept a change only if the TEST mean in `tools/heldout.py` does not get worse and no scenario row in `final_table.py` gets worse by more than 0.05 m. One change has already been rejected this way (tighter drag weight: train better, test worse).
- Report measured numbers only. If you did not run it, say so. Never write an accuracy figure into a README, slide or comment that a tool in this repository did not print.
- Reference numbers to reproduce (11 EuRoC sequences, mean ATE): clean 2.49 m, degraded seed 42 with inversion 2.49 m, constant baseline 3.45 m. A fresh checkout that does not reproduce these within 0.05 m has a data or environment problem; stop and report it.

## Data (not in the repository)

Download EuRoC MAV from the official source (DOI 10.3929/ethz-b-000690084) and, optionally, TUM-VI room1 to room6. Arrange as:

```
data/euroc/<sequence>/imu.csv    <- mav0/imu0/data.csv
data/euroc/<sequence>/gt.csv     <- mav0/state_groundtruth_estimate0/data.csv
```

Then create the degraded variants for every sequence:

```bash
python tools/reorder.py data/euroc/$S/imu.csv data/euroc/$S/imu_af.csv           # accel-first, as the script documents
python tools/degrade_imu.py data/euroc/$S/imu_af.csv data/euroc/$S/deg_af.csv
python tools/degrade_imu.py data/euroc/$S/imu.csv    data/euroc/$S/deg_raw.csv   # raw column order
# other seeds: copy degrade_imu.py, change SEED, write deg_seed1.csv, deg_seed2.csv, deg_seed3.csv
# long gaps: SEED = 7, "burst_len": (100, 400), "burst_prob_max": 0.0006 -> deg_s7.csv
# mid-flight blind window: keep the first 45, 60, 75 % of the rows of imu.csv, then reorder + degrade
#   -> data/mid/<sequence>_<pct>/{imu.csv,deg_af.csv,gt.csv}   (used by tools/evalset.py)
```

`data/` is git-ignored. Do not commit dataset files.

## Open tasks, in priority order

| # | Task | Done when |
|---|---|---|
| 1 | Reproduce the reference numbers on the official dataset downloads | `tools/final_table.py` matches `docs/SPEC.md` section 2 within 0.05 m |
| 2 | Build and run the Docker image once | the `docker run` line above writes a trajectory with the right row count |
| 3 | Re-run the NumPy 1.26 check on your machine (already passed on Python 3.11 + NumPy 1.26.4 during authoring) | unit and edge tests pass |
| 4 | Team details are filled in (Team MONARCH, VIT Vellore, Eshan, Harshita Kumar). Add the repository and viewer URLs where `TODO(team)` remains, including slide 7 of the deck | no `TODO(team)` left (`grep -rn "TODO(team)"`) |
| 5 | Deploy `web/` as a static site (Vercel or GitHub Pages; no build command, output directory `web`). Three demo flights are bundled in `web/flights.json` (regenerate with `python tools/export_web.py`) | the URL loads and shows the sample |
| 6 | Run `tools/make_submission.py` on the organiser's evaluation file | zip has `estimated_trajectory.txt`, `metadata.json`, `src/main.py`, `src/seed_inversion.py`, `src/README.md`; row counts match |
| 7 | Apply the organisers' answers (see `docs/SUBMISSION.md`, "Questions sent") | e.g. set `"use_seed_inversion": False` in `CFG` if they object |
| 8 | Confirm the GitHub Actions workflow (`.github/workflows/tests.yml`) passes after the first push | green check on the repository |

Optional experiments, each behind its acceptance rule above: heading drift without a rest start; heading inside long gaps. The estimator is otherwise frozen: three council seats and the error budget in `docs/SPEC.md` section 9 agree that the remaining error is not reachable by tuning.

## Things that were tried and rejected (do not redo)

- Per-sample Kalman or error-state filters in Python: slower, no accuracy gain over the batch fit.
- Constant-velocity or constant-rate extrapolation in the blind window: worse than holding when the file ends near landing (0.94 vs 0.67 m), slightly better mid-flight (1.65 vs 1.79 m). Hold is the minimax choice; do not change it without the organisers saying files are cut mid-flight.
- Trusting sensor values in the final 5 s: a noise-filled tail at vibration level is undetectable and costs 1.8 -> 7.5 m. `assume_blind_tail` stays on.
- Searching for other seeds in the seed check: three council seats rejected it (no gain unless two unlikely things coincide, and it reads as gaming).
- Drag refinements (lever arm, anisotropic, thrust-scaled, ground-truth offset): no gain. Tighter drag weight: fails the held-out check.
- A learned velocity model: published results on this dataset are worse than the physics fit, and training on the public test sequences is a leakage risk.
- Larger gyro-calibration prior: lowers ATE slightly, raises rotation drift.
- pandas or `np.loadtxt` on the whole file: tens of MB of heap.
- An Android APK or in-browser (Pyodide) estimator: no scoring value, real risk.

## Style

- Keep `src/main.py` readable by an evaluator: docstrings state the maths, comments state why.
- Tools may import `bench.py`; `src/` may not import anything from `tools/`.
- Plain ASCII in source files.
