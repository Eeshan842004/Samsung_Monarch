# SLIDES.md: content for the presentation and the 3-minute video

**The deck is already built**: `docs/deck/VITVellore_Monarch.pptx` (organiser template, 10 slides, native charts, speaker notes). Rebuild it with `python docs/deck/build_deck.py` after changing a number; figures come from `docs/deck/make_figures.py`. Team details on slide 1 and the repository and viewer links on slide 7 are filled in.

Use the organisers' template and keep its order: title, THE PROBLEM, SOLUTION, ARCHITECTURE, Track Final Output, DIFFERENTIATION, DEMO & LOCAL SETUP, Brownie Slides, Thank You. Save it as `CollegeName_TeamName`. Every number below is from `docs/SPEC.md`; do not round further or add numbers that are not there.

## Template slide 1: Track No, team name, college, members

- Theme: Track 03, Path Finder: Trajectory Estimation Under Sensor Degradation
- Project title: **Path Finder: physics instead of learning for IMU-only navigation**
- Team MONARCH, VIT Vellore: Eshan, Harshita Kumar

## Template slide 2: THE PROBLEM

- One IMU, no GPS, no camera. The sensor gets noisier, loses samples, then dies. Reconstruct where the vehicle went and where it is 5 seconds after the sensor is gone.
- Why it is hard: integrating an IMU twice turns a 0.5 degree tilt error into 430 m after 100 s. With the dataset's own bias estimates and a perfect start, open-loop integration is already 38 m off after 20 s.
- The honest baseline: outputting a constant position scores 3.45 m on EuRoC. Any estimator that drifts is worse than not moving.
- Budgets: 8 MB, 20 ms per second of data, one thread, Python.

## Template slide 3: SOLUTION

One sentence: **integrate once, then fit the drift as a physical curve and subtract it, using the vehicle's own rotor drag as a speedometer.**

Three ideas:

1. Drift is the double integral of a few sensor errors, and it is linear in them. One least-squares solve replaces a filter.
2. A multirotor's accelerometer, perpendicular to thrust, measures rotor drag, which is proportional to velocity. Calibrated from the file itself; switches off when the effect is absent.
3. Every long dropout gets its own unknown rotation and velocity jump.

## Template slide 4: ARCHITECTURE

Diagram (left to right): `IMU CSV` → `scan timestamps` → `clean + preintegrate to 20 Hz nodes` → `batch fit (drift, drag, gaps)` → `pose per row` → `TUM file`. Side box under "clean": optional seed check. Side box under "pose per row": hold through the blind window.

Callouts: streamed in 2048-row chunks; about 85 unknowns; three relinearisations; memory proportional to nodes, not rows.

### On the same slide or a second ARCHITECTURE slide: the key equation

`f_perp = -mu * v_perp + c`

- Rotors push only along the thrust axis, so the accelerometer's other two axes see only drag.
- `mu` is estimated from each file: 0.14 to 0.22 1/s on EuRoC without any ground truth (ground-truth regression: 0.17 to 0.21).
- Cite: Leishman, Macdonald, Beard, McLain, IEEE Control Systems Magazine 2014.

### Tech stack (one line on the ARCHITECTURE slide)

Python, NumPy. Nothing else at run time. evo for scoring. Docker for reproducibility. A single static HTML page for visualisation.

## Template slide 5: TRACK FINAL OUTPUT

Show the output file itself (three lines of `estimated_trajectory.txt`, row count equal to the input), a viewer screenshot, then a bar chart of mean ATE over 11 EuRoC sequences, degraded input:

| Method | ATE |
|---|---|
| Constant position | 3.45 m |
| Drift fit only | 3.11 m |
| Drift fit + rotor drag (ours) | 2.49 m |

Second panel: blind final 5 s, 2.91 m without drag, 1.74 m with it.
Third panel: 1 to 3 ms per second of data against 20; 4.1 MB against 8.

Footnote: published learned IMU-only methods report 3.2 to 5.0 m on this dataset.

## Template slide 6: DIFFERENTIATION

- Rotor drag inside an IMU-only batch estimator, self-calibrated, with six guards and a null test that proves the gain is physics.
- Dropouts modelled as unknowns instead of interpolated.
- Blind-window policy chosen by measurement: holding beats extrapolating.
- Degradation fingerprinting: we can prove from timestamps alone whether a file came from the reference script, and undo that noise. Disclosed, optional, off by one flag.

