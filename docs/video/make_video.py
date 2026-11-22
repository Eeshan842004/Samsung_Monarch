"""Composes the Path Finder demo video (1920x1080, 30 fps, silent, captioned).

Sources (all real): session.json (commands run in the repository and their exact output),
cap/*.jpg (frame-by-frame screenshots of the live GitHub Pages viewer and the GitHub repository).
"""
import json, math, os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

W, H, FPS = 1920, 1080, 30
CH = 940                                    # picture height; caption strip below
DSF = 1.5
OUT = sys.argv[1] if len(sys.argv) > 1 else "demo.mp4"
PREVIEW = os.environ.get("PREVIEW")          # "scene:t" -> write one PNG and exit

BG = (9, 13, 24); PANEL = (16, 22, 38); LINE = (40, 52, 78)
INK = (233, 238, 246); MUTE = (148, 163, 184); DIM = (100, 116, 139)
CY = (56, 189, 248); OR = (245, 158, 11); GR = (52, 211, 153); RD = (248, 113, 113); VI = (167, 139, 250)

FD = "C:/Windows/Fonts/"
def F(name, size): return ImageFont.truetype(FD + name, size)
SANS = lambda s: F("segoeui.ttf", s); SEMI = lambda s: F("seguisb.ttf", s); BOLD = lambda s: F("segoeuib.ttf", s)
MONO = lambda s: F("CascadiaMono.ttf", s)

meta = json.load(open("cap/meta.json"))
session = json.load(open("session.json"))[:8]          # last command (metadata head) is redundant

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def fade_in(t, start, dur=0.35): return ease((t - start) / dur)
def window(t, a, b, d=0.35): return min(fade_in(t, a, d), 1 - fade_in(t, b - d, d))

_cache = {}
def load(path):
    if path not in _cache:
        if len(_cache) > 6: _cache.clear()
        _cache[path] = Image.open(path).convert("RGB")
    return _cache[path]

# ---------------------------------------------------------------- drawing helpers
def rgba(c, a): return (c[0], c[1], c[2], int(255 * max(0, min(1, a))))

def text_w(d, s, f): return d.textlength(s, font=f)

def pill(d, x, y, s, f, fg, bg, a=1, pad=(16, 8), outline=None):
    w = text_w(d, s, f); bb = f.getbbox("Hg"); h = bb[3] - bb[1]
    r = (x, y, x + w + 2 * pad[0], y + h + 2 * pad[1])
    d.rounded_rectangle(r, radius=(r[3] - r[1]) // 2, fill=rgba(bg, 0.92 * a),
                        outline=rgba(outline, a) if outline else None, width=2)
    d.text((x + pad[0], y + pad[1] - bb[1]), s, font=f, fill=rgba(fg, a))
    return r

def caption_bar(im, text, chip=None, a=1):
    d = ImageDraw.Draw(im)
    d.rectangle((0, CH, W, H), fill=(6, 9, 18, 255)); d.line([(0, CH), (W, CH)], fill=LINE + (255,), width=2)
    f = SEMI(36)
    while text_w(d, text, f) > 1800: f = SEMI(f.size - 2)
    d.text(((W - text_w(d, text, f)) / 2, CH + 18), text, font=f, fill=rgba(INK, a))
    if chip: pill(d, 40, CH + 84, chip.upper(), SEMI(19), BG, CY, a=1, pad=(14, 6))
    fb = SANS(21); s2 = "Team MONARCH  ·  VIT Vellore"
    d.text((W - 40 - text_w(d, s2, fb), CH + 88), s2, font=fb, fill=(170, 182, 200, 255))

def arrow(d, p0, p1, col, a, w=4):
    d.line([p0, p1], fill=rgba(col, a), width=w)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); L = 18
    for s in (-0.45, 0.45):
        d.line([p1, (p1[0] - L * math.cos(ang + s), p1[1] - L * math.sin(ang + s))], fill=rgba(col, a), width=w)

