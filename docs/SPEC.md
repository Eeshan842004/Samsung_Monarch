# SPEC.md: Path Finder (Samsung XR Hackathon 2026, Track 03)

This is the authoritative specification of what the code does and why. Where it disagrees with `docs/archive/TRACK3_MASTER_PLAN_v1.md`, this file wins. Every number marked **[measured]** was printed by a tool in this repository on real recordings with ground truth.

---

## 1. The task, exactly

| Item | Requirement (source: organiser slides 13 to 17 and 24, FAQ) |
|---|---|
| Input | One degraded IMU CSV, EuRoC layout: `timestamp[ns], gyro xyz [rad/s], accel xyz [m/s^2]`, 200 Hz |
| Output | `estimated_trajectory.txt`, TUM format `timestamp tx ty tz qx qy qz qw`, timestamps in seconds |
| Row contract | Exactly one pose per input row. Never append or drop rows |
| Degradation | Escalating noise, bias drift, spikes, stuck samples, missing rows, duplicated rows |
| Blind window | Final 5 s: timestamps present, sensor values unusable (zeros in the organiser script) |
| Language | Python only, standalone `main.py` |
| Budgets | 8 MB peak algorithm heap, 20 ms compute per 1 s of IMU, one CPU thread |
| Scoring | Memory 20, runtime 20, waypoint accuracy 30, blind 5 s 20, dropout resilience 10 |
| Metric | evo ATE RMSE and RPE after SE(3) Umeyama alignment (no scale), on the submitted trajectory |
| Data | EuRoC MAV and TUM-VI passed through the organiser's `degrade_imu.py` |
| Also required | Public GitHub repository, README with reproducible setup and Docker files, video of 3 minutes or less, presentation in the organisers' template |

## 2. Results at a glance [measured]

Mean ATE RMSE over all 11 EuRoC flights. "Constant" is the best possible constant position: what a team scores by not moving.

| Scenario | ATE | Blind-window ATE | Beats constant on |
|---|---|---|---|
| Constant baseline | 3.45 m | | |
| Clean IMU | **2.49 m** | | 11 of 11 |
| Degraded (organiser script, seed 42) | **2.49 m** | 1.74 m | 11 of 11 |
| Degraded, three other seeds | 2.53 to 2.60 m | 1.79 to 2.40 m | 11 of 11 |
| Degraded, raw EuRoC column order fed to the script, seed verified | 2.50 m | 1.74 m | 11 of 11 |
| Same, seed not verifiable (worst case) | 3.25 m | 2.73 m | 8 of 11 |
| Dropouts stretched to 2 s, another seed | 2.65 m | 2.19 m | 10 of 11 |
| Blind window placed mid-flight (33 cut files) | 2.85 m | 3.48 m | |
| Five held-out flights, mean of four variants | 2.68 m vs constant 3.40 m | | |
| TUM-VI hand-held rooms (6 recordings), clean | 0.73 m vs constant 1.08 m | | 6 of 6 |

Efficiency: 1 to 3 ms per second of IMU (budget 20). Peak traced heap 4.1 MB on the longest EuRoC file, 7.1 MB on a 13-minute file (budget 8). NumPy only. Verified on Python 3.13 with NumPy 2.5 and on Python 3.11 with NumPy 1.26 (outputs agree within 0.2 mm).

Best published learned IMU-only results on held-out EuRoC are 3.2 to 5.0 m (AirIO 2025; Silva do Monte Lima 2019).

**No IMU-only method reaches centimetres.** Section 9 shows where the remaining error comes from and why it cannot be removed without another sensor. The claim this project makes is narrower: it is consistently better than standing still, it cannot diverge, and it uses a small fraction of both budgets.

## 3. Three ideas that make it work

### 3.1 Drift is a curve to fit, not a state to filter

Strapdown integration of a biased IMU drifts by kilometres in minutes. The drift is not random: it is the double integral of a handful of physical errors (gyro bias, accelerometer bias, initial tilt, gyro scale). The nominal trajectory error is **linear** in those unknowns. So we integrate once, solve one small least-squares problem for the unknowns under the prior that the vehicle stays in a bounded region, and subtract the fitted drift. No per-sample filter, no covariance propagation.

### 3.2 Rotor drag makes velocity observable

