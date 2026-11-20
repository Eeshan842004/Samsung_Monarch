"""Builds <team_name>.zip in the layout of slide 17.
Usage: python tools/make_submission.py <CollegeName_TeamName> <organiser imu0/data.csv>"""
import os, sys
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(_ROOT, "src")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil, subprocess, tempfile
team, imu = sys.argv[1], sys.argv[2]
root = tempfile.mkdtemp(); os.makedirs(os.path.join(root, "src"))   # files sit at the zip root, as on slide 17
for f in ("main.py", "seed_inversion.py", "README.md"):
    shutil.copy(os.path.join(_ROOT, "src", f), os.path.join(root, "src", f))
subprocess.check_call([sys.executable, os.path.join(_ROOT, "tools", "make_metadata.py"), imu,
                       os.path.join(root, "estimated_trajectory.txt"), os.path.join(root, "metadata.json")])
n_in = sum(1 for l in open(imu, encoding="utf-8-sig") if l.strip() and (l[0].isdigit() or l[0] in "-."))
n_out = sum(1 for l in open(os.path.join(root, "estimated_trajectory.txt")) if not l.startswith("#"))
assert n_in == n_out, "row count mismatch: %d input rows, %d poses" % (n_in, n_out)
shutil.make_archive(team, "zip", root)
print("wrote %s.zip (%d poses)" % (team, n_out))
