#!/usr/bin/env python3
"""A3 engineering drawing of the peg head + worm (RH) using build123d_drafting.

Views (third-angle, 5:1 on A3 landscape):
  - End view (camera at -X, looking +X): bearing end face, M2 tap hole, ring OD
  - Front view (camera at -Y): main profile — bearing / worm / shoulder / cap /
    ring / pip, with stacked length dims and diameter leaders
  - Shaded pictorial (pyvista raster embedded in the SVG/PDF, omitted from the
    DXF). An HLR line projection of the helical worm thread reads as a stack of
    floating rings, so the pictorial is rendered shaded instead.

All dimension labels are derived from the live config (worm_gear.json +
parameters.py), so the drawing cannot drift from the geometry.

Axis mappings (verified with build123d-mcp view_axes):
  front (camera -Y, up +Z): world_X -> page_X (+1), world_Z -> page_Y (+1)
  end   (camera -X, up +Z): world_Y -> page_X (-1), world_Z -> page_Y (+1)

Outputs: drawings/<gear>/peg_head_rh.svg / .dxf / .pdf
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import (
    Color, Compound, ExportDXF, ExportSVG, GeomType, LineType, Location, export_stl,
)
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_SurfaceType as ST
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, fix_svg_page_size, lint_drawing, set_page,
)
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.components.peg_head import create_peg_head
from gib_tuners.export.drawing_utils import (
    embed_png_in_svg, exactify_silhouettes, render_shaded_pictorial, text_block,
    third_angle_symbol,
)

# ── Config ────────────────────────────────────────────────────────────────────
GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'peg_head_rh'

SCALE  = 5.0
PAGE_W = 420.0   # A3 landscape
PAGE_H = 297.0
TB_W   = 150.0

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)
ph  = cfg.peg_head
w   = cfg.gear.worm

# ── Build geometry ────────────────────────────────────────────────────────────
print('Building peg head + worm geometry...')
part = create_peg_head(cfg, worm_step_path=gp.worm_step, worm_length=w.length)
bb = part.bounding_box()
cx, cy, cz = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2
print(f'  bbox X {bb.min.X:.2f}..{bb.max.X:.2f}  Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}')

# Key X stations (part axis along X, bearing end at -X, pip at +X)
bearing_len  = ph.get_bearing_wall(cfg.frame.box_outer)        # 1.3
x_bear_end   = bb.min.X                                        # -9.0
x_bear_worm  = x_bear_end + bearing_len                        # -7.7
x_worm_end   = x_bear_worm + w.length                          # 0.0
overall      = bb.max.X - bb.min.X                             # 28.0
x_ring       = bb.max.X - ph.pip_length - ph.pip_stalk_length - ph.ring_od / 2

# Shoulder length: extent of the ø7.0 cylinder face (axis along X)
sh_x = []
for f in part.faces():
    surf = BRepAdaptor_Surface(f.wrapped)
    if surf.GetType() != ST.GeomAbs_Cylinder:
        continue
    cyl = surf.Cylinder()
    if abs(cyl.Position().Direction().X()) > 0.999 and \
            abs(cyl.Radius() - ph.shoulder_diameter / 2) < 0.05:
        fb = f.bounding_box()
        sh_x += [fb.min.X, fb.max.X]
x_shoulder_end = max(sh_x)                                     # 1.2

# Relief groove at worm run-out: concave torus (axis along X, small minor radius)
for f in part.faces():
    surf = BRepAdaptor_Surface(f.wrapped)
    if surf.GetType() != ST.GeomAbs_Torus:
        continue
    t = surf.Torus()
    if abs(t.Position().Direction().X()) > 0.999 and t.MinorRadius() < 1.0 \
            and -2 < t.Position().Location().X() < 1:
        fb = f.bounding_box()
        groove_dia   = 2 * (t.MajorRadius() - t.MinorRadius())  # 4.05
        groove_width = fb.max.X - fb.min.X                      # 0.7
        groove_r     = t.MinorRadius()                          # 0.35
        x_groove     = t.Position().Location().X()              # -0.35
        break

# ── Project views ─────────────────────────────────────────────────────────────
part_s = part.scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
bbox_max = max(bb.size.X, bb.size.Y, bb.size.Z)
DIST = bbox_max * SCALE + 100

# Page positions (view centres) and pictorial image box (page mm)
EV_X, EV_Y = 40.0, 215.0     # end view (left, third-angle: viewed from -X)
FV_X, FV_Y = 145.0, 215.0    # front view (main)
PIC_X, PIC_Y, PIC_W, PIC_H = 255.0, 135.0, 130.0, 100.0  # pictorial: left, bottom, size

print('Projecting views (HLR)...')
front_vis, front_hid = part_s.project_to_viewport((cxs, cys - DIST, czs), (0, 0, 1), look)
end_vis, _ = part_s.project_to_viewport((cxs - DIST, cys, czs), (0, 0, 1), look)


# Raw projected coords are centred on look_at; signs per the view_axes mappings.
# tol=0.12 (24 um real at 5:1): the reference STEP's grip revolve is circular
# to ~21 um, while genuinely non-circular silhouettes (arm profiles) measure a
# spread of 0.9+ — the threshold sits in that gap.
faces_s = part_s.faces()
front_vis, n_f = exactify_silhouettes(
    list(front_vis), faces_s, (0, 1, 0), lambda p: (p.X() - cxs, p.Z() - czs))
end_vis, n_e = exactify_silhouettes(
    list(end_vis), faces_s, (1, 0, 0), lambda p: (-(p.Y() - cys), p.Z() - czs))
print(f'  exactified silhouettes: front {n_f}, end {n_e}')

front   = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))
front_h = Compound(children=list(front_hid)).locate(Location((FV_X, FV_Y, 0))) if front_hid else None
end     = Compound(children=list(end_vis)).locate(Location((EV_X, EV_Y, 0)))

# ── Coordinate helpers ────────────────────────────────────────────────────────
def FX(x): return FV_X + (x - cx) * SCALE      # front: world_X -> page_X (+1)
def FZ(z): return FV_Y + (z - cz) * SCALE      # front: world_Z -> page_Y (+1)
def EY(y): return EV_X - (y - cy) * SCALE      # end:   world_Y -> page_X (-1)
def EZ(z): return EV_Y + (z - cz) * SCALE      # end:   world_Z -> page_Y (+1)

# ── Annototations ─────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)
anns = []

def add(a):
    anns.append(a)
    return a

# Centerlines
add(Centerline((FX(bb.min.X) - 5, FZ(0), 0), (FX(bb.max.X) + 5, FZ(0), 0)))
add(Centerline((FX(x_ring), FZ(-ph.ring_od / 2) - 5, 0), (FX(x_ring), FZ(ph.ring_od / 2) + 5, 0)))
# Left end trimmed to 2 mm so it clears the ø12.5 dimension label
add(Centerline((EY(ph.cap_diameter / 2) - 2, EZ(0), 0), (EY(-ph.cap_diameter / 2) + 5, EZ(0), 0)))
add(Centerline((EY(0), EZ(-ph.ring_od / 2) - 5, 0), (EY(0), EZ(ph.ring_od / 2) + 5, 0)))

# Bore cylinder face (axis along Y, ring region) — used for the ring position
# dim and the bore leader; values track the geometry
bore_cyls = []
for f in part.faces():
    if f.geom_type == GeomType.CYLINDER and f.center().X > 4.5:
        cyl = BRepAdaptor_Surface(f.wrapped).Cylinder()
        if abs(cyl.Position().Direction().Y()) > 0.999:
            bore_cyls.append(cyl)
bore = min(bore_cyls, key=lambda c: c.Radius())
x_bore, z_bore, r_bore = bore.Position().Location().X(), bore.Position().Location().Z(), bore.Radius()

# Stacked length dims below front view — all dim lines land on common tiers.
# Tier 1 chains bearing | worm | shoulder; tier 2 locates the ring bore centre;
# tier 3 is the overall length.
TIER1, TIER2, TIER3 = 176.0, 168.0, 160.0
r_bear = ph.shaft_diameter / 2
r_worm = w.tip_diameter / 2
r_sh   = ph.shoulder_diameter / 2
add(Dimension((FX(x_bear_end), FZ(-r_bear), 0), (FX(x_bear_worm), FZ(-r_bear), 0),
              'below', FZ(-r_bear) - TIER1, draft, label=f'{bearing_len:.1f}'))
add(Dimension((FX(x_bear_worm), FZ(-r_worm), 0), (FX(x_worm_end), FZ(-r_worm), 0),
              'below', FZ(-r_worm) - TIER1, draft, label=f'{w.length:.1f}'))
add(Dimension((FX(x_worm_end), FZ(-r_sh), 0), (FX(x_shoulder_end), FZ(-r_sh), 0),
              'below', FZ(-r_sh) - TIER1, draft, label=f'{x_shoulder_end - x_worm_end:.1f}'))
add(Dimension((FX(x_bear_end), FZ(-r_bear), 0), (FX(x_bore), FZ(-r_bear), 0),
              'below', FZ(-r_bear) - TIER2, draft, label=f'{x_bore - x_bear_end:.1f}'))
add(Dimension((FX(x_bear_end), FZ(-r_bear), 0), (FX(bb.max.X), FZ(-r_bear), 0),
              'below', FZ(-r_bear) - TIER3, draft, label=f'{overall:.1f}'))

# Ring OD — vertical dim on the end view, left side
add(Dimension((EY(0), EZ(-ph.ring_od / 2), 0), (EY(0), EZ(ph.ring_od / 2), 0),
              'left', 24, draft, label=f'ø{ph.ring_od:.1f}'))

# Diameter leaders on front view. Leader text extends horizontally from the
# elbow in the tip->elbow direction, so all elbows sit right of their tips
# and above the view tops (y > 246).
add(Leader(tip=(FX(x_bear_end + 0.6), FZ(r_bear), 0), elbow=(FX(x_bear_end) + 4, FZ(0) + 53, 0),
           label=f'ø{ph.shaft_diameter:.1f} h7 BEARING', draft=draft))
add(Leader(tip=(FX((x_bear_worm + x_worm_end) / 2), FZ(r_worm), 0),
           elbow=(FX(x_bear_worm) + 5, FZ(0) + 41, 0),
           label='WORM M0.5 — SEE TABLE', draft=draft))
add(Leader(tip=(FX(x_worm_end + 0.5), FZ(ph.shoulder_diameter / 2), 0),
           elbow=(FX(x_worm_end + 0.5) + 6, FZ(0) + 53, 0),
           label=f'ø{ph.shoulder_diameter:.1f} SHOULDER', draft=draft))
add(Leader(tip=(FX(x_worm_end + 1.6), FZ(ph.cap_diameter / 2), 0),
           elbow=(FX(x_worm_end + 1.6) + 14, FZ(0) + 41, 0),
           label=f'ø{ph.cap_diameter:.1f} × {ph.cap_length:.1f} CAP', draft=draft))
add(Leader(tip=(FX(bb.max.X - 0.7), FZ(ph.pip_diameter / 2), 0),
           elbow=(FX(bb.max.X) + 8, FZ(0) + 24, 0),
           label=f'PIP ø{ph.pip_diameter:.1f} × {ph.pip_length:.1f}', draft=draft))

# Ring bore — centre and radius taken from the bore cylinder face itself
# (axis along Y, in the ring region), so the label tracks the geometry
add(Leader(tip=(FX(x_bore + r_bore * 0.707), FZ(z_bore + r_bore * 0.707), 0),
           elbow=(FX(bb.max.X) + 2, FZ(0) + 33, 0),
           label=f'ø{2 * r_bore:.1f} BORE', draft=draft))

# Relief groove at the worm run-out
add(Leader(tip=(FX(x_groove), FZ(groove_dia / 2), 0),
           elbow=(FX(x_groove) + 2, FZ(0) + 61, 0),
           label=f'RELIEF ø{groove_dia:.2f} × {groove_width:.1f} R{groove_r:.2f}', draft=draft))

# Ring axial width — on the end view, above the ring bar
add(Dimension((EY(ph.ring_width_top / 2), EZ(ph.ring_od / 2), 0),
              (EY(-ph.ring_width_top / 2), EZ(ph.ring_od / 2), 0),
              'above', 8, draft, label=f'{ph.ring_width_top:.1f}'))

# M2 tap hole — on the end view where it is visible; elbow up-right so the
# label lands in the clear band above the views
add(Leader(tip=(EY(0.57), EZ(0.57), 0), elbow=(EY(0) + 12, EZ(0) + 48, 0),
           label='M2 × 3.0 DEEP', draft=draft))

# ── Text blocks (worm data + notes) ───────────────────────────────────────────
worm_table = text_block([
    'WORM DATA',
    f'MODULE            {w.module:.1f}',
    f'TYPE              CYLINDRICAL',
    f'STARTS            {w.num_starts}',
    f'PITCH DIA         ø{w.pitch_diameter:.1f}',
    f'TIP DIA           ø{w.tip_diameter:.1f}',
    f'ROOT DIA          ø{w.root_diameter:.2f}',
    f'LEAD              {w.lead:.3f} RH',
    f'LEAD ANGLE        {w.lead_angle_deg:.2f}°',
    f'PRESSURE ANGLE    {cfg.gear.pressure_angle_deg:.0f}°',
], 20, 135)

notes = text_block([
    'NOTES',
    '1. MATERIAL: CZ121 BRASS',
    '2. SHAFT CONCENTRIC TO WORM PITCH DIA WITHIN 0.01',
    '3. BREAK ALL EDGES: 0.3 CHAMFER',
    '4. M2 TAP HOLE: ø1.6 DRILL × 3.0 DEEP, TAP M2 × 0.4',
    '5. LH VARIANT: MIRROR IMAGE, LEFT-HAND THREAD',
    f'6. RING BORE OFFSET {ph.bore_offset:.2f} FROM RING OD CENTRE, TOWARD PIP',
    '7. DO NOT SCALE DRAWING',
], 130, 135)

caption = text_block(['SHADED PICTORIAL — NOT TO SCALE'], PIC_X + 30, PIC_Y - 3)

# Third-angle projection symbol (ISO 5456-2), left of the title block.
# Unfilled circles must avoid the filled dims layer, hence the 'ann' layer.
symbol = third_angle_symbol(225, 22)
caption += text_block(['THIRD ANGLE PROJECTION'], 214, 15.5, size=2.0)

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    'PEG HEAD + WORM (RH)',
    'GIB-TUN-PH-RH',
    drawing_scale=SCALE,
    material='CZ121 BRASS',
    general_tolerance='ISO 2768-f',
    designed_by='P. Fremantle',
    date='2026-06-09',
    revision='A',
    legal_owner='P. FREMANTLE',
    width=TB_W,
    draft=draft,
).locate(Location((PAGE_W - TB_W - 11, 10.5, 0)))
anns.append(tb)

# ── Lint gate ─────────────────────────────────────────────────────────────────
set_page(PAGE_W, PAGE_H, margin=10)
view_shapes = [front, end]
issues = lint_drawing(anns, drawing_scale=SCALE, view_shapes=view_shapes)
if issues:
    print('Lint issues:')
    for iss in issues:
        print(f'  [{iss.severity}] {iss.code}: {iss.message}')
else:
    print('Lint: OK')

# ── Export SVG / DXF / PDF ────────────────────────────────────────────────────
print('Exporting...')
part_color = Color(0, 0, 0)
hid_color  = Color(0.45, 0.45, 0.45)
dim_color  = Color(0, 0.2, 0.7)

svg = ExportSVG(margin=10)
svg.add_layer('part',   line_color=part_color, line_weight=0.5)
svg.add_layer('hidden', line_color=hid_color,  line_weight=0.25, line_type=LineType.HIDDEN)
svg.add_layer('ann',    line_color=dim_color,  line_weight=0.18)
svg.add_layer('dims',   line_color=dim_color,  fill_color=dim_color, line_weight=0.05)
for v in (front, end):
    svg.add_shape(v, layer='part')
if front_h:
    svg.add_shape(front_h, layer='hidden')
for e in symbol:
    svg.add_shape(e, layer='ann')
for a in anns + worm_table + notes + caption:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

# ── Shaded pictorial (pyvista) embedded into the SVG ──────────────────────────
# HLR of the worm thread reads as floating rings, so the pictorial is a shaded
# raster instead. Camera looks from the worm side (-X), slightly above, so the
# thread reads as a screw.
print('Rendering shaded pictorial...')
import tempfile

with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
    stl_path = tmp.name
export_stl(part, stl_path, tolerance=0.0003, angular_tolerance=0.05)
png_path = stl_path.replace('.stl', '.png')
render_shaded_pictorial(stl_path, png_path, cam_dir=(-1.0, -1.1, 0.55),
                        dist=max(bb.size.X, bb.size.Y, bb.size.Z) * 2.2,
                        window_size=(int(PIC_W) * 10, int(PIC_H) * 10), zoom=1.5)
embed_png_in_svg(STEM.with_suffix('.svg'), png_path, PIC_X, PIC_Y, PIC_W, PIC_H)

dxf = ExportDXF()
dxf.add_layer('part',   line_weight=0.5)
dxf.add_layer('hidden', line_weight=0.25)
dxf.add_layer('ann',    line_weight=0.18)
dxf.add_layer('dims',   line_weight=0.05)
for v in (front, end):
    dxf.add_shape(v, layer='part')
if front_h:
    dxf.add_shape(front_h, layer='hidden')
for e in symbol:
    dxf.add_shape(e, layer='ann')
for a in anns + worm_table + notes + caption:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# PDF (A3 landscape, rasterised at 200 DPI)
import resvg_py
from fpdf import FPDF

png_bytes = bytes(resvg_py.svg_to_bytes(svg_path=str(STEM) + '.svg', dpi=200))
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
    tmp.write(png_bytes)
    tmp_png = tmp.name
pdf = FPDF(orientation='L', unit='mm', format='A3')
pdf.add_page()
pdf.image(tmp_png, x=0, y=0, w=PAGE_W, h=PAGE_H)
pdf.output(str(STEM) + '.pdf')

print(f'Wrote {STEM}.svg / .dxf / .pdf')
