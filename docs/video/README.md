# Demo video

`VITVellore_Monarch_demo.mp4`: 1920x1080, 30 fps, silent, captioned. What you see comes from the running project:

- **Terminal**: the commands in `session.json` were run in this repository on 21 Nov 2026. The video types out the first eight and replays their saved output, with long lines wrapped. It is a rendering of that session, not a screen recording. Input: the public EuRoC MH_01_easy IMU log, reordered with `tools/reorder.py` and degraded with the organisers' `tools/degrade_imu.py`. The file is not in the repository (`eval/` is git-ignored).
- **Viewer**: frame-by-frame screenshots of the live page (https://eeshan842004.github.io/Samsung_Monarch/), stepped with its own time slider. The per-flight numbers on screen are computed by the page.
- **GitHub**: screenshots of the public repository and its Actions page.
- The end card shows only the measured 11-flight figures from `docs/SPEC.md`.

Rebuild (needs `playwright`, Chrome, `Pillow`, `imageio-ffmpeg`, Windows fonts Segoe UI and Cascadia Mono):

```bash
python docs/video/record_session.py "<path to bash>" docs/video/session.json   # from the repository root
cd docs/video && python capture.py && python capture_gh.py && python make_video.py VITVellore_Monarch_demo.mp4
```

`capture.py` records the viewer and writes the layout file, then `capture_gh.py` adds the GitHub screenshots. The terminal step needs the demo input in `eval/demo/` first. The previous slide-based video's scripts are in `docs/archive/video_v1/`.