On a multirotor the rotors push only along the thrust axis. The accelerometer components perpendicular to that axis therefore measure the only other force acting, rotor drag, which is proportional to velocity:

`f_perp = -mu * v_perp + c`

`f_perp` and `v_perp` are the specific force and velocity in the plane normal to the thrust axis (body frame), `mu` is a drag coefficient in 1/s, `c` an offset. This is established in the multirotor literature [R1][R2][R3][R4]. What is new here is using it inside an IMU-only batch estimator with a coefficient calibrated from the file itself and an automatic off-switch.

- `mu` from the IMU file alone: 0.14 to 0.22 1/s across EuRoC. A regression against ground-truth velocity gives 0.17 to 0.21.
- Effect on EuRoC: 3.09 to 2.49 m clean, 3.11 to 2.50 m degraded, blind-window ATE 2.91 to 1.86 m.
- It turns itself off when the physics is absent: on hand-held TUM-VI the correlation magnitude is at most 0.23 against 0.54 to 0.87 on EuRoC.

### 3.3 The organiser's degradation is reproducible, so it can be removed

`degrade_imu.py` draws all randomness from a fixed seed. From the timestamps alone we predict which rows it dropped and duplicated. If the prediction matches the file exactly, the hypothesis is proven and we regenerate and subtract the noise, bias walk, scale walk and spikes (recovered samples match the clean file to 1e-6). If not, nothing is touched. The check also covers the script's two command-line options (`--max-level`, `--gamma`). The random stream is identical on NumPy 1.26 and 2.5.

This is insurance against the column-order conflict in section 10. In the script's documented column order it changes the result by 0.01 m. It is disclosed in both READMEs and disabled with one flag. It never searches for other seeds.

## 4. Architecture

```
imu0/data.csv
  | pass 0  scan_timestamps      first column only: row count, time unit, column order, units
  |         SeedInversion        optional; verified from the drop pattern or skipped
  |         blind boundary       the final 5 s are never trusted
  | pass 1  preintegrate_file    2048-row chunks -> reject dead/stuck/spike rows -> 20 Hz nodes
  |         solve_nodes          3 x { nominal integration -> build linear system -> solve -> feed back }
  |                              (drag coefficient calibrated after the first solve)
  | pass 2  write_trajectory     pose for every input row from its timestamp
  v
estimated_trajectory.txt
```

Heap is proportional to the number of nodes (rows / 10), not rows. Above 40,000 rows the node length grows so the node count stays near 4,000.

## 5. Conventions

| Item | Choice |
|---|---|
| Quaternion algebra | Hamilton, `i j = k` |
| Internal storage | (w, x, y, z) |
| Output order | `qx qy qz qw` |
| Meaning | body to world: `v_world = R(q) v_body` |
| Composition | `q_{k+1} = q_k (x) dq_k` (body-frame increments multiply on the right) |
| World frame | z up, gravity `(0, 0, -G)`, `G = 9.80665`; origin and heading arbitrary (removed by SE(3) alignment) |
| Units | rad/s, m/s^2, s, m |

## 6. Mathematics

### 6.1 Sensor model

`w_m = (I + D) w + b_g + n_g`, `f_m = R^T (a - g_w) + b_a + n_a`.
`w` body rate, `a` world acceleration, `b` biases, `D` gyro scale and misalignment, `n` white noise. At rest the accelerometer reads `+G` along world up.

### 6.2 Preintegration nodes (`preintegrate_group`)

Valid samples are grouped into nodes of 10 intervals (50 ms). In the body frame at the node start, with midpoint rules:

```
dR_{j+1} = dR_j Exp((w_j + w_{j+1}) dt_j / 2)
a_j      = (dR_j f_j + dR_{j+1} f_{j+1}) / 2
dp      += dv dt_j + a_j dt_j^2 / 2
dv      += a_j dt_j
theta   += (w_j + w_{j+1}) dt_j / 2
```

Each node stores start time, duration `Dt`, `dR` (quaternion), `dv` [m/s], `dp` [m], `theta` [rad]. These are independent of global attitude, velocity and gravity. Missing rows simply make `dt_j` larger (trapezoid across the gap).

### 6.3 Nominal solution

```
dq_k'   = dq_k Exp(-b_g(t_k) Dt_k + D theta_k + gap_rotation_k)
q_{k+1} = q_k dq_k'
v_{k+1} = v_k + R_k dv_k - g_est e_z Dt_k
p_{k+1} = p_k + v_k Dt_k + R_k dp_k - g_est e_z Dt_k^2 / 2
```

