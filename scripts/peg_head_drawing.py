#!/usr/bin/env python3
"""A3 engineering drawing of the peg head + worm (RH) using build123d_drafting.

Views (third-angle, 5:1 on A3 landscape):
  - End view (camera at -X, looking +X): bearing end face, M2 tap hole, ring OD
  - Front view (camera at -Y): main profile — bearing / worm / shoulder / cap /
    ring / pip, with stacked length dims and diameter leaders
  - Isometric pictorial (no dims)

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
    Align, Color, Compound, ExportDXF, ExportSVG, LineType, Location, Text,
)
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, fix_svg_page_size, lint_drawing, set_page,
)
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.components.peg_head import create_peg_head

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

# ── Project views ─────────────────────────────────────────────────────────────
part_s = part.scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
bbox_max = max(bb.size.X, bb.size.Y, bb.size.Z)
DIST = bbox_max * SCALE + 100
ID   = DIST / (3 ** 0.5)

# Page positions (view centres)
EV_X, EV_Y = 40.0, 215.0     # end view (left, third-angle: viewed from -X)
FV_X, FV_Y = 145.0, 215.0    # front view (main)
ISO_X, ISO_Y = 315.0, 185.0  # iso pictorial

print('Projecting views (HLR)...')
front_vis, front_hid = part_s.project_to_viewport((cxs, cys - DIST, czs), (0, 0, 1), look)
end_vis, _ = part_s.project_to_viewport((cxs - DIST, cys, czs), (0, 0, 1), look)
iso_vis, _ = part_s.project_to_viewport((cxs - ID, cys - ID, czs + ID), (0, 0, 1), look)

front   = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))
front_h = Compound(children=list(front_hid)).locate(Location((FV_X, FV_Y, 0))) if front_hid else None
end     = Compound(children=list(end_vis)).locate(Location((EV_X, EV_Y, 0)))
iso     = Compound(children=list(iso_vis)).locate(Location((ISO_X, ISO_Y, 0)))

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

# Stacked length dims below front view — all dim lines land on common tiers
TIER1, TIER2 = 174.0, 164.0
r_bear = ph.shaft_diameter / 2
r_worm = w.tip_diameter / 2
add(Dimension((FX(x_bear_end), FZ(-r_bear), 0), (FX(x_bear_worm), FZ(-r_bear), 0),
              'below', FZ(-r_bear) - TIER1, draft, label=f'{bearing_len:.1f}'))
add(Dimension((FX(x_bear_worm), FZ(-r_worm), 0), (FX(x_worm_end), FZ(-r_worm), 0),
              'below', FZ(-r_worm) - TIER1, draft, label=f'{w.length:.1f}'))
add(Dimension((FX(x_bear_end), FZ(-r_bear), 0), (FX(bb.max.X), FZ(-r_bear), 0),
              'below', FZ(-r_bear) - TIER2, draft, label=f'{overall:.1f}'))

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

# M2 tap hole — on the end view where it is visible; elbow up-right so the
# label lands in the clear band above the views
add(Leader(tip=(EY(0.57), EZ(0.57), 0), elbow=(EY(0) + 12, EZ(0) + 48, 0),
           label='M2 × 3.0 DEEP', draft=draft))

# ── Text blocks (worm data + notes) ───────────────────────────────────────────
def text_block(lines, x, y, line_h=4.5, size=2.5):
    out = []
    for i, line in enumerate(lines):
        t = Text(line, font_size=size, align=(Align.MIN, Align.MAX))
        out.append(Location((x, y - i * line_h, 0)) * t)
    return out

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
    '6. DO NOT SCALE DRAWING',
], 130, 135)

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
view_shapes = [front, end, iso]
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
svg.add_layer('dims',   line_color=dim_color,  fill_color=dim_color, line_weight=0.05)
for v in (front, end, iso):
    svg.add_shape(v, layer='part')
if front_h:
    svg.add_shape(front_h, layer='hidden')
for a in anns + worm_table + notes:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

dxf = ExportDXF()
dxf.add_layer('part',   line_weight=0.5)
dxf.add_layer('hidden', line_weight=0.25)
dxf.add_layer('dims',   line_weight=0.05)
for v in (front, end, iso):
    dxf.add_shape(v, layer='part')
if front_h:
    dxf.add_shape(front_h, layer='hidden')
for a in anns + worm_table + notes:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# PDF (A3 landscape, rasterised at 200 DPI)
import tempfile
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