def callout(im, rect, label, lpos, col=CY, a=1, sub=None):
    """rect in output px; label pill at lpos (x,y); arrow from pill to rect edge."""
    if a <= 0: return
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = rect
    d.rounded_rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), radius=14, fill=rgba(col, 0.10 * a), outline=rgba(col, a), width=4)
    f = SEMI(28); fs = SANS(22)
    w = text_w(d, label, f) + 36; h = 52 + (30 if sub else 0)
    if sub: w = max(w, text_w(d, sub, fs) + 36)
    lx, ly = lpos
    d.rounded_rectangle((lx, ly, lx + w, ly + h), radius=14, fill=rgba((8, 12, 22), 0.94 * a), outline=rgba(col, a), width=3)
    d.text((lx + 18, ly + 9), label, font=f, fill=rgba(INK, a))
    if sub: d.text((lx + 18, ly + 50), sub, font=fs, fill=rgba(MUTE, a))
    # arrow from nearest pill edge to nearest rect edge
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    px = min(max(cx, lx), lx + w); py = min(max(cy, ly), ly + h)
    tx = min(max(px, x0 - 8), x1 + 8); ty = min(max(py, y0 - 8), y1 + 8)
    if abs(tx - px) + abs(ty - py) > 30: arrow(d, (px, py), (tx, ty), col, a)
    im.alpha_composite(ov)

# ---------------------------------------------------------------- camera over page screenshots
class Cam:
    def __init__(self, img): self.img = img
    def render(self, rect):
        x, y, w, h = rect
        s = DSF
        crop = self.img.crop((int(x * s), int(y * s), int((x + w) * s), int((y + h) * s)))
        im = Image.new("RGBA", (W, H), BG + (255,))
        im.paste(crop.resize((W, CH), Image.BICUBIC), (0, 0)); return im
def to_out(rect, cam):
    """CSS rect (x,y,w,h) -> output px box under camera rect cam."""
    x, y, w, h = rect; cx, cy, cw, ch = cam
    k = W / cw
    return ((x - cx) * k, (y - cy) * k, (x + w - cx) * k, (y + h - cy) * k)
def cam_lerp(a, b, t): return tuple(lerp(a[i], b[i], ease(t)) for i in range(4))
def cam16(x, y, w): return (x, y, w, w * CH / W)

B = meta["boxes"]
def bx(k): b = B[k]; return (b["x"], b["y"], b["width"], b["height"])

CAM_HERO = cam16(0, 0, 1920)
CAM_MAIN = cam16(220, 302, 1490)
CAM_ERR = cam16(300, 925, 1320)
CAM_TOP = cam16(352, 396, 1000)

# metrics rows: measured from the card's position; rows are 36 px apart starting below the title
MC = bx("#metrics-card")
def mrow(i, n=1): return (MC[0] + 8, MC[1] + 44 + 36 * i, MC[2] - 16, 36 * n)

def rows_of(key):
    out = {}
    for ln in meta[key].splitlines():
        if "\t" in ln: k, v = ln.split("\t", 1); out[k.strip()] = v.strip()
    return out

# ---------------------------------------------------------------- scenes
def bg_canvas():
    im = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 64): d.line([(x, 0), (x, H)], fill=(14, 20, 34, 255))
    for y in range(0, H, 64): d.line([(0, y), (W, y)], fill=(14, 20, 34, 255))
    return im

