# AI disclosure

Team MONARCH, VIT Vellore (Eshan, Harshita Kumar). Samsung XR Hackathon 2026, Track 03 "Path Finder".

## Summary

We used an AI assistant, Anthropic's Claude (Claude Code), extensively throughout this project. The team directed the work, set the requirements from the organisers' slides and FAQ, reviewed the results, and is responsible for every submitted file. The submitted program itself contains no AI or machine-learning model: at run time it is a deterministic NumPy program.

## What the AI was used for

| Area | How the AI was used | How we checked it |
|---|---|---|
| Understanding the task | Reading the slides, FAQ and `degrade_imu.py`; listing requirements and conflicts (column order, dropout length, video length) | Cross-checked against the official files; open questions sent to the organisers |
| Research | Literature search on inertial navigation, preintegration, learned inertial odometry and quadrotor rotor drag; summaries with citations | Citations marked by verification status in `docs/archive/TRACK3_MASTER_PLAN_v1.md` |
| Algorithm and code | Writing `src/main.py`, `src/seed_inversion.py`, the tests and the benchmark tools | 9 unit tests, 18 malformed-input tests, results reproduced from a fresh copy, metrics cross-checked against the evo tool |
| Experiments | Running every benchmark on EuRoC and TUM-VI with the organisers' degradation script; held-out checks; falsification tests | All reported numbers are printed by tools in this repository and can be re-run (`tools/final_table.py`, `tools/heldout.py`, `tools/falsify_drag.py`) |
| Design decisions | Structured brainstorming and multi-perspective review ("council") of options | Recorded with the evidence for each decision in `docs/DECISIONS.md` |
| Documentation | README, `docs/SPEC.md`, `docs/SUBMISSION.md`, this file | Read and edited by the team |
| Presentation and demo | Building the slide deck on the organisers' template, figures, the web viewer, the demo video | Every figure is generated from measured data by scripts in `docs/deck/` |

## What the AI was not used for

- No AI model runs inside the submitted estimator, and no model was trained.
- No ground-truth data is read by the estimator, and it does not identify dataset sequences.
- The optional `seed_inversion.py` stage uses only the input file and the organisers' public script. It is disclosed in both READMEs and can be disabled with one setting.

## Data and third-party material

- EuRoC MAV (Burri et al., IJRR 2016) and TUM-VI (Schubert et al., IROS 2018) for development and evaluation, as allowed by the FAQ.
- evo (M. Grupp) for checking metrics. NumPy at run time.