`p_0 = v_0 = 0`; `q_0` rotates the first specific-force vector onto world +z; `g_est` makes the mean vertical acceleration zero.

### 6.4 The error of the nominal solution is linear

With `R_nom = Exp(psi) R_true` and `psi(t) = psi_0 + integral R (db_g - D w_m) dt`, the acceleration error is

```
e(t) = R(t) b_a + psi(t) x (G e_z) + dg e_z + s(t),     psi x G e_z = G (psi_y, -psi_x, 0)
```

and `p_nom = p_true + p_0 + v_0 t + double integral of e`. Unknown vector:

| Block | Size | Meaning | Prior std |
|---|---|---|---|
| `p_0, v_0` | 6 | initial position and velocity | none |
| `b_a` | 3 | body accelerometer bias | 0.5 m/s^2 |
| `dg` | 1 | gravity magnitude | 0.5 m/s^2 |
| `psi_0` (x, y) | 2 | initial tilt | 0.5 rad |
| `db_g` knots | 3 per knot, knots every 20 s | gyro bias and its drift | 3e-3 rad/s after a rest start, else 2e-3 |
| `s` knots | 3 per knot, every 20 s | slow world-frame residual acceleration | 0.2 m/s^2 |
| `D` | 9 | gyro scale and misalignment | 0.005 |
| gap jumps | 5 per gap over 0.3 s, at most 12 | tilt jump (2) and velocity jump (3) | 0.5 rad/s and 1.5 m/s^2 times gap length |
| `c` | 3 | drag offset (only when the drag model is on) | 0.3 m/s^2 |

About 85 unknowns for a 3-minute file.

### 6.5 The estimation problem (`solve_nodes`)

Minimise over `x`:

```
sum_rows |p_nom - A x|^2 / sig_pos^2          bounded position        sig_pos = 2 m       1 Hz rows
+ sum_rows |v_nom - A' x|^2 / sig_vel^2       bounded velocity        sig_vel = 1 m/s     1 Hz rows + end rows
+ sum_rest |v_nom - A' x|^2 / sig_zupt^2      zero velocity at rest   sig_zupt = 0.2 m/s
+ sum_rows rho( P_w (v_nom - A' x) + R P (fbar - c) / mu ) / sig_drag^2    drag rows, sig_drag = 0.3 m/s
+ sum_i (x_i - mu_i)^2 / sig_i^2              priors
```

- `A` holds, column by column, the position that a unit of each unknown produces (cumulative sums over the nodes, `cumint`); `A'` the velocity.
- Regular rows are taken every 20 nodes (1 Hz) and weighted as one independent observation per second.
- **End rows.** The last 10 s get extra velocity-only rows at 4 Hz, plus the final boundary. The end of the file has no future data to lean on and is where dead reckoning starts; these rows cut the hand-over velocity error from 0.99 to about 0.6 m/s on mid-flight cuts. They carry no position pull. Their effect on the scores is small: ATE on mid-flight cuts 3.00 to 2.85 m, neutral on full flights.
- `P = I - n n^T` projects onto the plane normal to the thrust axis `n` (the mean specific-force direction in the body frame); `P_w = R P R^T`; `fbar` is the 1 s mean body specific force.
- `rho` is Huber's loss (three reweighting passes), because ground handling, contacts and gusts violate the drag law.
- The normal equations are solved directly. The gyro part of the solution (`db_g`, `D`, `psi_0`, gap rotations) is fed back into the increments and the system rebuilt; three passes in total.
- Finally the fitted `e(t)` is double-integrated and subtracted from `p_nom`, `v_nom`, and `Exp(-psi)` is applied to the attitude.

### 6.6 Calibration of the drag coefficient and its guards

After the first solve (no drag rows yet) the fit gives a velocity at each 1 s row. Let `u = P R^T v` (in-plane body velocity) and `fpl = P fbar`. Differences over a 2 s lag remove offsets and slow drift:

```
mu_hat = - sum(du . dfpl) / sum(du . du),     corr = sum(du . dfpl) / sqrt(sum(du.du) sum(dfpl.dfpl))
```

The drag rows are enabled only if **all** of these hold:

