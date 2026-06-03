"""Engineering drawing: 5-gang frame.

A4 landscape, third-angle projection, scale 1:1.
Four views: front elevation (side), plan (top), end elevation, isometric.

Run:
    uv run python scripts/drawings/frame.py
Outputs:
    drawings/frame.svg
    drawings/frame.dxf
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from build123d import (
    Color, Compound, ExportDXF, ExportSVG, LineType, Location,
)
from build123d_drafting import (
    Dimension, Leader, TitleBlock,
    annotate, draft_preset, lint_drawing, place_dims, set_page,
)

from gib_tuners.config.defaults import calculate_worm_z, create_default_config, resolve_gear_config
from gib_tuners.components.frame import create_frame

# ── Build geometry from source ────────────────────────────────────────────────
gear_paths = resolve_gear_config("c13-10")
config = create_default_config(
    gear_json_path=gear_paths.json_path,
    config_dir=gear_paths.config_dir,
)
frame = create_frame(config, label=False)

cfg = config.frame
gear = config.gear

total_length = cfg.total_length       # 145.0
housing_length = cfg.housing_length   # 16.2
end_length = cfg.end_length           # 10.0
pitch = cfg.tuner_pitch               # 27.2
box_outer = cfg.box_outer             # 10.0
centers = list(cfg.housing_centers)
mounting_holes = list(cfg.mounting_hole_positions)
effective_cd = gear.center_distance - gear.extra_backlash
post_y_1 = centers[0] - effective_cd / 2   # first post-bearing hole Y position
worm_z = calculate_worm_z(config)           # worm axis Z in frame (-5.0)

# ── Sheet layout ──────────────────────────────────────────────────────────────
# A4 landscape: 297 × 210 mm, 10 mm margin
#
# View centres (sheet coords, origin bottom-left):
#   Front elevation (looking from -X): centre (148, 85)
#   Plan/top (looking from +Z):        centre (148, 108) — above front
#   End elevation (looking from +Y):   centre (240, 85)  — right of front
#   Isometric (0.5× scale):            centre (257, 150) — top-right
#
# Coordinate formulas (confirmed via view_axes()):
#   Front / Top: sheet_x = 220.5 − world_Y   (world_Y → page_X sign=−1)
#   Front:       sheet_y = 90 + world_Z       (world_Z → page_Y sign=+1)
#   Top:         sheet_y = 108 + world_X      (world_X → page_Y sign=+1)
#   End:         sheet_x = 240 − world_X      (world_X → page_X sign=−1)
#   End:         sheet_y = 90 + world_Z       (same vertical mapping as front)

FX = lambda y: 220.5 - y            # world Y → front/top sheet X
FRONT_YBOT = 80.0                    # sheet_y at Z=−10 (frame bottom)
FRONT_YTOP = 90.0                    # sheet_y at Z=0   (frame top)

# ── Project views ─────────────────────────────────────────────────────────────
FV_CX, FV_CY = 148, 85
TV_CX, TV_CY = 148, 108
EV_CX, EV_CY = 240, 85

# Front elevation (side view, shows frame length and height)
fv_vis, fv_hid = frame.project_to_viewport((-100, 72.5, -5), (0, 0, 1), (0, 72.5, -5))
fv = Compound(children=list(fv_vis)).locate(Location((FV_CX, FV_CY, 0)))
fv_h = (Compound(children=list(fv_hid)).locate(Location((FV_CX, FV_CY, 0)))
        if fv_hid else None)

# Plan / top view (up=(1,0,0) keeps world-Y horizontal, aligning with front)
tv_vis, tv_hid = frame.project_to_viewport((0, 72.5, 100), (1, 0, 0), (0, 72.5, -5))
tv = Compound(children=list(tv_vis)).locate(Location((TV_CX, TV_CY, 0)))
tv_h = (Compound(children=list(tv_hid)).locate(Location((TV_CX, TV_CY, 0)))
        if tv_hid else None)

# End elevation (cross-section, third-angle: placed right of front)
ev_vis, ev_hid = frame.project_to_viewport((0, 300, -5), (0, 0, 1), (0, 72.5, -5))
ev = Compound(children=list(ev_vis)).locate(Location((EV_CX, EV_CY, 0)))
ev_h = (Compound(children=list(ev_hid)).locate(Location((EV_CX, EV_CY, 0)))
        if ev_hid else None)

# Isometric (0.5× scale — spatial context only, no dimensions)
frame_half = frame.scale(0.5)
iso_vis, _ = frame_half.project_to_viewport((50, -15, 50), (0, 0, 1), (0, 36.25, -2.5))
iso_v = Compound(children=list(iso_vis)).locate(Location((257, 150, 0)))

# ── Draft settings ────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)

# ── Dimension coordinates ─────────────────────────────────────────────────────
x_y0   = FX(0)                            # sheet_x at Y=0   (frame start)
x_end  = FX(end_length)                   # sheet_x at Y=10  (end of first end gap)
x_h1e  = FX(end_length + housing_length)  # sheet_x at Y=26.2 (end of housing 1)
x_c1   = FX(centers[0])                   # sheet_x at housing centre 1
x_c2   = FX(centers[1])                   # sheet_x at housing centre 2
x_y145 = FX(total_length)                 # sheet_x at Y=145  (frame end)

# ── Stacked dimensions below front elevation ──────────────────────────────────
dims_below = place_dims([
    ((x_y0,  FRONT_YBOT, 0), (x_y145, FRONT_YBOT, 0), "below", f"{total_length:.1f}"),
    ((x_y0,  FRONT_YBOT, 0), (x_end,  FRONT_YBOT, 0), "below", f"{end_length:.1f}"),
    ((x_end, FRONT_YBOT, 0), (x_h1e,  FRONT_YBOT, 0), "below", f"{housing_length:.1f}"),
    ((x_c1,  FRONT_YBOT, 0), (x_c2,   FRONT_YBOT, 0), "below", f"{pitch:.1f}"),
], draft)
for i, d in enumerate(dims_below):
    annotate(d, f"dim_below_{i}")

# ── Box height (left of front elevation) ─────────────────────────────────────
d_height = Dimension(
    (x_y145 - 8, FRONT_YTOP, 0),
    (x_y145 - 8, FRONT_YBOT, 0),
    "left", 5, draft, label=f"{box_outer:.1f}",
)
annotate(d_height, "dim_height")

# ── Leaders (max 3) ───────────────────────────────────────────────────────────
# Post-bearing holes — circles in the plan view
px = FX(post_y_1)
ldr_post = Leader(
    tip=(px, 110.6, 0),
    elbow=(px - 18, 122, 0),
    label="ø5.05 THRU ×5",
    draft=draft,
)
annotate(ldr_post, "ldr_post_bearing")

# Mounting holes — circles in the plan view
mx = FX(mounting_holes[0])
ldr_mount = Leader(
    tip=(mx, 109.8, 0),
    elbow=(mx + 12, 122, 0),
    label="ø3.2 THRU ×6",
    draft=draft,
)
annotate(ldr_mount, "ldr_mounting")

# Worm-entry holes — circles on +X face in end elevation
# END_X(5) = 235; END_Y(worm_z = -5) = 85
ldr_worm = Leader(
    tip=(235 - cfg.worm_entry_hole / 2, 85, 0),
    elbow=(226, 93, 0),
    label=f"ø{cfg.worm_entry_hole:.2f} ×5",
    draft=draft,
)
annotate(ldr_worm, "ldr_worm_entry")

# ── End view dimensions ─────────────────────────────────────────────────────
# Camera at +Y→-Y, up=+Z: world_X → page_X (-1), world_Z → page_Y (+1)
# Scale 1:1. look_at z=-5 → END_Z(z) = EV_CY + z + 5
END_X = lambda x: EV_CX - x
END_Z = lambda z: EV_CY + z + 5
d_end_w = Dimension(
    (END_X(-box_outer / 2), END_Z(-box_outer) - 3, 0),
    (END_X( box_outer / 2), END_Z(-box_outer) - 3, 0),
    "below", 3, draft, label=f"{box_outer:.1f}",
)
annotate(d_end_w, "dim_end_width")

d_end_h = Dimension(
    (END_X(-box_outer / 2) + 3, END_Z(-box_outer), 0),
    (END_X(-box_outer / 2) + 3, END_Z(0), 0),
    "right", 3, draft, label=f"{box_outer:.1f}",
)
annotate(d_end_h, "dim_end_height")

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    "FRAME - 5 GANG", "DWG-001",
    scale="1:1",
    material="CuZn37 BRASS TUBE",
    general_tolerance="ISO 2768-m",
    designed_by="GIB TUNERS",
    date="2026-06-03",
    width=170.0,
    draft=draft,
).locate(Location((116, 11, 0)))
annotate(tb, "title_block")

# ── Lint gate ─────────────────────────────────────────────────────────────────
all_anns = list(dims_below) + [d_height, ldr_post, ldr_mount, ldr_worm,
                               d_end_w, d_end_h, tb]
set_page(297, 210, margin=10)
issues = lint_drawing(all_anns, drawing_scale=1.0)
if issues:
    print(f"WARNING: {len(issues)} lint issue(s):")
    for iss in issues:
        print(f"  [{iss.severity}] {iss.code}: {iss.message}")
else:
    print("Lint: OK")

# ── Export SVG ────────────────────────────────────────────────────────────────
output_dir = Path(__file__).parent.parent.parent / "drawings"
output_dir.mkdir(exist_ok=True)

part_color = Color(0, 0, 0)
hid_color  = Color(0.5, 0.5, 0.5)
dim_color  = Color(0, 0.2, 0.7)

svg_exp = ExportSVG(margin=10)
svg_exp.add_layer("part",   line_color=part_color, line_weight=0.5)
svg_exp.add_layer("hidden", line_color=hid_color,  line_weight=0.25,
                  line_type=LineType.HIDDEN)
svg_exp.add_layer("dims",   line_color=dim_color,  fill_color=dim_color,
                  line_weight=0.05)
for shape in [fv, tv, ev, iso_v]:
    svg_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, tv_h, ev_h] if s]:
    svg_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    svg_exp.add_shape(ann, layer="dims")
svg_path = output_dir / "frame.svg"
svg_exp.write(str(svg_path))
print(f"SVG: {svg_path}")

# ── Export DXF ────────────────────────────────────────────────────────────────
dxf_exp = ExportDXF()
dxf_exp.add_layer("part",   line_weight=0.5)
dxf_exp.add_layer("hidden", line_weight=0.25, line_type=LineType.HIDDEN)
dxf_exp.add_layer("dims",   line_weight=0.05)
for shape in [fv, tv, ev, iso_v]:
    dxf_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, tv_h, ev_h] if s]:
    dxf_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    dxf_exp.add_shape(ann, layer="dims")
dxf_path = output_dir / "frame.dxf"
dxf_exp.write(str(dxf_path))
print(f"DXF: {dxf_path}")
