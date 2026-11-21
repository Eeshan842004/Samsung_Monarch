"""Runs the demo commands in the repository root and stores their exact output in session.json.
Usage (from the repository root, Git Bash available): python docs/video/record_session.py <bash.exe> docs/video/session.json"""
import json, subprocess, sys
bash, out = sys.argv[1], sys.argv[2]
cmds = [
    "python tests/test_core.py",
    "python tools/degrade_imu.py eval/demo/imu_af.csv eval/demo/data.csv",
    "TRACK3_VERBOSE=1 python src/main.py eval/demo/data.csv eval/demo/estimated_trajectory.txt",
    "grep -vc '^#' eval/demo/data.csv",
    "grep -vc '^#' eval/demo/estimated_trajectory.txt",
    "head -3 eval/demo/estimated_trajectory.txt",
    "python tools/make_submission.py SAMPLE_MH01 eval/demo/data.csv",
    "unzip -l SAMPLE_MH01.zip",
    "unzip -p SAMPLE_MH01.zip metadata.json | head -7",
]
sess = []
for c in cmds:
    r = subprocess.run([bash, "-c", c], capture_output=True, text=True)
    sess.append({"cmd": c, "out": (r.stdout + r.stderr).rstrip("\n"), "rc": r.returncode})
json.dump(sess, open(out, "w"), indent=1)
