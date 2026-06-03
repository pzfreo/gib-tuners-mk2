"""Engineering drawing: Single tuner unit assembly.

A4 landscape, scale 2:1.
1-housing frame with all internal components positioned.

Four views (third-angle projection):
  Front view — looking from -X (worm entry side), shows frame length and post
  Plan view  — looking from +Z (above), shows footprint, holes, peg head
  End view   — looking from -Y (frame end), shows cross-section

Coordinate convention (view_axes verified):
  Front (camera -X, up +Z): world_Y → page_X (-1), world_Z → page_Y (+1)
  Plan  (camera +Z, up +Y): world_X → page_X (+1), world_Y → page_Y (+1)
  End   (camera -Y, up +Z): world_X → page_X (+1), world_Z → page_Y (+1)

Run:
    uv run python scripts/drawings/assembly.py
Outputs:
    drawings/assembly.svg
    drawings/assembly.dxf
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from build123d import Color, Compound, ExportDXF, ExportSVG, LineType, Location
from build123d_drafting import (
    Dimension, Leader, TitleBlock,
    annotate, draft_preset, lint_drawing, place_dims, set_page,
)

from gib_tuners.config.defaults import calculate_worm_z, create_default_config, resolve_gear_config
from gib_tuners.assembly.gang_assembly import create_positioned_assembly

# ── Build 1-housing assembly ───────────────────────────────────────────────────
gear_paths = resolve_gear_config("c13-10")
config_5 = create_default_config(
    gear_json_path=gear_paths.json_path,
    config_dir=gear_paths.config_dir,
)
# Override to 1 housing for the assembly drawing
config = replace(
    config_5,
    frame=replace(config_5.frame, num_housings=1),
)

asm = create_positioned_assembly(
    config,
    wheel_step_path=gear_paths.wheel_step,
    worm_step_path=gear_paths.worm_step,
    include_hardware=True,
)
frame      = asm["frame"]
all_parts  = asm["all_parts"]   # dict: "frame", "string_post_1", "wheel_1", "peg_head_1", …

# Merge all parts into a single Compound for projection
all_shapes = list(all_parts.values())
assembly = Compound(children=[s for s in all_shapes if s is not None])

fr  = config.frame
gear = config.gear

total_length = fr.total_length           # 36.2mm (1-housing)
box_outer   = fr.box_outer               # 10.0mm
post_h      = config.string_post.post_height  # 5.5mm  (above frame top)
y_center    = total_length / 2           # 18.1mm
z_center    = -box_outer / 2            # -5.0mm

# ── Scale 2:1 ─────────────────────────────────────────────────────────────────
SCALE = 2.0
asm_2x = assembly.scale(SCALE)

# look_at in 2x space
y2 = y_center * SCALE    # 36.2
z2 = z_center * SCALE    # -10.0

# ── Project views ──────────────────────────────────────────────────────────────
# Front: looking from -X
fv_vis, fv_hid = asm_2x.project_to_viewport((-200, y2, z2), (0, 0, 1), (0, y2, z2))

# Plan: looking from +Z (above)
tv_vis, tv_hid = asm_2x.project_to_viewport((0, y2, 200), (0, 1, 0), (0, y2, z2))

# End: looking from -Y
ev_vis, ev_hid = asm_2x.project_to_viewport((0, -200, z2), (0, 0, 1), (0, y2, z2))

# Isometric pictorial (1:1) — front-right-above diagonal
iso_vis, iso_hid = assembly.project_to_viewport(
    (100, -100, 100), (0, 0, 1), (0, y_center, z_center)
)

# ── Sheet layout ───────────────────────────────────────────────────────────────
# Full assembly bbox: X=-7..22.9 (peg head extends far +X), Y=0..36.2, Z=-11.2..6.5
# At SCALE=2: front view 72.4mm wide × 35.4mm tall; plan view 59.6mm wide × 72.4mm tall
# End view from -Y shows peg head extending to X=22.9 → 45.8mm wide at 2:1
#
# Layout chosen to clear overlap between end view and front view:
#   EV_X=40  → end right edge at 40+45.8=85.8, front left at 195-36.2=158.8 → 73mm gap
#   FV_X=195 → front centred at 195
#   TV_X=185, TV_Y=155 → plan bottom 118.8, front top 93 → 25.8mm gap

FV_X, FV_Y = 195.0, 70.0
TV_X, TV_Y = 185.0, 155.0    # above front
EV_X, EV_Y = 40.0,  70.0     # far left of front
ISO_X, ISO_Y = 60.0, 150.0   # isometric: above end view (1:1)

fv  = Compound(children=list(fv_vis )).locate(Location((FV_X,  FV_Y,  0)))
tv  = Compound(children=list(tv_vis )).locate(Location((TV_X,  TV_Y,  0)))
ev  = Compound(children=list(ev_vis )).locate(Location((EV_X,  EV_Y,  0)))
iso = Compound(children=list(iso_vis)).locate(Location((ISO_X, ISO_Y, 0)))
fv_h  = (Compound(children=list(fv_hid )).locate(Location((FV_X,  FV_Y,  0))) if fv_hid  else None)
tv_h  = (Compound(children=list(tv_hid )).locate(Location((TV_X,  TV_Y,  0))) if tv_hid  else None)
ev_h  = (Compound(children=list(ev_hid )).locate(Location((EV_X,  EV_Y,  0))) if ev_hid  else None)
iso_h = (Compound(children=list(iso_hid)).locate(Location((ISO_X, ISO_Y, 0))) if iso_hid else None)

# ── Draft settings ─────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)

# ── Coordinate helpers (original 1:1 mm) ──────────────────────────────────────
# Front view: world_Y → page_X (-1), world_Z → page_Y (+1), look_at (0, y_center, z_center)
def FX(y): return FV_X - (y - y_center) * SCALE
def FZ(z): return FV_Y + (z - z_center) * SCALE

# Plan view: world_X → page_X (+1), world_Y → page_Y (+1), look_at (0, y_center, z_center)
def TX(x): return TV_X + x * SCALE
def TY(y): return TV_Y + (y - y_center) * SCALE

# End view: world_X → page_X (+1), world_Z → page_Y (+1), look_at (0, y_center, z_center)
def EX(x): return EV_X + x * SCALE
def EZ(z): return EV_Y + (z - z_center) * SCALE

# Profile extents  (with FV_Y=70: FZ(-11.2)=57.6, FZ(6.5)=93)
FRONT_YBOT = FZ(-box_outer) - 3    # below frame bottom face (= 57)
FRONT_YTOP = FZ(post_h) + 2        # above post top (= 93)

# ── Frame length dimension (below front view) ──────────────────────────────────
dims_below = place_dims([
    ((FX(0), FRONT_YBOT, 0), (FX(total_length), FRONT_YBOT, 0),
     "below", f"{total_length:.1f}"),
], draft)
for i, d in enumerate(dims_below):
    annotate(d, f"dim_length_{i}")

# Post height above frame
d_post_h = Dimension(
    (FX(0) + 3, FZ(0), 0),
    (FX(0) + 3, FZ(post_h), 0),
    "left", 5, draft, label=f"{post_h:.1f}",
)
annotate(d_post_h, "dim_post_height")

# Frame height
d_frame_h = Dimension(
    (FX(total_length) - 3, FZ(-box_outer), 0),
    (FX(total_length) - 3, FZ(0), 0),
    "right", 6, draft, label=f"{box_outer:.1f}",
)
annotate(d_frame_h, "dim_frame_height")

# ── End view dimensions (box section) ─────────────────────────────────────────
# Width across frame
d_end_w = Dimension(
    (EX(-box_outer / 2), EZ(-box_outer) - 4, 0),
    (EX( box_outer / 2), EZ(-box_outer) - 4, 0),
    "below", 4, draft, label=f"{box_outer:.1f}",
)
annotate(d_end_w, "dim_end_width")

# Height of frame
d_end_h = Dimension(
    (EX(box_outer / 2) + 3, EZ(-box_outer), 0),
    (EX(box_outer / 2) + 3, EZ(0), 0),
    "right", 4, draft, label=f"{box_outer:.1f}",
)
annotate(d_end_h, "dim_end_height")

# ── Part identification leaders ────────────────────────────────────────────────
housing_y = fr.housing_centers[0]       # ≈ 18.1mm
eff_cd    = gear.center_distance - gear.extra_backlash
post_y    = housing_y - eff_cd / 2      # string post Y ≈ 15mm
worm_z    = calculate_worm_z(config)    # ≈ -5.0mm

# Peg head ring in front view (visible as large circle)
ldr_peg = Leader(
    tip=(FX(post_y), FZ(worm_z), 0),
    elbow=(FX(post_y) - 16, FZ(worm_z) - 12, 0),
    label="PEG HEAD",
    draft=draft,
)
annotate(ldr_peg, "ldr_peg_head")

# String post above frame in front view
ldr_post = Leader(
    tip=(FX(post_y), FZ(post_h * 0.5), 0),
    elbow=(FX(post_y) + 18, FZ(post_h * 0.5) + 14, 0),
    label="STRING POST",
    draft=draft,
)
annotate(ldr_post, "ldr_string_post")

# Worm wheel — labelled in end view where its face is visible looking from -Y
# Wheel center: X≈0, Z≈-5 (same as worm axis)
ldr_wheel = Leader(
    tip=(EX(0), EZ(worm_z), 0),
    elbow=(EX(box_outer / 2) + 16, EZ(worm_z) - 10, 0),
    label="WORM WHEEL",
    draft=draft,
)
annotate(ldr_wheel, "ldr_wheel")

# Frame — label at top edge of end view
ldr_frame = Leader(
    tip=(EX(0), EZ(0), 0),
    elbow=(EX(0) - 14, EZ(0) + 12, 0),
    label="FRAME",
    draft=draft,
)
annotate(ldr_frame, "ldr_frame")

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    "ASSEMBLY - 1 UNIT", "DWG-004",
    scale="2:1",
    material="SEE BOM",
    general_tolerance="N/A",
    designed_by="GIB TUNERS",
    date="2026-06-03",
    width=170.0,
    draft=draft,
).locate(Location((116, 11, 0)))
annotate(tb, "title_block")

# ── Lint gate ─────────────────────────────────────────────────────────────────
all_anns = (list(dims_below)
            + [d_post_h, d_frame_h,
               d_end_w, d_end_h,
               ldr_peg, ldr_post, ldr_wheel, ldr_frame, tb])
set_page(297, 210, margin=10)
issues = lint_drawing(all_anns, drawing_scale=SCALE)
if issues:
    print(f"WARNING: {len(issues)} lint issue(s):")
    for iss in issues:
        print(f"  [{iss.severity}] {iss.code}: {iss.message}")
else:
    print("Lint: OK")

# ── Export SVG ─────────────────────────────────────────────────────────────────
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
for shape in [fv, tv, ev, iso]:
    svg_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, tv_h, ev_h, iso_h] if s]:
    svg_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    svg_exp.add_shape(ann, layer="dims")
svg_path = output_dir / "assembly.svg"
svg_exp.write(str(svg_path))
print(f"SVG: {svg_path}")

# ── Export DXF ─────────────────────────────────────────────────────────────────
dxf_exp = ExportDXF()
dxf_exp.add_layer("part",   line_weight=0.5)
dxf_exp.add_layer("hidden", line_weight=0.25, line_type=LineType.HIDDEN)
dxf_exp.add_layer("dims",   line_weight=0.05)
for shape in [fv, tv, ev, iso]:
    dxf_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, tv_h, ev_h, iso_h] if s]:
    dxf_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    dxf_exp.add_shape(ann, layer="dims")
dxf_path = output_dir / "assembly.dxf"
dxf_exp.write(str(dxf_path))
print(f"DXF: {dxf_path}")
