"""Engineering drawing: Worm wheel (DWG-005).

A4 landscape, scale 2:1.
Four views: face (camera -Z), side elevation (camera +Y), bore end (camera +Z),
and isometric.

Coordinate convention (view_axes verified):
  Face (-Z cam, up +Y): world_X → page_X (-1), world_Y → page_Y (+1)
  Side (+Y cam, up +Z): world_X → page_X (-1), world_Z → page_Y (+1)
  Bore end (+Z cam, up +Y): world_X → page_X (+1), world_Y → page_Y (+1)

Run:
    uv run python scripts/drawings/worm_wheel.py
Outputs:
    drawings/worm_wheel.svg
    drawings/worm_wheel.dxf
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from build123d import Color, Compound, ExportDXF, ExportSVG, LineType, Location, import_step
from build123d_drafting import (
    Dimension, Leader, TitleBlock,
    annotate, draft_preset, lint_drawing, set_page,
)

from gib_tuners.config.defaults import resolve_gear_config

gear_paths = resolve_gear_config("c13-10")

# Load wheel geometry from STEP file
wheel = import_step(str(gear_paths.wheel_step))

# Load gear parameters from JSON
with open(gear_paths.json_path) as f:
    gear_json = json.load(f)

tip_d     = gear_json["wheel"]["tip_diameter_mm"]                  # 7.6mm
pitch_d   = gear_json["wheel"]["pitch_diameter_mm"]                # 6.5mm
root_d    = gear_json["wheel"]["root_diameter_mm"]                 # 5.55mm
face_w    = gear_json["manufacturing"]["wheel_width_mm"]           # 7.7mm
bore_d    = gear_json["features"]["wheel"]["bore_diameter_mm"]     # 3.5mm
num_teeth = gear_json["wheel"]["num_teeth"]                        # 13
module    = gear_json["wheel"]["module_mm"]                        # 0.5
pa_deg    = gear_json["assembly"]["pressure_angle_deg"]            # 20

# DD bore: across flats 2.5mm, flat depth 0.5mm
dd_af    = 2.5
dd_depth = 0.5

tip_r  = tip_d / 2    # 3.8mm
face_h = face_w / 2   # 3.85mm

# ── Scale and project ──────────────────────────────────────────────────────────
SCALE = 2.0
wheel_2x = wheel.scale(SCALE)

# Face view: camera from -Z, looking +Z, up=Y
fv_vis, fv_hid = wheel_2x.project_to_viewport((0, 0, -200), (0, 1, 0))

# Side elevation: camera from +Y, looking -Y, up=Z
sv_vis, sv_hid = wheel_2x.project_to_viewport((0, 200, 0), (0, 0, 1))

# Bore end: camera from +Z, looking -Z, up=Y
bev_vis, bev_hid = wheel_2x.project_to_viewport((0, 0, 200), (0, 1, 0))

# Isometric pictorial (1:1, no scale)
iso_vis, iso_hid = wheel.project_to_viewport((80, 80, 80), (0, 0, 1))

# ── Sheet layout ───────────────────────────────────────────────────────────────
# Face view centre-left; side to its right; bore end below face; iso top-right
FV_X, FV_Y   = 75.0,  110.0
SEV_X, SEV_Y = 140.0, 110.0
BEV_X, BEV_Y = 75.0,   60.0
ISO_X, ISO_Y = 220.0,  100.0

fv  = Compound(children=list(fv_vis )).locate(Location((FV_X,  FV_Y,  0)))
sv  = Compound(children=list(sv_vis )).locate(Location((SEV_X, SEV_Y, 0)))
bev = Compound(children=list(bev_vis)).locate(Location((BEV_X, BEV_Y, 0)))
iso = Compound(children=list(iso_vis)).locate(Location((ISO_X, ISO_Y, 0)))
fv_h  = (Compound(children=list(fv_hid )).locate(Location((FV_X,  FV_Y,  0))) if fv_hid  else None)
sv_h  = (Compound(children=list(sv_hid )).locate(Location((SEV_X, SEV_Y, 0))) if sv_hid  else None)
bev_h = (Compound(children=list(bev_hid)).locate(Location((BEV_X, BEV_Y, 0))) if bev_hid else None)
iso_h = (Compound(children=list(iso_hid)).locate(Location((ISO_X, ISO_Y, 0))) if iso_hid else None)

draft = draft_preset(font_size=2.5, decimal_precision=1)

# ── Coordinate helpers ────────────────────────────────────────────────────────
# Face (-Z cam): world_X → page_X (-1), world_Y → page_Y (+1)
def FX(x): return FV_X - x * SCALE
def FY(y): return FV_Y + y * SCALE

# Side (+Y cam): world_X → page_X (-1), world_Z → page_Y (+1)
def SX(x): return SEV_X - x * SCALE
def SZ(z): return SEV_Y + z * SCALE

# Bore end (+Z cam): world_X → page_X (+1), world_Y → page_Y (+1)
def BX(x): return BEV_X + x * SCALE
def BY(y): return BEV_Y + y * SCALE

# ── Side view dimensions ───────────────────────────────────────────────────────
# Face width (vertical extent in side view: world_Z maps to page_Y)
d_face_w = Dimension(
    (SX(-tip_r) + 3, SZ(-face_h), 0),
    (SX(-tip_r) + 3, SZ( face_h), 0),
    "right", 4, draft, label=f"{face_w:.1f}",
)
annotate(d_face_w, "dim_face_w")

# OD in side view (horizontal extent: world_X maps to page_X mirrored)
d_od_sv = Dimension(
    (SX(-tip_r), SZ(-face_h) - 3, 0),
    (SX( tip_r), SZ(-face_h) - 3, 0),
    "below", 4, draft, label=f"ø{tip_d:.1f}",
)
annotate(d_od_sv, "dim_od_sv")

# ── Face view leaders ──────────────────────────────────────────────────────────
# Tip OD
ldr_tip = Leader(
    tip=(FX(0), FY(tip_r), 0),
    elbow=(FX(0) + 15, FY(tip_r) + 8, 0),
    label=f"ø{tip_d:.1f} TIP OD",
    draft=draft,
)
annotate(ldr_tip, "ldr_tip")

# Bore: point to inner bore circle edge
ldr_bore = Leader(
    tip=(FX(0), FY(bore_d / 2), 0),
    elbow=(FX(0) + 14, FY(bore_d / 2) + 10, 0),
    label=f"ø{bore_d:.1f} BORE",
    draft=draft,
)
annotate(ldr_bore, "ldr_bore")

# Gear data note: point to a tooth on the face
ldr_data = Leader(
    tip=(FX(-tip_r * 0.6), FY(tip_r * 0.6), 0),
    elbow=(FX(-tip_r * 0.6) - 8, FY(tip_r * 0.6) + 12, 0),
    label=f"Z={num_teeth}  MOD {module:.1f}  PA {pa_deg:.0f}°",
    draft=draft,
)
annotate(ldr_data, "ldr_gear_data")

# ── Bore end view leader ───────────────────────────────────────────────────────
# DD across-flats annotation
ldr_dd = Leader(
    tip=(BX(dd_af / 2), BY(0), 0),
    elbow=(BX(dd_af / 2) + 12, BY(0) + 10, 0),
    label=f"{dd_af:.1f} AF  DD BORE",
    draft=draft,
)
annotate(ldr_dd, "ldr_dd")

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    "WORM WHEEL", "DWG-005",
    scale="2:1",
    material="CAST BRASS",
    general_tolerance="ISO 2768-m",
    designed_by="GIB TUNERS",
    date="2026-06-03",
    width=150.0,
    draft=draft,
).locate(Location((126, 11, 0)))
annotate(tb, "title_block")

# ── Lint gate ─────────────────────────────────────────────────────────────────
all_anns = [d_face_w, d_od_sv, ldr_tip, ldr_bore, ldr_data, ldr_dd, tb]
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
for shape in [fv, sv, bev, iso]:
    svg_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, sv_h, bev_h, iso_h] if s]:
    svg_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    svg_exp.add_shape(ann, layer="dims")
svg_path = output_dir / "worm_wheel.svg"
svg_exp.write(str(svg_path))
print(f"SVG: {svg_path}")

# ── Export DXF ─────────────────────────────────────────────────────────────────
dxf_exp = ExportDXF()
dxf_exp.add_layer("part",   line_weight=0.5)
dxf_exp.add_layer("hidden", line_weight=0.25, line_type=LineType.HIDDEN)
dxf_exp.add_layer("dims",   line_weight=0.05)
for shape in [fv, sv, bev, iso]:
    dxf_exp.add_shape(shape, layer="part")
for shape in [s for s in [fv_h, sv_h, bev_h, iso_h] if s]:
    dxf_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    dxf_exp.add_shape(ann, layer="dims")
dxf_path = output_dir / "worm_wheel.dxf"
dxf_exp.write(str(dxf_path))
print(f"DXF: {dxf_path}")
