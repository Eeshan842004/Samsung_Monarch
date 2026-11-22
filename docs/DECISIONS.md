# DECISIONS.md: brainstorm log, council verdicts and what was tested

Each round asks a question, proposes answers, and settles it with a measurement where one is possible. "Kept" means it is in the code.

## Round 1: where is the solution weak?

| Weakness found in v1 | How we checked | Outcome |
|---|---|---|
| Only 10% better than a constant position | Ceiling test with ground-truth attitude: 2.92 m | Attitude is not the bottleneck; new information is needed (round 3) |
| Parameters tuned on the sequences they are reported on | Train/test split, grid of 27 settings chosen on train only | Default and train-selected settings score the same on test (within 0.01 m in v1). Not overfitted |
| One seed only | Seeds 1, 2, 3 | 3.20 to 3.30 m in v1; 2.66 to 2.77 m now |
| Blind window uses a poor velocity | Oracle with true velocity | Even perfect velocity gains only 20% over holding. Kept: hold |
| Seed inversion fails if the organisers used `--max-level` or `--gamma` | Files made with (0.6, 1.0) and (0.8, 2.5) | Added a ramp search; both recovered exactly. Kept |
| Tail might hold garbage instead of zeros | Edge case with values of 1e6 | Added physical-range limits. Kept. Plausible-looking noise is still undetected |
| Crash on unseen data | First TUM-VI run crashed | Fixed; 17 edge cases |
| Deliverables missing from the brief | Re-read slide 24 | README must include Docker files; added a Dockerfile |

## Round 2: what information have we not used?

Ideas listed without judging:

