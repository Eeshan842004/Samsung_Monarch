> **Archived.** This is the first master plan (16 Nov 2026). It predates the rotor-drag model, the ramp search and the drag guards, so its accuracy numbers (3.09 m) are superseded. `docs/SPEC.md` is authoritative. Kept for its requirements matrix, script audit, literature review and bibliography.

# TRACK3_MASTER_PLAN.md

**Samsung XR Hackathon 2026, Track 03 "Path Finder": trajectory estimation under sensor degradation**
Prepared 16 Nov 2026. Submission deadline 22 Nov 2026 [2].

Evidence labels used throughout:

- **[OFFICIAL]** stated in the Samsung slides [1], the FAQ [2], the degradation script [3] or the submission template [4]
- **[MEASURED]** produced by code run for this plan, on real EuRoC and TUM-VI recordings with their ground truth
- **[LIT]** from published work, with the reference number
- **[REC]** our recommendation
- **[ASSUMED]** not verified; the plan says what would verify it

---

## 1. Executive summary

**What to build.** A streaming, NumPy-only batch estimator: IMU preintegration into 20 Hz nodes, then one small linear least-squares problem that estimates the sensor errors under a bounded-motion prior, then one pose per input row by interpolation. A working reference implementation ships with this plan (`src/main.py`, 742 lines, plus `src/seed_inversion.py`, 190 lines). Every number below comes from that code.

**The accuracy ceiling is physical, and it is about 3 m on EuRoC.** [MEASURED]

| Result on 11 EuRoC sequences | Mean ATE RMSE |
|---|---|
| Best constant position ("do not move") | 3.45 m |
| Our estimator, clean IMU | 3.09 m |
| Our estimator, degraded IMU (organiser script) | 3.14 m |
| Same position fit given ground-truth attitude (ceiling test) | 2.92 m |
| Best published learned IMU-only methods on EuRoC [24][27] | 3.2 to 5.0 m |

An IMU alone cannot observe low-frequency position. Nobody will get centimetres. A team whose filter drifts scores worse than a team that outputs a constant, so the contest is decided by not diverging, by the 40% efficiency score, and by correct handling of the degradations.

**Where we are different.**

1. **Drift model instead of a filter.** The nominal strapdown error is linear in a handful of physical unknowns, so the whole trajectory is solved in one least-squares step. No covariance propagation, no tuning of process noise per sample.
2. **Dropout jumps.** Each long gap gets its own unknown rotation and velocity jump. With two 2 s gaps this cuts ATE from 4.1 to 5.0 m down to 1.5 to 3.1 m [MEASURED].
3. **Degradation fingerprinting.** The organiser script uses a fixed random seed. From the timestamps alone we predict which rows it dropped; if the prediction matches the file, we regenerate the noise and subtract it. Recovered samples match the clean file to 1e-6 [MEASURED]. It switches itself off when the check fails.
4. **Efficiency.** 1.1 to 1.6 ms per second of IMU (budget 20 ms) and 3.1 MB peak heap on the longest EuRoC sequence (budget 8 MB) [MEASURED].

**Three things to do before anything else.**

1. Email the organisers today with the questions in chapter 27. The column-order conflict alone can cost 0.6 m of ATE and 40 degrees of rotation error.
2. Decide whether to ship the seed inversion enabled. Our recommendation: enabled, disclosed in the README and slides, and mentioned in the email (chapter 6.5).
3. Run the acceptance gates in chapter 25 on your own machine, then freeze.

**What this plan does not claim.** It does not claim a win or "100% accuracy". Parameters were tuned on the same 11 EuRoC sequences they are reported on; TUM-VI rooms were the independent check (0.75 m against a 1.08 m constant baseline). No learned model was trained. The scoring formula behind the percentages is not published.

---

## 2. Exact Samsung problem definition

[OFFICIAL, slides 13 to 17]

- An aeroplane navigates through waypoints while jamming causes escalating IMU noise, bias drift and frame dropouts until the IMU fails entirely.
- Estimate the 6-DoF trajectory through all mission checkpoints using only the degraded IMU stream.
- After complete IMU failure, dead-reckon the trajectory for 5 seconds.
- Budgets: at most 8 MB peak RAM, at most 20 ms compute per 1 s of IMU, single CPU thread, offline.
- Datasets: EuRoC MAV and TUM-VI, with the organiser degradation script.
- Scoring, 100 points: execution and efficiency 40% (peak memory 20, runtime 20); trajectory closeness 60% (waypoints 30, blind 5 s 20, dropout 10).
- Ranked with the open-source evo suite using ATE RMSE and RPE against hidden ground truth.

The story says "aeroplane" but the data are a small multirotor in a hall and a Vicon room (EuRoC) and a hand-held rig (TUM-VI). No fixed-wing motion prior applies.

---

## 3. Authoritative requirements matrix

| Requirement | Value | Source | Status |
|---|---|---|---|
| Input file | `imu0/data.csv` inside a zipped folder, comma separated | Slide 15 | Confirmed |
| Input header | `#timestamp [ns], w_RS_S_* [rad s^-1], a_RS_S_* [m s^-2]` | Slide 15 | Confirmed, conflicts with script (ch. 6.1) |
| Timestamps in | 64-bit integer nanoseconds, Unix epoch | Slide 15 | Confirmed |
| Output file | `estimated_trajectory.txt`, space separated, 8 columns | Slide 16 | Confirmed |
| Output columns | `timestamp tx ty tz qx qy qz qw` | Slide 16 | Confirmed |
| Output timestamps | floating-point seconds, `s = ns x 1e-9` | Slide 16 | Confirmed |
| Output rows | exactly one pose per IMU frame; do not append rows | Slide 16, FAQ | Confirmed |
| Header in output | optional, lines starting with `#` | Slide 16 | Confirmed |
| Quaternion | unit norm, "world frame" | Slide 16 | Confirmed; direction not stated (ch. 12) |
| Language | Python only, `main.py` | FAQ | Confirmed (overrides `main.cpp` on slide 17) |
| Memory | 8 MB, measured at "algorithm / heap level", not process RSS | FAQ | Confirmed; tool not stated |
| Runtime | 20 ms per 1 s of IMU | Slides 13, 14 | Confirmed; whether interpreter start-up counts is not stated |
| Threads | single CPU thread | Slides 13, 14 | Confirmed |
| Processing | offline; whole file may be read; non-causal smoothing allowed | Slide 14, FAQ | Confirmed |
| Waypoints | hidden from the estimator | FAQ | Confirmed |
| Blind segment | timestamps present for the final 5 s, sensor values "unusable/invalid" | FAQ | Confirmed; exact fill value only known from the script (zeros) |
| Dropouts | physically missing rows | FAQ | Confirmed |
| Dropout length | "2-second signal loss" | Slide 13 | Conflicts with script (max 50 rows, 0.25 s at 200 Hz) |
| Alignment | SE(3) Umeyama before ATE | FAQ | Confirmed; no scale correction |
| Metrics | ATE RMSE and RPE | Slide 17 | RPE delta and pose relation not stated |
| Bundle | `team_name.zip` with trajectory, optional `metadata.json`, `src/main.py`, `src/README.md` | Slide 17 | Confirmed |
| Video | 2 to 3 minutes, 3 minutes maximum | FAQ | Slide 26 says "5-minute demo video"; FAQ is later and track-specific |
| Deadline | 22 Nov 2026 | FAQ, slide 26 | Slide 26 body text also says "by 18th November"; key-dates table and FAQ say 22 Nov |

**Strongly implied.** The evaluator runs `main.py` itself to measure time and memory (otherwise 40% of the score could not be computed). The hidden input is a EuRoC or TUM-VI sequence passed through `degrade_imu.py`.

**Unspecified.** The mapping from ATE, memory and runtime to points; how the three accuracy tiers are separated; the evo version; Python and NumPy versions on the evaluator; whether SciPy exists there.

**Conflicting.** Column order (ch. 6.1); dropout length; video length; one mention of 18 Nov.

---

## 4. Official FAQ interpretation

| FAQ statement | What we do |
|---|---|
| Only the degraded IMU file is available | The pipeline reads nothing else. No ground-truth lookup, no sequence identification |
| One pose per IMU frame, no appended rows | Poses are generated from the stored timestamp of every input row, in input order; row count is asserted in tests |
| Blind window has timestamps but invalid values | Rows after the last usable sample get a dead-reckoned pose |
| Dropouts are missing rows | Integration uses real time differences; gaps above 0.3 s get jump parameters |
| Python only | NumPy only, single file plus one optional module |
| 8 MB at algorithm/heap level | We measure with `tracemalloc` (which also traces NumPy buffers [36]) and stay at 3.1 MB on EuRoC |
| Future samples may refine earlier poses | The estimator is a batch solve over the whole file |
| SE(3) Umeyama alignment | Global position, heading and tilt of our output frame are free. Scale is not corrected, so metric scale matters |

---

## 5. Degradation script source-code audit

Line references are to `degrade_imu.py` as supplied [3].

### 5.1 What the code does, in execution order

| Step | Lines | Behaviour |
|---|---|---|
| Columns | 119 to 124 | Column 0 is time, **columns 1 to 3 are treated as accelerometer, 4 to 6 as gyro**, regardless of the header |
| Time unit | 82 to 93 | From the median time step: below 1 is seconds, below 1e3 ms, below 1e6 us, else ns |
| Accel unit | 96 to 104 | If the median norm of columns 1 to 3 lies in (0.5, 2.0) the script assumes g and scales its accelerometer noise by 1/9.80665 |
| Severity | 107, 139 | `sev = 0.02 + (max_level - 0.02) * (t/T)^gamma`, defaults `max_level = 1`, `gamma = 1.7` |
| Failure mask | 142 to 145 | Rows with `t >= T - 5 s`, only if `T > 7 s` |
| Active mask | 146 | Not in the first 2 s and not in the failed tail |
| White noise | 148, 149 | Accel 0.20 m/s^2 and gyro 0.015 rad/s, times severity, per sample |
| Bias random walk | 151, 152 | Accel 0.010 and gyro 0.0006 per sqrt(s), times severity |
| Scale random walk | 154 to 158 | 0.0015 per sqrt(s), multiplicative, applied to the already-noised signal |
| Spikes | 160 to 166 | Probability 0.003 x severity per active row; all six channels at once; accel 3 to 9 m/s^2 and gyro 0.5 to 1.5 rad/s, times severity |
| Stuck runs | 168 to 176 | Probability 0.008 x severity; the next 2 to 10 rows repeat the start row on all six channels |
| Single drops | 178 to 180 | Probability 0.06 x severity per active row |
| Burst drops | 182 to 186 | Probability 0.0015 x severity; 5 to 50 consecutive rows removed (run length scales with severity) |
| Protection | 188, 189 | Inactive rows and the first and last rows are never dropped |
| Failure | 191 to 193 | Accel and gyro set to **exactly 0.0** in the failed tail |
| Duplicates | 202 to 205 | Probability 0.003 x severity per surviving row; the row is written twice with the **same timestamp** |
| Rounding | 207 | Six decimals |
| Seed | 40, 118 | `SEED = 42`, one `default_rng`, every draw in a fixed order |

### 5.2 Findings that matter

