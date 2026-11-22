# AI disclosure

Team MONARCH, VIT Vellore (Eeshan, Harshita Kumar). Samsung XR Hackathon 2026, Track 03 "Path Finder".

## Summary

We used Anthropic's AI assistant, Claude (Claude Code), extensively throughout this project. The team directed the work, set the requirements from the organisers' slides and FAQ and reviewed the results. We are responsible for every file we submit. The submitted program has no AI or machine-learning model in it and is a deterministic NumPy program at run time.

## What the AI was used for

| Area | How the AI was used | How we checked it |
|---|---|---|
| Understanding the task | Reading the slides, FAQ and `degrade_imu.py`; listing requirements and conflicts (column order, dropout length, video length) | Cross-checked against the official files and FAQ; open questions documented in `docs/SUBMISSION.md` (they were not sent to the organisers) |
| Research | Literature search on inertial navigation, preintegration, learned inertial odometry and quadrotor rotor drag; summaries with citations | Citations marked by verification status in `docs/archive/TRACK3_MASTER_PLAN_v1.md` |
| Algorithm and code | Writing `src/main.py`, `src/seed_inversion.py`, the tests and the benchmark tools; finding and fixing bugs | 9 unit tests, 18 malformed-input tests, results reproduced from a fresh copy, metrics cross-checked against the evo tool |
| Experiments | Running every benchmark on EuRoC and TUM-VI with the organisers' degradation script; held-out checks; falsification tests | All reported numbers are printed by tools in this repository and can be re-run (`tools/final_table.py`, `tools/heldout.py`, `tools/falsify_drag.py`) |
| Design decisions | Structured brainstorming and multi-perspective review ("council") of options, with the AI playing the council seats | Recorded with the evidence for each decision in `docs/DECISIONS.md` |
| Documentation | Writing the README, `docs/SPEC.md`, `docs/SUBMISSION.md` and this file, and editing their wording for readability | Reviewed by the team |
| Presentation and demo | Building the slide deck on the organisers' template, figures, the web viewer and the demo video | Figures are generated from measured data by scripts in `docs/deck/`; the video uses captured program output and screenshots (`docs/video/`) |
| Packaging and publishing | Building the sample submission package, setting up GitHub Pages, the CI workflows and the releases | Automated tests, a Docker run in CI and checks of the published files |

## What the AI was not used for

- No AI model runs inside the submitted estimator, and no model was trained.
- The estimator doesn't read ground-truth data and doesn't identify dataset sequences.
- The optional `seed_inversion.py` stage uses only the input file and the organisers' public script. Both READMEs disclose it, and one setting turns it off.

## Data and third-party material

- EuRoC MAV (Burri et al., IJRR 2016) and TUM-VI (Schubert et al., IROS 2018) for development and evaluation, as allowed by the FAQ.
- The sample package uses the copy of the EuRoC MH_01_easy IMU file published in the ORB-SLAM3 repository.
- evo (M. Grupp) for checking metrics. NumPy at run time.
