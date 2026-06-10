#!/usr/bin/env python3
"""A3 general arrangement drawing of a single tuner station (RH).

Views (5:1 on A3 landscape):
  - Front view (camera at -Y): post up, peg head + worm to the right; the
    frame is sectioned at the post axis so the wheel and retention hardware
    are visible
  - Side view (camera at +X): frame length, post/worm centre distance
  - Shaded pictorial + item balloons + BOM table

The assembly comes from create_positioned_assembly() (the same path as
build.py/viz.py) with num_housings=1, so positions cannot drift from the
production assembly. One station of five is shown; the full frame is on
GIB-TUN-FR-RH.

Axis mappings (verified with build123d-mcp view_axes):
  front (camera -Y, up +Z): world_X -> page_X (+1), world_Z -> page_Y (+1)
  side  (camera +X, up +Z): world_Y -> page_X (+1), world_Z -> page_Y (+1)

Outputs: drawings/<gear>/assembly_ga_rh.svg / .dxf / .pdf
"""

import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import (
    Box, Color, Compound, ExportDXF, ExportSVG, Location, export_stl,
)
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, fix_svg_page_size, lint_drawing, set_page,
)
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.assembly.gang_assembly import create_positioned_assembly
from gib_tuners.export.drawing_utils import (
    embed_png_in_svg, exactify_silhouettes, project_visible,
    render_shaded_pictorial, text_block,
)

# ── Config ────────────────────────────────────────────────────────────────────
GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'assembly_ga_rh'

SCALE  = 5.0
PAGE_W = 420.0   # A3 landscape
PAGE_H = 297.0
TB_W   = 150.0

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)
cfg = replace(cfg, frame=replace(cfg.frame, num_housings=1))
cd  = cfg.gear.center_distance - cfg.gear.extra_backlash

# ── Build geometry ────────────────────────────────────────────────────────────
print('Building single-station assembly...')
asm = create_positioned_assembly(cfg, wheel_step_path=gp.wheel_step,
                                 worm_step_path=gp.worm_step)
parts = asm['all_parts']

whole = Compound(children=list(parts.values()))
bb = whole.bounding_box()
cx, cy, cz = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2
print(f'  bbox X {bb.min.X:.2f}..{bb.max.X:.2f}  Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}')

y_post = (parts['string_post_1'].bounding_box().min.Y
          + parts['string_post_1'].bounding_box().max.Y) / 2
y_worm = y_post + cd
z_top  = parts['string_post_1'].bounding_box().max.Z   # post cap top

# ── Project views ─────────────────────────────────────────────────────────────
# Front view: the frame is sectioned at the post axis (everything between the
# viewer and that plane removed) so the wheel and retention hardware are
# actually visible — fully hidden parts read as missing on a GA. The wheel is
# projected separately with smooth seam edges suppressed (its lofted tooth
# patches stripe otherwise); everything else keeps smooth edges, which the
# peg head ring needs for its bore line work.
frame_cut = parts['frame'] - Location((0, y_post - 50, -5)) * Box(40, 100, 40)
front_parts = [frame_cut] + [p for n, p in parts.items()
                             if n not in ('frame', 'wheel_1')]
front_s = Compound(children=front_parts).scale(SCALE)
wheel_s = parts['wheel_1'].scale(SCALE)
side_s  = Compound(children=[p for n, p in parts.items() if n != 'wheel_1']).scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
DIST = max(bb.size.X, bb.size.Y, bb.size.Z) * SCALE + 100

FV_X, FV_Y = 100.0, 205.0    # front view (post up, peg right)
SV_X, SV_Y = 280.0, 205.0    # side view (frame length)
PIC_X, PIC_Y, PIC_W, PIC_H = 240.0, 45.0, 150.0, 95.0

print('Projecting views (HLR, this is the slow part)...')
front_cam = (cxs, cys - DIST, czs)
front_vis = project_visible(front_s, front_cam, (0, 0, 1), look)
front_vis += project_visible(wheel_s, front_cam, (0, 0, 1), look,
                             include_smooth=False)
side_vis = project_visible(side_s, (cxs + DIST, cys, czs), (0, 0, 1), look,
                           include_smooth=False)

