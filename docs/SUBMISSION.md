# SUBMISSION.md: what to hand in, field by field

Deadline: **22 Nov 2026, 11:59 PM IST**, one Google Form submission per team. Slide 24 warns that teams not following the guideline are disqualified.

## The form fields

| Form field | What to put | Where it comes from |
|---|---|---|
| Submission package (as per theme) | `VITVellore_Monarch.zip`: slide 17 says the submitted `estimated_trajectory.txt` is what gets compared with the hidden ground truth | `python tools/make_submission.py VITVellore_Monarch <organiser csv>` |
| Source code | Public GitHub repository URL | this repository |
| Presentation | `docs/deck/VITVellore_Monarch.pptx` (PDF alongside) | built on the organiser template |
| Video | `docs/video/VITVellore_Monarch_demo.mp4` (2 min 15 s, captioned, silent) uploaded to YouTube or Drive | add a voice-over if you have time |
| AI Disclosure | Text from `AI_DISCLOSURE.md` | written |
| README | In the repository root and inside the zip (`src/README.md`) | already written; repository and viewer links filled |
| APK/SDK (if any) | "No APK. Python API documented in the README (`solve_file`, `poses_at`, `write_trajectory`)." | README, "Python API" |
| Other | Live viewer URL | `web/` deployed as a static site (Vercel or GitHub Pages) |

### Why no APK

- The track is scored by running `main.py` on a file. An app adds nothing to that score.
- The team has no hardware to test on.
- The strongest part of the method, rotor drag, does not apply to a phone in a hand, so a phone demo would show the estimator at its weakest.
- A three-seat council reviewed the options and all three seats chose: repository plus Docker, the API as documentation, and the static viewer; skip the APK and an in-browser port (`docs/DECISIONS.md`).

## The zip (slide 17 layout)

```
VITVellore_Monarch.zip
├── estimated_trajectory.txt      one pose per row of the organisers' file
├── metadata.json                 runtime and memory measured on your machine
└── src/
    ├── main.py
    ├── seed_inversion.py
    └── README.md
```

`tools/make_submission.py` builds this, measures time and heap, and refuses to finish if the pose count differs from the input row count.

## Checklist before pressing submit

- [ ] `python tests/test_core.py` prints "9 tests passed"
- [ ] `python tools/edge_tests.py` ends with "ALL PASS"
- [ ] `tools/final_table.py` on the official dataset downloads reproduces `docs/SPEC.md` section 2 within 0.05 m
- [ ] Docker image builds and the `docker run` line in the README produces a trajectory
- [ ] The zip was built from the organisers' evaluation file, by the code in the zip
- [ ] `grep -vc '^#' estimated_trajectory.txt` equals the number of data rows in the input
- [ ] `evo_ape tum <any TUM file with overlapping times> estimated_trajectory.txt -a` runs without error
- [ ] Repository is public, has no dataset files, and `grep -rn "TODO("` returns nothing
- [ ] Presentation file is named `VITVellore_Monarch` and follows the template order
- [ ] Video is 3 minutes or less and the link opens without signing in
- [ ] Viewer URL loads on a phone and a laptop
- [ ] Any reply from the organisers has been applied (see below)

## Questions sent to the organisers

Send to prism@samsung.com (the contact on the organisers' slides) as soon as possible; do not wait for a reply before finishing.

1. Slide 15 lists gyro columns before accelerometer columns, but `degrade_imu.py` treats columns 1 to 3 as the accelerometer. Which order does the evaluation file use, and was the clean file reordered before the script was applied?
2. The script uses a fixed seed and its output is reproducible from its input. Our code can verify from the timestamps that a file was produced that way and then remove the regenerated noise. It uses only the input file and your script. Is that acceptable? We will disable it otherwise.
3. In the blind final 5 seconds, are the sensor values exactly zero as in the script, or something else?
4. Slide 13 mentions 2-second signal loss; the script removes at most 50 consecutive rows. Which applies?
5. How is the 8 MB measured (tracemalloc, memory_profiler, other)? Does the 20 ms per second include interpreter start-up?
6. Which evo options are used for RPE (delta, pose relation)? Is orientation scored?
7. Which Python and NumPy versions run on the evaluator?

### Email text, ready to send

Subject: Track 03 Path Finder: clarifications before submission (Team MONARCH, VIT Vellore)

> Dear organisers,
>
> We are finalising our Track 03 submission and want to make sure we follow your rules exactly. Could you clarify the following?
>
> 1. Column order. Slide 15 lists gyro columns before accelerometer columns, while `degrade_imu.py` treats columns 1 to 3 as the accelerometer. Which order does the evaluation file use, and was the clean file reordered before the script was applied?
> 2. Reproducible degradation. The script uses a fixed seed, so its output can be reproduced from its input. Our code can verify from the timestamps alone that a file was produced by the script and then subtract the regenerated noise. It uses only the input file and your script, and we describe it in our README. Is this acceptable? We will disable it if you prefer.
> 3. Blind window. Are the sensor values in the final 5 seconds exactly zero, as in the script? Is the blind window always the last 5 seconds of a complete recording?
> 4. Dropouts. Slide 13 mentions 2-second signal loss; the script removes at most 50 consecutive rows. Which applies to the evaluation file?
> 5. Efficiency. How is the 8 MB measured (tracemalloc, memory_profiler, other)? Does the 20 ms per second include interpreter start-up? Are these taken from our `metadata.json` or measured by you?
> 6. Metrics. Which evo options are used for RPE (delta and pose relation)? Is the blind window scored with the global alignment or aligned on its own?
> 7. Environment. Which Python and NumPy versions will be used if you re-run our code?
>
> Thank you,
> Eshan and Harshita Kumar, Team MONARCH, VIT Vellore

What to change for each possible answer:

| Answer | Action |
|---|---|
| Seed inversion not allowed | `"use_seed_inversion": False` in `CFG`; update both READMEs; rebuild the zip |
| Blind tail is random noise, not zeros | Add a tail detector (task in `CLAUDE.md`), re-run all tests |
| Memory measured as process RSS | Nothing can bring a NumPy process under 8 MB; state the tracemalloc figure in `metadata.json` and the README |
| NumPy older than 1.26 | Run the unit and edge tests on that version; `np.fromstring` text mode and `default_rng` need NumPy 1.17 or newer |

## Timeline

| Date | Work |
|---|---|
| 17 Nov | Email the organisers. Create the GitHub repository. Download the official datasets and reproduce the numbers |
| 18 Nov | Docker build. NumPy 1.26 test. Deploy the viewer |
| 19 Nov | Slides from `docs/SLIDES.md`. Record the video |
| 20 Nov | Freeze `src/`. Apply organiser answers |
| 21 Nov | Build the zip. Run the checklist. Ask a teammate to follow the README on a clean machine |
| 22 Nov | Submit before noon |
| 29 Nov | Shortlist announced |
| 9 Dec | Jury demo for the top 12 to 15 teams: use the viewer live |
