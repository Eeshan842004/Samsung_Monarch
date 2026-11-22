"""Fills the organisers' submission template with the Path Finder content.
Every number here comes from tools in the repository (see docs/SPEC.md)."""
import copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.oxml.ns import qn

SRC = "structured.pptx"
OUT = "VITVellore_Monarch.pptx"
INK = RGBColor(0xE8, 0xED, 0xF5); MUTE = RGBColor(0x9A, 0xA7, 0xB4); CARD = RGBColor(0x12, 0x1A, 0x2E)
CARD2 = RGBColor(0x0D, 0x1B, 0x3E); CYAN = RGBColor(0x00, 0xB4, 0xD8); TEAL = RGBColor(0x00, 0xE5, 0xB0)
AMBER_T = RGBColor(0xF5, 0x9E, 0x0B); OURS = RGBColor(0x0E, 0x9C, 0xC2); AMBER = RGBColor(0xD0, 0x7E, 0x08)
TRUTH = RGBColor(0x8A, 0x94, 0xA0); GRID = RGBColor(0x1E, 0x2A, 0x3E); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"; MONO = "Courier New"

prs = Presentation(SRC)
S = list(prs.slides)


def text(slide, x, y, w, h, paras, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         font=FONT, name=None, space_after=4, line=None):
    """paras: list of paragraphs; a paragraph is a str or a list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(space_after)
        if line:
            para.line_spacing = line
        runs = [(p, {})] if isinstance(p, str) else p
        for t, o in runs:
            r = para.add_run(); r.text = t
            f = r.font; f.name = o.get("font", font); f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False); f.color.rgb = o.get("color", color)
    return tb


def bullets(slide, x, y, w, h, items, size=14, color=INK, name=None, gap=6):
    tb = text(slide, x, y, w, h, items, size=size, color=color, name=name, space_after=gap)
    for para in tb.text_frame.paragraphs:
        pPr = para._p.get_or_add_pPr()
        pPr.set("marL", str(Emu(Inches(0.2)))); pPr.set("indent", str(-Emu(Inches(0.2))))
        for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
            for e in pPr.findall(qn(tag)):
                pPr.remove(e)
        bc = pPr.makeelement(qn("a:buClr"), {}); sc = bc.makeelement(qn("a:srgbClr"), {"val": "00B4D8"}); bc.append(sc)
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        pPr.append(bc); pPr.append(bu)
    return tb


def box(slide, x, y, w, h, fill=CARD, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None, radius=0.08):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1)
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.text_frame.text = ""
    return s


def set_header(slide, title):
    for sh in slide.shapes:
        if sh.name == "Text 2" and sh.has_text_frame:
            r = sh.text_frame.paragraphs[0].runs
            r[0].text = title
            for extra in r[1:]:
                extra.text = ""


def drop_empty_textboxes(slide):
    for sh in list(slide.shapes):
        if sh.shape_type == 17 and sh.has_text_frame and not sh.text_frame.text.strip():
            sh._element.getparent().remove(sh._element)


def headline(slide, t, color=WHITE):
    text(slide, 0.5, 1.05, 9.0, 0.5, [t], size=22, bold=True, color=color, name="Headline")


def caption(slide, x, y, w, t, name="Caption"):
    text(slide, x, y, w, 0.3, [t], size=10, color=MUTE, name=name)


def style_chart(chart, colors, maxv, fmt='0.00" m"', cat_size=12, horizontal=False):
    chart.has_legend = False
    chart.has_title = False
    chart.font.name = FONT; chart.font.size = Pt(12); chart.font.color.rgb = INK
    plot = chart.plots[0]; plot.gap_width = 60; plot.vary_by_categories = False
    ser = plot.series[0]
    for i, c in enumerate(colors):
        pt = ser.points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = c; pt.format.line.fill.background()
    plot.has_data_labels = True
    dl = plot.data_labels; dl.number_format = fmt; dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END; dl.font.size = Pt(13); dl.font.bold = True; dl.font.color.rgb = INK
    va = chart.value_axis; va.maximum_scale = maxv; va.minimum_scale = 0
    va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = GRID; va.major_gridlines.format.line.width = Pt(0.75)
    va.format.line.fill.background(); va.tick_labels.font.color.rgb = MUTE; va.tick_labels.font.size = Pt(10)
    va.visible = False
    ca = chart.category_axis; ca.format.line.color.rgb = GRID; ca.tick_labels.font.color.rgb = INK; ca.tick_labels.font.size = Pt(cat_size)
    ca.has_major_gridlines = False


def stat(slide, x, y, w, big, label, color=CYAN, big_size=30, name="Stat", h=1.0):
    box(slide, x, y, w, h, fill=CARD, name=name + " card")
    text(slide, x + 0.15, y + 0.06, w - 0.3, 0.5, [big], size=big_size, bold=True, color=color, name=name + " value")
    text(slide, x + 0.15, y + h - 0.36, w - 0.3, 0.3, [label], size=11, color=MUTE, name=name + " label")


# ---------------------------------------------------------------- 1. title
s = S[0]
for sh in s.shapes:
    if sh.name == "Text 7":
        sh.text_frame.paragraphs[0].runs[0].text = "Track 03"
    if sh.name == "Text 8":
        sh.text_frame.paragraphs[0].runs[0].text = "Path Finder"
    if sh.name == "Text 10":
        ps = sh.text_frame.paragraphs
        ps[0].runs[0].text = "Team MONARCH"
        ps[1].runs[0].text = "VIT Vellore"
    if sh.name == "Text Box 22":
        ps = sh.text_frame.paragraphs
        ps[0].runs[0].text = "Eeshan"
        np_ = copy.deepcopy(ps[0]._p); ps[0]._p.addnext(np_)
        sh.text_frame.paragraphs[1].runs[0].text = "Harshita Kumar"
text(s, 0.55, 3.75, 7.6, 0.9, [
    "IMU-only 6-DoF trajectory estimation under sensor degradation",
    [("Physics, not learning: the rotor's own drag becomes a speedometer", {"color": CYAN, "italic": True})]],
    size=16, color=INK, name="Subtitle", space_after=6)

# ---------------------------------------------------------------- 2. problem
s = S[1]
headline(s, "One IMU, no GPS, no camera: and the sensor fails")
bullets(s, 0.5, 1.75, 4.6, 2.6, [
    "Noise, bias drift, spikes, stuck samples and missing rows grow over the flight, then the IMU dies",
    "Estimate every pose, and dead-reckon the final 5 s with no sensor at all",
    "Budget: 8 MB heap, 20 ms per second of data, one thread, Python",
    [("Honest baseline: ", {"bold": True}), ("outputting a constant position already scores 3.45 m. A drifting estimator does worse than standing still", {})],
], size=15, name="Problem bullets", gap=8)
text(s, 5.45, 1.72, 4.0, 0.3, ["Integrating the IMU twice, even with a perfect start"], size=12, color=MUTE, name="Drift label")
for i, (v, l) in enumerate((("0.87 m", "after 5 s"), ("38 m", "after 20 s"), ("893 m", "after 80 s"))):
    stat(s, 5.45, 2.08 + i * 1.0, 4.0, v, l, color=AMBER_T if i else CYAN, big_size=26, name="Drift %d" % i, h=0.88)
caption(s, 5.45, 5.06, 4.0, "EuRoC V1_01, dataset bias estimates and true initial state")

# ---------------------------------------------------------------- 3. solution
s = S[2]
headline(s, "Integrate once, then fit the drift as a physical curve")
cards = [
    ("1", "Fit the drift, don't filter it", "Drift is the double integral of a few sensor errors, and it is linear in them. One least-squares solve under a bounded-motion prior removes it."),
    ("2", "Rotor drag is a speedometer", "Perpendicular to thrust, a multirotor's accelerometer feels only drag, f = -μ v. μ is calibrated from each file; the model switches off when the effect is absent."),
    ("3", "Every dropout is an unknown", "Each gap over 0.3 s gets its own rotation and velocity jump. The final 5 s are never trusted; the pose is held."),
]
for i, (n, t, d) in enumerate(cards):
    x = 0.5 + i * 3.07
    box(s, x, 1.8, 2.85, 3.3, fill=CARD, name="Card %s" % n)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.25), Inches(2.05), Inches(0.55), Inches(0.55))
    c.name = "Badge %s" % n; c.fill.solid(); c.fill.fore_color.rgb = TEAL; c.line.fill.background(); c.shadow.inherit = False
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = n
    r.font.size = Pt(18); r.font.bold = True; r.font.color.rgb = RGBColor(0x0A, 0x0E, 0x1A); r.font.name = FONT
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    text(s, x + 0.25, 2.8, 2.4, 0.7, [t], size=17, bold=True, color=WHITE, name="Card %s title" % n)
    text(s, x + 0.25, 3.5, 2.4, 1.55, [d], size=13, color=INK, name="Card %s text" % n, line=1.05)

# ---------------------------------------------------------------- 4. architecture
s = S[3]
headline(s, "One streaming pass in, one small solve, one pass out")
steps = [("Scan", "timestamps, column order, units"), ("Clean + preintegrate", "reject dead, stuck, spike rows; 20 Hz nodes"),
         ("Batch fit", "gyro bias, accel bias, tilt, drag, gap jumps"), ("Pose per row", "interpolate; hold in the blind 5 s"),
         ("TUM file", "one line per input row")]
bw, gap, y0 = 1.62, 0.22, 1.85
for i, (t, d) in enumerate(steps):
    x = 0.5 + i * (bw + gap)
    hl = i == 2
    box(s, x, y0, bw, 1.45, fill=CARD2 if hl else CARD, line=CYAN if hl else None, name="Step %d" % (i + 1))
    text(s, x + 0.12, y0 + 0.14, bw - 0.24, 0.55, [t], size=14, bold=True, color=CYAN if hl else WHITE, name="Step %d title" % (i + 1))
    text(s, x + 0.12, y0 + 0.68, bw - 0.24, 0.75, [d], size=11, color=INK, name="Step %d text" % (i + 1))
    if i < len(steps) - 1:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.03), Inches(y0 + 0.6), Inches(gap - 0.06), Inches(0.25))
        a.name = "Arrow %d" % (i + 1); a.fill.solid(); a.fill.fore_color.rgb = MUTE; a.line.fill.background(); a.shadow.inherit = False
facts = [("2048-row chunks", "memory follows nodes, not rows"), ("about 85 unknowns", "three relinearisations"),
         ("seed check, optional", "removes the organiser noise only if verified"), ("NumPy only", "Docker, single thread")]
for i, (t, d) in enumerate(facts):
    x = 0.5 + i * 2.28
    text(s, x, 3.65, 2.1, 0.3, [t], size=14, bold=True, color=TEAL, name="Fact %d" % i)
    text(s, x, 3.98, 2.1, 0.6, [d], size=12, color=MUTE, name="Fact %d text" % i)
text(s, 0.5, 4.75, 9.0, 0.5, [[("Model: ", {"bold": True, "color": WHITE}),
     ("p_nom = p_true + p0 + v0 t + ∬(R b_a + G(ψ_y, −ψ_x, 0) + s(t))", {"font": MONO, "size": 12}), ("   linear in every unknown", {"color": MUTE, "size": 12})]],
     size=13, color=INK, name="Model line")

# ---------------------------------------------------------------- 5. track final output
s = S[4]
set_header(s, "TRACK FINAL OUTPUT")
headline(s, "2.49 m where standing still scores 3.45 m")
s.shapes.add_picture("fig/trajectory.png", Inches(0.5), Inches(1.65), height=Inches(3.45)).name = "Trajectory figure"
caption(s, 0.5, 5.12, 4.6, "MH_03 (near-median flight), degraded input: ATE 2.13 m vs 3.58 m constant. Amber dot: end of blind 5 s")
cd = CategoryChartData(); cd.categories = ["Constant", "Drift fit only", "Ours"]; cd.add_series("Mean ATE", (3.45, 3.11, 2.49))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(5.25), Inches(1.6), Inches(4.25), Inches(2.25), cd)
gf.name = "ATE chart"; style_chart(gf.chart, [TRUTH, TRUTH, OURS], 4.2)
text(s, 5.3, 3.85, 4.2, 0.3, ["Mean ATE, 11 EuRoC flights, degraded input"], size=10, color=MUTE, name="Chart caption")
stat(s, 5.25, 4.15, 1.35, "1.74 m", "blind 5 s ATE", big_size=20, name="Blind")
stat(s, 6.7, 4.15, 1.35, "1-3 ms", "per s; budget 20", big_size=20, name="Time")
stat(s, 8.15, 4.15, 1.35, "4.1 MB", "heap; budget 8", big_size=20, name="Heap")

# ---------------------------------------------------------------- 6. differentiation
s = S[5]
headline(s, "The vehicle tells us its own speed")
s.shapes.add_picture("fig/drag.png", Inches(0.5), Inches(1.65), height=Inches(3.3)).name = "Drag figure"
caption(s, 0.5, 4.98, 4.3, "V1_02, 1 s means. Ground-truth velocity is used here only to show the effect")
box(s, 5.05, 1.7, 4.45, 0.7, fill=CARD2, name="Equation card")
text(s, 5.2, 1.78, 4.2, 0.55, [[("f", {"bold": True}), ("⊥", {}), (" = −μ v", {"bold": True}), ("⊥", {}), (" + c", {"bold": True})]],
     size=24, color=CYAN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="Equation")
bullets(s, 5.05, 2.6, 4.45, 2.6, [
    [("Calibrated per file: ", {"bold": True}), ("μ = 0.14 to 0.22 1/s, no ground truth", {})],
    [("Null test: ", {"bold": True}), ("shift the force by 37 s and the model switches off on 11 of 11 flights", {})],
    [("Leave-one-out μ: ", {"bold": True}), ("2.486 m vs 2.489 m self-calibrated", {})],
    [("Hand-held data: ", {"bold": True}), ("stays off on 6 of 6, no harm", {})],
    [("Disclosed seed check: ", {"bold": True}), ("removes the organiser noise only when proven", {})],
], size=13, name="Differentiation bullets", gap=6)

# ---------------------------------------------------------------- 7. demo & local setup
s = S[6]
drop_empty_textboxes(s)
headline(s, "One command, one file, one pose per row")
box(s, 0.5, 1.7, 4.4, 2.35, fill=RGBColor(0x05, 0x08, 0x10), line=GRID, name="Terminal")
text(s, 0.68, 1.85, 4.1, 2.1, [
    [("$ ", {"color": TEAL}), ("pip install numpy", {})],
    [("$ ", {"color": TEAL}), ("python src/main.py data.csv \\", {})],
    [("      estimated_trajectory.txt", {})],
    [("$ ", {"color": TEAL}), ("docker build -t pathfinder .", {})],
    [("$ ", {"color": TEAL}), ("python tools/make_submission.py \\", {})],
    [("      VITVellore_Monarch data.csv", {})],
], size=12, font=MONO, color=INK, name="Commands", space_after=3)
bullets(s, 0.5, 4.2, 4.4, 1.1, [
    "GitHub: github.com/Eeshan842004/Samsung_Monarch",
    "Live viewer: eeshan842004.github.io/Samsung_Monarch",
], size=12, name="Links", gap=4)
s.shapes.add_picture("fig/viewer_crop.png", Inches(5.1), Inches(1.7), width=Inches(4.4)).name = "Viewer screenshot"
caption(s, 5.1, 3.85, 4.4, "Static viewer (one HTML file): top and side views, dropouts and blind window marked, ATE preview")
box(s, 5.1, 4.3, 4.4, 0.95, fill=RGBColor(0x05, 0x08, 0x10), line=GRID, name="Output snippet")
text(s, 5.25, 4.38, 4.15, 0.8, [
    [("estimated_trajectory.txt", {"color": TEAL, "font": FONT, "bold": True}), ("   26189 input rows, 26189 poses", {"color": MUTE, "font": FONT})],
    "1403637130.498319104 -0.058140 -0.563933 ...",
    "1403637130.503319040 -0.057883 -0.564000 ...",
], size=10, font=MONO, color=INK, name="Output lines", space_after=2)

# ---------------------------------------------------------------- 8. brownie: robustness
s = S[7]
set_header(s, "BROWNIE: ROBUSTNESS")
drop_empty_textboxes(s)
headline(s, "Stress-tested, and checked on flights never used for tuning")
rows = [("Scenario (mean ATE)", "Ours", "Constant"),
        ("Organiser script, seed 42", "2.49 m", "3.45 m"),
        ("Three other random seeds", "2.53 to 2.60 m", "3.45 m"),
        ("2 s dropouts (gap model off: 3.53 m)", "2.65 m", "3.45 m"),
        ("Blind window cut mid-flight (33 files)", "2.85 m", "n/a"),
        ("5 held-out flights, settings from the other 6", "2.48 to 2.59 m (worst variant 3.15 m)", "3.40 m"),
        ("Hand-held TUM-VI rooms (drag off)", "0.73 m", "1.08 m"),
        ("Python 3.11 + NumPy 1.26 vs 3.13 + NumPy 2.5", "same within 0.2 mm", "")]
tbl = s.shapes.add_table(len(rows), 3, Inches(0.5), Inches(1.7), Inches(9.0), Inches(3.3)).table
tbl.columns[0].width = Inches(5.4); tbl.columns[1].width = Inches(2.0); tbl.columns[2].width = Inches(1.6)
for r, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c); cell.fill.solid(); cell.fill.fore_color.rgb = CARD2 if r == 0 else (CARD if r % 2 else RGBColor(0x0E, 0x14, 0x24))
        cell.margin_left = Inches(0.12); cell.margin_top = cell.margin_bottom = Inches(0.04)
        tf = cell.text_frame; tf.text = ""; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
        run = p.add_run(); run.text = val; run.font.name = FONT; run.font.size = Pt(13)
        run.font.bold = r == 0 or c == 1; run.font.color.rgb = (CYAN if c == 1 and r else (WHITE if r == 0 else INK))
for r in range(len(rows)):
    for c in range(3):
        tcPr = tbl.cell(r, c)._tc.get_or_add_tcPr()
        for side in ("a:lnB", "a:lnT", "a:lnR", "a:lnL"):
            ln = tcPr.makeelement(qn(side), {"w": "6350"}); sf = ln.makeelement(qn("a:solidFill"), {})
            sf.append(sf.makeelement(qn("a:srgbClr"), {"val": "1E2A3E"})); ln.append(sf); tcPr.insert(0, ln)
caption(s, 0.5, 5.12, 9.0, "18 malformed-input cases (no header, either column order, g units, deg/s, NaN or noise tail, duplicates, 2-row file) all give one valid pose per row")

# ---------------------------------------------------------------- 9. brownie: error budget and limits
s = S[8]
set_header(s, "BROWNIE: WHERE THE ERROR COMES FROM")
drop_empty_textboxes(s)
headline(s, "Attitude is solved; slow velocity is the physical limit")
cd = CategoryChartData()
cd.categories = ["Full pipeline", "Our velocity, true attitude", "Our attitude, true velocity"]
cd.add_series("ATE", (2.49, 2.49, 0.15))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1.65), Inches(5.0), Inches(2.6), cd)
gf.name = "Error budget chart"; style_chart(gf.chart, [OURS, AMBER, TRUTH], 3.2, cat_size=12)
gf.chart.category_axis.reverse_order = True
text(s, 0.5, 4.3, 5.0, 0.8, ["Mean ATE, 11 clean EuRoC flights. Swapping in the true velocity removes almost all error; swapping in the true attitude removes none."],
     size=11, color=MUTE, name="Budget caption")
box(s, 5.75, 1.7, 3.75, 3.2, fill=CARD, name="Limits card")
text(s, 5.95, 1.82, 3.4, 0.35, ["Honest limits"], size=16, bold=True, color=WHITE, name="Limits title")
bullets(s, 5.95, 2.25, 3.4, 2.85, [
    "Metres, not centimetres: in-plane accel bias / μ ≈ 0.05 / 0.19 = 0.26 m/s of velocity no IMU can see",
    "Heading drifts without a rest at the start",
    "Raw column order + unverifiable seed: 3.25 m",
    "Drag validated on one airframe",
], size=14, name="Limits", gap=8)

# ---------------------------------------------------------------- notes
notes = {
    0: "Track 03, Path Finder. IMU-only trajectory estimation. Our idea in one line: physics, not learning; the multirotor's own rotor drag gives us its speed.",
    1: "An IMU drifts by tens of metres in seconds even with a perfect start. The honest baseline is to output a constant position: 3.45 m on EuRoC. Any estimator that drifts is worse than that.",
    2: "Three ideas. Fit the drift as a curve. Use rotor drag as a speedometer. Model each dropout as unknowns and never trust the blind window.",
    3: "The file is streamed once into 20 Hz preintegration nodes, one small linear solve removes the drift, and every input row gets a pose from its timestamp.",
    4: "Mean ATE 2.49 m on 11 EuRoC flights with the organiser degradation, against 3.45 m for a constant and 3.11 m without the drag model. 1 to 3 ms per second of data and 4.1 MB.",
    5: "The scatter shows the physics: in-plane force falls linearly with velocity. We calibrate the coefficient from each file and prove it is physics with a null test.",
    6: "One command produces the submission file. The viewer shows our path against the truth, with dropouts and the blind window marked.",
    7: "Every row was measured. Settings were chosen on six flights only; the other five give the same accuracy.",
    8: "With the true velocity our attitude alone would give 0.15 m. What is left is slow horizontal velocity, which an IMU cannot observe. We say so.",
}
for i, n in notes.items():
    S[i].notes_slide.notes_text_frame.text = n

prs.save(OUT)
print("saved", OUT)
