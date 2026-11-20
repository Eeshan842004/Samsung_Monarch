import sys
# EuRoC (t,gyro,accel) <-> script order (t,accel,gyro); self-inverse
with open(sys.argv[1]) as f, open(sys.argv[2],"w") as o:
    for line in f:
        c=line.rstrip("\n").split(",")
        o.write(",".join([c[0]]+c[4:7]+c[1:4])+"\n")
