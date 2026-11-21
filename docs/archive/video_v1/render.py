import subprocess, os, glob
from PIL import Image
from compose import frame
ENC=["-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p","-r","30"]
def still(name, img, cap, dur, step=None):
    p=f"cap/{name}.png"; frame(img,cap,step).save(p)
    out=f"scenes/{name}.mp4"; tmp=out+".tmp.mp4"
    vf=f"format=yuv420p,loop=-1:1,trim=duration={dur},fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4}:d=0.4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate","30","-i",p,"-vf",vf]+ENC+[tmp],check=True); os.replace(tmp,out)
S=lambda i: f"frames/s-{i:02d}.png"
scenes=[
 ("01", S(1), "Samsung XR Hackathon 2026, Track 03: Path Finder. Team MONARCH, VIT Vellore.", 6, None),
 ("02", S(2), "An IMU alone drifts by tens of metres in seconds. Ours also gets noisier, loses samples, then dies. Standing still already scores 3.45 m.", 12, "The problem"),
 ("03", S(3), "Our idea: integrate once, then fit the drift as a physical curve, and use the drone's own rotor drag as a speedometer.", 12, "The solution"),
 ("04", S(4), "One streaming pass, one small least-squares solve, one pose for every input row. NumPy only.", 10, "Architecture"),
]
for s in scenes: still(*s)
# viewer playback
fr=sorted(glob.glob("frames/view/a*.jpg"))
os.makedirs("cap/view",exist_ok=True)
for i,f in enumerate(fr):
    frame(f,"Grey is the motion-capture truth, blue is our estimate, white dots are dropouts. The error stays well under the constant-position line.","Live viewer").save(f"cap/view/{i:04d}.jpg",quality=92)
out="scenes/05.mp4"; tmp=out+".tmp.mp4"
subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate","15","-i","cap/view/%04d.jpg","-vf","format=yuv420p,fade=t=in:st=0:d=0.4"]+ENC+[tmp],check=True); os.replace(tmp,out)
still("06", "frames/view/a0269.jpg", "At the end the sensor is gone. We hold the last pose: the policy with the smallest worst case in our tests.", 5, "Blind final 5 s")
still("07", "frames/view/b.jpg", "Vicon Room 1-02: 0.74 m against 1.78 m for standing still.", 5, "Live viewer")
still("08", "frames/view/c.jpg", "Machine Hall 05, difficult: 4.77 m against 6.87 m. Metres, not centimetres: that is the physics of an IMU.", 6, "Live viewer")
rest=[
 ("09", S(5), "Across all 11 EuRoC flights with the organisers' degradation: 2.49 m, in 1 to 3 ms per second of data and 4.1 MB of memory.", 12, "Results"),
 ("10", S(6), "Sideways to the thrust, the accelerometer feels only drag, proportional to speed. Shift the signal in time and the gain disappears: it is physics.", 13, "Differentiation"),
 ("11", S(8), "Three other noise seeds, 2-second dropouts, flights never used for tuning, hand-held data: it holds up.", 11, "Robustness"),
 ("12", S(9), "With the true velocity our attitude alone gives 0.15 m. What remains is slow velocity no IMU can observe. We say so.", 11, "Honest limits"),
 ("13", S(7), "One command produces the submission file. Everything is reproducible from the repository.", 9, "Demo & setup"),
 ("14", S(10), "Thank you. Team MONARCH: Eshan and Harshita Kumar, VIT Vellore.", 5, None),
]
for s in rest: still(*s)
files=sorted(glob.glob("scenes/??.mp4"))
open("list.txt","w").write("".join(f"file '{f}'\n" for f in files))
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i","list.txt","-c","copy","VITVellore_Monarch_demo.tmp.mp4"],check=True)
os.replace("VITVellore_Monarch_demo.tmp.mp4","VITVellore_Monarch_demo.mp4")
