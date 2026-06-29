#!/usr/bin/env python3
"""A3 engineering drawing of the 5-gang frame (RH) using build123d_drafting.

Views (third-angle, 2:1 on A3 landscape):
  - Plan view (camera at +Z): post bearing and mounting holes along the length
  - Front view (camera at +X, the worm-entry side): housing layout with the
    chained length stack and worm entry holes
  - End view (right of the front view, same 2:1 scale): box section and wall
  - Shaded pictorial (pyvista raster, embedded in the SVG/PDF; omitted from
    the DXF)

All dimension labels are derived from the live config (tuner_config.json +
parameters.py), so the drawing cannot drift from the geometry. Hole
tolerances follow docs/component-details.md §1 (H7 reamed bearings, +0.1
clearance holes).

Axis mappings (verified with build123d-mcp view_axes):
  front (camera +X, up +Z):      world_Y -> page_X (+1), world_Z -> page_Y (+1)
  plan  (camera +Z, up (-1,0,0)): world_Y -> page_X (+1), world_X -> page_Y (-1)
  end   (camera +Y, up +Z):      world_X -> page_X (-1), world_Z -> page_Y (+1)

Outputs: drawings/<gear>/frame_rh.svg / .dxf / .pdf
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import (
    Color, Compound, ExportDXF, ExportSVG, Location, export_stl,
)
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, lint_drawing, set_page,
)
from gib_tuners.config.defaults import (
    calculate_worm_z, create_default_config, resolve_gear_config,
)
from gib_tuners.components.frame import create_frame
from gib_tuners.export.drawing_utils import (
    embed_png_in_svg, exactify_silhouettes, fix_svg_page_size,
    render_shaded_pictorial, text_block, third_angle_symbol,
)

# ── Config ────────────────────────────────────────────────────────────────────
GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'frame_rh'

SCALE = 2.0
PAGE_W = 420.0    # A3 landscape
PAGE_H = 297.0
TB_W   = 150.0

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)
f   = cfg.frame

worm_z   = calculate_worm_z(cfg)                                 # -5.0
cd       = cfg.gear.center_distance - cfg.gear.extra_backlash
# Post axes sit CD/2 toward the frame datum end from each housing centre;
# worm axes CD/2 the other way (verified against the built hole positions)
post_ys  = [hc - cd / 2 for hc in f.housing_centers]             # post hole centres
worm_ys  = [y + cd for y in post_ys]                             # worm/peg centres (post + CD)
mount_ys = list(f.mounting_hole_positions)

# ── Build geometry ────────────────────────────────────────────────────────────
print('Building frame geometry...')
part = create_frame(cfg, label=False)
bb = part.bounding_box()
cx, cy, cz = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2
print(f'  bbox X {bb.min.X:.2f}..{bb.max.X:.2f}  Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}')

# ── Project views ─────────────────────────────────────────────────────────────
part_s = part.scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
DIST = max(bb.size.X, bb.size.Y, bb.size.Z) * SCALE + 100

# Page positions (view centres) and pictorial image box (page mm)
PV_X, PV_Y = 195.0, 252.0    # plan view (top)
FV_X, FV_Y = 195.0, 207.0    # front view (worm-entry side)
EV_X, EV_Y = 372.0, 207.0    # end view (right of front, same scale)
PIC_X, PIC_Y, PIC_W, PIC_H = 240.0, 55.0, 150.0, 90.0

print('Projecting views (HLR)...')
plan_vis, _ = part_s.project_to_viewport((cxs, cys, czs + DIST), (-1, 0, 0), look)
front_vis, _ = part_s.project_to_viewport((cxs + DIST, cys, czs), (0, 0, 1), look)

end_vis, _ = part_s.project_to_viewport((cxs, cys + DIST, czs), (0, 0, 1), look)

faces_s = part_s.faces()
plan_vis, n_p = exactify_silhouettes(
    list(plan_vis), faces_s, (0, 0, 1), lambda p: (p.Y() - cys, -(p.X() - cxs)))
front_vis, n_f = exactify_silhouettes(
    list(front_vis), faces_s, (1, 0, 0), lambda p: (p.Y() - cys, p.Z() - czs))
print(f'  exactified silhouettes: plan {n_p}, front {n_f}')

plan  = Compound(children=list(plan_vis)).locate(Location((PV_X, PV_Y, 0)))
front = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))
end   = Compound(children=list(end_vis)).locate(Location((EV_X, EV_Y, 0)))

# ── Coordinate helpers ────────────────────────────────────────────────────────
def FY(y): return FV_X + (y - cy) * SCALE      # front: world_Y -> page_X (+1)
def FZ(z): return FV_Y + (z - cz) * SCALE      # front: world_Z -> page_Y (+1)
def PYp(y): return PV_X + (y - cy) * SCALE     # plan:  world_Y -> page_X (+1)
def PXp(x): return PV_Y - (x - cx) * SCALE     # plan:  world_X -> page_Y (-1)
def EX(x): return EV_X - (x - cx) * SCALE      # end:   world_X -> page_X (-1)
def EZ(z): return EV_Y + (z - cz) * SCALE      # end:   world_Z -> page_Y (+1)

# ── Annotations ───────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)
anns = []

def add(a):
    anns.append(a)
    return a

# Centerlines: through first post/worm holes and plan long axis
add(Centerline((PYp(bb.min.Y) - 4, PXp(0), 0), (PYp(bb.max.Y) + 4, PXp(0), 0)))
add(Centerline((PYp(post_ys[0]), PXp(5) - 3, 0), (PYp(post_ys[0]), PXp(-5) + 3, 0)))
add(Centerline((FY(worm_ys[0]), FZ(-10) - 3, 0), (FY(worm_ys[0]), FZ(0) + 3, 0)))
add(Centerline((FY(worm_ys[0]) - 10, FZ(worm_z), 0), (FY(worm_ys[0]) + 10, FZ(worm_z), 0)))

# Chained length stack below the front view
TIER1, TIER2, TIER3 = 184.0, 176.0, 168.0
z_bot = bb.min.Z
add(Dimension((FY(0), FZ(z_bot), 0), (FY(f.end_length), FZ(z_bot), 0),
              'below', FZ(z_bot) - TIER1, draft, label=f'{f.end_length:.1f}'))
add(Dimension((FY(f.end_length), FZ(z_bot), 0),
              (FY(f.end_length + f.housing_length), FZ(z_bot), 0),
              'below', FZ(z_bot) - TIER1, draft, label=f'{f.housing_length:.1f}'))
add(Dimension((FY(0), FZ(z_bot), 0), (FY(post_ys[0]), FZ(z_bot), 0),
              'below', FZ(z_bot) - TIER2, draft, label=f'{post_ys[0]:.2f}'))
add(Dimension((FY(post_ys[0]), FZ(z_bot), 0), (FY(post_ys[1]), FZ(z_bot), 0),
              'below', FZ(z_bot) - TIER2, draft, label=f'{f.tuner_pitch:.1f}'))
add(Dimension((FY(0), FZ(z_bot), 0), (FY(f.total_length), FZ(z_bot), 0),
              'below', FZ(z_bot) - TIER3, draft, label=f'{f.total_length:.1f}'))

# Box height (front, left) and width (plan, left)
add(Dimension((FY(0), FZ(z_bot), 0), (FY(0), FZ(0), 0),
              'left', FY(0) - 40, draft, label=f'{f.box_outer:.1f}'))
add(Dimension((PYp(0), PXp(5), 0), (PYp(0), PXp(-5), 0),
              'left', PYp(0) - 40, draft, label=f'{f.box_outer:.1f}'))

# Hole callouts (counts and tolerances per component-details §1)
add(Leader(tip=(PYp(post_ys[0]), PXp(0) + f.post_bearing_hole * SCALE / 2, 0),
           elbow=(110, 277, 0),
           label=f'{len(post_ys)} × ø{f.post_bearing_hole:.2f} H7 POST BEARING', draft=draft))
add(Leader(tip=(PYp(mount_ys[0]), PXp(0) + f.mounting_hole * SCALE / 2, 0),
           elbow=(44, 272, 0),
           label=f'{len(mount_ys)} × ø{f.mounting_hole:.1f} MOUNTING', draft=draft))
add(Leader(tip=(FY(worm_ys[0]), FZ(worm_z) + f.worm_entry_hole * SCALE / 2, 0),
           elbow=(120, 228, 0),
           label=f'{len(worm_ys)} × ø{f.worm_entry_hole:.2f} +0.1 WORM ENTRY (THIS SIDE)',
           draft=draft))
# Worm exit / peg bearing on the far wall — visible through the entry holes
add(Leader(tip=(FY(worm_ys[2]), FZ(worm_z) + f.peg_bearing_hole * SCALE / 2, 0),
           elbow=(230, 232, 0),
           label=f'{len(worm_ys)} × ø{f.peg_bearing_hole:.2f} H7 WORM EXIT / PEG BEARING (FAR WALL)',
           draft=draft))
eng = f.engraving
add(Leader(tip=(PYp(cy + 30), PXp(f.box_outer / 2 - eng.inset - eng.band_width / 2), 0),
           elbow=(290, 274, 0), label='BORDER ENGRAVING — SEE NOTE 8', draft=draft))

# End view: box section + wall
add(Leader(tip=(EX(-(f.box_outer / 2 - f.wall_thickness / 2)), EZ(worm_z), 0),
           elbow=(366, 236, 0),
           label=f'BOX {f.box_outer:.0f} × {f.box_outer:.0f} — WALL {f.wall_thickness:.1f}',
           draft=draft))

# ── Text blocks (notes) ───────────────────────────────────────────────────────
notes = text_block([
    'NOTES',
    '1. MATERIAL: CZ121 BRASS BOX SECTION',
    '2. RH SHOWN — LH IS MIRROR IMAGE (WORM/PEG HOLES SWAP SIDES)',
    f'3. PEG BEARING: {len(post_ys)} × ø{f.peg_bearing_hole:.2f} H7 (REAMED), FAR SIDE, '
    'COAXIAL WITH WORM ENTRY',
    f'4. WHEEL INLET: {len(post_ys)} × ø{f.wheel_inlet_hole:.1f} IN BOTTOM FACE, '
    'COAXIAL WITH POST BEARING',
    f'5. WORM AXIS {abs(worm_z):.1f} BELOW MOUNTING FACE (MID-HEIGHT)',
    '6. MOUNTING HOLES AT Y = ' + ' / '.join(f'{y:.1f}' for y in mount_ys),
    '7. POST CENTRES AT Y = ' + ' / '.join(f'{y:.2f}' for y in post_ys)
    + f' — WORM/PEG CENTRES {cd:.2f} (CD) FURTHER ALONG',
    f'8. TOP FACE BORDER ENGRAVING (ROPE MOTIF): {eng.depth:.1f} DEEP, '
    f'{eng.groove_width:.1f} GROOVES, BAND {eng.band_width:.1f} AT {eng.inset:.1f} INSET, '
    f'HATCH PITCH {eng.hatch_spacing:.1f}',
    '9. PRODUCTION FRAMES ARE UNLABELLED (build with --label-frames no)',
    '10. DO NOT SCALE DRAWING',
], 20, 150)

caption = text_block(['SHADED PICTORIAL — NOT TO SCALE'], PIC_X + 38, PIC_Y - 3)
caption += text_block(['END VIEW'], EV_X - 8, EV_Y - 15)

# Third-angle projection symbol (ISO 5456-2), left of the title block.
# Unfilled circles need the 'ann' layer (no fill).
symbol = third_angle_symbol(225, 22)
caption += text_block(['THIRD ANGLE PROJECTION'], 214, 15.5, size=2.0)

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    'FRAME — 5-GANG (RH)',
    'GIB-TUN-FR-RH',
    drawing_scale=SCALE,
    material='CZ121 BRASS',
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
issues = lint_drawing(anns, drawing_scale=SCALE, view_shapes=[plan, front, end])
if issues:
    print('Lint issues:')
    for iss in issues:
        print(f'  [{iss.severity}] {iss.code}: {iss.message}')
else:
    print('Lint: OK')

# ── Export SVG / DXF ──────────────────────────────────────────────────────────
print('Exporting...')
svg = ExportSVG(margin=10)
svg.add_layer('part', line_color=Color(0, 0, 0), line_weight=0.5)
svg.add_layer('ann',  line_color=Color(0, 0.2, 0.7), line_weight=0.18)
svg.add_layer('dims', line_color=Color(0, 0.2, 0.7), fill_color=Color(0, 0.2, 0.7),
              line_weight=0.05)
for v in (plan, front, end):
    svg.add_shape(v, layer='part')
for e in symbol:
    svg.add_shape(e, layer='ann')
for a in anns + notes + caption:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

dxf = ExportDXF()
dxf.add_layer('part', line_weight=0.5)
dxf.add_layer('ann',  line_weight=0.18)
dxf.add_layer('dims', line_weight=0.05)
for v in (plan, front, end):
    dxf.add_shape(v, layer='part')
for e in symbol:
    dxf.add_shape(e, layer='ann')
for a in anns + notes + caption:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# ── Shaded pictorial embedded into the SVG ────────────────────────────────────
print('Rendering shaded pictorial...')
with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
    stl_path = tmp.name
export_stl(part, stl_path, tolerance=0.001, angular_tolerance=0.1)
png_path = stl_path.replace('.stl', '.png')
render_shaded_pictorial(stl_path, png_path, cam_dir=(0.9, -0.9, 0.7),
                        dist=max(bb.size.X, bb.size.Y, bb.size.Z) * 1.6,
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