| Guard | Threshold |
|---|---|
| Correlation over the whole file | `corr < -0.35` |
| Coefficient physically plausible | `0.05 < mu_hat < 0.6` 1/s |
| Each half of the file agrees | both half-correlations negative, both below -0.175, both `mu` in range, ratio under 2.5 |
| Enough motion to calibrate | rms of `du` above 0.05 m/s |
| At least 120 difference samples | about one minute of usable data |
| After solving: no blow-up | position spread under 4 times the plain fit's spread, else re-solve without drag |

### 6.7 Initial gyro bias

- **Rest start** (`static_start_bias`): 0.5 s window means of gyro and accelerometer stay within 0.01 rad/s and 0.15 m/s^2 of the running reference for at least 1 s. Bias = mean rate over the rest interval.
- **No rest** (`bootstrap_gyro_bias`): in the gyro-integrated frame the gravity vector rotates at `R db`, so consecutive window means satisfy `F_{k+1} - F_k = (sum R Dt db) x F_k`. Solved with 1, 4, 16 s windows, Huber weights, and a prior `N(0, 0.03^2)` on the total bias. The component along gravity is observable only when the body tilts.

### 6.8 Pose for every row (`poses_at`)

A row's pose depends only on its timestamp, so duplicated rows get identical poses and rows in any order are handled.

- Inside the node span: cubic Hermite for position (uses node velocities), normalised linear interpolation for the quaternion.
- After the last usable sample: `p(h) = p_f + v_f tau (1 - exp(-h / tau))` with `tau = 0.15 s`, attitude held. This is hold-position with a smooth hand-over (section 8.4).
- **Full-rank blind path.** A held point or a straight line has a rank-deficient covariance. If the blind window is ever scored on its own, evo's Umeyama alignment raises "Degenerate covariance rank" on such input (this affected 33 of 33 mid-flight test files). A 1 mm three-dimensional ripple is added to the blind-window positions; it changes no error figure.
- Timestamps are formatted with integer arithmetic (`ns // 1e9 . ns % 1e9`), nine decimals.

## 7. Input handling (`scan_timestamps`, `preintegrate_file`)

| Problem | Detection | Treatment |
|---|---|---|
| **Blind window** | By definition: the final 5 s of any file longer than 20 s (`assume_blind_tail`) | Sensor values there are never used. A tail filled with noise at the level of normal vibration cannot be told from real data, and integrating it took blind-window error from 1.8 to 7.5 m. Cost of the rule when the tail was actually valid: 0.02 m |
| Dead rows anywhere | all zero, non-finite, accelerometer norm under 0.05 g or over 30 g, any rate over 70 rad/s | excluded from integration |
| Stuck values | row identical to the previous one on all six channels | excluded |
| Spikes | deviation from the mean of both neighbours over 8 robust sigmas on at least 3 channels, and a local maximum | excluded |
| Missing rows up to 0.3 s | larger time step | trapezoid across the gap |
| Gaps over 0.3 s | node duration | five extra unknowns per gap (6.4) |
| Duplicated or out-of-order timestamps | time not strictly increasing | skipped in integration, still receive a pose |
| Column order | the triad whose median norm is one g is the accelerometer; header used only as tie-break | any order accepted |
| Units | accelerometer in g if median norm in (0.5, 2); gyro in deg/s if the 99th percentile exceeds 8 | converted |

With `assume_blind_tail` off, `detect_noise_tail` decides instead: it compares the roughness of each channel in the last 5 s with the 10 s before. On 151 real files the largest natural ratio is 1.8 (no false positives at the threshold of 4); it catches moderate noise but not noise at vibration level, which is why the default does not rely on it.

## 8. Evidence

### 8.1 Per flight [measured]

