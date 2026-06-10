#!/usr/bin/env python3
"""A3 engineering drawing of the string post using build123d_drafting.

Views (third-angle, 10:1 on A3 landscape):
  - Front view (camera at -Y): full profile — DD section / bearing / post /
    cap, with a chained height stack, string hole, and diameter leaders
  - Bottom view (camera at -Z, below the front view): DD flats, across-flats
    dim, and the M2 tap hole
  - Cap top view (removed view, labelled): the three engraved V-grooves
  - Shaded pictorial (pyvista raster, embedded in the SVG/PDF; omitted from
    the DXF)

All dimension labels are derived from the live config (worm_gear.json +
parameters.py) or measured from the geometry, so the drawing cannot drift.

Axis mappings (verified with build123d-mcp view_axes):
  front  (camera -Y, up +Z): world_X -> page_X (+1), world_Z -> page_Y (+1)
  bottom (camera -Z, up +Y): world_X -> page_X (-1), world_Y -> page_Y (+1)

Outputs: drawings/<gear>/string_post.svg / .dxf / .pdf
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import (
    Color, Compound, ExportDXF, ExportSVG, LineType, Location, export_stl,
)
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, fix_svg_page_size, lint_drawing, set_page,
)
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.components.string_post import create_string_post
from gib_tuners.export.drawing_utils import (
    embed_png_in_svg, exactify_silhouettes, render_shaded_pictorial, text_block,
)

# ── Config ────────────────────────────────────────────────────────────────────
GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'string_post'

SCALE  = 10.0
PAGE_W = 420.0   # A3 landscape
PAGE_H = 297.0
TB_W   = 150.0

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)
sp  = cfg.string_post

# ── Build geometry ────────────────────────────────────────────────────────────
print('Building string post geometry...')
part = create_string_post(cfg)
bb = part.bounding_box()
cx, cy, cz = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2
print(f'  bbox X {bb.min.X:.2f}..{bb.max.X:.2f}  Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}')

# Z stations (axis along Z, DD at bottom, cap on top)
dd_len      = sp.get_dd_cut_length(cfg.gear.wheel.face_width)   # 7.2
bearing_len = sp.get_bearing_length(cfg.frame.wall_thickness)   # 1.1
z_dd_top    = dd_len                                            # 7.2
z_bear_top  = z_dd_top + bearing_len                            # 8.3
z_post_top  = z_bear_top + sp.post_height                       # 13.8
z_top       = bb.max.Z                                          # 14.8
z_hole      = z_bear_top + sp.string_hole_position              # 11.05
dd_dia      = sp.dd_cut.diameter - sp.dd_shaft_clearance        # 3.4
dd_af       = sp.dd_cut.across_flats - sp.dd_shaft_clearance    # 2.4

# Groove centre radii — mirrors the placement in create_string_post():
# evenly spaced from min_r 0.75 to the outermost groove centre
groove_outer_r = sp.cap_groove_outer_od / 2 - sp.cap_groove_width / 2   # 2.835
groove_rs = [0.75 + i * (groove_outer_r - 0.75) / (sp.cap_groove_count - 1)
             for i in range(sp.cap_groove_count)]

# ── Project views ─────────────────────────────────────────────────────────────
part_s = part.scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
DIST = max(bb.size.X, bb.size.Y, bb.size.Z) * SCALE + 100

# Page positions (view centres) and pictorial image box (page mm)
FV_X, FV_Y = 110.0, 190.0    # front view (main)
BV_X, BV_Y = 110.0, 60.0     # bottom view (third-angle: below the front view)
TV_X, TV_Y = 195.0, 55.0     # cap top view (removed view, labelled)
PIC_X, PIC_Y, PIC_W, PIC_H = 250.0, 140.0, 120.0, 100.0  # pictorial: left, bottom, size

print('Projecting views (HLR)...')
front_vis, front_hid = part_s.project_to_viewport((cxs, cys - DIST, czs), (0, 0, 1), look)
bot_vis, _ = part_s.project_to_viewport((cxs, cys, czs - DIST), (0, 1, 0), look)
top_vis, _ = part_s.project_to_viewport((cxs, cys, czs + DIST), (0, 1, 0), look)

# Raw projected coords are centred on look_at; signs per the view_axes mappings
faces_s = part_s.faces()
front_vis, n_f = exactify_silhouettes(
    list(front_vis), faces_s, (0, 1, 0), lambda p: (p.X() - cxs, p.Z() - czs))
bot_vis, n_b = exactify_silhouettes(
    list(bot_vis), faces_s, (0, 0, 1), lambda p: (-(p.X() - cxs), p.Y() - cys))
top_vis, n_t = exactify_silhouettes(
    list(top_vis), faces_s, (0, 0, 1), lambda p: (p.X() - cxs, p.Y() - cys))
print(f'  exactified silhouettes: front {n_f}, bottom {n_b}, top {n_t}')

front   = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))
front_h = Compound(children=list(front_hid)).locate(Location((FV_X, FV_Y, 0))) if front_hid else None
bot     = Compound(children=list(bot_vis)).locate(Location((BV_X, BV_Y, 0)))
top     = Compound(children=list(top_vis)).locate(Location((TV_X, TV_Y, 0)))

# ── Coordinate helpers ────────────────────────────────────────────────────────
def FX(x): return FV_X + (x - cx) * SCALE      # front:  world_X -> page_X (+1)
def FZ(z): return FV_Y + (z - cz) * SCALE      # front:  world_Z -> page_Y (+1)
def BX(x): return BV_X - (x - cx) * SCALE      # bottom: world_X -> page_X (-1)
def BY(y): return BV_Y + (y - cy) * SCALE      # bottom: world_Y -> page_Y (+1)
def TX(x): return TV_X + (x - cx) * SCALE      # top:    world_X -> page_X (+1)
def TY(y): return TV_Y + (y - cy) * SCALE      # top:    world_Y -> page_Y (+1)

# ── Annotations ───────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)
anns = []

def add(a):
    anns.append(a)
    return a

# Centerlines: post axis in front view, crosshair + string hole axis in bottom
add(Centerline((FX(0), FZ(bb.min.Z) - 5, 0), (FX(0), FZ(bb.max.Z) + 5, 0)))
add(Centerline((FX(0) - sp.cap_diameter / 2 * SCALE - 5, FZ(z_hole), 0),
               (FX(0) + sp.cap_diameter / 2 * SCALE + 5, FZ(z_hole), 0)))
add(Centerline((BX(sp.cap_diameter / 2) + 5, BY(0), 0), (BX(-sp.cap_diameter / 2) - 5, BY(0), 0)))
# Bottom end trimmed to 2 mm so it clears the A/F dimension label
add(Centerline((BX(0), BY(-sp.cap_diameter / 2) - 2, 0), (BX(0), BY(sp.cap_diameter / 2) + 5, 0)))

# Chained height stack, left of the front view (tier 1), overall on tier 2
TIER1, TIER2 = 62.0, 50.0
chain = [
    (bb.min.Z, z_dd_top,   -dd_af / 2,            f'{dd_len:.1f}'),
    (z_dd_top, z_bear_top, -sp.bearing_diameter / 2, f'{bearing_len:.1f}'),
    (z_bear_top, z_post_top, -sp.post_diameter / 2,  f'{sp.post_height:.1f}'),
    (z_post_top, z_top,    -sp.cap_diameter / 2,   f'{sp.cap_height:.1f}'),
]
for z0, z1, x_edge, label in chain:
    add(Dimension((FX(x_edge), FZ(z0), 0), (FX(x_edge), FZ(z1), 0),
                  'left', FX(x_edge) - TIER1, draft, label=label))
add(Dimension((FX(-sp.cap_diameter / 2), FZ(bb.min.Z), 0),
              (FX(-sp.cap_diameter / 2), FZ(z_top), 0),
              'left', FX(-sp.cap_diameter / 2) - TIER2, draft, label=f'{z_top - bb.min.Z:.1f}'))

# String hole position from the bearing shoulder (right side)
add(Dimension((FX(sp.post_diameter / 2), FZ(z_bear_top), 0),
              (FX(sp.post_diameter / 2), FZ(z_hole), 0),
              'right', 158 - FX(sp.post_diameter / 2), draft,
              label=f'{sp.string_hole_position:.2f}'))

# Diameter / feature leaders on the front view (elbows right, staggered)
add(Leader(tip=(FX(sp.cap_diameter / 2 * 0.85), FZ(z_top - 0.2), 0),
           elbow=(168, 272, 0), label=f'ø{sp.cap_diameter:.1f} CAP', draft=draft))
add(Leader(tip=(FX(sp.post_diameter / 2), FZ(z_post_top - 1.0), 0),
           elbow=(168, 262, 0), label=f'ø{sp.post_diameter:.1f} POST', draft=draft))
add(Leader(tip=(FX(0.85 * 0.707), FZ(z_hole + 0.85 * 0.707), 0),
           elbow=(168, 243, 0),
           label=f'ø{sp.string_hole_diameter:.1f} THRU', draft=draft))
add(Leader(tip=(FX(sp.bearing_diameter / 2), FZ((z_dd_top + z_bear_top) / 2), 0),
           elbow=(170, 188, 0),
           label=f'ø{sp.bearing_diameter:.1f} h7 BEARING', draft=draft))

# Bottom view: DD across-flats, DD diameter, M2 tap hole
add(Dimension((BX(-dd_af / 2), BY(0), 0), (BX(dd_af / 2), BY(0), 0),
              'below', BY(0) - 16, draft, label=f'{dd_af:.1f} A/F'))
# Leaders routed left so they clear the cap top view to the right
add(Leader(tip=(BX(dd_dia / 2 * 0.707), BY(dd_dia / 2 * 0.707), 0),
           elbow=(48, 92, 0), label=f'ø{dd_dia:.1f} DD', draft=draft))
add(Leader(tip=(BX(0.57), BY(-0.57), 0),
           elbow=(42, 40, 0),
           label=f'M2 × {sp.thread_length:.1f} DEEP', draft=draft))

# Cap top view: crosshair, groove label, view caption
add(Centerline((TX(-sp.cap_diameter / 2) - 2, TY(0), 0), (TX(sp.cap_diameter / 2) + 2, TY(0), 0)))
add(Centerline((TX(0), TY(-sp.cap_diameter / 2) - 2, 0), (TX(0), TY(sp.cap_diameter / 2) + 2, 0)))
add(Leader(tip=(TX(-groove_rs[-1] * 0.707), TY(groove_rs[-1] * 0.707), 0),
           elbow=(150, 105, 0),
           label=f'{sp.cap_groove_count} × V-GROOVES '
                 f'{sp.cap_groove_width:.2f} × {sp.cap_groove_depth:.2f}', draft=draft))

# ── Text blocks (notes) ───────────────────────────────────────────────────────
notes = text_block([
    'NOTES',
    '1. MATERIAL: CZ121 BRASS',
    '2. SAME PART FOR RH AND LH',
    f'3. DD SHAFT ø{dd_dia:.1f} / {dd_af:.1f} A/F — SLIP FIT IN WHEEL DD BORE '
    f'(ø{sp.dd_cut.diameter:.1f} / {sp.dd_cut.across_flats:.1f})',
    f'4. M2 TAP HOLE: ø{sp.tap_bore_diameter:.1f} DRILL × {sp.thread_length:.1f} DEEP, TAP M2 × 0.4',
    f'5. STRING HOLE: CHAMFER {sp.string_hole_chamfer:.1f} BOTH ENDS',
    f'6. CAP: {sp.cap_groove_count} CONCENTRIC V-GROOVES {sp.cap_groove_width:.2f} WIDE × '
    f'{sp.cap_groove_depth:.2f} DEEP, CENTRES AT '
    + ', '.join(f'ø{2 * r:.2f}' for r in groove_rs)
    + f' (OUTER EDGE ø{sp.cap_groove_outer_od:.1f})',
    f'7. CAP EDGES: FILLET R{sp.cap_fillet:.2f} TOP AND BOTTOM, {sp.cap_chamfer:.1f} CHAMFER',
    '8. DO NOT SCALE DRAWING',
], 215, 130)

caption = text_block(['SHADED PICTORIAL — NOT TO SCALE'], PIC_X + 25, PIC_Y - 3)
caption += text_block(['CAP TOP VIEW'], TV_X - 11, TV_Y - sp.cap_diameter / 2 * SCALE - 4)

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    'STRING POST',
    'GIB-TUN-SP',
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
issues = lint_drawing(anns, drawing_scale=SCALE, view_shapes=[front, bot, top])
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
svg.add_layer('hidden', line_color=Color(0.45, 0.45, 0.45), line_weight=0.25,
              line_type=LineType.HIDDEN)
svg.add_layer('dims',   line_color=Color(0, 0.2, 0.7), fill_color=Color(0, 0.2, 0.7),
              line_weight=0.05)
for v in (front, bot, top):
    svg.add_shape(v, layer='part')
if front_h:
    svg.add_shape(front_h, layer='hidden')
for a in anns + notes + caption:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

dxf = ExportDXF()
dxf.add_layer('part',   line_weight=0.5)
dxf.add_layer('hidden', line_weight=0.25)
dxf.add_layer('dims',   line_weight=0.05)
for v in (front, bot, top):
    dxf.add_shape(v, layer='part')
if front_h:
    dxf.add_shape(front_h, layer='hidden')
for a in anns + notes + caption:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# ── Shaded pictorial embedded into the SVG ────────────────────────────────────
print('Rendering shaded pictorial...')
with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
    stl_path = tmp.name
export_stl(part, stl_path, tolerance=0.0003, angular_tolerance=0.05)
png_path = stl_path.replace('.stl', '.png')
# Camera high enough to show the cap grooves; zoom < 1 so the full part fits
render_shaded_pictorial(stl_path, png_path, cam_dir=(1.0, -1.0, 0.9),
                        dist=max(bb.size.X, bb.size.Y, bb.size.Z) * 2.6,
                        window_size=(int(PIC_W) * 10, int(PIC_H) * 10), zoom=0.85)
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