1. Rotor vibration frequency as a thrust proxy
2. The accelerometer's in-plane components as a drag sensor
3. Rest detection anywhere in the file
4. Earth rotation in the gyro (far below this sensor's noise)
5. A learned motion prior
6. The fixed seed (already used)
7. Timestamps of dropped rows as a severity clock

Idea 2 is known physics for multirotors, costs almost nothing, and can be tested in an hour. Tested first.

## Round 3: is rotor drag real in this data?

| Question | Test | Result |
|---|---|---|
| Does in-plane specific force follow velocity? | Regress on ground-truth body velocity | Correlation -0.5 to -0.8; coefficient 0.15 to 0.21 1/s on every sequence |
| Is drag alone enough for dead reckoning? | Integrate drag velocity only | No: 20 m mean. Ground handling and noise ruin it |
| Does it help as extra rows in the fit, with a fixed coefficient? | `drag_mu = 0.19` | 3.09 to 2.55 m |
| Can the coefficient come from the IMU alone? | 2 s differences of fitted velocity against in-plane force | 0.137 to 0.226 1/s; 2.58 m |
| Does it stay off on hand-held data? | TUM-VI rooms | Correlation magnitude at most 0.20; off on 6 of 6 |

Kept, on by default.

## Round 4: how could the drag model fool us? (council round, then tests)

A three-seat quick council (first-principles physics, incentives and judges, user-centred reduction) reviewed the measured facts. All three said: ship the drag model on, but add guards. The physics seat asked for specific falsification tests. All were run:

| Requested test | Result |
|---|---|
| Break the physics, keep the statistics (shift the force by 37 s) | Correlation within 0.11 of zero; model off on 11 of 11; ATE returns to the no-drag value |
| Coefficient stable across halves of a file | Yes on all 11 (0.13 to 0.24) |
| Leave-one-out coefficient | 2.55 m against 2.58 m self-calibrated |
| Plausibility bounds, excitation threshold, half-split agreement | Implemented as guards |
| Fall back if the solution blows up | Implemented: re-solve without drag if the spread exceeds 4 times the plain fit |

## Round 5: which extra deliverable?

| Option | Council | Decision |
|---|---|---|
| Nothing beyond repository, README, Docker, video, deck | Required base | Done |
| Python API as documentation | 3 of 3: yes, as a README section, not a product | Done |
| Static web viewer | 3 of 3: yes; it is the only thing that lets a juror see the dropout and blind-window behaviour | Built: `web/index.html`, alignment checked against the Python harness |
| Android APK | 3 of 3: no. No hardware, no scoring value, and the drag model does not apply to a phone | Rejected |
| In-browser estimator (Pyodide) | 3 of 3: no. Fragile, no scoring value | Rejected |

## Round 6: what should the story lead with?

All three seats, in different words: **physics, not learning; rotor drag as a speedometer; honest limits.** The seed inversion is a robustness footnote, never the headline, and always disclosed.

## Round 7: what would make us lose anyway?

| Risk | Likelihood | What we did |
|---|---|---|
| Hidden data unlike EuRoC | Low to medium | TUM-VI tested; guards; fallback |
| Evaluator environment differs | Medium | Dockerfile; NumPy-only; test on NumPy 1.26 (open task) |
| Organisers dislike the seed inversion | Low if disclosed | Disclosed in both READMEs; one flag; question drafted, not sent |
| Scoring is relative and everyone clusters near the constant baseline | Medium | The drag gain and the 40% efficiency score are the separation |
| Another team uses public ground truth | Unknown | Outside our control |

## Earlier council (16 Nov), for the record

Three seats (first-principles, tail risk, shipping) chose the physics batch estimator over a learned or hybrid model and asked for adversarial tests. The first adversarial test, TUM-VI, found a crash and a bad prior within the hour.

## Process notes

- Both councils ran in quick mode with three seats and one round, plus one counterfactual challenge in the first. The coordinator wrote the syntheses; there was no separate chairman.
- A web search found no public solution to this hackathon track.
- Nothing in this log is a measurement unless a tool in `tools/` printed it.

---

# Final round (17 Nov, afternoon)

The same loop again: measure where the error is, brainstorm against that, test, and send what measurement cannot settle to the council.

## Round 8: where exactly is the remaining error?

| Question | Test | Result |
|---|---|---|
| Is it attitude or velocity? | Dead-reckon with our attitude and the true body velocity, then the reverse | 0.21 m against 2.57 m on the morning build (0.15 m against 2.49 m on the final build). Attitude is solved; velocity is everything |
| Horizontal or vertical? | Split the aligned error | 2.45 m horizontal, 0.42 m vertical (final build) |
| Can a better drag law fix the velocity? | Regress in-plane force on true velocity with five model variants | Isotropic drag leaves 0.22 m/s at 1 s and 0.12 m/s at 10 s. Anisotropic, thrust-scaled and vertical-coupled variants: no better. Lever arm: 0.22 to 0.18 m/s in regression, but 2.577 to 2.570 m in the estimator. Rejected |
| Would knowing the drag offset help? | Fix it to its ground-truth value | Worse (3.35 m). The offset is confounded with body-frame velocity; only the position prior resolves it |

Conclusion: the remaining error is accelerometer in-plane bias divided by the drag coefficient (0.05 / 0.19 = 0.26 m/s). No IMU-only change reaches it. Stop chasing ATE.

## Round 9: what if the blind window is not at a landing?

All earlier blind-window tuning used full EuRoC flights, which end near a landing. Built 33 files cut at 45, 60 and 75% and then degraded, so the window falls mid-flight (2.9 m of true travel).

| Finding | Evidence | Action |
|---|---|---|
| Hand-over velocity was worse than guessing zero | Velocity error rises from 0.4 m/s in the interior to 0.99 m/s in the last second | Extra velocity-only rows in the last 10 s: 0.99 to about 0.6 m/s. Kept |
| A held point breaks per-segment alignment | Rank check failed on 33 of 33 files; evo raises "Degenerate covariance rank" on such input | 1 mm three-dimensional ripple in the blind path. Kept |
| Hold or decay? | Near landing: 0.67 m (hold) against 0.94 m (1 s decay). Mid-flight: 1.79 m against 1.65 m | Hold: worst-case regret 8% against 40% |

## Round 10: what if the tail is not zeros?

| Tail content | Result before | Action |
|---|---|---|
| Out-of-range garbage | Caught by range limits | none |
| Strong or moderate noise | A roughness-jump detector catches it; 0 false positives on 151 real files | Kept as the fallback path |
| Noise at vibration level | Undetectable; blind-window error 1.8 to 7.5 m | **Never trust the final 5 s.** Cost when the data were actually valid: 0.02 m. Kept as the default |

## Round 11: gyro model and held-out discipline

- Settings are now selected on six flights only (`tools/tune.py`) and reported on the other five.
- Looser gyro-bias knots (prior 3e-4 to 3e-3 rad/s): held-out mean 2.90 to 2.68 m, and the worst case (raw column order, unverifiable seed) 3.58 to 3.25 m. Kept.
- Tighter drag weight: train 2.69 to 2.55 m, held-out 2.68 to 2.72 m. Rejected as overfitting.
- Verified on Python 3.11 with NumPy 1.26.4: same trajectory within 0.2 mm, seed check matches.
- Heap trimmed back to 4.1 MB after the additions.

## Round 12: council on what measurement cannot settle

Seats: bias audit and premortem; terrain and opponents; inversion and opportunity cost. Quick mode, one round, coordinator synthesis. All three agreed on every question.

| Question | Verdict (3 of 3) | Reason given |
|---|---|---|
| Try a list of common seeds when the default seed does not match? | **No** | Pays only if the organisers changed the seed to one on the list and the column-order accident also happened; otherwise 0.01 m. Reads as gaming and must be disclosed |
| Blind window: hold or decay? | **Hold** | Minimax under an unknown cut point |
| Where should the remaining days go? | Email the organisers today; reproduce on official data, Docker and a clean machine; then deck and video. **Stop estimator work** | The estimator is at its floor and further tuning has already shown overfitting |
| Most likely reason not to win? | An assumption about the hidden file (column order, seed, tail format, how memory is measured), or a rushed deck | Not accuracy |

Actions taken from this round: the seed search was not built; the estimator is frozen; the email text is in `docs/SUBMISSION.md`; the deck was built from the organisers' template with measured figures (`docs/deck/`).

## What changed in the numbers today

| Mean over 11 EuRoC flights | Morning | Now |
|---|---|---|
| Degraded, seed 42 | 2.62 m | 2.49 m |
| Three other seeds | 2.66 to 2.77 m | 2.53 to 2.60 m |
| 2 s dropouts | 2.72 m | 2.65 m |
| Raw column order, unverifiable seed | 3.58 m | 3.25 m |
| TUM-VI hand-held | 0.75 m, better on 5 of 6 | 0.73 m, better on 6 of 6 |
| Blind-window ATE, degraded | 1.59 m | 1.74 m |

The blind-window figure moved the wrong way by 0.15 m while every other row improved. It is the least stable metric here (it changes by 0.2 m between otherwise equivalent settings), and the dead-reckoning drift inside the window improved from 0.61 to 0.57 m.
