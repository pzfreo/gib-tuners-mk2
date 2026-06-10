#!/usr/bin/env python3
"""A3 engineering drawing of the worm wheel (RH) using build123d_drafting.

Views (third-angle, 10:1 on A3 landscape):
  - Plan view (camera at +Z, above): tooth profile, DD bore with across-flats
    dim and bore/tip leaders
  - Front view (camera at -Y, below the plan): face width
  - Shaded pictorial (pyvista raster, embedded in the SVG/PDF; omitted from
    the DXF) — HLR line art of helical teeth reads poorly, hence shaded

The wheel geometry comes from the gear calculator STEP
(config/<gear>/wheel_m0.5_z13.step) via load_wheel(); the gear data table and
all labels derive from the live config so the sheet cannot drift.

Axis mappings (verified with build123d-mcp view_axes):
  plan  (camera +Z, up +Y): world_X -> page_X (+1), world_Y -> page_Y (+1)
  front (camera -Y, up +Z): world_X -> page_X (+1), world_Z -> page_Y (+1)

Outputs: drawings/<gear>/wheel_rh.svg / .dxf / .pdf
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from build123d import (
    Color, Compound, ExportDXF, ExportSVG, Location, Plane, export_stl,
)
from build123d_drafting import (
    Centerline, Dimension, Leader, TitleBlock,
    draft_preset, fix_svg_page_size, lint_drawing, set_page,
)
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.components.wheel import load_wheel
from gib_tuners.export.drawing_utils import (
    embed_png_in_svg, exactify_silhouettes, project_visible,
    render_shaded_pictorial, section_profile, text_block,
)

# ── Config ────────────────────────────────────────────────────────────────────
GEAR    = 'c13-10'
OUT_DIR = Path(__file__).parent.parent / 'drawings' / GEAR
OUT_DIR.mkdir(parents=True, exist_ok=True)
STEM    = OUT_DIR / 'wheel_rh'

SCALE  = 10.0
PAGE_W = 420.0   # A3 landscape
PAGE_H = 297.0
TB_W   = 150.0

gp  = resolve_gear_config(GEAR)
cfg = create_default_config(gear_json_path=gp.json_path, config_dir=gp.config_dir)
wh  = cfg.gear.wheel

# Tip reduction (interference relief) is already cut into the STEP; recover it
# from the standard tip formula so the note tracks the config
tip_reduction = wh.pitch_diameter + 2 * wh.module * (1 + wh.profile_shift) - wh.tip_diameter

# DD shaft dims (the mating post) for the slip-fit note
dd_shaft_dia = wh.bore.diameter - cfg.string_post.dd_shaft_clearance
dd_shaft_af  = wh.bore.across_flats - cfg.string_post.dd_shaft_clearance

# ── Build geometry ────────────────────────────────────────────────────────────
print('Loading wheel geometry...')
part = load_wheel(gp.wheel_step)
bb = part.bounding_box()
cx, cy, cz = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2, (bb.min.Z + bb.max.Z) / 2
print(f'  bbox X {bb.min.X:.2f}..{bb.max.X:.2f}  Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}')

# ── Project views ─────────────────────────────────────────────────────────────
part_s = part.scale(SCALE)
cxs, cys, czs = cx * SCALE, cy * SCALE, cz * SCALE
look = (cxs, cys, czs)
DIST = max(bb.size.X, bb.size.Y, bb.size.Z) * SCALE + 100

# Page positions (view centres) and pictorial image box (page mm)
PV_X, PV_Y = 110.0, 215.0    # plan view (tooth profile + bore)
FV_X, FV_Y = 110.0, 120.0    # front view (face width), below the plan
PIC_X, PIC_Y, PIC_W, PIC_H = 250.0, 140.0, 120.0, 100.0  # pictorial: left, bottom, size

# The gear calculator builds each tooth from stacked surface patches, so an
# HLR view of the wheel carries ~170 tangent seam edges that stripe every
# flank, and a direct axial view shows both end profiles twisted by the helix.
# Hence: the tooth-profile view is a transverse section at mid-face (single
# clean profile), and the front view is projected with smooth seam edges
# suppressed. Hidden lines are omitted (they blanket the face view; the bore
# is fully described in the profile view).
print('Projecting views (section + HLR)...')
plan_vis = section_profile(part_s, Plane.XY.offset(czs))
front_vis = project_visible(part_s, (cxs, cys - DIST, czs), (0, 0, 1), look,
                            include_smooth=False)

front_vis, n_f = exactify_silhouettes(
    list(front_vis), part_s.faces(), (0, 1, 0), lambda p: (p.X() - cxs, p.Z() - czs))
print(f'  exactified silhouettes: front {n_f}')

plan  = Compound(children=list(plan_vis)).locate(Location((PV_X - cxs, PV_Y - cys, 0)))
front = Compound(children=list(front_vis)).locate(Location((FV_X, FV_Y, 0)))

# ── Coordinate helpers ────────────────────────────────────────────────────────
def PX(x): return PV_X + (x - cx) * SCALE      # plan:  world_X -> page_X (+1)
def PY(y): return PV_Y + (y - cy) * SCALE      # plan:  world_Y -> page_Y (+1)
def FX(x): return FV_X + (x - cx) * SCALE      # front: world_X -> page_X (+1)
def FZ(z): return FV_Y + (z - cz) * SCALE      # front: world_Z -> page_Y (+1)

# ── Annotations ───────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)
anns = []

def add(a):
    anns.append(a)
    return a

r_tip = wh.tip_diameter / 2

# Centerlines: crosshair on plan, axis + mid-plane on front
add(Centerline((PX(-r_tip) - 4, PY(0), 0), (PX(r_tip) + 4, PY(0), 0)))
add(Centerline((PX(0), PY(-r_tip) - 2, 0), (PX(0), PY(r_tip) + 4, 0)))
add(Centerline((FX(0), FZ(bb.min.Z) - 4, 0), (FX(0), FZ(bb.max.Z) + 4, 0)))

# Plan view: across-flats dim in the gap below the view, bore leader left,
# tip leader right
add(Dimension((PX(-wh.bore.across_flats / 2), PY(0), 0),
              (PX(wh.bore.across_flats / 2), PY(0), 0),
              'below', r_tip * SCALE + 11, draft,
              label=f'{wh.bore.across_flats:.1f} A/F'))
add(Leader(tip=(PX(-wh.bore.diameter / 2 * 0.707), PY(wh.bore.diameter / 2 * 0.707), 0),
           elbow=(58, 262, 0), label=f'ø{wh.bore.diameter:.1f} BORE', draft=draft))
add(Leader(tip=(PX(r_tip * 0.643), PY(r_tip * 0.766), 0),
           elbow=(155, 268, 0), label=f'ø{wh.tip_diameter:.1f} TIP', draft=draft))

# Front view: face width (left side)
add(Dimension((FX(-r_tip), FZ(bb.min.Z), 0), (FX(-r_tip), FZ(bb.max.Z), 0),
              'left', FX(-r_tip) - 58, draft, label=f'{wh.face_width:.1f}'))

# ── Text blocks (wheel data + notes) ──────────────────────────────────────────
wheel_table = text_block([
    'WHEEL DATA',
    f'MODULE            {wh.module:.1f}',
    f'TEETH             {wh.num_teeth}',
    f'PRESSURE ANGLE    {cfg.gear.pressure_angle_deg:.0f}°',
    f'PITCH DIA         ø{wh.pitch_diameter:.1f}',
    f'TIP DIA           ø{wh.tip_diameter:.1f}',
    f'ROOT DIA          ø{wh.root_diameter:.2f}',
    f'PROFILE SHIFT     +{wh.profile_shift:.1f}',
    f'FACE WIDTH        {wh.face_width:.1f}',
    f'CENTRE DISTANCE   {cfg.gear.center_distance:.2f} (TO WORM)',
], 20, 105)

notes = text_block([
    'NOTES',
    '1. MATERIAL: PHOSPHOR BRONZE PB102',
    '2. RH SHOWN — LH VARIANT IS MIRROR IMAGE (OPPOSITE HELIX)',
    f'3. DD BORE ø{wh.bore.diameter:.1f} / {wh.bore.across_flats:.1f} A/F — '
    f'SLIP FIT ON POST DD (ø{dd_shaft_dia:.1f} / {dd_shaft_af:.1f})',
    f'4. TOOTH TIPS REDUCED {tip_reduction:.1f} TO CLEAR WORM ROOT — '
    f'ø{wh.tip_diameter:.1f} IS AS-CUT',
    f'5. TOOTH GEOMETRY FROM config/{GEAR} STEP — DO NOT RE-DERIVE FROM TABLE',
    '6. DO NOT SCALE DRAWING',
], 215, 105)

caption = text_block(['SHADED PICTORIAL — NOT TO SCALE'], PIC_X + 25, PIC_Y - 3)
caption += text_block(['TOOTH PROFILE — TRANSVERSE SECTION AT MID-FACE'],
                      PV_X - 35, PV_Y + r_tip * SCALE + 12)

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    'WORM WHEEL (RH)',
    'GIB-TUN-WW-RH',
    drawing_scale=SCALE,
    material='PHOS BRONZE PB102',
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
issues = lint_drawing(anns, drawing_scale=SCALE, view_shapes=[plan, front])
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
for v in (plan, front):
    svg.add_shape(v, layer='part')
for a in anns + wheel_table + notes + caption:
    svg.add_shape(a, layer='dims')
svg.write(str(STEM) + '.svg')
fix_svg_page_size(str(STEM) + '.svg', PAGE_W, PAGE_H)

dxf = ExportDXF()
dxf.add_layer('part',   line_weight=0.5)
dxf.add_layer('dims',   line_weight=0.05)
for v in (plan, front):
    dxf.add_shape(v, layer='part')
for a in anns + wheel_table + notes + caption:
    dxf.add_shape(a, layer='dims')
dxf.write(str(STEM) + '.dxf')

# ── Shaded pictorial embedded into the SVG ────────────────────────────────────
print('Rendering shaded pictorial...')
with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
    stl_path = tmp.name
export_stl(part, stl_path, tolerance=0.0003, angular_tolerance=0.05)
png_path = stl_path.replace('.stl', '.png')
# Camera low enough that the tooth helix is visible on the flanks
render_shaded_pictorial(stl_path, png_path, cam_dir=(1.0, -1.0, 0.5),
                        dist=max(bb.size.X, bb.size.Y, bb.size.Z) * 2.6,
                        window_size=(int(PIC_W) * 10, int(PIC_H) * 10), zoom=1.1)
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