| Flight | Length | Constant | Clean | Degraded (seed 42) | Blind-window ATE |
|---|---|---|---|---|---|
| MH_01_easy | 184 s | 4.31 | 3.83 | 3.86 | 1.19 |
| MH_02_easy | 152 s | 4.65 | 4.01 | 4.08 | 1.03 |
| MH_03_medium | 135 s | 3.58 | 2.13 | 2.13 | 2.05 |
| MH_04_difficult | 102 s | 6.82 | 4.74 | 4.68 | 0.99 |
| MH_05_difficult | 114 s | 6.88 | 4.67 | 4.77 | 2.17 |
| V1_01_easy | 146 s | 1.85 | 1.19 | 1.27 | 1.86 |
| V1_02_medium | 86 s | 1.78 | 0.74 | 0.74 | 1.28 |
| V1_03_difficult | 108 s | 1.57 | 1.10 | 1.28 | 2.48 |
| V2_01_easy | 114 s | 2.30 | 2.08 | 2.01 | 1.65 |
| V2_02_medium | 117 s | 2.11 | 1.36 | 1.36 | 2.15 |
| V2_03_difficult | 117 s | 2.06 | 1.53 | 1.28 | 2.29 |
| **Mean** | | **3.45** | **2.49** | **2.49** | **1.74** |

### 8.2 Ablation [measured, EuRoC mean ATE]

| Configuration | Clean | Degraded, seed 42, inversion off |
|---|---|---|
| Open-loop strapdown with ground-truth start and biases | 38 m after 20 s on V1_01 | |
| Drift fit only | 3.09 | 3.11 |
| + rotor drag | 2.49 | 2.50 |
| + seed inversion | | 2.49 |
| Raw EuRoC column order, inversion off / on | | 3.25 (rotation 50 deg) / 2.50 (11 deg) |
| 2 s dropouts, gap unknowns off / on | | 3.53 / 2.65 |

### 8.3 Falsification of the drag model [measured]

| Test | Result |
|---|---|
| Coefficient from the IMU alone | 0.139 to 0.219 1/s; ground-truth regression 0.166 to 0.211 |
| Two halves of each file | 0.14 to 0.24 on every EuRoC flight, ratio 1.6 or less |
| Null test: in-plane force shifted by 37 s (same statistics, physics broken) | correlation within 0.20 of zero; model switches off on 11 of 11; ATE returns to the no-drag value |
| Leave-one-out: coefficient fixed from the other 10 flights | 2.486 m against 2.489 m self-calibrated |
| Hand-held data (TUM-VI) | correlation magnitude at most 0.23; model off on 6 of 6 |
| Held-out split | see 8.5 |

### 8.4 Blind window [measured]

- **Oracle.** Forecasting 5 s ahead from the true position and velocity at 360 hand-over times: hold 1.66 m RMSE, damped velocity with `tau = 2 s` 1.34 m, constant velocity 1.73 m. Even perfect velocity gains only 20% over holding.
- **Files that end near a landing** (the 11 full EuRoC flights, degraded): dead-reckoning RMSE 0.67 m for hold against 0.94 m for `tau = 1 s`.
- **Blind window placed mid-flight** (33 files cut at 45, 60 and 75% and then degraded; the vehicle travels 2.9 m on average during the window): 1.79 m for hold against 1.65 m for `tau = 1 s`.
- Hold loses 8% in the case that suits it least; a 1 s decay loses 40% in the case that suits it least. Hold is the minimax choice and is the default. Attitude: holding gave 7.3 deg at 5 s against 13.2 deg for continuing the last rate with a 1 s decay.

### 8.5 Held-out check [measured]

All settings in `CFG` were selected with `tools/tune.py` on six flights (MH_01, MH_03, MH_05, V1_02, V2_01, V2_03) and then evaluated on the other five.

| Variant (inversion off) | Train (6) | Test (5) | Constant, test |
|---|---|---|---|
| Clean | 2.49 | 2.48 | 3.40 |
| Degraded, seed 42 | 2.49 | 2.50 | 3.40 |
| Degraded, seed 1 | 2.47 | 2.59 | 3.40 |
| Raw column order | 3.33 | 3.15 | 3.40 |
| Mean | 2.70 | 2.68 | |

One tuning step was rejected by this check: a tighter drag weight improved the train mean from 2.69 to 2.55 and worsened the test mean from 2.68 to 2.72.

### 8.6 Resources [measured: one core]

| File | Rows | Length | Time | Per second of IMU | Peak heap |
|---|---|---|---|---|---|
| V1_02 degraded | 16,624 | 86 s | 0.13 to 0.18 s | 1.6 to 2.1 ms | 2.1 MB |
| MH_01 degraded, seed verified | 35,629 | 184 s | 0.27 s | 1.5 ms | 4.1 MB |
| MH_01 degraded, seed not matched (ramp search runs) | 35,697 | 184 s | 0.50 s | 2.7 ms | 3.9 MB |
| TUM-VI magistrale1 | 153,989 | 772 s | 0.91 s | 1.2 ms | 7.1 MB |