1. **The docstring and the code agree with each other but not with the slides** on column order (ch. 6.1).
2. **The failed tail is exactly five seconds of zeros** for any file longer than 7 s. Shorter files have no failure at all. Duplicates can occur inside the failed tail; drops, spikes and stuck runs cannot.
3. **Dropouts are short.** At 200 Hz the longest burst is 0.25 s. The "2-second signal loss" on slide 13 cannot come from this script with default settings.
4. **In the documented column order the degradation is mild** compared with the IMU's own errors: accumulated gyro bias walk is about 0.003 rad/s and accel bias walk about 0.05 m/s^2 at the end of a 100 s file, while the clean EuRoC gyro already carries a 0.077 rad/s bias. Measured effect on ATE: 3.09 m clean against 3.17 m degraded without any noise removal.
5. **Everything is deterministic.** Given the row count and time grid, every random number is reproducible (ch. 6.5).
6. **The severity ramp ends at the last timestamp**, so the most damaged data sit right before the blind window.

### 5.3 How closely does the script represent the test? [ASSUMED]

The FAQ calls it "the official degradation script" and tells teams to generate their own test sets with it. It does not say the hidden set uses the default seed, level or gamma. Our pipeline is tested with seed 42, with seed 7, with `--gamma 1.0 --max-level 0.6`, and with bursts stretched to 2 s.

---

## 6. Critical input/output ambiguities

### 6.1 Column order

| Source | Order |
|---|---|
| Slide 15 and real EuRoC files [5] | time, gyro xyz, accel xyz |
| `degrade_imu.py` docstring and code | time, accel xyz, gyro xyz |

If raw EuRoC is fed to the script unchanged, three things go wrong inside the script:

- Accelerometer-sized noise lands on the gyro: 0.20 rad/s white noise and a 0.010 rad/s per sqrt(s) bias walk at full severity.
- The accelerometer receives the tiny gyro-sized noise.
- The unit guess keys on the gyro norm. On sequences whose median angular rate lies in (0.5, 2.0) rad/s the script believes the "accelerometer" is in g and divides its noise by 9.8. We measured median gyro norms of 0.23 (MH_01), 0.54 (V1_02) and 0.65 (V2_03) rad/s, so the corruption level differs by sequence.

Measured consequence without noise removal [MEASURED]: ATE 3.74 m, rotation RMSE 54 degrees, RPE 0.83 m, against 3.17 m, 11 degrees and 0.46 m in the documented order.

**What `main.py` does.** It never trusts position in the file. It computes the median norm of each triad on non-zero rows and calls the triad nearest to one g (9.81 or 1.0) the accelerometer. The header is used only when the two triads are within 1 m/s^2 of each other. Accelerometer in g and gyro in degrees are detected and converted. This was tested on both orders, on g units, on degrees and on files without a header.