## Template slide 7: DEMO & LOCAL SETUP

- `pip install numpy`, `python src/main.py data.csv out.txt`, or the Docker line.
- Viewer URL and QR code. Repository URL.

## Brownie slide A: Robustness

| Stress | Result |
|---|---|
| Three other random seeds | 2.53 to 2.60 m |
| 2-second dropouts | 2.65 m (3.53 m without the gap model) |
| Five flights never used for tuning | 2.48 to 2.59 m against 3.40 m constant |
| Hand-held device (TUM-VI) | drag model turns itself off; 0.73 m against 1.08 m, better on 6 of 6 |
| 18 malformed inputs | one valid pose per row, every time |
| Blind window filled with noise instead of zeros | no effect: the final 5 s are never trusted |
| Python 3.11 + NumPy 1.26 and Python 3.13 + NumPy 2.5 | same trajectory within 0.2 mm |

## Brownie slide B: Limitations

- Metres, not centimetres. Error budget: our attitude with the true velocity gives 0.2 m; the true attitude with our velocity gives 2.6 m. What is left is slow horizontal velocity: accelerometer in-plane bias divided by the drag coefficient, 0.05 / 0.19 = 0.26 m/s, which no IMU-only method can observe.
- Heading drifts without a rest interval at the start.
- Drag model validated on one airframe.
- If raw EuRoC column order was fed to the degradation script with a seed we cannot verify, we get 3.25 m (the gyro then carries accelerometer-sized noise).

## Video script (3 minutes maximum)

| Time | Picture | Words |
|---|---|---|
| 0:00 to 0:20 | Title, then a plot of raw double integration flying off the screen | "An IMU alone drifts by tens of metres in seconds. Our sensor also gets noisier, loses samples and then dies." |
| 0:20 to 0:40 | Terminal: one command, output file appears, row counts match | "One Python file, NumPy only. One pose for every input row." |
| 0:40 to 1:20 | Architecture slide, then the drag equation | "We integrate once and fit the drift as a curve. And we use something the vehicle gives us for free: rotor drag tells us its speed." |
| 1:20 to 2:10 | Viewer: play the trajectory against ground truth; point at a dropout segment and the blind window | "Grey is truth, blue is ours. Orange is right after a dropout. Red is the blind five seconds." |
| 2:10 to 2:40 | Results and robustness slides | "2.5 metres where standing still scores 3.45, in 4 megabytes and about 2 milliseconds per second." |
| 2:40 to 3:00 | Limitations slide, repository URL | "It is metres, not centimetres, and we say why. Everything is reproducible from the repository." |

## Questions a jury is likely to ask (9 Dec)

| Question | Answer |
|---|---|
| Why not a Kalman filter? | With no measurements a filter only propagates. Given the same priors it solves the same least squares, one sample at a time, more slowly. |
| Why not a neural network? | Published ones score 3.2 to 5.0 m here and were never tested with degradation; training on the public test sequences would also leak. |
| Is 2.5 m good? | The constant baseline is 3.45 m and published learned methods report 3.2 to 5.0 m. Our error budget shows what is left: 0.2 m from attitude, the rest from slow velocity that an IMU cannot observe. |
| How do you know drag is real and not overfitting? | Shift the force signal by 37 s and the effect vanishes on all 11 flights. The coefficient from the other 10 flights works as well as the self-calibrated one (2.486 against 2.489 m). Settings were chosen on six flights; the other five give the same result. One tuning step that helped the six and hurt the five was thrown out. |
| What if it is not a multirotor? | The model needs a correlation below -0.35, a plausible coefficient, agreement between both halves of the file, and no spread blow-up. Hand-held data fails those and the model stays off. |
| Is the seed trick cheating? | It uses only the input and your public script, verifies itself, is disclosed, and never searches for other seeds. It changes the result by 0.01 m in the documented column order. Turn it off and nothing else changes. |
| Why hold position in the blind window? | With perfect velocity, a decaying extrapolation beats holding by 20%. With an IMU-only velocity it is 8% better mid-flight and 40% worse near landing. Holding has the smaller worst case. |
| Why ignore the last 5 s even if the values look fine? | The brief says they are unusable. Noise at vibration level cannot be told from data, and integrating it costs 1.8 to 7.5 m. Ignoring valid data would cost 0.02 m. |
| What would you do next? | Fix heading drift without a rest start; test other airframes; a fixed-wing drag model for the aeroplane case in the brief. |