def scene_title(t):
    im = bg_canvas(); d = ImageDraw.Draw(im)
    a = fade_in(t, 0.2, 0.6)
    pill(d, 160, 250, "SAMSUNG XR HACKATHON 2026  \u00b7  TRACK 03", SEMI(24), CY, (12, 30, 48), a, outline=CY)
    d.text((152, 318), "Path Finder", font=BOLD(132), fill=rgba(INK, fade_in(t, 0.5, 0.6)))
    d.text((160, 492), "IMU-only 6-DoF trajectory estimation under sensor degradation", font=SANS(44), fill=rgba(MUTE, fade_in(t, 0.9, 0.6)))
    a2 = fade_in(t, 1.5, 0.6)
    d.text((160, 600), "Live project demo: real commands, the live viewer, the public repository", font=SEMI(34), fill=rgba(CY, a2))
    a3 = fade_in(t, 2.1, 0.6)
    d.line([(160, 700), (900, 700)], fill=rgba(LINE, a3), width=2)
    d.text((160, 726), "Team MONARCH  \u00b7  VIT Vellore", font=SEMI(38), fill=rgba(INK, a3))
    d.text((160, 780), "Eeshan  \u00b7  Harshita Kumar", font=SANS(34), fill=rgba(MUTE, a3))
    # stylised trajectory doodle
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    n = int(260 * ease((t - 0.3) / 3.5))
    pts = [(1590 + 190 * math.sin(i / 20) * math.cos(i / 47), 290 + 135 * math.sin(i / 13 + 1) * math.cos(i / 61)) for i in range(n)]
    if len(pts) > 2: o.line(pts, fill=(56, 189, 248, 230), width=5, joint="curve")
    if pts: x, y = pts[-1]; o.ellipse((x - 11, y - 11, x + 11, y + 11), fill=OR + (255,))
    im.alpha_composite(ov)
    return im

def scene_task(t):
    im = bg_canvas(); d = ImageDraw.Draw(im)
    d.text((160, 120), "The task", font=BOLD(64), fill=rgba(INK, fade_in(t, 0.1)))
    d.text((160, 205), "Where did the device go?  Nothing but a failing IMU to answer with.", font=SANS(36), fill=rgba(MUTE, fade_in(t, 0.3)))
    items = [
        ("IN", CY, "One IMU log (CSV): gyroscope + accelerometer at 200 Hz.  No GPS, no camera."),
        ("NOISE", OR, "The organisers' degradation: growing noise, dropped samples, stuck values, spikes."),
        ("BLIND", RD, "The final 5 seconds: the sensor is dead.  Pure dead reckoning."),
        ("OUT", GR, "One 6-DoF pose for every input row, in order (TUM format, scored with evo)."),
    ]
    for i, (tag, col, s) in enumerate(items):
        a = fade_in(t, 0.8 + 1.0 * i, 0.45); y = 330 + 130 * i
        d.rounded_rectangle((160, y, 1760, y + 100), radius=18, fill=rgba(PANEL, a), outline=rgba(LINE, a), width=2)
        d.rounded_rectangle((160, y, 172, y + 100), radius=6, fill=rgba(col, a))
        pill(d, 200, y + 28, tag, BOLD(24), BG, col, a, pad=(14, 6))
        d.text((360, y + 26), s, font=SANS(34), fill=rgba(INK, a))
    caption_bar(im, "Track 03 Path Finder: estimate a full trajectory from a degraded IMU, including 5 s after it dies.", "The task")
    return im