# Exact circles for the axis-aligned silhouettes (peg ring bore, cap blends)
front_faces = list(front_s.faces()) + list(wheel_s.faces())
front_vis, n_f = exactify_silhouettes(
    list(front_vis), front_faces, (0, 1, 0), lambda p: (p.X() - cxs, p.Z() - czs))
print(f'  exactified silhouettes: front {n_f}')

front = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))
side  = Compound(children=list(side_vis)).locate(Location((SV_X, SV_Y, 0)))

# ── Coordinate helpers ────────────────────────────────────────────────────────
def FXa(x): return FV_X + (x - cx) * SCALE     # front: world_X -> page_X (+1)
def FZa(z): return FV_Y + (z - cz) * SCALE     # front: world_Z -> page_Y (+1)
def SY(y):  return SV_X + (y - cy) * SCALE     # side:  world_Y -> page_X (+1)
def SZ(z):  return FV_Y + (z - cz) * SCALE     # side:  world_Z -> page_Y (+1)

# ── Annotations ───────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)
anns = []

def add(a):
    anns.append(a)
    return a

# Centerlines: post axis (front + side), worm axis (front), CD pair (side)
add(Centerline((FXa(0), FZa(bb.min.Z) - 3, 0), (FXa(0), FZa(z_top) + 3, 0)))
add(Centerline((FXa(bb.min.X) - 3, FZa(-5), 0), (FXa(bb.max.X) + 3, FZa(-5), 0)))
add(Centerline((SY(y_post), SZ(bb.min.Z) - 3, 0), (SY(y_post), SZ(z_top) + 3, 0)))
add(Centerline((SY(y_worm), SZ(-10) - 3, 0), (SY(y_worm), SZ(0) + 3, 0)))

# Key GA dimensions: post height above face, peg projection, centre distance
add(Dimension((FXa(-3), FZa(0), 0), (FXa(-3), FZa(z_top), 0),
              'left', FXa(-3) - 32, draft, label=f'{z_top:.1f}'))
add(Dimension((FXa(5), FZa(bb.min.Z), 0), (FXa(bb.max.X), FZa(bb.min.Z), 0),
              'below', FZa(bb.min.Z) - 154, draft, label=f'{bb.max.X - 5:.1f}'))
add(Dimension((SY(y_post), SZ(z_top), 0), (SY(y_worm), SZ(z_top), 0),
              'above', 8, draft, label=f'{cd:.2f}'))

# Item balloons (numbers map to the BOM table). Left-side balloons sit on a
# vertical rail at page x~30 with short parallel leaders; top balloons clear
# the 6.5 height dim (its line is at x~32, y 245..277)
BALLOONS = [
    ('1', (FXa(-4.5), FZa(-9.8)), (40, 170)),        # frame
    ('2', (FXa(1.5), FZa(z_top)), (75, 272)),        # string post
    ('3', (FXa(-3.7), FZa(-5.0)), (30, 180)),        # wheel, near edge
    ('4', (FXa(19.5), FZa(1.2)), (158, 262)),        # peg head + worm
    ('5', (FXa(1.8), FZa(-9.1)), (58, 162)),         # wheel washer
    ('6', (FXa(0.8), FZa(-10.4)), (44, 154)),        # wheel screw
    ('7', (FXa(-5.4), FZa(-2.6)), (30, 208)),        # peg washer
    ('8', (FXa(-6.8), FZa(-5.0)), (24, 196)),        # peg screw
]
for label, tip, elbow in BALLOONS:
    add(Leader(tip=(tip[0], tip[1], 0), elbow=(elbow[0], elbow[1], 0),
               label=label, draft=draft))

# ── Text blocks (BOM + notes) ─────────────────────────────────────────────────
bom = text_block([
    'PARTS LIST (PER 5-GANG UNIT)',
    'ITEM  QTY  DESCRIPTION',
    '1     1    FRAME, 5-GANG — CZ121 BRASS (GIB-TUN-FR)',
    '2     5    STRING POST — CZ121 BRASS (GIB-TUN-SP)',
    '3     5    WORM WHEEL — PB102 BRONZE (GIB-TUN-WW)',
    '4     5    PEG HEAD + WORM — CZ121 BRASS (GIB-TUN-PH)',
    '5     5    WHEEL WASHER ø4.9 × ø2.2 × 0.5',
    '6     5    WHEEL SCREW M2 × 4 PAN HEAD',
    '7     5    PEG WASHER ø5.5 × ø2.2 × 0.5',
    '8     5    PEG SCREW M2 × 4 PAN HEAD',
], 20, 135)