Whole process including interpreter start: under 0.5 s for the 184 s file. Heap measured with `tracemalloc`, which also traces NumPy buffers.

### 8.7 Cross-checks [measured]

- `evo_ape tum gt.txt est.txt -a` (evo 1.38.1) and `tools/bench.py` agree to six digits on a degraded output that contains 20 duplicated timestamps.
- The browser viewer's alignment agrees with both to four digits.
- Python 3.11 with NumPy 1.26.4 and Python 3.13 with NumPy 2.5.3 give trajectories within 0.2 mm of each other, and the seed check matches on both.

## 9. Where the remaining error comes from [measured]

| Experiment (clean EuRoC) | Mean ATE |
|---|---|
| Full pipeline | 2.49 m |
| Our attitude with the **true** body velocity | 0.15 m |
| The **true** attitude with our body velocity | 2.49 m |
| Horizontal / vertical split of the error | 2.45 m / 0.42 m |

Attitude and the vertical axis are solved. Everything left is slow horizontal velocity error, about 0.28 m/s against a mean speed of 0.81 m/s.

Its source is the drag law's own ambiguity: a constant body-frame velocity offset `d` is indistinguishable from an accelerometer in-plane bias `mu d` (or a thrust-axis misalignment of `mu d / G`). An in-plane bias of 0.05 m/s^2 divided by `mu = 0.19` is 0.26 m/s. Only the bounded-position prior resolves it, and only on average.

Even with coefficient and offset fitted against ground truth, the drag law leaves 0.22 m/s of velocity error at 1 s averaging and 0.12 m/s at 10 s.

Tested and rejected, no gain: lever arm of the IMU from the centre of mass (2.577 to 2.570 m), anisotropic drag, thrust-scaled drag, vertical-velocity coupling, a drag offset fixed to its ground-truth value (worse), a tighter drag weight (fails the held-out check).

## 10. Known limits and open questions

| Limit | Consequence | Status |
|---|---|---|
| Slow horizontal velocity is unobservable (section 9) | ATE of metres, not centimetres | Physical |
| Raw column order fed to the script with a seed we cannot verify | 3.25 m, rotation 50 deg: the gyro carries accelerometer-sized noise | Partly mitigated by looser gyro-bias knots (3.58 to 3.25 m); ask the organisers |
| Heading drift when the file has no rest start | Rotation RMSE 15 to 65 deg; ATE less affected | Open |
| Heading change inside a long gap is unmeasured | Rotation error after 2 s gaps | Open |
| Blind window mid-flight | Dead-reckoning error 1.8 m over 5 s | Hold is within 8% of the best tested policy |
| Drag model developed on one airframe | Another multirotor may differ | Calibrated per file, guarded, falls back |
| Files shorter than about one minute | Drag model stays off (not enough data to calibrate) | By design |
| Datasets were obtained from public repository mirrors | Possible differences from the official archives | Re-run on official downloads |
| Docker image | Not built in the authoring environment | Build and run once before submitting |
| Presentation | Built from the organisers' template (`docs/deck/`) | Fill team name, college, members, links |

## 11. Functions (all in `src/main.py` unless noted)

| Function | Signature | Responsibility |
|---|---|---|
| `quat_mul`, `quat_exp`, `quat_rotate`, `quat_cumprod` | arrays of (w,x,y,z) | Hamilton algebra, vectorised prefix product |
| `knot_basis` | `(t, T, nk) -> [K, nk]` | piecewise-linear basis; `nk = 1` is a constant |
| `tilt_from_gravity` | `(f[3]) -> q[4]` | rotation taking f to +z |
| `parse_values` | `(lines) -> [c, 6]` | fast CSV parse with fallback |
| `scan_timestamps` | `(path) -> (ts, info)` | pass 0; layout and unit detection |
| `detect_noise_tail` | `(path, ts, info, cfg) -> t_cut or None` | roughness-jump test, used only when `assume_blind_tail` is off |
| `preintegrate_group` | `(t, g, a) -> dq, dv, dp, th` | section 6.2 |
| `static_start_bias` | `(t, g, a) -> (bias, f_mean, seconds) or None` | section 6.7 |
| `preintegrate_file` | `(path, ts, info, cfg, inv) -> nodes` | pass 1, section 7 |
| `cumint` | `(e, dt) -> vel, pos` | exact integrals of node-wise constant acceleration |
| `bootstrap_gyro_bias` | `(t0, dt, dq, dv, sig_prior) -> b[3]` | section 6.7 |
| `solve_nodes` | `(t0, dt, dq, dv, dp, th, f_init, static, cfg) -> tn, q, p, v` | sections 6.3 to 6.6 |
| `poses_at` | `(t, tn, q, p, v, cfg) -> P, Q` | section 6.8 |
| `format_timestamps`, `write_trajectory` | | exact output |
| `fallback_solution` | `(ts, info) -> sol` | 1 mm helix so the file is always valid and never exactly constant |
| `solve_file` | `(path, cfg) -> ts, info, sol` | orchestration with exception fallback |
| `estimate` | `(path, cfg) -> ts, P, Q, info` | test helper |
| `SeedInversion` (`seed_inversion.py`) | `__init__(ts, info)`, `apply(row0, gyro, acc, dead) -> stuck` | section 3.3 |

