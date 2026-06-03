"""Engineering drawing: Peg head.

A4 landscape, scale 2:1.
Four views: side profile (axis horizontal), ring-end view, shaft-end view, isometric.

The peg head exits create_peg_head() with its axis along X:
  -X = bearing/shaft end (inside frame)
  +X = ring/pip end (outside frame, user-facing)
  Shoulder datum at X=0 (frame worm-entry face)

Third-angle projection:
  Side view (main) - looking from +Y, shows full XZ profile
  Ring-end view (left) - looking from +X, shows ring OD and bore

Coordinate convention (view_axes verified):
  Side (camera +Y, up +Z): world_X → page_X (-1), world_Z → page_Y (+1)
  Ring end (camera +X, up +Z): world_Y → page_X (+1), world_Z → page_Y (+1)

Run:
    uv run python scripts/drawings/peg_head.py
Outputs:
    drawings/peg_head.svg
    drawings/peg_head.dxf
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
from gib_tuners.components.peg_head import create_peg_head
from gib_tuners.components.peg_head_procedural import DEFAULT_GEOMETRY

# ── Build geometry ─────────────────────────────────────────────────────────────
gear_paths = resolve_gear_config("c13-10")
config = create_default_config(
    gear_json_path=gear_paths.json_path,
    config_dir=gear_paths.config_dir,
)
peg_head = create_peg_head(
    config,
    worm_step_path=gear_paths.worm_step,
)

ph_params = config.peg_head
worm_params = config.gear.worm
geom = DEFAULT_GEOMETRY       # procedural geometry constants

# Key dimensions
shaft_d       = ph_params.shaft_diameter        # 4.0mm
shoulder_d    = ph_params.shoulder_diameter     # 7.0mm
cap_d_ph      = ph_params.cap_diameter          # 8.5mm
ring_od       = ph_params.ring_od               # 12.5mm
ring_bore     = ph_params.ring_bore             # 9.8mm
worm_length   = worm_params.length              # 7.7mm (from JSON)
shaft_length  = geom.shaft_length               # 10.4mm (worm + bearing)
bearing_len   = shaft_length - worm_length       # 2.7mm
tap_depth     = 4.0                             # M2 tap depth from shaft end
tap_d_ph      = 1.6                             # M2 tap drill

# Part X extents (shoulder datum at X=0):
# +X direction: ring/pip  –X direction: worm + bearing shaft
x_shaft_end   = -shaft_length                   # -10.4
x_shoulder    = 0.0
x_ring_center = geom.ring_center_depth          # +11.45
x_pip_end     = geom.ring_center_depth + geom.sphere_r + geom.pip_height  # ≈ 18.85

# ── Scale 2:1 ─────────────────────────────────────────────────────────────────
SCALE = 2.0
peg_2x = peg_head.scale(SCALE)

# Centre of 2x part for look_at
x_center = (x_shaft_end + x_pip_end) / 2       # ≈ +4.23
look_at_2x = (x_center * SCALE, 0.0, 0.0)      # ≈ (8.46, 0, 0)

# ── Project views ──────────────────────────────────────────────────────────────
# Side view — camera from +Y, axis along X becomes horizontal on page
sv_vis, sv_hid = peg_2x.project_to_viewport((0, 200, 0), (0, 0, 1), look_at_2x)

# Ring-end view — camera from +X (looking at ring face)
rev_vis, rev_hid = peg_2x.project_to_viewport((200, 0, 0), (0, 0, 1), look_at_2x)

# Shaft-end view — camera from -X (looking at bearing/worm shaft end)
sev_vis, sev_hid = peg_2x.project_to_viewport((-200, 0, 0), (0, 0, 1), look_at_2x)

# Isometric pictorial (1:1) — looking from diagonal
iso_vis, iso_hid = peg_head.project_to_viewport(
    (100, 100, 100), (0, 0, 1), (x_center, 0, 0)
)

# ── Sheet layout ───────────────────────────────────────────────────────────────
# Side view at (152, 128); ring-end view to the left at (92, 128)
SV_X, SV_Y = 152.0, 110.0
REV_X, REV_Y = 90.0, 110.0

# Shaft-end view to the right of side view; isometric far right
SEV_X, SEV_Y = 215.0, 110.0    # shaft-end: right of side view
ISO_X, ISO_Y = 263.0, 125.0    # isometric: far right

sv  = Compound(children=list(sv_vis )).locate(Location((SV_X,  SV_Y,  0)))
rev = Compound(children=list(rev_vis)).locate(Location((REV_X, REV_Y, 0)))
sev = Compound(children=list(sev_vis)).locate(Location((SEV_X, SEV_Y, 0)))
iso = Compound(children=list(iso_vis)).locate(Location((ISO_X, ISO_Y, 0)))
sv_h  = (Compound(children=list(sv_hid )).locate(Location((SV_X,  SV_Y,  0))) if sv_hid  else None)
rev_h = (Compound(children=list(rev_hid)).locate(Location((REV_X, REV_Y, 0))) if rev_hid else None)
sev_h = (Compound(children=list(sev_hid)).locate(Location((SEV_X, SEV_Y, 0))) if sev_hid else None)
iso_h = (Compound(children=list(iso_hid)).locate(Location((ISO_X, ISO_Y, 0))) if iso_hid else None)

# ── Draft settings ─────────────────────────────────────────────────────────────
draft = draft_preset(font_size=2.5, decimal_precision=1)

# ── Coordinate helpers (original 1:1 world coords) ────────────────────────────
# Side view: world_X → page_X (-1), world_Z → page_Y (+1)
# SVX(x) = SV_X - (x - x_center) * SCALE  = SV_X - x*SCALE + x_center*SCALE
# SVZ(z) = SV_Y + z * SCALE
x_offset = x_center * SCALE   # 8.46

def SVX(x): return SV_X - x * SCALE + x_offset
def SVZ(z): return SV_Y + z * SCALE

# Key X positions on the page
x_sh_end = SVX(x_shaft_end)       # shaft end (rightmost on page)
x_sh_0   = SVX(x_shoulder)        # shoulder datum
x_worm_b = SVX(-worm_length)      # worm/bearing boundary
x_tap_in = SVX(x_shaft_end + tap_depth)   # inner end of tap bore
x_pip_e  = SVX(x_pip_end)         # pip end (leftmost on page)
x_ring_c = SVX(x_ring_center)     # ring centre

SIDE_YBOT = SVZ(-ring_od / 2) - 3   # 3mm below widest ring

# ── Stacked dims below shaft section (right side) ─────────────────────────────
dims_shaft = place_dims([
    ((x_sh_0, SIDE_YBOT, 0), (x_sh_end, SIDE_YBOT, 0), "below", f"{shaft_length:.1f}"),
    ((x_sh_0, SIDE_YBOT, 0), (x_worm_b, SIDE_YBOT, 0), "below", f"{worm_length:.1f}"),
    ((x_worm_b, SIDE_YBOT, 0), (x_sh_end, SIDE_YBOT, 0), "below", f"{bearing_len:.1f}"),
], draft)
for i, d in enumerate(dims_shaft):
    annotate(d, f"dim_shaft_{i}")

# Tap depth dimension (below, nested)
d_tap = Dimension(
    (x_sh_end, SIDE_YBOT, 0),
    (x_tap_in, SIDE_YBOT, 0),
    "below", 20, draft, label=f"{tap_depth:.1f}",
)
annotate(d_tap, "dim_tap_depth")

# ── Diameter leaders on side view ─────────────────────────────────────────────
elbow_right_x = x_sh_end + 10

ldr_shaft_d = Leader(
    # Point to smooth bearing section (x between -worm_length and -shaft_length)
    tip=(SVX(-worm_length - bearing_len * 0.5), SVZ(shaft_d / 2), 0),
    elbow=(elbow_right_x, SV_Y + 10, 0),
    label=f"ø{shaft_d:.1f} BEARING",
    draft=draft,
)
annotate(ldr_shaft_d, "ldr_shaft_d")

ldr_shoulder_d = Leader(
    tip=(x_sh_0 - 1, SVZ(shoulder_d / 2), 0),
    elbow=(elbow_right_x, SV_Y + 3, 0),
    label=f"ø{shoulder_d:.1f} SHOULDER",
    draft=draft,
)
annotate(ldr_shoulder_d, "ldr_shoulder_d")

ldr_cap_d_ph = Leader(
    tip=(x_sh_0 + 2, SVZ(cap_d_ph / 2), 0),
    elbow=(elbow_right_x, SV_Y - 4, 0),
    label=f"ø{cap_d_ph:.1f} CAP",
    draft=draft,
)
annotate(ldr_cap_d_ph, "ldr_cap_d")

# ── Leaders on ring-end view (looking from +X) ────────────────────────────────
# Ring-end: world_Y → page_X (+1), world_Z → page_Y (+1)
# sheet_x = REV_X + world_Y * SCALE
# sheet_y = REV_Y + world_Z * SCALE
ldr_ring_od = Leader(
    tip=(REV_X, REV_Y + ring_od / 2 * SCALE, 0),
    elbow=(REV_X - 14, REV_Y + ring_od / 2 * SCALE + 6, 0),
    label=f"ø{ring_od:.1f} OD",
    draft=draft,
)
annotate(ldr_ring_od, "ldr_ring_od")

ldr_ring_bore = Leader(
    tip=(REV_X, REV_Y + ring_bore / 2 * SCALE, 0),
    elbow=(REV_X - 14, REV_Y + ring_bore / 2 * SCALE + 2, 0),
    label=f"ø{ring_bore:.1f} BORE",
    draft=draft,
)
annotate(ldr_ring_bore, "ldr_ring_bore")

# ── Title block ───────────────────────────────────────────────────────────────
tb = TitleBlock(
    "PEG HEAD", "DWG-003",
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
all_anns = (list(dims_shaft)
            + [d_tap, ldr_shaft_d, ldr_shoulder_d, ldr_cap_d_ph,
               ldr_ring_od, ldr_ring_bore, tb])
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
for shape in [sv, rev, sev, iso]:
    svg_exp.add_shape(shape, layer="part")
for shape in [s for s in [sv_h, rev_h, sev_h, iso_h] if s]:
    svg_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    svg_exp.add_shape(ann, layer="dims")
svg_path = output_dir / "peg_head.svg"
svg_exp.write(str(svg_path))
print(f"SVG: {svg_path}")

# ── Export DXF ─────────────────────────────────────────────────────────────────
dxf_exp = ExportDXF()
dxf_exp.add_layer("part",   line_weight=0.5)
dxf_exp.add_layer("hidden", line_weight=0.25, line_type=LineType.HIDDEN)
dxf_exp.add_layer("dims",   line_weight=0.05)
for shape in [sv, rev, sev, iso]:
    dxf_exp.add_shape(shape, layer="part")
for shape in [s for s in [sv_h, rev_h, sev_h, iso_h] if s]:
    dxf_exp.add_shape(shape, layer="hidden")
for ann in all_anns:
    dxf_exp.add_shape(ann, layer="dims")
dxf_path = output_dir / "peg_head.dxf"
dxf_exp.write(str(dxf_path))
print(f"DXF: {dxf_path}")
