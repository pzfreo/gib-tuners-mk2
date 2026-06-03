"""Engineering drawing: String post.

A4 landscape, scale 2:1.
Three views: side (axis horizontal), bottom end (DD bore face), top end (cap face).

Third-angle projection:
  - Bottom end view (left) — DD bore face at Z=0
  - Side view (centre)     — complete stepped profile
  - Top/cap end view (right) — cap with V-grooves

Coordinate convention (view_axes verified):
  Side (camera -X, up +Y): world_Z → page_X (+1), world_Y → page_Y (+1)
  Bottom end (camera -Z, up +Y): world_X → page_X (-1), world_Y → page_Y (+1)
  Top end    (camera +Z, up +Y): world_X → page_X (+1), world_Y → page_Y (+1)

Run:
    uv run python scripts/drawings/string_post.py
Outputs:
    drawings/string_post.svg
    drawings/string_post.dxf
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from build123d import Color, Compound, ExportDXF, ExportSVG, LineType, Location
from build123d_drafting import (
    Dimension, Leader, TitleBlock,
    annotate, draft_preset, lint_drawing, place_dims, set_page,
)

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.components.string_post import create_string_post

# ── Build geometry ─────────────────────────────────────────────────────────────
gear_paths = resolve_gear_config("c13-10")
config = create_default_config(
    gear_json_path=gear_paths.json_path,
    config_dir=gear_paths.config_dir,
)
string_post = create_string_post(config)

sp = config.string_post
fr = config.frame
wh = config.gear.wheel

dd_len    = sp.get_dd_cut_length(wh.face_width)          # 7.1
bearing_h = sp.get_bearing_length(fr.wall_thickness)      # 1.2
post_h    = sp.post_height                                # 5.5
cap_h     = sp.cap_height                                 # 1.0
total_h   = dd_len + bearing_h + post_h + cap_h          # 14.8

cap_d     = sp.cap_diameter         # 7.5
post_d    = sp.post_diameter        # 6.0
bearing_d = sp.bearing_diameter     # 5.0
# DD shaft is undersized for slip fit
dd_shaft_d = sp.dd_cut.diameter - sp.dd_shaft_clearance  # 3.4
dd_af      = sp.dd_cut.across_flats - sp.dd_shaft_clearance  # 2.4
tap_d      = 1.6                    # M2 tap drill
tap_depth  = sp.thread_length       # 4.0
hole_d     = sp.string_hole_diameter       # 1.7
hole_pos   = sp.string_hole_position       # 2.75 mm from frame top
frame_top_z = dd_len + bearing_h           # 8.3 — Z where post exits frame
hole_z     = frame_top_z + hole_pos        # 11.05

# ── Scale 2:1 ─────────────────────────────────────────────────────────────────
SCALE = 2.0
post_2x = string_post.scale(SCALE)
# At 2:1 the part spans Z=[0, 29.6]; centre at Z=14.8
z_center = total_h  # = total_h*SCALE/2 when SCALE=2

# ── Project views ──────────────────────────────────────────────────────────────
SV_X, SV_Y = 148.0, 115.0   # side view sheet centre

sv_vis,  sv_hid  = post_2x.project_to_viewport((-200, 0, z_center), (0, 1, 0), (0, 0, z_center))
bev_vis, bev_hid = post_2x.project_to_viewport((0, 0, -200),        (0, 1, 0), (0, 0, z_center))
tev_vis, tev_hid = post_2x.project_to_viewport((0, 0,  200),        (0, 1, 0), (0, 0, z_center))

# Third-angle placement: bottom-end LEFT, cap-end RIGHT
cap_r_2x   = cap_d * SCALE / 2    # 7.5
half_len_2x = total_h              # 14.8 (= total_h*SCALE/2, since SCALE=2)

BEV_X = SV_X - half_len_2x - 13 - cap_r_2x   # 111.7
TEV_X = SV_X + half_len_2x + 13 + cap_r_2x   # 184.3

sv  = Compound(children=list(sv_vis )).locate(Location((SV_X,  SV_Y, 0)))
bev = Compound(children=list(bev_vis)).locate(Location((BEV_X, SV_Y, 0)))
tev = Compound(children=list(tev_vis)).locate(Location((TEV_X, SV_Y, 0)))
sv_h  = (Compound(children=list(sv_hid )).locate(Location((SV_X,  SV_Y, 0))) if sv_hid  else None)
bev_h = (Compound(children=list(bev_hid)).locate(Location((BEV_X, SV_Y, 0))) if bev_hid else None)
tev_h = (Compound(children=list(tev_hid)).locate(Location((TEV_X, SV_Y, 0))) if tev_hid else None)

# ── Draft settings ─────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)

# ── Coordinate helpers (original 1:1 mm) ──────────────────────────────────────
# Side view: world_Z → page_X (+1), look_at Z = z_center
# SX(z_orig) = SV_X + z_orig*SCALE - z_center
# SY(y_orig) = SV_Y + y_orig*SCALE
def SX(z): return SV_X + z * SCALE - z_center
def SY(y): return SV_Y + y * SCALE

# Section X positions in sheet coords
x_z0    = SX(0)                               # 133.2 — DD bore end (left)
x_z_dd  = SX(dd_len)                          # 147.4 — DD/bearing boundary
x_z_br  = SX(dd_len + bearing_h)             # 149.8 — bearing/post boundary
x_z_po  = SX(dd_len + bearing_h + post_h)    # 160.8 — post/cap boundary
x_z_cap = SX(total_h)                         # 162.8 — cap end (right)

SIDE_YBOT = SY(-cap_d / 2) - 2   # 2mm below widest profile
SIDE_YTOP = SY( cap_d / 2) + 2

# ── Stacked dimensions below side view ────────────────────────────────────────
dims_below = place_dims([
    ((x_z0,  SIDE_YBOT, 0), (x_z_cap, SIDE_YBOT, 0), "below", f"{total_h:.1f}"),
    ((x_z0,  SIDE_YBOT, 0), (x_z_dd,  SIDE_YBOT, 0), "below", f"{dd_len:.1f}"),
    ((x_z_dd, SIDE_YBOT, 0), (x_z_br, SIDE_YBOT, 0), "below", f"{bearing_h:.1f}"),
    ((x_z_br, SIDE_YBOT, 0), (x_z_po, SIDE_YBOT, 0), "below", f"{post_h:.1f}"),
    ((x_z_po, SIDE_YBOT, 0), (x_z_cap,SIDE_YBOT, 0), "below", f"{cap_h:.1f}"),
], draft)
for i, d in enumerate(dims_below):
    annotate(d, f"dim_len_{i}")

# ── Diameter leaders (right of side view, fanning up) ─────────────────────────
# Tips touch the profile surface; elbows fan upward to avoid overlap
elbow_x = x_z_cap + 16   # common elbow X, right of cap edge

ldr_cap_d = Leader(
    tip=(SX(total_h - cap_h * 0.5), SY(cap_d / 2), 0),
    elbow=(elbow_x, SV_Y + 13, 0),
    label=f"ø{cap_d:.1f}",
    draft=draft,
)
annotate(ldr_cap_d, "ldr_d_cap")

ldr_post_d = Leader(
    tip=(SX(dd_len + bearing_h + post_h * 0.4), SY(post_d / 2), 0),
    elbow=(elbow_x, SV_Y + 6, 0),
    label=f"ø{post_d:.1f}",
    draft=draft,
)
annotate(ldr_post_d, "ldr_d_post")

# Bearing section is narrow; point from below-profile to avoid clutter
ldr_bearing_d = Leader(
    tip=(SX(dd_len + bearing_h * 0.5), SY(-bearing_d / 2), 0),
    elbow=(SX(dd_len + bearing_h * 0.5), SV_Y - 13, 0),
    label=f"ø{bearing_d:.1f}",
    draft=draft,
)
annotate(ldr_bearing_d, "ldr_d_bearing")

# ── Feature leaders ────────────────────────────────────────────────────────────
# String hole: cross-drilled at Z=hole_z
ldr_hole = Leader(
    tip=(SX(hole_z), SY(post_d / 2), 0),
    elbow=(SX(hole_z) - 12, SV_Y + 20, 0),
    label=f"ø{hole_d:.1f} THRU ×1  {hole_pos:.2f} FROM FRAME TOP",
    draft=draft,
)
annotate(ldr_hole, "ldr_string_hole")

# M2 tap bore: shown on bottom-end view (BEV)
ldr_tap = Leader(
    tip=(BEV_X, SV_Y, 0),
    elbow=(BEV_X - 12, SV_Y + 14, 0),
    label=f"ø{tap_d:.1f} × {tap_depth:.0f} DEEP (M2 TAP)",
    draft=draft,
)
annotate(ldr_tap, "ldr_tap_bore")

# DD bore specification on bottom-end view
ldr_dd = Leader(
    tip=(BEV_X, SV_Y - dd_af / 2 * SCALE - 1, 0),
    elbow=(BEV_X - 15, SV_Y - dd_af / 2 * SCALE - 10, 0),
    label=f"ø{dd_shaft_d:.1f}  {dd_af:.1f} AF (DD BORE)",
    draft=draft,
)
annotate(ldr_dd, "ldr_dd_bore")

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    "STRING POST", "DWG-002",
    scale="2:1",
    material="CZ121 BRASS",
    general_tolerance="ISO 2768-f",
    designed_by="GIB TUNERS",
    date="2026-06-03",
    width=150.0,
    draft=draft,
).locate(Location((126, 11, 0)))
annotate(tb, "title_block")

# ── Lint gate ─────────────────────────────────────────────────────────────────
all_anns = (list(dims_below)
            + [ldr_cap_d, ldr_post_d, ldr_bearing_d, ldr_hole, ldr_tap, ldr_dd, tb])
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
for shape in [sv, bev, tev]:
    svg_exp.add_shape(shape, layer="part")
for shape in [s for s in [sv_h, bev_h, tev_h] if s]:
    svg_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    svg_exp.add_shape(ann, layer="dims")
svg_path = output_dir / "string_post.svg"
svg_exp.write(str(svg_path))
print(f"SVG: {svg_path}")

# ── Export DXF ─────────────────────────────────────────────────────────────────
dxf_exp = ExportDXF()
dxf_exp.add_layer("part",   line_weight=0.5)
dxf_exp.add_layer("hidden", line_weight=0.25, line_type=LineType.HIDDEN)
dxf_exp.add_layer("dims",   line_weight=0.05)
for shape in [sv, bev, tev]:
    dxf_exp.add_shape(shape, layer="part")
for shape in [s for s in [sv_h, bev_h, tev_h] if s]:
    dxf_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    dxf_exp.add_shape(ann, layer="dims")
dxf_path = output_dir / "string_post.dxf"
dxf_exp.write(str(dxf_path))
print(f"DXF: {dxf_path}")