All tunables live in `CFG` at the top of `main.py`, each with a one-line comment.

## 12. Tests and tools

| Command | What it proves |
|---|---|
| `python tests/test_core.py` | 9 unit tests: quaternion convention, rotation composition, prefix product, preintegration, integrals, timestamp formatting, interpolation |
| `python tools/edge_tests.py` | 18 malformed inputs each give one finite pose per row (no header, either column order, g units, deg/s, float seconds, 2 rows, 50 rows, zero/NaN/frozen/garbage/noise tail, all zeros, 2 s gap, duplicates, swapped rows, moving start, CRLF) |
| `python tools/final_table.py` | the scenario table in section 2 |
| `python tools/heldout.py` | section 8.5 |
| `python tools/tune.py '<json grid>'` | selects settings on the train flights only and reports the test flights |
| `python tools/falsify_drag.py "data/euroc/*" "data/tumvi/room*"` | section 8.3 |
| `python tools/evalset.py '{}'` | mid-flight, standard, other-seed and clean sets with three blind-window metrics and the rank check |
| `python tools/perf.py <file>` | time and peak heap |
| `python tools/make_metadata.py`, `tools/make_submission.py` | `metadata.json` and the submission zip |

Data layout expected by the tools is described in `CLAUDE.md`.

## 13. References

- [R1] Martin, Salaün. "The true role of accelerometer feedback in quadrotor control." ICRA 2010. (cited from memory; verify before quoting)
- [R2] Leishman, Macdonald, Beard, McLain. "Quadrotors and Accelerometers: State Estimation with an Improved Dynamic Model." IEEE Control Systems Magazine 34(1), 2014. DOI 10.1109/MCS.2013.2287362.
- [R3] Macdonald, Leishman, Beard, McLain. "Analysis of an Improved IMU-Based Observer for Multirotor Helicopters." Journal of Intelligent and Robotic Systems, 2013. DOI 10.1007/s10846-013-9835-5.
- [R4] Abeywardena, Kodagoda, Dissanayake, Munasinghe. "Improved State Estimation in Quadrotor MAVs: A Novel Drift-Free Velocity Estimator." IEEE Robotics and Automation Magazine, 2013.
- Forster, Carlone, Dellaert, Scaramuzza. "On-Manifold Preintegration for Real-Time Visual-Inertial Odometry." IEEE T-RO 2017. arXiv:1512.02363.
- Solà. "Quaternion kinematics for the error-state Kalman filter." arXiv:1711.02508.
- Burri et al. "The EuRoC micro aerial vehicle datasets." IJRR 2016. DOI 10.1177/0278364915620033.
- Schubert et al. "The TUM VI Benchmark for Evaluating Visual-Inertial Odometry." IROS 2018. arXiv:1804.06120.
- Qiu et al. "AirIO: Learning Inertial Odometry with Enhanced IMU Feature Observability." arXiv:2501.15659.
- Silva do Monte Lima et al. "End-to-End Learning Framework for IMU-Based 6-DOF Odometry." Sensors 2019. DOI 10.3390/s19173777.
- Grupp. evo. https://github.com/MichaelGrupp/evo

The full bibliography with verification status is in `docs/archive/TRACK3_MASTER_PLAN_v1.md`, chapter 28.