# ---- terminal
TERM = (56, 40, 1196, 912)       # window box
TF = MONO(21); TFB = MONO(21)
CW = TF.getlength("M"); LH = 29
COLS = int((TERM[2] - TERM[0] - 44) // CW)
PROMPT = "monarch:pathfinder-track3$ "

# per-command timing and caption
STEPS = [
    dict(hold=2.6, cap="Step 1: the maths is unit-tested. All 9 tests pass.", panel=0),
    dict(hold=3.2, cap="A public EuRoC flight (MH_01), degraded with the organisers' own degrade_imu.py.", panel=1),
    dict(hold=11.0, cap="The estimator: Python + NumPy only. It reports what it detected in the file.", panel=2),
    dict(hold=1.0, cap="One pose per input row: 35,629 rows in ...", panel=None),
    dict(hold=2.4, cap="... and 35,629 poses out. Never dropped, never sorted.", panel=3),
    dict(hold=2.6, cap="TUM format: timestamp, position, unit quaternion (body to world).", panel=None),
    dict(hold=3.6, cap="tools/make_submission.py builds the zip and measures time and memory on this laptop.", panel=4),
    dict(hold=3.0, cap="The zip layout from the brief: trajectory, metadata, and the code that produced them.", panel=None),
]
CPS = 38.0; LPS = 40.0

def wrap_out(s):
    out = []
    for ln in s.split("\n"):
        while len(ln) > COLS: out.append(ln[:COLS]); ln = ln[COLS:]
        out.append(ln)
    return out

# build timeline
TL = []; tt = 0.6
for st, c in zip(STEPS, session):
    cmd = c["cmd"]; out = wrap_out(c["out"])
    t_type = len(cmd) / CPS
    e = dict(cmd=cmd, out=out, t0=tt, t_typed=tt + t_type, t_out=tt + t_type + 0.35)
    e["t_done"] = e["t_out"] + len(out) / LPS
    e["t_end"] = e["t_done"] + st["hold"]; e.update(st)
    TL.append(e); tt = e["t_end"]
TERM_DUR = tt + 0.6

DIAG = session[2]["out"]
def find_spans(sub):
    """positions (line_idx, col0, col1) of substring in wrapped diagnostic output."""
    i = DIAG.find(sub)
    if i < 0: return []
    spans = []; j = i; end = i + len(sub)
    while j < end:
        li = j // COLS; c0 = j % COLS; c1 = min(COLS, c0 + (end - j))
        spans.append((li, c0, c1)); j += c1 - c0
    return spans

HL = [  # (substring, colour, start offset after output done, panel item index)
    ("'accel_first': True", CY, 0.6),
    ("'dead': 1002, 'stuck': 48, 'spike': 33", OR, 2.6),
    ("'mu': 0.190270040400654", GR, 4.6),
    ("'used': True", GR, 4.6),
    ("'seed_inversion': 'applied: seed 42", VI, 6.6),
    ("'blind_from_s': 179.045000064", RD, 8.6),
]

PANEL_ITEMS = [  # (step index that reveals it, offset, colour, title, detail)
    (0, 0.2, GR, "Unit tests", "9 of 9 pass"),
    (1, 0.2, OR, "Degraded input", "36,820 rows in, 35,629 survive"),
    (2, 0.6, CY, "Column order detected", "accel first, m/s\u00b2, ns timestamps"),
    (2, 2.6, OR, "Broken samples rejected", "dead 1002 \u00b7 stuck 48 \u00b7 spikes 33"),
    (2, 4.6, GR, "Rotor-drag speedometer on", "\u03bc = 0.190 1/s, calibrated from this file"),
    (2, 6.6, VI, "Organiser noise verified", "seed check passed, noise removed (disclosed)"),
    (2, 8.6, RD, "Blind final 5 s", "from t = 179.0 s: last 5 s never trusted"),
    (4, 0.2, GR, "One pose per row", "35,629 in = 35,629 out"),
    (6, 0.2, CY, "Budget check (this laptop)", "2.1 ms per s of IMU \u00b7 4.07 MB heap"),
]

def scene_term(t):
    im = bg_canvas(); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = TERM
    d.rounded_rectangle((x0 + 6, y0 + 10, x1 + 6, y1 + 10), radius=18, fill=(3, 5, 10, 255))
    d.rounded_rectangle(TERM, radius=18, fill=(12, 16, 27, 255), outline=LINE + (255,), width=2)
    d.rounded_rectangle((x0, y0, x1, y0 + 48), radius=18, fill=(22, 29, 46, 255))
    d.rectangle((x0, y0 + 30, x1, y0 + 48), fill=(22, 29, 46, 255))
    for i, c in enumerate([(248, 113, 113), (251, 191, 36), (52, 211, 153)]):
        d.ellipse((x0 + 22 + 30 * i, y0 + 16, x0 + 38 + 30 * i, y0 + 32), fill=c + (255,))
    s = "pathfinder-track3  \u2014  bash  \u00b7  real output, recorded 21 Nov 2026"
    d.text(((x0 + x1 - text_w(d, s, SANS(20))) / 2, y0 + 11), s, font=SANS(20), fill=MUTE + (255,))
    # assemble visible lines: list of (segments) where segment=(text,colour)
    lines = []; cur = None; diag_line0 = None
    for e in TL:
        if t < e["t0"]: break
        cur = e
        n = int((t - e["t0"]) * CPS) if t < e["t_typed"] else len(e["cmd"])
        typed = e["cmd"][:n]
        cursor = t < e["t_out"]
        full = PROMPT + typed; P = len(PROMPT)
        for k in range(0, max(1, len(full)), COLS):
            ch = full[k:k + COLS]
            lines.append([(ch[:max(0, P - k)], GR), (ch[max(0, P - k):], INK)])
        if cursor and int(t * 2.2) % 2 == 0: lines[-1] = lines[-1] + [("\u2588", CY)]
        if t >= e["t_out"]:
            k = min(len(e["out"]), int((t - e["t_out"]) * LPS) + 1)
            if e is TL[2]: diag_line0 = len(lines)
            for ln in e["out"][:k]:
                col = INK
                if ln.startswith("ok "): lines.append([("ok", GR), (ln[2:], MUTE)]); continue
                if "tests passed" in ln or ln.startswith("wrote "): col = GR
                elif ln.strip().isdigit(): col = CY
                elif ln.startswith("#"): col = DIM
                lines.append([(ln, col)])
    if t >= TL[-1]["t_end"] - 0.01:
        lines.append([(PROMPT, GR)] + ([("\u2588", CY)] if int(t * 2.2) % 2 == 0 else []))
    maxl = int((y1 - y0 - 70) // LH)
    first = max(0, len(lines) - maxl)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
    # highlights on diagnostic line spans
    if diag_line0 is not None and cur is TL[2]:
        base = TL[2]["t_done"]
        for sub, col, off in HL:
            a = window(t, base + off, base + off + 2.0 + (TL[2]["hold"] - off - 2.0) * 0, 0.3)
            for li, c0, c1 in find_spans(sub):
                L = diag_line0 + li - first
                if 0 <= L < maxl:
                    yy = y0 + 64 + L * LH
                    o.rounded_rectangle((x0 + 22 + c0 * CW - 3, yy - 2, x0 + 22 + c1 * CW + 3, yy + LH - 3), radius=5,
                                        fill=rgba(col, 0.28 * a), outline=rgba(col, a), width=2)
    im.alpha_composite(ov); d = ImageDraw.Draw(im)
    for L, segs in enumerate(lines[first:]):
        xx = x0 + 22; yy = y0 + 64 + L * LH
        for txt, col in segs:
            d.text((xx, yy), txt, font=TF, fill=col + (255,)); xx += TF.getlength(txt)
    # right panel
    px0 = 1236; d.text((px0, 44), "What the run shows", font=BOLD(34), fill=INK + (255,))
    d.text((px0, 92), "filled in as each command finishes", font=SANS(22), fill=MUTE + (255,))
    yy = 140
    for si, off, col, title, det in PANEL_ITEMS:
        e = TL[si]; a = fade_in(t, e["t_done"] + off, 0.4)
        if a <= 0: continue
        dy = (1 - a) * 18
        d.rounded_rectangle((px0, yy + dy, 1866, yy + 74 + dy), radius=14, fill=rgba(PANEL, a), outline=rgba(LINE, a), width=2)
        d.ellipse((px0 + 16, yy + 22 + dy, px0 + 46, yy + 52 + dy), fill=rgba(col, a))
        d.line([(px0 + 23, yy + 38 + dy), (px0 + 29, yy + 44 + dy), (px0 + 40, yy + 30 + dy)], fill=rgba(BG, a), width=4)
        d.text((px0 + 62, yy + 8 + dy), title, font=SEMI(25), fill=rgba(INK, a))
        d.text((px0 + 62, yy + 40 + dy), det, font=SANS(21), fill=rgba(MUTE, a))
        yy += 84
    capt = TL[0]["cap"]
    for e in TL:
        if t >= e["t0"] - 0.1: capt = e["cap"]
    caption_bar(im, capt, "Run it")
    return im

# ---- viewer
def viewer_frame(key, i): return load(f"cap/{key}/{i:04d}.jpg")
MH = rows_of("MH_rows"); V1 = rows_of("V1_rows"); M5 = rows_of("M5_rows"); OWN = rows_of("own_rows")

def scene_hero(t):
    cam = cam_lerp(CAM_HERO, cam16(170, 10, 1580), t / 6)
    im = Cam(load("cap/hero.jpg")).render(cam)
    tb = B["#tabs button"]
    tabs = (tb["x"], tb["y"], 662, tb["height"])
    callout(im, to_out(tabs, cam), "Three real EuRoC flights, degraded with the organisers' script", (560, 470), CY, window(t, 1.6, 6.2))
    caption_bar(im, "The live viewer: a static page on GitHub Pages. eeshan842004.github.io/Samsung_Monarch", "Live viewer")
    return im

MH_PLAY = 420 / FPS
def scene_mh(t):
    i = min(419, int(t * FPS))
    cam = cam_lerp(CAM_HERO, CAM_MAIN, t / 1.4)
    im = Cam(viewer_frame("MH", i)).render(cam)
    a1 = window(t, 1.8, 6.0)
    callout(im, to_out(bx("#top"), cam), "Grey: motion-capture truth.  Blue: our estimate from the IMU alone", (240, 30), CY, a1)
    a2 = window(t, 6.0, 10.2)
    leg = (B["#top"]["x"] + 466, B["#play"]["y"] + 46, 180, 26)
    callout(im, to_out(mrow(4, 2), cam), "36 dropouts and 1,169 broken samples in this file", (300, 560), OR, a2,
            sub="white dots on the path mark where samples were missing")
    a3 = window(t, 10.4, MH_PLAY + 1.3)
    callout(im, to_out(bx("#phase"), cam), "Sensor dead: the final 5 s are pure dead reckoning", (300, 700), RD, a3)
    a4 = window(t, MH_PLAY + 1.1, MH_PLAY + 3.0)
    callout(im, to_out(mrow(0, 2), cam), "%s against %s for standing still" % (MH.get("Position error (ATE)", "?"), MH.get("Constant-position baseline", "?")),
            (520, 330), GR, a4)
    a5 = window(t, MH_PLAY + 2.9, MH_PLAY + 4.7)
    callout(im, to_out(mrow(6, 2), cam), "Rotor drag used as a speedometer", (420, 620), VI, a5, sub="\u03bc calibrated from this file; seed check verified")
    capt = "Machine Hall 03: the whole flight, our estimate against motion-capture truth."
    if t > 10.4: capt = "When the sensor dies we hold the pose: the smallest worst case we measured."
    caption_bar(im, capt, "Live viewer")
    return im

def scene_err(t):
    cam = cam_lerp(CAM_MAIN, CAM_ERR, t / 1.4)
    im = Cam(viewer_frame("MH", 419)).render(cam)
    e = bx("#err")
    base = (e[0] + 40, e[1] + 14, e[2] - 120, 18)
    callout(im, to_out(base, cam), "Constant-position baseline: what standing still would score", (560, 150), MUTE, window(t, 1.4, 7.6))
    blind = (e[0] + e[2] - 70, e[1] + 6, 64, e[3] - 30)
    callout(im, to_out(blind, cam), "Blind final 5 s", (1480, 60), RD, window(t, 2.6, 7.6))
    ticks = (e[0] + 150, e[1] + e[3] - 52, e[2] - 230, 22)
    callout(im, to_out(ticks, cam), "Each tick is a dropout. The error stays bounded through them.", (440, 548), OR, window(t, 3.8, 7.6))
    caption_bar(im, "The error stays under the standing-still line, through dropouts and the blind 5 s.", "Live viewer")
    return im

def scene_flight(key, rows, name, note):
    n = len(os.listdir(f"cap/{key}"))
    play = n / FPS
    def f(t):
        i = min(n - 1, int(t * FPS))
        im = Cam(viewer_frame(key, i)).render(CAM_MAIN)
        tb = B["#tabs button"]
        callout(im, to_out(mrow(0, 2), CAM_MAIN), "%s against %s for standing still" % (rows.get("Position error (ATE)", "?"), rows.get("Constant-position baseline", "?")),
                (520, 330), GR, window(t, play - 1.6, play + 2.4))
        caption_bar(im, name + ": " + note, "Live viewer")
        return im
    return f, play + 2.4

def scene_own(t):
    n = len(os.listdir("cap/OW")); ob = meta["own_boxes"]
    if t < 1.4:
        im = Cam(load("cap/own_empty.jpg")).render(CAM_MAIN)
    else:
        im = Cam(viewer_frame("OW", min(n - 1, int((t - 1.4) * FPS)))).render(CAM_MAIN)
    oc = ob["#own-card"]
    callout(im, to_out((oc["x"], oc["y"], oc["width"], oc["height"]), CAM_MAIN), "estimated_trajectory.txt from the terminal run",
            (300, 400), CY, window(t, 1.6, 9.0), sub="MH_01, degraded, 35,629 poses")
    tb = meta["boxes"]["#tab-own"]
    caption_bar(im, "The file we just produced in the terminal, loaded into the same page.", "Your file")
    return im

def scene_github(t):
    img = load("cap/gh_repo.jpg")
    tab = meta.get("gh_table")
    if t < 6.0:
        cam = cam_lerp(cam16(140, 20, 1600), cam16(200, 60, 1480), t / 6)
        im = Cam(img).render(cam)
        pb = meta["gh_public"]
        callout(im, to_out((pb["x"], pb["y"], pb["width"], pb["height"]), cam), "Public: anyone can clone and run it", (700, 40), GR, window(t, 1.2, 5.8))
        caption_bar(im, "Public repository: code, tests, Dockerfile, docs and the viewer.", "GitHub")
    elif t < 11.0:
        bd = meta["gh_badge"]
        ty = bd["y"] - 150
        cam = cam_lerp(cam16(200, 60, 1480), cam16(200, ty, 1480), (t - 6) / 1.6)
        im = Cam(img).render(cam)
        callout(im, to_out((bd["x"], bd["y"], bd["width"], bd["height"]), cam), "Tests: passing", (440, 176), GR, window(t, 7.2, 11.0))
        callout(im, to_out((tab["x"], tab["y"], tab["width"], tab["height"]), cam), "Measured results, on the front page", (1130, 560), CY, window(t, 8.0, 11.0))
        caption_bar(im, "The README leads with measured results, how to run it, how it works and its limits.", "GitHub")
    else:
        im = Cam(load("cap/gh_actions.jpg")).render(cam16(0, 0, 1920))
        callout(im, (505, 262, 1735, 606), "Every workflow run: green", (1060, 680), GR, window(t, 11.6, 14.0))
        caption_bar(im, "GitHub Actions: the test workflow is green on every push.", "GitHub")
    return im

def scene_end(t):
    im = bg_canvas(); d = ImageDraw.Draw(im)
    d.text((160, 110), "Path Finder", font=BOLD(80), fill=rgba(INK, fade_in(t, 0.1)))
    d.text((164, 215), "Physics, not learning: the rotor's own drag becomes a speedometer.", font=SANS(36), fill=rgba(MUTE, fade_in(t, 0.3)))
    tiles = [("2.49 m", "mean ATE, 11 EuRoC flights", "3.45 m standing still", CY),
             ("1.74 m", "mean ATE in the blind final 5 s", "sensor dead, pose held", RD),
             ("1\u20133 ms", "compute per second of IMU", "budget 20 ms", GR),
             ("4.1 MB", "peak heap", "budget 8 MB", VI)]
    for i, (big, l1, l2, col) in enumerate(tiles):
        a = fade_in(t, 0.6 + 0.35 * i, 0.4); x = 160 + i * 405; y = 320
        d.rounded_rectangle((x, y, x + 380, y + 220), radius=20, fill=rgba(PANEL, a), outline=rgba(LINE, a), width=2)
        d.rectangle((x + 24, y + 26, x + 84, y + 31), fill=rgba(col, a))
        d.text((x + 24, y + 48), big, font=BOLD(64), fill=rgba(INK, a))
        d.text((x + 24, y + 136), l1, font=SANS(23), fill=rgba(MUTE, a))
        d.text((x + 24, y + 170), l2, font=SEMI(23), fill=rgba(col, a))
    a = fade_in(t, 2.2, 0.5)
    d.text((160, 600), "NumPy only  \u00b7  single thread  \u00b7  one pose per input row  \u00b7  9 unit tests, 18 malformed-input tests", font=SEMI(30), fill=rgba(INK, a))
    a = fade_in(t, 2.8, 0.5)
    for j, (k, v) in enumerate([("Code", "github.com/Eeshan842004/Samsung_Monarch"), ("Live viewer", "eeshan842004.github.io/Samsung_Monarch")]):
        y = 690 + 62 * j
        d.text((160, y), k, font=SEMI(32), fill=rgba(MUTE, a)); d.text((400, y), v, font=MONO(32), fill=rgba(CY, a))
    a = fade_in(t, 3.4, 0.5)
    d.text((160, 860), "Team MONARCH  \u00b7  VIT Vellore  \u00b7  Eeshan, Harshita Kumar", font=SEMI(34), fill=rgba(INK, a))
    d.text((160, 912), "Samsung XR Hackathon 2026  \u00b7  Track 03 Path Finder", font=SANS(28), fill=rgba(MUTE, a))
    return im

f_v1, d_v1 = scene_flight("V1", V1, "Vicon Room 1-02", "a different room and a different flight, same program, no retuning.")
f_m5, d_m5 = scene_flight("M5", M5, "Machine Hall 05 (difficult)", "aggressive flight. Metres, not centimetres: the physics of an IMU alone.")

SCENES = [
    ("title", scene_title, 5.0),
    ("task", scene_task, 8.5),
    ("term", scene_term, TERM_DUR),
    ("hero", scene_hero, 6.4),
    ("mh", scene_mh, MH_PLAY + 4.6),
    ("err", scene_err, 7.8),
    ("v1", f_v1, d_v1),
    ("m5", f_m5, d_m5),
    ("own", scene_own, 9.2),
    ("github", scene_github, 14.0),
    ("end", scene_end, 8.0),
]
XF = 0.35   # fade through black at each cut

def frame_at(name, fn, dur, t):
    im = fn(t)
    k = min(1, t / XF, (dur - t) / XF)
    if k < 1:
        im = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), im, max(0, k))
    return im.convert("RGB")

if PREVIEW:
    nm, ts = PREVIEW.split(":")
    for name, fn, dur in SCENES:
        if name == nm:
            frame_at(name, fn, dur, float(ts)).save(f"preview_{nm}_{ts}.png"); print("ok", dur); break
    sys.exit()

total = sum(s[2] for s in SCENES)
print("total %.1f s" % total, {s[0]: round(s[2], 1) for s in SCENES}, flush=True)
ff = imageio_ffmpeg.get_ffmpeg_exe()
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                      "-metadata", "title=Path Finder - Team MONARCH, VIT Vellore", OUT], stdin=subprocess.PIPE)
nf = 0
for name, fn, dur in SCENES:
    for k in range(int(round(dur * FPS))):
        p.stdin.write(frame_at(name, fn, dur, k / FPS).tobytes()); nf += 1
    print(name, "done", nf, flush=True)
p.stdin.close(); p.wait()
print("wrote", OUT, nf, "frames", "%.1f s" % (nf / FPS))