notes = text_block([
    'NOTES',
    '1. SINGLE STATION SHOWN — FULL FRAME HAS 5 AT 27.2 PITCH (SEE GIB-TUN-FR-RH)',
    f'2. POST TO WORM CENTRE DISTANCE {cd:.2f}',
    '3. FRONT VIEW: FRAME SECTIONED AT THE POST AXIS TO SHOW THE MECHANISM',
    '4. RH SHOWN — LH UNIT IS MIRROR IMAGE',
    '5. DO NOT SCALE DRAWING',
], 20, 80)

caption = text_block(['SHADED PICTORIAL — NOT TO SCALE'], PIC_X + 38, PIC_Y - 3)
caption += text_block(['FRONT VIEW (FRAME SECTIONED)'], FV_X - 30, 148)
caption += text_block(['SIDE VIEW'], SV_X - 11, 148)

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    'GENERAL ARRANGEMENT (RH)',
    'GIB-TUN-GA-RH',
    drawing_scale=SCALE,
    material='SEE PARTS LIST',
    general_tolerance='ISO 2768-f',
    designed_by='P. Fremantle',
    date='2026-06-10',
    revision='A',
    legal_owner='P. FREMANTLE',
    width=TB_W,
    draft=draft,
).locate(Location((PAGE_W - TB_W - 11, 10.5, 0)))
anns.append(tb)

# ── Lint gate ─────────────────────────────────────────────────────────────────
set_page(PAGE_W, PAGE_H, margin=10)
issues = lint_drawing(anns, drawing_scale=SCALE, view_shapes=[front, side])
if issues:
    print('Lint issues:')
    for iss in issues:
        print(f'  [{iss.severity}] {iss.code}: {iss.message}')
else:
    print('Lint: OK')

# ── Export SVG / DXF ──────────────────────────────────────────────────────────
print('Exporting...')
svg = ExportSVG(margin=10)
svg.add_layer('part',   line_color=Color(0, 0, 0), line_weight=0.5)
svg.add_layer('dims',   line_color=Color(0, 0.2, 0.7), fill_color=Color(0, 0.2, 0.7),
              line_weight=0.05)
for v in (front, side):
    svg.add_shape(v, layer='part')
for a in anns + bom + notes + caption:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

dxf = ExportDXF()
dxf.add_layer('part',   line_weight=0.5)
dxf.add_layer('dims',   line_weight=0.05)
for v in (front, side):
    dxf.add_shape(v, layer='part')
for a in anns + bom + notes + caption:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# ── Shaded pictorial embedded into the SVG ────────────────────────────────────
# One STL per part (export_stl drops solids from a multi-part Compound);
# the bronze wheel gets its own colour
print('Rendering shaded pictorial...')
BRONZE = (0.72, 0.45, 0.30)
tmpdir = Path(tempfile.mkdtemp())
stl_entries = []
for name, p in parts.items():
    path = tmpdir / f'{name}.stl'
    export_stl(p, str(path), tolerance=0.001, angular_tolerance=0.1)
    stl_entries.append((str(path), BRONZE if name.startswith('wheel_1') else (0.80, 0.64, 0.32)))
png_path = str(tmpdir / 'assembly.png')
render_shaded_pictorial(stl_entries, png_path, cam_dir=(1.0, -1.0, 0.8),
                        dist=max(bb.size.X, bb.size.Y, bb.size.Z) * 2.4,
                        window_size=(int(PIC_W) * 10, int(PIC_H) * 10), zoom=1.2)
embed_png_in_svg(STEM.with_suffix('.svg'), png_path, PIC_X, PIC_Y, PIC_W, PIC_H)

# ── PDF (A3 landscape, rasterised at 200 DPI) ─────────────────────────────────
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