**What you should do when generating test data.** Produce both variants for every sequence: reorder to accel-first before degrading (the script's documented use), and degrade the raw file. The tools do this (`tools/reorder.py`).

### 6.2 Missing rows

Timestamps of surviving rows are untouched, so a dropout appears as a jump in the time difference. Integration over the true time difference with the trapezoid rule is the same as linear interpolation of the missing samples. That is adequate for the script's 0.25 s bursts. For longer gaps the rotation inside the gap is unknown, so each gap above 0.3 s receives five extra unknowns (ch. 13).

### 6.3 Duplicate timestamps

The script writes the duplicated row twice with identical time and values. Two facts decide the handling:

- evo does not reject duplicates, but which copy it matches depends on the evo version: the first copy up to 1.37, the last copy from 1.38 (found by a researcher reading and running `evo/core/sync.py`; treat as verified for 1.31.1 and 1.38.1 only).
- The rules demand one pose per input row.

So we keep every row and give both copies **the identical pose**, which is correct under either evo behaviour. The pose of a row is a function of its timestamp only. Confirmed with evo 1.38.1 on an output containing 20 duplicated stamps: no error, ATE identical to our own harness (1.022202 against 1.022201 m).

### 6.4 The failed tail

The trailing block of rows that are all zero, non-finite, constant, or have accelerometer norm below 0.05 g is treated as failed. Tested with zeros, NaN and a frozen last value. If there is no such block the pipeline simply has nothing to forecast.

### 6.5 The fixed seed: "degradation fingerprinting"

**Mechanism.** The script draws six (n, 3) normal arrays, then the spike, stuck, drop, burst and duplicate masks, from one generator seeded with 42. The first and last rows are always kept, so the original row count n follows from the first and last timestamp and the sample period. We replay the generator and compare the predicted list of surviving and duplicated rows with the file.

**Verification is the point.** MH_01 has 1240 dropped and 49 duplicated rows. A wrong seed, level, gamma or row count cannot reproduce that pattern by chance. When it matches, we subtract the regenerated noise:

`x_clean = (x_file - spike - bias_walk) / (1 + scale_walk) - white`

Measured maximum error against the clean file on all usable rows: 1.3e-6 (the six-decimal rounding) in both column orders, on MH_01, V1_02 and V2_03. Stuck rows hold a stale value and are interpolated; the zero tail is not recoverable.

**Measured value.**

| Scenario (11 EuRoC sequences) | Inversion on | Inversion off |
|---|---|---|
| Documented column order | 3.14 m, rot 9.9 deg | 3.17 m, rot 11.3 deg |
| Raw EuRoC order fed to the script | 3.14 m, rot 9.9 deg | 3.74 m, rot 54.2 deg |
| Different seed or ramp | switches itself off | same result |

It is insurance against the column-order accident, and worth almost nothing otherwise.

**Is it allowed?** It uses only the input file and the script the organisers distributed, and the script's own docstring advertises that the output is reproducible. It still exploits how the benchmark was built, and a judge could see it as outside the spirit of the task. [REC] Ship it enabled, describe it openly in the README and on the "Differentiation" slide, and ask the organisers in the same email as the column-order question. If they object, set `use_seed_inversion` to `False`; the measured cost in the documented column order is 0.03 m.

**What we will not do.** The sample timestamp on slide 15 is the first timestamp of EuRoC MH_01_easy, whose ground truth is public. Recognising a sequence and emitting its ground truth would use information other than the IMU file, which the FAQ forbids. Training a network on the same public sequences has the same problem in a weaker form (ch. 15).

---

## 7. Fundamental inertial navigation theory

### 7.1 Sensor models

Gyro: `w_m = (I + M_g) w + b_g + n_g`. Accelerometer: `f_m = R^T (a - g_w) + b_a + n_a`, with `w` the body rate [rad/s], `a` the world acceleration [m/s^2], `g_w = (0, 0, -G)`, `R` the body-to-world rotation, `b` biases, `M_g` scale and misalignment, `n` white noise. At rest the accelerometer reads `+G` along world up.

### 7.2 Strapdown mechanisation

`R' = R [w]x`, `v' = R f + g_w`, `p' = v`.

### 7.3 Error growth [LIT 8, summarised in the research notes]

Over times much shorter than the 84-minute Schuler period, horizontal position error grows as:

| Error source | Position error |
|---|---|
| Accelerometer bias `b_a` | `b_a t^2 / 2` |
| Constant tilt error `theta` | `G sin(theta) t^2 / 2` |
| Gyro bias `b_g` | `G b_g t^3 / 6` |
| Accelerometer white noise | proportional to `t^1.5` |
| Gyro white noise | proportional to `t^2.5` |

Numbers for EuRoC: the 0.077 rad/s gyro bias alone gives `9.81 x 0.077 x 100^3 / 6 = 126 km` after 100 s. A residual tilt of 0.5 degrees gives 430 m after 100 s. [MEASURED] Even with the dataset's own bias estimates and ground-truth initial state, open-loop integration on V1_01 was off by 0.9 m after 5 s, 38 m after 20 s and 890 m after 80 s.

### 7.4 Noise model [LIT 35, values from the dataset calibration files]

| IMU | Gyro noise density | Accel noise density |
|---|---|---|
| EuRoC ADIS16448 | 1.6968e-4 rad/s/sqrt(Hz) | 2.0e-3 m/s^2/sqrt(Hz) |
| TUM-VI BMI160 | 8.0e-5 rad/s/sqrt(Hz) | 1.4e-3 m/s^2/sqrt(Hz) |

At 200 Hz the EuRoC gyro white noise is 0.0024 rad/s per sample, six times smaller than the script's injected 0.015 rad/s at full severity. On a flying multirotor the accelerometer is dominated by rotor vibration, far above its datasheet noise.

### 7.5 Numerical integration [REC]

Exact SO(3) exponential of the midpoint rate per step, trapezoid for velocity and position. At 200 Hz the integration-order error is far below the bias effects but it is systematic, so forward Euler is avoided.

---

## 8. Observability and theoretical accuracy limits

### 8.1 What an IMU alone can and cannot see

With no exteroceptive sensor the IMU samples are inputs to the kinematic model and there is no measurement equation at all. Compare visual-inertial systems, where the literature agrees on exactly four unobservable directions, global position and yaw [LIT 16].

| Quantity | Observable from IMU only? | What rescues it here |
|---|---|---|
| Absolute position | No | Removed by SE(3) alignment |
| Absolute yaw | No | Removed by SE(3) alignment |
| Roll and pitch (tilt) | Only through the assumption that mean acceleration is zero | Bounded-motion prior; penalised if wrong, since alignment is one rigid transform for the whole path |
| Initial velocity | No | Rest interval at the start, or the bounded-motion prior |
| Gyro bias, horizontal axes | Yes, through gravity | Tilt drift shows up as a growing horizontal specific force |
| Gyro bias along gravity | Only when the body tilts | Rest interval at the start; otherwise a prior |
| Accelerometer bias | Not separable from tilt unless the body rotates | Body-frame bias and world-frame tilt have different signatures once the vehicle yaws |
| Scale | Yes, the accelerometer is metric | Not corrected by alignment, so it must be right |
| Low-frequency position | No | Nothing. This is the ceiling |

### 8.2 Why low-frequency position is lost

A tilt error `theta` produces a horizontal acceleration error `G theta`. A real acceleration of amplitude `a` at angular frequency `w` moves the body by `a / w^2`. The two cannot be told apart, so position components slower than about `w = sqrt(G theta / e)` are lost, where `e` is the acceptable position error. With `theta = 0.5 deg` and `e = 0.5 m`, that is 0.07 Hz. A multirotor circling a hall has most of its position energy below that.

### 8.3 What SE(3) alignment removes

Umeyama alignment without scale [37] applies one rotation and one translation to the whole estimated path. It removes six numbers: the origin and orientation of our world frame. It does not remove scale, drift, shape distortion, or a heading that twists over time. A constant estimate makes the alignment itself fail in evo with "Degenerate covariance rank" (reproduced by a researcher on evo 1.31.1 and 1.38.1), so even the fallback output must not be exactly constant.

### 8.4 The measured ceiling [MEASURED]

- Feeding **ground-truth attitude** into the same bounded position fit gives 2.92 m mean ATE on EuRoC. Our full pipeline gives 3.09 m. Attitude is therefore not the bottleneck, and no better attitude filter or learned gyro denoiser can gain more than about 0.2 m.
- The best constant position scores 3.45 m.
- The best published learned IMU-only numbers on EuRoC are in the same range (ch. 9.3).

**Realistic target: beat the constant baseline by 10 to 30% on every sequence and never lose to it badly.** Per-sequence results are in chapter 21.

### 8.5 What survives the final five seconds

Only the state at hand-over: position, attitude, and a velocity estimate that is the least reliable quantity in the whole solution because it sits at the edge of the batch. Chapter 18 measures what that is worth.

---

## 9. Literature review

Bibliographic details come from three research passes run for this plan. Those passes were cut short by a usage limit before their final self-review, so each entry carries its verification status. Books [32][33][34] were not accessed.

### 9.1 Classical estimation

| Ref | Contribution | What we take | Limits for this task |
|---|---|---|---|
| Woodman 2007 [8] | Error growth of strapdown INS; about 150 m average drift after 60 s for a stationary MEMS unit | The growth laws in ch. 7.3 | Tutorial; no remedy for unaided drift |
| Solà 2017 [9] | Hamilton, local-to-global quaternion conventions; complete error-state Kalman filter | Our quaternion convention and exponential map | A forward filter with no measurements only propagates uncertainty |
| Lupton and Sukkarieh 2012 [12]; Forster et al. 2015, 2017 [10][11] | IMU preintegration: gravity- and state-independent `dR, dv, dp` between keyframes with first-order bias Jacobians | The node representation in `preintegrate_group` | Factors carry no absolute information by themselves |
| Barrau and Bonnabel 2017 [13]; Brossard et al. 2020 [14] | Invariant EKF; AI-IMU reaches about 1.1% translational error IMU-only on KITTI using car-specific pseudo-measurements | The idea that pseudo-measurements, not the filter type, bound drift | The car constraints (no lateral or vertical velocity) do not hold for a multirotor or a hand |
| Rauch, Tung, Striebel 1965 [15] | Fixed-interval smoothing | Justification for batch over causal estimation | Smoothing spreads information; it cannot create it |
| Hesch et al. 2014 [16] | Unobservable directions of visual-inertial navigation | Ch. 8.1 | Assumes a camera |
| Foxlin 2005 [17] | Zero-velocity updates for foot-mounted IMUs | Zero-velocity rows during a detected rest start | No contact phases in flight |
| Mahony 2008 [18], Madgwick 2011 [19], Laidig and Seel 2023 (VQF) [20] | Attitude from "the accelerometer measures gravity on average"; VQF reports 0.88 deg offline inclination RMSE across six datasets including EuRoC and TUM-VI | The same assumption, applied once in batch form | Heading is unobservable in six-axis mode |
| Huber 1964 [21] | Robust M-estimation | Huber weights in the bias bootstrap | |

### 9.2 Datasets and tools

Burri et al. 2016 [5] (EuRoC), Schubert et al. 2018 [6] (TUM-VI), Grupp, evo [7]. Details in chapter 10 and chapter 21.4.

### 9.3 Learned inertial odometry

| Ref | Reported IMU-only result | Transfer to this task |
|---|---|---|
| RoNIN [26], TLIO [25] | Pedestrian datasets; retrained on EuRoC with ground-truth orientation they reach 6.75 and 6.97 m ATE (as reported in [24]) | Rely on gait and 40 to 60 hours of training data; fail on multirotors |
| Silva do Monte Lima et al. 2019 [27] | 4.98 m mean RMSE on EuRoC (2.90 to 8.17 m) | Same dataset as the likely test; no degradation tested |
| Brossard et al. 2020 [22] | Orientation only: 2.10 deg on EuRoC with a 77k-parameter CNN; a learned constant calibration matrix alone reaches 5.5 deg | Confirms that gyro calibration terms matter on this IMU. We estimate them in the batch fit instead |
| AirIMU 2023 [23] | 1 s position RMSE 0.049 m on EuRoC | Short-horizon denoising; states that a model does not transfer across IMU types |
| AirIO 2025 [24] | 3.18 m (with EKF) and 3.85 m (network) average ATE on held-out EuRoC | The best published full-sequence number; no better than our physics fit |
| TinyOdom 2022 [28] | 31 to 110 kB networks; trained on one dataset, error rose from 1.26 m to 97 m on another | Small models are feasible in memory, fragile in generalisation |
| Cioffi et al. 2023 [30], Buchanan et al. 2023 [29] | Need thrust commands or a camera | Not applicable |
| Schöller et al. 2020 [31] | Constant velocity matches neural pedestrian predictors (abstract only) | Weak support for simple forecasting |

No paper found tests robustness to injected noise, bias drift, spikes or dropped samples.

**Synthesis.** The published learned methods do not beat a bounded physics fit on EuRoC, need hours of data from the same device, and were never exposed to this kind of corruption. A tiny network fits the budgets (a researcher's NumPy timing: 0.2 to 1.7 ms per forward pass for 45k to 480k parameters), so compute is not the obstacle. Evidence of benefit is.

---

## 10. Dataset research and data preparation

### 10.1 EuRoC MAV [5]

- 11 sequences (MH_01 to MH_05 in a machine hall, V1_01 to V2_03 in a Vicon room), ADIS16448 at 200 Hz, gyro first then accelerometer, integer nanosecond stamps.
- Durations of the IMU files we used: 85.5 s (V1_02) to 184.1 s (MH_01). Row counts 17,100 to 36,820.
- Ground truth `state_groundtruth_estimate0/data.csv`: 200 Hz position, quaternion in **w, x, y, z** order, velocity, and bias estimates. The ground truth starts 1 to 2.4 s after the IMU file.
- Gravity lies mostly along sensor +x: the sensor x axis points up.
- [MEASURED] The gyro bias is about (-0.002, 0.021, 0.077) rad/s on every sequence we checked. Timestamps step by 4,999,936 or 5,000,192 ns (a regular 5 ms grid rounded to float precision).
- [MEASURED] V1_01 is nearly at rest for its first 5 s, and the gyro mean over that interval equals the dataset's bias estimate to 0.002 rad/s. Machine Hall sequences start with the vehicle being handled.
- Ground-truth orientation is not fully trustworthy on the Vicon sequences: with it, the constant-parameter position fit diverged on V2 (12 to 26 m) while it worked on MH. OpenVINS documents the same doubt about V1_01. Our rotation-error figures on V sequences should be read with that in mind.
- Official download: ETH Research Collection, DOI 10.3929/ethz-b-000690084. Licence not verified.

### 10.2 TUM-VI [6]

- BMI160 at 200 Hz, hand-held, EuRoC-style export with the same column order.
- Full motion-capture ground truth only in room1 to room6 (120 Hz); other sequences have it at the start and end only.
- The published IMU data are already calibrated: [MEASURED] gyro bias below 0.002 rad/s on room3 and room4.
- Timestamps are **not** on an exact grid (steps of 5.00 to 5.04 ms), and the recordings start in motion. Both properties make TUM-VI a harder and more honest test of the no-rest path.
- Long sequences exist: corridor1 is 300 s, magistrale1 is 772 s (153,989 rows).

### 10.3 How we obtained data in this session

The official hosts were unreachable from the build environment. All 11 EuRoC IMU files, their ground truth, and eight TUM-VI IMU files were found committed in public GitHub repositories (ORB-SLAM3 example folders, a VINS benchmark fork, OpenVINS ground truth). **You should download the official archives** and confirm identical results; the copies were only checked for row count, rate, header and gravity magnitude.

### 10.4 Splits and leakage

- [MEASURED, limitation] The few global priors in `CFG` were chosen by sweeps over all 11 EuRoC sequences. There is no held-out EuRoC split. The sweeps were coarse (two or three values per parameter) and the result was flat (2.9 to 3.2 m across settings), so overfitting is limited, but the EuRoC numbers are in-sample.
- TUM-VI room1 to room6 were first run after the EuRoC tuning. They exposed one crash and one bad prior; two gyro-bias priors were then adjusted, so TUM-VI is not untouched either.
- [REC] If you tune further, hold out MH_02, MH_04, V1_01, V1_03, V2_02 (the test split used in [23][24]) and report those separately.
- Use several degradation seeds. With seed 42 only, the inversion hides every weakness of the cleaning code.

### 10.5 Test matrix

| # | Scenario | How to generate | Covered in this session |
|---|---|---|---|
| 1 | Clean | original file | Yes, 11 + 6 sequences |
| 2, 3, 4 | Mild, medium, severe | `--max-level 0.3 / 0.6 / 1.0` | 0.6 and 1.0 |
| 5 | Bias drift only | edit CONFIG, other terms zero | No |
| 6 | White noise only | same | No |
| 7 | Spikes | default | Yes |
| 8 | Stuck runs | default | Yes |
| 9 | Short dropouts | default (up to 0.25 s) | Yes |
| 10 | Long dropouts | `burst_len (100, 400)`, or delete 400 rows | Yes |
| 11 | Irregular timestamps | TUM-VI | Yes |
| 12 | Duplicate timestamps | default; every 97th row doubled | Yes |
| 13 | Complete failure | default; NaN tail; frozen tail | Yes |
| 14 | Different initial orientation | EuRoC (x up) and TUM-VI | Yes |
| 15 | Different motion | multirotor and hand-held | Yes |
| 16 | Different lengths | 2 rows, 50 rows, 30 s, 85 to 772 s | Yes |
| 17 | Several seeds | seed 42 and seed 7 | Two seeds only |
| 18 | Both column orders | reorder before or after degrading | Yes |

---

## 11. Mathematical state model

### 11.1 Symbols and units

| Symbol | Meaning | Unit | Frame |
|---|---|---|---|
| `p, v` | position, velocity | m, m/s | world, z up |
| `q`, `R` | body-to-world rotation | unit quaternion (w, x, y, z) | |
| `w_m, f_m` | measured angular rate and specific force | rad/s, m/s^2 | body |
| `b_g(t)` | gyro bias, piecewise linear in time | rad/s | body |
| `D` | gyro scale and misalignment correction, 3 x 3 | none | body |
| `b_a` | accelerometer bias, constant | m/s^2 | body |
| `psi(t)` | attitude error of the nominal solution, `R_nom = Exp(psi) R_true` | rad | world |
| `s(t)` | slow residual acceleration, piecewise linear | m/s^2 | world |
| `dg` | gravity magnitude correction | m/s^2 | world z |
| `G` | 9.80665 | m/s^2 | |

### 11.2 Preintegration nodes

Valid samples are grouped into nodes of 10 intervals (50 ms). For node k starting at sample i, in the body frame at the node start, with midpoint rules [10][11]:

- `dR_{j+1} = dR_j Exp((w_j + w_{j+1}) dt_j / 2)`
- `a_j = (dR_j f_j + dR_{j+1} f_{j+1}) / 2`
- `dp += dv dt_j + a_j dt_j^2 / 2`, then `dv += a_j dt_j`
- `theta += (w_j + w_{j+1}) dt_j / 2`

Each node stores its start time, duration `Dt`, `dR` (as a quaternion), `dv` [m/s], `dp` [m] and `theta` [rad]. These do not depend on the global attitude, velocity or gravity. A constant bias found during a rest start is subtracted before preintegration.

### 11.3 Nominal solution

With the current gyro corrections, the corrected increment is `dR_k Exp(-b_g(t_k) Dt_k + D theta_k)`. Then:

- `q_{k+1} = q_k dR_k`
- `v_{k+1} = v_k + R_k dv_k - g_est e_z Dt_k`
- `p_{k+1} = p_k + v_k Dt_k + R_k dp_k - g_est e_z Dt_k^2 / 2`

starting from `p_0 = v_0 = 0` and `q_0` = the rotation that takes the first specific-force vector to world +z. `g_est` is chosen so the mean vertical acceleration is zero.

### 11.4 The error of the nominal solution is linear

Let the true gyro signal be `w_nom + D w_m - db_g`. To first order the nominal attitude carries the world-frame error

`psi(t) = psi_0 + integral of R (db_g - D w_m) dt`

and the nominal specific force in the world is `R_nom f = (I + [psi]x)(G e_z + a)`, so the acceleration error is

`e(t) = R(t) b_a + psi(t) x G e_z + dg e_z + s(t)`, with `psi x G e_z = G (psi_y, -psi_x, 0)`.

The nominal position is the truth plus `p_0 + v_0 t +` the double integral of `e`. Dimensional check: `b_a` and `s` in m/s^2; `psi` in rad times `G` gives m/s^2; double integral gives m.

Every term is linear in the unknown vector

`x = (p_0, v_0, b_a, dg, psi_0x, psi_0y, db_g knots, s knots, D, gap jumps)`.

Sizes for a 180 s file: 6 + 3 + 1 + 2 + 3 x 10 + 3 x 10 + 9 + 5 per long gap = 81 plus gaps.

### 11.5 The bounded-motion MAP problem

Minimise over `x`:

`sum_rows |p_nom - A x|^2 / sig_pos^2 + sum_rows |v_nom - A' x|^2 / sig_vel^2 + sum_i (x_i - mu_i)^2 / sig_i^2`

where `A` holds, for each unknown, the position its unit value would produce (computed by cumulative sums on the nodes) and `A'` the corresponding velocity. This states that the true position and velocity are zero-mean and bounded (`sig_pos = 2 m`, `sig_vel = 1 m/s`), and everything else in the nominal solution is sensor error. Rows are taken every 20 nodes (1 Hz) and weighted as one independent observation per second. During a detected rest start, extra velocity rows with `sig = 0.2 m/s` are added.

The normal equations are at most about 180 x 180 (16 knots per model and 12 gaps). After solving, the gyro part (`db_g`, `D`, `psi_0`, gap rotations) is applied to the increments and the problem is rebuilt; three passes absorb the nonlinearity of the gyro terms. Finally the fitted `e(t)` is double-integrated and subtracted from the nominal position and velocity, and `Exp(-psi)` is applied to the attitude.

### 11.6 Priors (all in `CFG`)

| Parameter | Prior std | Reason |
|---|---|---|
| Position about its mean | 2 m | Room-scale motion; sets the trade between following the IMU and staying put |
| Velocity | 1 m/s | EuRoC mean speeds are 0.4 to 0.9 m/s |
| Accelerometer bias | 0.5 m/s^2 | EuRoC bias estimates reach 0.55 m/s^2 on one axis |
| Gyro bias knots after a rest start | 3e-4 rad/s | 5 s of rest averages the noise down to about 1e-4 |
| Gyro bias, motion bootstrap | total 0.03, knots 2e-3 rad/s | Compromise between EuRoC (0.077) and calibrated TUM-VI (below 0.002) |
| Gyro calibration terms | 0.005 | Larger values lowered ATE slightly but raised rotation drift |
| Residual acceleration knots | 0.2 m/s^2 every 20 s | |
| Gap rotation, gap velocity | 0.5 rad/s and 1.5 m/s^2 times gap length | Typical manoeuvre rates |

### 11.7 Uncertainty during dropouts

There is no recursive covariance. A dropout widens the posterior through the gap unknowns, whose prior standard deviation grows linearly with the gap length. If a filter-based fallback is built instead (ch. 15), the equivalent is to add `Q = diag((0.5 rad/s x gap)^2, (1.5 m/s^2 x gap)^2)` to the attitude and velocity covariance at each gap.

---

## 12. Quaternion and coordinate frame conventions

| Item | Choice |
|---|---|
| Algebra | Hamilton: `i j = k` |
| Storage inside the code | (w, x, y, z) |
| Output order | `qx qy qz qw` (TUM) |
| Meaning | body to world: `v_world = R(q) v_body` |
| Composition | `q_{k+1} = q_k (x) dq_k`, increment on the right because rates are in the body frame |
| Exponential | `Exp(phi) = (cos(|phi|/2), sin(|phi|/2) phi/|phi|)`, series for `|phi| < 1e-8` |
| World frame | z up, origin and heading arbitrary |
| Body frame | the IMU sensor frame, unchanged |
| Normalisation | after every cumulative product and before output |

EuRoC ground truth stores `q_RS` as (w, x, y, z), sensor to reference, which is the same meaning as ours. evo compares relative rotations, and the FAQ confirms SE(3) alignment, so the constant offset between our world frame and theirs is harmless.

**One risk [ASSUMED].** If the organisers computed their orientation error without removing the constant body-frame offset, a team that outputs world-to-body would score badly. Slide 16 says "normalized unit quaternion (world frame)", which matches the TUM convention of body-to-world. We follow it.

Unit tests (`tests/test_core.py`, all passing): Hamilton sign, rotation equals the matrix form, `R(ab) = R(a) R(b)`, a +90 degree rotation about z maps x to y, the vectorised cumulative product equals a sequential loop, tilt initialisation maps any vector to +z, preintegration of a spinning body at rest returns gravity, exact timestamp formatting, interpolation and tail behaviour.

---

## 13. Degradation detection and missing-data treatment

| Problem | Detection | Treatment | Why not something else |
|---|---|---|---|
| Failed tail | Row all zero, non-finite, or accelerometer norm below 0.05 g | Excluded from integration; pose forecast (ch. 18) | Integrating zeros means free fall at 9.8 m/s^2 |
| Stuck run | Row identical to the previous row on all six channels | Excluded; time step spans it (linear interpolation) | Holding the stale value biases the integral |
| Spike | Deviation from the mean of both neighbours above 8 robust sigmas on at least three channels, and a local maximum | Excluded | Script spikes hit all six channels at once, so the three-channel rule separates them from vibration |
| Single missing row | Time step of two periods | Trapezoid over the real time step | Exact for linear signals |
| Burst up to 0.3 s | Larger time step | Same | Measured: the default script's bursts cost nothing visible |
| Gap above 0.3 s | Node duration above `gap_s` | Five unknowns per gap: tilt jump (2) and velocity jump (3); up to 12 gaps | Rotation inside the gap is not measured; interpolating the gyro guesses it |
| Duplicate timestamp | Time not strictly increasing | Skipped in integration; the row still gets the pose of its timestamp | Deleting it breaks the row contract |
| Out-of-order rows | Same test | Same | |
| Seeded noise | Row-pattern match (ch. 6.5) | Subtracted exactly | |
| Unseeded noise, bias and scale walk | Not detected explicitly | Absorbed by the gyro-bias knots and residual-acceleration knots | Low-pass filtering the IMU before integration buys nothing: integration is already a low-pass |

**Not handled.** The heading change inside a long gap is unobservable; the prior sets it to the interpolated value. On V2_02 with two 2 s gaps the gap model cut ATE from 4.72 to 2.48 m but rotation RMSE stayed at 77 degrees.

Spike detection has false positives on real vibration (150 of 28,000 rows on V1_01). They cost nothing measurable because an excluded row is interpolated from its neighbours.

---

## 14. Algorithm comparison

| Method | State and model | Cost | Verdict for this task |
|---|---|---|---|
| Plain strapdown, any integrator | p, v, q | O(n) | Diverges: tens of km. Baseline only |
| Higher-order integration (RK4, coning) | same | O(n) | Integration error is not the problem |
| Complementary, Mahony, Madgwick, VQF | q, gyro bias | O(n) | Attitude only. Our ceiling test shows perfect attitude gains 0.2 m |
| EKF or error-state EKF, forward only | 15 states | O(n) with 15 x 15 matrices per sample; about 30 to 60 microseconds per sample in NumPy against a budget of 100 | No measurements, so it only propagates. Needs the same pseudo-measurements we use, and then it is a slower way to solve the same least squares |
| Invariant EKF | SE_2(3) plus biases | same | Better linearisation; same missing information |
| Unscented KF | 15 states, 31 sigma points | 30 times the EKF cost | Over the time budget in Python; no information gain |
| ESKF plus RTS smoother | 15 states, stored covariances | n x 15 x 15 x 8 bytes = 66 MB at 36k samples unless decimated | Equivalent to our batch solve when given the same priors; the fallback architecture runs it on nodes |
| Factor graph with preintegration, Gauss-Newton or LM | node states and biases | sparse solve; GTSAM is not Python-only | Our problem is this graph with the node states eliminated analytically |
| **Batch linear drift fit on nodes (chosen)** | 81 to about 180 unknowns | one small dense solve, 3 passes | 1.1 to 1.6 ms per second of data, 3 MB |
| Robust losses (Huber) | | | Used in the bias bootstrap, where vehicle acceleration is heavy-tailed noise |
| Adaptive covariance | | | Not needed: the severity ramp is absorbed by knots |
| Learned velocity or displacement regression | CNN, TCN, GRU, transformer | fits the budgets | No evidence of gain; leakage and generalisation risk (ch. 9.3, ch. 15) |

---

## 15. Architecture candidates and decision matrix

**A. Physics batch estimator** (this plan). **B. Learned inertial odometry**: a small TCN regressing velocity or displacement, trained on EuRoC and TUM-VI. **C. Hybrid**: A plus a learned prior (velocity pseudo-measurements or a gyro denoiser). **D. Error-state filter with RTS smoothing** on the same nodes and the same pseudo-measurements.

| Criterion | A physics batch | B learned | C hybrid | D filter + smoother |
|---|---|---|---|---|
| ATE | 3.09 m measured | 3.2 to 5.0 m published on held-out EuRoC | Unknown; bounded by the 2.92 m ceiling unless the network supplies low-frequency position | Same as A in theory |
| RPE | 0.38 m per 1 s measured | AirIMU reports 0.05 m at 1 s on clean data | Possible gain here | Same as A |
| Blind 5 s | Hold: 0.8 to 1.3 m RMSE | Unknown | Better hand-over velocity could reach the 1.34 m oracle | Same as A |
| Dropouts | Gap jumps, measured | Untested in any paper | As A | Needs covariance inflation |
| Memory | 3.1 MB measured | About 3 MB estimated | A plus weights | Higher (stored covariances) |
| Runtime | 1.1 to 1.6 ms/s measured | 0.2 to 2 ms per window estimated | Sum | 5 to 10 times A |
| Complexity | Done | Training pipeline, data loaders, weight packing in 6 days | Highest | Moderate |
| Generalisation | Same code on multirotor and hand-held; 30% better than constant on TUM-VI | Papers report failure across devices | Depends on B | As A |
| Reproducibility | Deterministic | Deterministic at inference | | Deterministic |
| Rule risk | None beyond the disclosed inversion | Training on the public test sequences is a leakage question | Same | None |

**Decision.** Primary: **A**. Fallback: **D** on the same nodes, only if a reviewer finds the batch fit unstable on data we have not seen. Minimum viable baseline: A with `use_seed_inversion`, `gyro_knot_s`, `acc_knot_s` and `sig_gyro_cal` all switched off, which is 30 unknowns.

**Why A wins.** It is at the measured ceiling, uses a tenth of the time budget and under half the memory budget, and exists.

**What would change the decision.** A learned velocity prior that, trained without the evaluation sequences, lowers held-out EuRoC ATE below 2.7 m and survives the degradation script. That is the experiment to run after the deadline, not before it.

**Essential components.** Preintegration nodes, the linear drift fit with position and velocity priors, rest-start bias, row-timestamp pose lookup, tail detection, gap jumps.
**Avoid.** Per-sample Kalman updates in Python, pandas (import alone exceeds the heap budget), low-pass filtering the raw IMU, constant-velocity extrapolation in the blind window, any lookup keyed on timestamps.

### 15.1 Council verdict

A three-seat council (first-principles, tail-risk, shipping) deliberated on the measured facts in quick mode: one independent round, then one counterfactual challenge to the consensus. The coordinator wrote the synthesis because of the usage limit; no separate chairman was run.

- All three independently chose A, hardened, and rejected B and C as centrepieces. Shared reason: the ground-truth-attitude ceiling shows the missing information is not something a network can supply.
- All three said to ship the seed inversion **enabled, as insurance**, documented, with the organisers informed. Two said not to wait for a reply.
- The counterfactual round asked how this plan loses. Answer: not through a small accuracy gap but through an unseen systematic failure, such as non-EuRoC data, a misdetected unit, or a crash. It asked for adversarial fixtures and a guard against divergence.
- That prediction was confirmed the same hour. The first run on TUM-VI crashed in the bias bootstrap on room1 and produced 100-degree rotation errors on room2 and room3. Both are fixed (ch. 24), and the edge-case suite was extended.

### 15.2 Ideas considered in brainstorming

| Idea | Outcome |
|---|---|
| Replay the fixed seed and subtract the noise | Built; ch. 6.5 |
| Treat drift as a parametric curve and fit it, instead of filtering | Built; this is the estimator |
| Give each dropout its own jump unknowns | Built; largest single gain on long gaps |
| Self-calibrate the gyro inside the batch | Built with a tight prior |
| Detect rest anywhere in the file, not only at the start | Not built. A hovering multirotor looks like rest; needs a vibration test |
| Fit level and gamma of the ramp from the drop pattern when the seed matches but the ramp does not | Not built. Each dropped or kept row bounds the severity at that time, so two parameters are identifiable. About half a day |
| Choose the knot spacing per file by cross-validation | Not built. ATE was flat between 10 and 80 s spacing |
| Shrink toward the constant trajectory when the fit looks unreliable | Not built as an explicit guard. The position prior already does this continuously; the hard fallback covers failures |
| Learned velocity prior | Rejected for this deadline; ch. 15 |
| Output the constant trajectory | Rejected: 3.45 m, loses RPE, and exactly constant output crashes evo's alignment |

---

## 16. Recommended primary architecture

```
imu0/data.csv
   |
   |  pass 0  scan_timestamps        first column -> ts[n], time unit, column order, units
   |          SeedInversion(ts)      predict drop/duplicate pattern; ok only on exact match
   |
   |  pass 1  preintegrate_file      2048-row chunks:
   |             parse_values -> [inv.apply] -> validity (dead, stuck, spike, order)
   |             -> static_start_bias (first chunk) -> preintegrate_group -> nodes
   |
   |          solve_nodes            bootstrap_gyro_bias (only if no rest start)
   |                                 3 x { nominal -> build A, A' -> solve -> feed back gyro part }
   |                                 subtract fitted drift -> q, p, v at node boundaries
   |
   |  pass 2  write_trajectory       per chunk of ts: poses_at -> format -> write
   v
estimated_trajectory.txt
```

Heap is proportional to the number of nodes, not rows. Above 40,000 rows the node length grows so the node count stays near 4,000.

---

## 17. Detailed end-to-end pipeline

1. **Header and layout.** If the first field of the first line is not a number, it is a header. Integer or float timestamps are detected from the first data line.
2. **Timestamps.** All first-column values are kept (8 bytes per row). The time unit follows the median positive step, the same rule the organiser script uses.
3. **Column and unit detection** from the first 2,048 rows (ch. 6.1). Every 16th row of the whole file contributes to the median norm of columns 1 to 3, which the inversion needs to reproduce the script's unit guess.
4. **Seed check** (ch. 6.5). On success, six generators are positioned at the start of the six noise arrays and replayed chunk by chunk, including rows that were dropped, so the random walks stay in step.
5. **Chunk loop.** Convert to canonical order and units; remove seeded noise if verified; mark dead, stuck and spike rows using two rows of context from the previous chunk and holding the newest row back until its right neighbour arrives; drop rows whose time does not increase.
6. **Rest start.** On the first chunk, 0.5 s window means of gyro and accelerometer are compared with the running reference; rest lasts while they stay within 0.01 rad/s and 0.15 m/s^2. At least 1 s of rest gives the gyro bias (mean rate) and the initial gravity direction.
7. **Preintegration** of every 10 valid intervals; leftover rows carry to the next chunk; the last partial node is closed at end of file.
8. **Bias bootstrap** if there was no rest: in the gyro-integrated frame the gravity vector rotates at `R db`, so consecutive window means satisfy `F_{k+1} - F_k = (sum R Dt db) x F_k`. Solved with 1, 4 and 16 s windows, Huber weights, and a Gaussian prior on the total bias.
9. **Joint fit** (ch. 11.5), three passes.
10. **Pose per row.** Cubic Hermite interpolation of position using node velocities; normalised linear interpolation of quaternions (node rotations are below 0.1 rad). After the last node: ch. 18.
11. **Write** with exact integer arithmetic for the timestamp (`ns // 1e9 . ns % 1e9`, nine decimals), six decimals for position, nine for the quaternion.
12. **Failure handling.** Any exception or non-finite value in steps 4 to 9 switches to a fallback trajectory (a 1 mm helix, identity attitude) so the file is always valid and never exactly constant.

---

## 18. Five-second dead-reckoning strategy

### 18.1 What the data say [MEASURED]

**Oracle test.** At 360 hand-over times across the 11 EuRoC ground-truth files, forecast 5 s ahead from the **true** position and **true** velocity with `p(h) = p_f + v_f tau (1 - exp(-h / tau))`:

| Decay constant tau | RMSE over 5 s | Error at 5 s | Error at 1 s | Error at 0.5 s |
|---|---|---|---|---|
| 0 (hold position) | 1.66 m | 2.58 m | 0.70 m | 0.36 m |
| 0.5 s | 1.50 m | 2.44 m | 0.46 m | 0.16 m |
| 1 s | 1.40 m | 2.35 m | 0.37 m | 0.12 m |
| 2 s | 1.34 m | 2.30 m | 0.33 m | 0.11 m |
| 4 s | 1.39 m | 2.45 m | 0.32 m | 0.10 m |
| infinite (constant velocity) | 1.73 m | 3.28 m | 0.33 m | 0.10 m |

- Constant velocity is the worst choice over 5 s even with perfect velocity.
- The best possible gain from a perfect velocity is 20% (1.34 against 1.66 m).
- Velocity information is worth a lot up to 1 s and little after 2 s.

**With our estimated velocity** (degraded EuRoC, inversion on, earlier estimator version): hold gave 1.26 m RMSE over the blind window; tau of 0.3, 0.7, 1.5 and 3.0 s gave 1.55, 1.89, 2.37 and 2.86 m. The velocity at the edge of the batch is wrong by more than the motion it would predict.

**Attitude.** Holding the last attitude gave 7.3 degrees error at 5 s; continuing the last body rate with decay constants 0.3, 1, 3 s gave 8.4, 13.2, 23.8 degrees.

### 18.2 Strategy [REC]

- **Position:** damped velocity with `blind_tau_s = 0.15 s`. This is hold-position with a smooth 2 cm hand-over.
- **Attitude:** hold.
- **Hand-over point:** the last valid sample, found from the data, not assumed to be 5.0 s before the end.

### 18.3 Why not more

Acceleration extrapolation is worse than velocity extrapolation by the same argument. A learned forecaster would need the hand-over velocity that we cannot estimate. EuRoC sequences end with a landing, so true travel in the last 5 s is only 0.08 to 1.94 m; on the real ends, hold is close to optimal anyway.

### 18.4 The experiment that could improve it

Improve the hand-over velocity. Candidates: weight the velocity prior more strongly in the last 10 s; add a rest detector for the end of the file. Gate: adopt a non-zero tau only if blind-window RMSE on held-out sequences drops below the hold result on at least 8 of 11 sequences.

### 18.5 Interaction of rotation and translation

During the sensed part, a tilt error of `theta` leaks `G theta` into horizontal acceleration, so attitude and position errors are coupled and the fit estimates them together. In the blind window there is no accelerometer, so the coupling disappears: attitude error no longer feeds position. That is another reason hold-and-hold is hard to beat.

---

## 19. Python function specifications

All in `src/main.py` unless noted. Arrays are float64 unless stated. n = rows, K = nodes.

| Function | Signature | Purpose and maths | Validation and errors | Cost |
|---|---|---|---|---|
| `quat_mul` | `(a[...,4], b[...,4]) -> [...,4]` | Hamilton product | none | O(n) |
| `quat_exp` | `(rv[n,3]) -> q[n,4]` | Rotation vector to quaternion, series below 1e-8 rad | none | O(n) |
| `quat_rotate` | `(q[n,4], v[n,3]) -> [n,3]` | `v + w t + u x t`, `t = 2 u x v` | none | O(n) |
| `quat_cumprod` | `(dq[n,4], block=256) -> [n,4]` | Prefix product: vectorised inside blocks, short loop across blocks | renormalises | O(n) |
| `knot_basis` | `(t[K], T, nk) -> [K,nk]` | Piecewise-linear hat functions; `nk = 1` is a constant | clips time to [0, T] | O(K nk) |
| `tilt_from_gravity` | `(f[3]) -> q[4]` | Rotation taking f to +z about `f x z` | handles f parallel or anti-parallel to z | O(1) |
| `parse_values` | `(lines) -> [c,6]` | Fast text parse; falls back to `np.loadtxt` on irregular rows | shape check | O(c) |
| `scan_timestamps` | `(path) -> (ts[n], info)` | Pass 0 (ch. 17 steps 1 to 3) | raises `ValueError` below two rows | O(n) |
| `preintegrate_group` | `(t[k,m+1], g[k,m+1,3], a[k,m+1,3]) -> dq, dv, dp, th` | Ch. 11.2 | none | O(k m) |
| `static_start_bias` | `(t, g, a) -> (bias, f_mean, seconds) or None` | Ch. 17 step 6 | needs four windows | O(first chunk) |
| `preintegrate_file` | `(path, ts, info, cfg, inv) -> t0, dt, dq, dv, dp, th, f_init, static` | Pass 1 | raises `ValueError` if no usable sample | O(n) |
| `cumint` | `(e[K,3] or [K], dt[K]) -> vel[K+1], pos[K+1]` | Exact integrals of node-wise constant acceleration | none | O(K) |
| `bootstrap_gyro_bias` | `(t0, dt, dq, dv, sig_prior) -> b[3]` | Ch. 17 step 8 | skips windows longer than T/4 | O(K) x 3 |
| `solve_nodes` | `(t0, dt, dq, dv, dp, th, f_init, static, cfg) -> tn[K+1], q, p, v` | Ch. 11.3 to 11.5 | short files (below 30 s) use constant terms only | O(K P) + O(P^3), P up to about 180 |
| `poses_at` | `(t[c], tn, q, p, v, cfg) -> P[c,3], Q[c,4]` | Hermite and nlerp inside, damped hold after, clamp before | any order, duplicates allowed | O(c log K) |
| `format_timestamps` | `(ts[c], scale) -> list[str]` | Exact integer division for integer ticks | | O(c) |
| `write_trajectory` | `(path, ts, info, sol, cfg)` | Pass 2 in chunks | | O(n) |
| `fallback_solution` | `(ts, info) -> sol` | 1 mm helix | | O(1) |
| `solve_file` | `(path, cfg) -> ts, info, sol` | Orchestration with exception fallback | catches everything after pass 0 | |
| `estimate` | `(path, cfg) -> ts, P, Q, info` | Test helper that materialises all poses | not used by `main` | |
| `SeedInversion.__init__` (`seed_inversion.py`) | `(ts, info)` | Ch. 6.5 verification; sets `.ok`, `.status` | refuses float stamps, irregular grids, fewer than 20 confirming rows, more than 400,000 rows | O(n) |
| `SeedInversion.apply` | `(row0, gyro[c,3], acc[c,3], dead[c]) -> stuck[c]` | In-place noise removal for one chunk | leaves dead rows untouched | O(c) |

Functions named in the brief that are deliberately absent: a separate `normalize_sensor_units`, `convert_timestamps`, `detect_dropout_regions`, `propagate_covariance`, `perform_filter_update`, `estimate_forecast_uncertainty`, `blend_failure_transition`. Their work is done inside the functions above or is not needed by a batch solve.

Evaluation tools (`tools/`): `bench.py` (`metrics`, `umeyama`, `associate`, `run`), `suite.py`, `final_table.py`, `edge_tests.py`, `perf.py`, `oracle.py`, `reorder.py`.

---

## 20. Pseudocode and data flow

```
solve_file(path):
    ts, info = scan_timestamps(path)
    inv = SeedInversion(ts, info) if integer stamps else None
    if inv and not inv.ok: inv = None
    try:
        nodes = preintegrate_file(path, ts, info, cfg, inv)
        sol   = solve_nodes(*nodes, cfg)
        assert all finite
    except: sol = fallback_solution(ts, info)
    return ts, info, sol

preintegrate_file:
    carry = empty; context = empty
    for chunk in file (2048 rows):
        x = canonical(chunk)                      # gyro rad/s, accel m/s^2
        bad = all-zero rows
        if inv: bad |= inv.apply(row0, x.gyro, x.acc, bad)
        W = context + x                           # context: 2 finished rows + 1 pending
        valid = ~bad & ~dead & ~same_as_previous & ~spike & time_increasing
        if first valid rows: b0, f_init, rest = static_start_bias(...) or (0, mean accel, 0)
        carry += valid rows (gyro - b0)
        while carry has >= 11 rows: emit node(preintegrate_group(next 11 rows)); keep the 11th
    emit last partial node

solve_nodes:
    b = 0 if rest else bootstrap_gyro_bias(...)
    repeat 3 times:
        dq_c  = dq * Exp(-(b + Bg cb) Dt + theta D^T [+ gap rotations])
        q     = q0 * cumprod(dq_c)
        v_nom, p_nom = cumulative sums of R dv, R dp with gravity removed
        A, A' = columns for p0, v0, b_a, dg, psi0, gyro knots, D, acc knots, gap jumps
        x     = solve(A^T W A + A'^T W' A' + priors)
        feed back: cb += db; D += dD; q0 = Exp(-psi0) q0; gap rotations
    e(t) = R b_a + G(psi_y, -psi_x, 0) + dg e_z + s(t)
    return q = Exp(-psi) q,  p = p_nom - double integral(e) - v0 t - p0 - gap ramps,  v likewise

write_trajectory:
    for chunk of ts: P, Q = poses_at((ts - ts0) * scale, sol); write lines
```

Input and output files:

```
imu0/data.csv                                   estimated_trajectory.txt
#timestamp [ns],w_x,w_y,w_z,a_x,a_y,a_z         # timestamp tx ty tz qx qy qz qw
1403715273262142976,-0.0021,0.0175,0.0775,...   1403715273.262142976 0.628254 0.909744 0.067416 -0.001042085 -0.823317447 0.017618059 0.567306706
```

---

## 21. Experimental design and benchmark protocol

### 21.1 Metrics in our harness (`tools/bench.py`)

- **ATE RMSE** after SE(3) Umeyama on all matched pairs, nearest-timestamp association within 0.01 s (evo's default).
- **Constant baseline**: RMS distance of the ground truth from its own centroid.
- **Blind ATE**: the same aligned errors restricted to the last 5 s.
- **Blind dead-reckoning error**: displacement from the hand-over pose, estimate against truth, as RMSE over the window and at its end.
- **RPE over 1 s**: translation [m] and rotation [deg].
- **Rotation RMSE** after removing the constant frame offset at the first pose.
- **Runtime** per second of IMU and **peak traced heap**.

Cross-check with evo 1.38.1 on V1_02 degraded: `evo_ape tum gt.txt est.txt -a` printed rmse 1.022202; our harness 1.022201.

### 21.2 Results on EuRoC [MEASURED, final code]

| Scenario | ATE | Blind ATE | Blind DR RMSE | RPE 1 s | Rot RMSE | Worst sequence ATE |
|---|---|---|---|---|---|---|
| Constant baseline | 3.45 m | | | | | 6.88 m |
| Clean | 3.09 m | 3.10 m | 0.84 m | 0.379 m, 0.08 deg | 11.4 deg | 6.56 m |
| Degraded, accel-first, inversion on | 3.14 m | 2.67 m | 1.02 m | 0.442 m, 0.77 deg | 9.9 deg | 6.63 m |
| Degraded, accel-first, inversion off | 3.17 m | 3.23 m | 1.26 m | 0.458 m, 0.78 deg | 11.3 deg | 6.61 m |
| Degraded, raw order, inversion on | 3.14 m | 2.70 m | 1.03 m | 0.442 m, 0.77 deg | 9.9 deg | 6.63 m |
| Degraded, raw order, inversion off | 3.74 m | 4.10 m | 2.55 m | 0.828 m, 1.97 deg | 54.2 deg | 7.02 m |
| Seed 7, bursts up to 2 s, gap model on | 3.27 m | 3.20 m | 1.05 m | 0.640 m, 2.82 deg | 26.6 deg | 6.70 m |
| Same, gap model off | 4.29 m | 4.27 m | 1.94 m | 1.133 m, 3.49 deg | 57.9 deg | 7.41 m |

The rotation RPE of 0.77 deg in degraded runs comes from holding attitude through the blind 5 s.

Per sequence (clean, and degraded accel-first with inversion):

| Sequence | Length | Constant | Clean ATE | Degraded ATE | Blind ATE | True travel in last 5 s |
|---|---|---|---|---|---|---|
| MH_01_easy | 184 s | 4.31 | 4.18 | 4.22 | 4.95 | 1.30 m |
| MH_02_easy | 152 s | 4.65 | 4.45 | 4.48 | 6.04 | 0.85 m |
| MH_03_medium | 135 s | 3.58 | 2.83 | 2.84 | 1.87 | 0.44 m |
| MH_04_difficult | 102 s | 6.82 | 6.52 | 6.47 | 4.70 | 0.50 m |
| MH_05_difficult | 114 s | 6.88 | 6.56 | 6.63 | 3.60 | 1.94 m |
| V1_01_easy | 146 s | 1.85 | 1.62 | 1.57 | 1.01 | 0.39 m |
| V1_02_medium | 86 s | 1.78 | 1.00 | 1.02 | 0.57 | 1.11 m |
| V1_03_difficult | 108 s | 1.57 | 1.34 | 1.48 | 1.54 | 0.44 m |
| V2_01_easy | 114 s | 2.30 | 2.27 | 2.41 | 1.15 | 0.08 m |
| V2_02_medium | 117 s | 2.11 | 1.63 | 1.65 | 2.12 | 0.37 m |
| V2_03_difficult | 117 s | 2.06 | 1.57 | 1.74 | 1.82 | 0.75 m |

We beat the constant baseline on 11 of 11 clean and 10 of 11 degraded (V2_01: 2.41 against 2.30). The margin is small on the Machine Hall sequences, where the vehicle travels far and slowly.

Two 2 s gaps cut from the clean file at 40% and 75%:

| Sequence | Constant | No gaps | Gaps, model off | Gaps, model on |
|---|---|---|---|---|
| V1_02 | 1.77 | 1.00 | 4.13 | 1.47 |
| MH_03 | 3.61 | 2.83 | 4.97 | 3.14 |
| V2_02 | 2.13 | 1.63 | 4.72 | 2.48 |

### 21.3 Results on TUM-VI rooms [MEASURED]

| Sequence | Constant | ATE | RPE 1 s | Rot RMSE |
|---|---|---|---|---|
| room1 | 1.00 | 0.48 | 0.127 m | 42 deg |
| room2 | 1.22 | 1.29 | 0.666 m | 120 deg |
| room3 | 1.25 | 0.96 | 0.585 m | 3 deg |
| room4 | 1.08 | 0.66 | 0.147 m | 2 deg |
| room5 | 0.93 | 0.47 | 0.112 m | 18 deg |
| room6 | 0.99 | 0.64 | 0.221 m | 48 deg |
| Mean | 1.08 | 0.75 | 0.310 m | 39 deg |

No rest start exists here, so the gyro bias along gravity is set by the prior and heading drifts. room2 loses to the constant baseline.

### 21.4 Reproducing the organisers' evaluation

Verified against evo 1.38.1 on this machine:

```
evo_ape tum gt.txt estimated_trajectory.txt -a                     # ATE, SE(3) Umeyama, translation part
evo_rpe tum gt.txt estimated_trajectory.txt -a                     # RPE, default delta = 1 frame
evo_rpe tum gt.txt estimated_trajectory.txt -a --delta 1 --delta_unit m
evo_rpe tum gt.txt estimated_trajectory.txt -a --pose_relation angle_deg --delta 1 --delta_unit m
evo_ape tum gt.txt estimated_trajectory.txt -a --t_start <unix seconds of hand-over>   # blind window, global alignment
```

- `--delta_unit` accepts `f`, `d`, `r`, `m` only; there is no seconds unit.
- `--t_start` and `--t_end` exist on both commands in 1.38.1 and crop the reference before association.
- `-s` adds scale correction; the FAQ says SE(3), so do not use it.
- With the default one-frame delta at 200 Hz, RPE is tiny for any smooth output (we measured 0.0015 m) and mostly measures jitter. [ASSUMED] The organisers' delta is unknown.
- EuRoC ground truth to TUM: write `t_ns / 1e9, p, qx, qy, qz, qw` from columns 0, 1 to 3, and 5, 6, 7, 4. `evo_traj euroc data.csv --save_as_tum` does the same according to the evo documentation; we did not run that command.

### 21.5 Experiment log format

One JSON line per run: dataset, sequence, degradation file hash, seed, `CFG` overrides, git commit, every metric in 21.1, and the `info` dictionary. `tools/final_table.py` writes `out/final_table.json` in this form.

---

## 22. Accuracy optimisation and ablation study

All EuRoC mean ATE unless stated. Rows marked (v1) were measured on the earlier whole-array version of the estimator, whose results differ from the final streaming version by a few centimetres.

| Component | Without | With | Other effect |
|---|---|---|---|
| Any drift model at all (ground-truth initial state and biases, open loop) | 38 m after 20 s on V1_01 | | |
| Bounded fit, constant terms only (v1) | | 3.18 m | Rot 20 to 30 deg |
| Residual-acceleration knots, 80 / 40 / 20 / 10 s (v1) | 3.18 | 2.94 / 2.95 / 3.01 / 3.14 | Shorter knots: better blind window and rotation |
| Gyro-bias knots, degraded without inversion (v1) | 3.87 | 3.32 to 3.34 (60 s residual knots) | Rot 45 to 36 deg |
| Gyro calibration prior 0 / 0.005 / 0.01 / 0.03 (v1) | 3.07 | 2.94 / 2.90 / 2.88 | RPE rotation 0.06 / 0.07 / 0.13 / 0.33 deg: larger values overfit |
| Velocity prior 1 m/s (v1, degraded) | 3.20 | 3.17 | Blind ATE 4.50 to 4.17 |
| Rest-start zero-velocity rows | 3.095 | 3.094 | Neutral |
| Fit rows every 10 / 20 / 40 / 80 nodes | 3.151 / 3.146 / 3.148 / 3.223 | | 20 chosen: half the memory, same accuracy |
| Forcing the no-rest path on EuRoC | 3.09 | 3.20 | Rot 11 to 62 deg: the yaw-axis bias is unobservable |
| Seed inversion | ch. 6.5 | | |
| Gap jumps | ch. 21.2 | | |
| Blind decay constant | ch. 18.1 | | |

**Sensitivity summary.** ATE moves by less than 0.3 m across every reasonable setting. Rotation and the blind window are the sensitive outputs.

**Priorities for further tuning** [REC], in order: (1) hand-over velocity for the blind window, (2) the no-rest heading problem, (3) `sig_pos` and `sig_vel` on held-out sequences. Do not spend time on integration order, float32, or knot spacing.

**Not done.** Leave-one-sequence-out tuning; more than two seeds; isolated single-degradation runs; any learned baseline; numerical-precision study.

---

## 23. Memory and runtime optimisation

### 23.1 Measured [MEASURED, Python 3.13, NumPy 2.5.3, one core of the build machine]

| File | Rows | Length | Compute time | Per second of IMU | Peak traced heap |
|---|---|---|---|---|---|
| V1_02 degraded | 16,624 | 86 s | 0.12 s | 1.4 ms | 2.1 MB |
| MH_01 degraded | 35,629 | 184 s | 0.26 s | 1.4 ms | 3.1 MB |
| MH_01 clean | 36,820 | 184 s | 0.30 s | 1.6 ms | 3.2 MB |
| TUM-VI corridor1 | 59,721 | 300 s | 0.43 s | 1.4 ms | 4.2 MB |
| TUM-VI magistrale1 | 153,989 | 772 s | 0.92 s | 1.2 ms | 7.1 MB |

Whole process including interpreter start and NumPy import, MH_01: 0.37 s wall, 2.0 ms per second of IMU. Budget: 20 ms.

Heap by stage on MH_01 before the last optimisations: timestamps 1.2 MB, seed check 3.9 MB peak, preintegration 4.7 MB peak, solve 6.9 MB peak, writing 4.0 MB peak. After them the overall peak is 3.1 MB.

### 23.2 Memory budget for a 37,000-row file

| Item | Size |
|---|---|
| Timestamps, int64 | 0.30 MB |
| Seed inversion: index int32, severity and step float32, stuck mask | 0.48 MB |
| Nodes: 3,700 x (2 + 4 + 3 + 3 + 3) x 8 bytes | 0.44 MB |
| One chunk: 2,048 x 7 text fields, parsed and converted | about 0.5 MB transient |
| Fit matrices `A`, `A'`: 190 rows x 3 x 81 x 8 bytes, each | 0.37 MB x 2 |
| Knot bases, float32 | 0.30 MB |
| Node states q, p, v and scratch | about 0.5 MB |
| NumPy submodules imported lazily (`random`, `linalg`) | about 0.8 MB |

### 23.3 What made the difference

| Change | Effect |
|---|---|
| Whole-array version with `np.loadtxt` and full-rate bases | 50 MB peak |
| Streaming in chunks, solving on nodes | 5.1 MB |
| Fit rows every 20 nodes, in-place scaling of `A`, float32 bases, int32 index | 3.1 MB |
| Cap on knots and fit rows, node length grows above 40,000 rows | 772 s file: 37.9 MB to 7.1 MB |

Writing 36,000 formatted lines at once would allocate about 8 MB of Python floats; output is formatted per chunk.

### 23.4 How the limit might be measured [ASSUMED]

The FAQ says "algorithm / heap level", not which tool. `tracemalloc` traces Python objects and NumPy array buffers [36]; `resource.getrusage` reports process RSS, which for any NumPy program is tens of MB. If the organisers use RSS, every Python team fails equally and the FAQ answer would be meaningless, so we assume a heap tracer. Our margin is 2.5 times.

### 23.5 Runtime measurement plan

- Time `solve_file` plus `write_trajectory` with `time.perf_counter`, five repeats, report the median.
- Also time the whole process from the shell.
- Pin threads: `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` are set to 1 before NumPy is imported. Verify with `taskset -c 0 python main.py ...`.
- Fill `metadata.json` with measured values, machine, Python and NumPy versions.

### 23.6 Dependencies

NumPy only. pandas and SciPy are not imported. `np.fromstring(text, sep=",")` is used for speed with a fallback to `np.loadtxt`; if a future NumPy removes the text mode, the fallback still works. Test on the oldest NumPy you expect (1.26) before submitting; we ran only 2.5.3.

---

## 24. Failure-mode analysis

Severity: 1 = lose most of the score, 3 = minor.

| # | Failure | Why | Detection | Mitigation | Measured impact | Test | Sev |
|---|---|---|---|---|---|---|---|
| 1 | Wrong triad taken as accelerometer | Slides and script disagree | Median-norm test | Gravity-based detection | Without it: total failure | `accel_first`, `no_header` | 1 |
| 2 | Output row count differs | Dropping duplicates or bad rows | Count check | Pose from timestamp for every row | Disqualification | all 16 edge cases | 1 |
| 3 | Crash on unseen data | Untested path | Exception | Try/except to fallback helix | Found one on TUM-VI room1 (index out of range in the bootstrap); fixed | `tumvi` suite | 1 |
| 4 | Exactly constant output | Fallback | | 1 mm helix | evo raises "Degenerate covariance rank" on constant input | `all_zero` | 1 |
| 5 | Integrating the zero tail | Zeros read as free fall | Dead-row rule | Tail excluded | Kilometres | `zeros_tail`, `nan_tail`, `const_tail` | 1 |
| 6 | Unknown initial orientation | Gravity along sensor x on EuRoC | | Initial tilt from gravity, refined in the fit | None | EuRoC and TUM-VI | 1 |
| 7 | Large accelerometer bias | 0.55 m/s^2 on V1_01 | | Body-frame bias unknown with 0.5 prior | Absorbed | EuRoC | 2 |
| 8 | Gyro bias, rest start present | 0.077 rad/s | Rest detector | Mean rate at rest | Rot 11 deg | EuRoC | 1 |
| 9 | Gyro bias, no rest | Yaw-axis bias unobservable | `static_start_s = 0` | Gravity-transport bootstrap with prior | ATE 3.20 against 3.09; rot 62 deg | forced no-rest; TUM-VI | 2 |
| 10 | Bias prior wrong for the device | First TUM-VI run put 0.05 rad/s on the yaw axis of a calibrated IMU | Rot 100 deg | Prior 0.03 total, 0.002 on knots | TUM-VI ATE 1.03 to 0.75 | `tumvi` suite | 2 |
| 11 | Noise level changes during the file | Severity ramp | | Knots; inversion | 3.09 to 3.17 | degraded suite | 3 |
| 12 | Short dropouts | Up to 0.25 s | Time step | Trapezoid over the gap | None visible | degraded suite | 3 |
| 13 | Long dropouts | Rotation unmeasured | Node duration | Gap jumps | 4.1 to 5.0 m down to 1.5 to 3.1 m | `gap2`, seed 7 | 2 |
| 14 | Duplicate timestamps | Script | Non-increasing time | Skip in integration, same pose out | None | `dup_rows` | 2 |
| 15 | Rows out of order | Not in script | Same | Same | None | `swapped_rows` | 3 |
| 16 | Stuck values | Script | Equality with previous row | Excluded | None visible | degraded suite | 3 |
| 17 | Spikes during manoeuvres | Up to 9 m/s^2 | Three-channel outlier test | Excluded | None visible; 0.5% false positives | degraded suite | 3 |
| 18 | Tail invalid but not zero | FAQ says "unusable/invalid" | Non-finite, constant, or below 0.05 g | Covered for those three | Random noise in the tail would not be detected | add a test with noise if organisers confirm | 2 |
| 19 | Very short file | Below 30 s | | Constant terms only; below 7 s no failure exists | Valid output | `two_rows`, `short_50` | 3 |
| 20 | Very long file | Heap grows | Row count | Longer nodes, capped knots | 7.1 MB at 772 s | `perf` | 2 |
| 21 | Start in motion | TUM-VI, MH | Rest detector fails | Bootstrap | See 9 | `moving_start` | 2 |
| 22 | Aggressive rotation | Nlerp and first-order bias terms | | 50 ms nodes | V1_03, V2_03 fine | EuRoC difficult | 3 |
| 23 | Unfamiliar motion (real aeroplane) | Bounded-motion prior is wrong for sustained flight | Output stays in a few-metre box | Raise `sig_pos`, `sig_vel` | Untested | none available | 2 |
| 24 | Gyro in degrees not detected | Threshold on the 99th percentile | | Threshold 8 rad/s | Was missed at 30; fixed | `gyro_deg` | 3 |
| 25 | Quaternion not unit | Interpolation | Norm check in tests | Normalise before output | None | all cases | 3 |
| 26 | Timestamp precision | Float formatting of 1.4e9 s | | Integer formatting, nine decimals | Exact | unit test | 2 |
| 27 | Seed check passes wrongly | Chance match | Needs 20 confirming rows; hundreds in practice | | Not observed | seed 7, other ramp | 3 |
| 28 | Seed check right, units wrong | Script's unit guess keyed on a median near 0.5 or 2.0 | V1_02 median is 0.54 | We reproduce the rule on the degraded file's median | Correct on all tested files; a borderline file could flip | add a roughness check | 3 |
| 29 | Memory over budget | Different tracer | | 2.5 times margin | | `perf` | 2 |
| 30 | Runtime over budget | Slow evaluator | | 10 times margin | | `perf` | 3 |

---

## 25. Implementation roadmap and acceptance gates

The reference implementation exists. The remaining six days go to verification on your side, the questions to the organisers, and the deliverables.

| Day | Work | Gate to pass |
|---|---|---|
| 17 Nov | Send the organiser email (ch. 27). Download official EuRoC and TUM-VI room archives. Run `tests/test_core.py`, `tools/edge_tests.py`, `tools/final_table.py` | 9 of 9 unit tests; 16 of 16 edge cases; EuRoC mean ATE within 0.05 m of 3.09 (clean) and 3.14 (degraded) |
| 18 Nov | Run with NumPy 1.26 and your target Python. Measure heap and time on your machine. Generate three more seeds per sequence | Peak heap below 4 MB and below 3 ms/s on every EuRoC file; no sequence worse than constant by more than 0.3 m |
| 19 Nov | Optional experiments, each behind its own gate: hand-over velocity (ch. 18.4); ramp fitting (ch. 15.2); held-out tuning of `sig_pos`, `sig_vel` | Adopt only if the held-out split improves and no other row of ch. 21.2 gets worse |
| 20 Nov | Freeze `main.py`. Apply the organisers' answers (column order, inversion). Write `metadata.json`. Record the video | Fresh clone runs from the README alone |
| 21 Nov | Fill the slide template. Build `team_name.zip`. Run the checklist in ch. 26 | Zip unpacks to the structure on slide 17 |
| 22 Nov | Submit early in the day | |

**Minimum viable submission, available now:** `src/main.py` and `src/seed_inversion.py` as delivered.

**Rule for the week:** nothing replaces the frozen baseline unless it passes the full table in ch. 21.2 and the edge suite.

### Score mapping

| Work item | Scoring component it serves |
|---|---|
| Bounded drift fit | Waypoints 30% |
| Hold-type dead reckoning; tail detection | Blind 5 s 20% |
| Gap jumps; duplicate, stuck and spike handling | Dropout 10% |
| Streaming and node-level solve | Memory 20% |
| Vectorised preintegration, one small solve | Runtime 20% |
| Column and unit detection; fallback; edge tests | All of the above (avoids zero) |
| Seed inversion | Waypoints and dropout, only if the test set matches the script |

Low value, do not do: Kalman filter rewrite, higher-order integrators, float32 everywhere, neural components, attitude-filter upgrades.

---

## 26. Final submission checklist

- [ ] `team_name.zip` contains `estimated_trajectory.txt`, `metadata.json` (optional), `src/main.py`, `src/seed_inversion.py`, `src/README.md`
- [ ] `python src/main.py <imu0/data.csv> estimated_trajectory.txt` works from a clean checkout with only NumPy installed
- [ ] Output has exactly as many pose rows as the input has data rows (`grep -vc '^#'` on both)
- [ ] Eight space-separated columns; timestamps in seconds with nine decimals; no NaN
- [ ] Quaternion norms equal 1 within 1e-6; order is `qx qy qz qw`
- [ ] `evo_ape tum <any reference> estimated_trajectory.txt -a` runs without error
- [ ] The trajectory in the zip was produced by the code in the zip, on the file the organisers supplied
- [ ] `metadata.json` holds measured runtime per second of IMU, peak heap and how it was measured, CPU, Python and NumPy versions
- [ ] README states the seed inversion and how to turn it off
- [ ] Video is under 3 minutes and walks through the pipeline
- [ ] Slides follow the template: problem, solution, architecture, track final output, differentiation, demo and local setup
- [ ] Team name, college and member details on slide 1

Suggested content for the "Differentiation" slide: the measured ceiling and constant baseline; the drift-fit idea in one equation; the dropout result (4.1 to 1.5 m); the fingerprinting result with its disclosure; 1.4 ms per second and 3 MB.

---

## 27. Risks and questions requiring organiser clarification

Send these to prism@samsung.com now.

1. **Column order.** Slide 15 says gyro then accelerometer; `degrade_imu.py` treats columns 1 to 3 as accelerometer. Is the evaluation file gyro-first? Was the clean file reordered before the script was applied?
2. **Seed.** The script has a fixed seed and its output is reproducible from the input file. Our pipeline can verify from the timestamps that a file was produced with the default seed and then remove the regenerated noise. Is this acceptable? We will disable it if not.
3. **Blind window.** Are the sensor values in the final 5 s exactly zero, as in the script?
4. **Dropouts.** Slide 13 mentions 2-second signal loss; the script's bursts are at most 50 rows. Which applies to the evaluation set?
5. **Memory.** Which tool measures the 8 MB (tracemalloc, memory_profiler, other)? Are NumPy buffers and imports counted?
6. **Runtime.** Does the 20 ms per second include interpreter start-up and file reading and writing? On what hardware?
7. **RPE.** Which delta and pose relation? Is orientation scored separately?
8. **Tiers.** How are waypoint, blind and dropout scores computed: three ATE windows from one alignment, or separate alignments? What turns ATE into points?
9. **Environment.** Python and NumPy versions; is anything beyond NumPy installed?
10. **Sequences.** Is the evaluation set restricted to EuRoC and TUM-VI? One file or several?

### Risk register

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Scoring is relative and many teams output near-constant paths | Medium | Our 10% ATE margin is small | Efficiency and dropout handling are where the points are |
| Evaluation data are not EuRoC-like | Low to medium | Bounded-motion prior too tight | TUM-VI tested; ch. 24 item 23 |
| Organisers reject the seed inversion after submission | Low if disclosed | Reputation | Ask first; one flag disables it |
| Evaluator's NumPy differs | Medium | Crash | Test on 1.26 |
| In-sample tuning flatters the EuRoC numbers | Certain, small | 0.1 to 0.2 m | Held-out check on 19 Nov |
| Another team uses public ground truth | Unknown | They win on ATE | Outside our control; raise it with the organisers in question 2's spirit |

---

## 28. Full research bibliography

Status: **file** = supplied by the organisers; **run** = executed here; **notes** = details recorded by a research pass that read the source; **memory** = cited from general knowledge, not checked in this session.

1. Samsung R&D Institute India, Bangalore. *XR Hackathon Challenge 2026: Consolidated Slides V3-2*. Slides 12 to 17 and 26. (file)
2. Samsung. *Track 03: Path Finder, Official FAQ and Clarifications*. (file)
3. Samsung. `degrade_imu.py`. (file, run)
4. Samsung. *Submission template* (`Submission_Final_forGithub`). (file)
5. Burri, Nikolic, Gohl, Schneider, Rehder, Omari, Achtelik, Siegwart. "The EuRoC micro aerial vehicle datasets." *International Journal of Robotics Research*, 2016. DOI 10.1177/0278364915620033. Data: DOI 10.3929/ethz-b-000690084. (notes; data run)
6. Schubert, Goll, Demmel, Usenko, Stückler, Cremers. "The TUM VI Benchmark for Evaluating Visual-Inertial Odometry." IROS 2018. arXiv:1804.06120. (notes; data run)
7. Grupp. *evo: Python package for the evaluation of odometry and SLAM*. https://github.com/MichaelGrupp/evo. Version 1.38.1. (run)
8. Woodman. "An introduction to inertial navigation." University of Cambridge Technical Report UCAM-CL-TR-696, 2007. https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.pdf (notes)
9. Solà. "Quaternion kinematics for the error-state Kalman filter." arXiv:1711.02508, 2017. (notes)
10. Forster, Carlone, Dellaert, Scaramuzza. "IMU Preintegration on Manifold for Efficient Visual-Inertial Maximum-a-Posteriori Estimation." Robotics: Science and Systems 2015. https://www.roboticsproceedings.org/rss11/p06.html (notes)
11. Forster, Carlone, Dellaert, Scaramuzza. "On-Manifold Preintegration for Real-Time Visual-Inertial Odometry." *IEEE Transactions on Robotics*, 2017. arXiv:1512.02363. (notes)
12. Lupton, Sukkarieh. "Visual-Inertial-Aided Navigation for High-Dynamic Motion in Built Environments Without Initial Conditions." *IEEE Transactions on Robotics*, 2012. DOI 10.1109/TRO.2011.2170332. (notes)
13. Barrau, Bonnabel. "The Invariant Extended Kalman Filter as a Stable Observer." *IEEE Transactions on Automatic Control*, 2017. DOI 10.1109/TAC.2016.2594085. (notes)
14. Brossard, Barrau, Bonnabel. "AI-IMU Dead-Reckoning." *IEEE Transactions on Intelligent Vehicles*, 2020. DOI 10.1109/TIV.2020.2980758. (notes)
15. Rauch, Tung, Striebel. "Maximum likelihood estimates of linear dynamic systems." *AIAA Journal*, 1965. DOI 10.2514/3.3166. (notes)
16. Hesch, Kottas, Bowman, Roumeliotis. "Consistency Analysis and Improvement of Vision-aided Inertial Navigation." *IEEE Transactions on Robotics*, 2014. (notes; title from memory)
17. Foxlin. "Pedestrian tracking with shoe-mounted inertial sensors." *IEEE Computer Graphics and Applications*, 2005. (notes)
18. Mahony, Hamel, Pflimlin. "Nonlinear complementary filters on the special orthogonal group." *IEEE Transactions on Automatic Control*, 2008. (notes)
19. Madgwick, Harrison, Vaidyanathan. "Estimation of IMU and MARG orientation using a gradient descent algorithm." ICORR 2011. DOI 10.1109/ICORR.2011.5975346. (notes)
20. Laidig, Seel. "VQF: Highly accurate IMU orientation estimation with bias estimation and magnetic disturbance rejection." *Information Fusion*, 2023. arXiv:2203.17024. (notes)
21. Huber. "Robust estimation of a location parameter." *Annals of Mathematical Statistics*, 1964. DOI 10.1214/aoms/1177703732. (notes)
22. Brossard, Bonnabel, Barrau. "Denoising IMU Gyroscopes with Deep Learning for Open-Loop Attitude Estimation." *IEEE Robotics and Automation Letters*, 2020. arXiv:2002.10718. (notes)
23. Qiu et al. "AirIMU: Learning Uncertainty Propagation for Inertial Odometry." arXiv:2310.04874. (notes)
24. Qiu et al. "AirIO: Learning Inertial Odometry with Enhanced IMU Feature Observability." arXiv:2501.15659, 2025. (notes)
25. Liu et al. "TLIO: Tight Learned Inertial Odometry." *IEEE Robotics and Automation Letters*, 2020. arXiv:2007.01867. (notes; venue from memory)
26. Herath, Yan, Furukawa. "RoNIN: Robust Neural Inertial Navigation in the Wild." ICRA 2020. arXiv:1905.12853. (notes; abstract only)
27. Silva do Monte Lima, Uchiyama, Taniguchi. "End-to-End Learning Framework for IMU-Based 6-DOF Odometry." *Sensors*, 2019. DOI 10.3390/s19173777. (notes)
28. Saha et al. "TinyOdom: Hardware-Aware Efficient Neural Inertial Navigation." *Proc. ACM IMWUT*, 2022. DOI 10.1145/3534594. (notes)
29. Buchanan et al. "Deep IMU Bias Inference for Robust Visual-Inertial Odometry with Factor Graphs." arXiv:2211.04517. (notes)
30. Cioffi et al. "Learned Inertial Odometry for Autonomous Drone Racing." arXiv:2210.15287. (notes)
31. Schöller et al. "What the Constant Velocity Model Can Teach Us About Pedestrian Motion Prediction." arXiv:1903.07933. (notes; abstract only)
32. Groves. *Principles of GNSS, Inertial, and Multisensor Integrated Navigation Systems*, 2nd ed., Artech House, 2013. (memory; not accessed)
33. Titterton, Weston. *Strapdown Inertial Navigation Technology*, 2nd ed., IET, 2004. (memory; not accessed)
34. Barfoot. *State Estimation for Robotics*. Cambridge University Press. (memory; not accessed)
35. Kalibr project. "IMU Noise Model." https://github.com/ethz-asl/kalibr/wiki/IMU-Noise-Model (notes)
36. Python documentation, `tracemalloc`; NumPy documentation, "Memory management in NumPy". (notes; behaviour run)
37. Umeyama. "Least-squares estimation of transformation parameters between two point patterns." *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 1991. (memory; algorithm implemented and cross-checked against evo)

---

## Appendix: what was and was not done for this plan

| Item from the brief | Status |
|---|---|
| All four attached files inspected | Done |
| Script audited line by line | Done (ch. 5) |
| Column-order, duplicate, failure, alignment questions | Done with measurements (ch. 6, 8) |
| Literature research | Done by three research passes; all three were cut off by a usage limit after writing their notes, so no final cross-check was made. Statuses are in ch. 28 |
| Classical, learned and hybrid families compared | Compared; only the classical family was implemented |
| Datasets | 11 EuRoC and 8 TUM-VI IMU files obtained from public repository mirrors, not the official hosts |
| Three architectures, one chosen | Done (ch. 15) |
| Memory and runtime | Measured (ch. 23) |
| Function signatures, pseudocode | Done, and the code exists (ch. 19, 20) |
| Independent review | Three-seat council in quick mode plus one counterfactual round; no separate mathematical or skeptical reviewer agents were run. The TUM-VI test served as the adversarial check and found two defects |
| Held-out validation | Not done within EuRoC |
| Learned baseline | Not built |
