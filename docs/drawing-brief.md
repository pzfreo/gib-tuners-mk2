# Technical Drawing Session Brief

## What This Is

A session brief for producing fabrication-ready engineering drawings for the **gib-tuners-mk2** parametric CAD project. Use this to resume work after a context reset.

---

## Project: gib-tuners-mk2

Parametric build123d project for historic guitar tuner restoration. Generates 5-gang tuning machine assemblies (RH and LH variants).

**Production gear profile:** `c13-10` — cylindrical worm, M0.5 module, 13-tooth wheel, 20° PA.

**Production build command:**
```bash
python scripts/build.py --hand both --gear c13-10 -n 5 --label-frames no
```

**Key source files:**
- `src/gib_tuners/config/parameters.py` — all component dataclasses
- `src/gib_tuners/config/defaults.py` — `create_default_config()`, `resolve_gear_config()`
- `src/gib_tuners/components/frame.py` — `create_frame(config, label=False)`
- `src/gib_tuners/components/string_post.py` — `create_string_post(config)`
- `src/gib_tuners/components/wheel.py` — `load_wheel(step_path)`
- `src/gib_tuners/components/peg_head.py` — `create_peg_head(config, include_worm=False)`
- `config/c13-10/worm_gear.json` — gear parameters (source of truth for gear dims)

---

## Drawing Goal

One A4 engineering drawing per component, plus one general arrangement (GA). Outputs: SVG (review) and DXF (fabrication).

**Sheets planned:**
| Sheet | Component | DWG# |
|-------|-----------|------|
| DWG-001 | Frame — 5-gang RH | scripts/drawings/frame.py |
| GIB-TUN-SP | String Post — A3 10:1 | scripts/string_post_drawing.py |
| GIB-TUN-WW-RH | Worm Wheel — A3 10:1 | scripts/wheel_drawing.py |
| GIB-TUN-PH-RH | Peg Head (RH) — A3 5:1 | scripts/peg_head_drawing.py |
| DWG-005 | General Arrangement (1-gang) | scripts/drawings/assembly_ga.py |
| PDF | All sheets combined | scripts/drawings/make_pdf.py |

**Output directory:** `drawings/`

---

## Drawing Conventions

- A4 landscape (297 × 210 mm), margin 10 mm
- ISO, **third-angle projection** (top above front, right-side to the right)
- Metric, ISO 2768-m general tolerance in title block
- Scale: appropriate per component (frame 1:1, small parts 3:1 or 5:1)
- Black part geometry, blue annotations (two SVG layers)

**View layout (third-angle):**
```
      [TOP VIEW]      [ISO]
[FRONT VIEW] [END VIEW]
```

---

## Architecture: Build from Source, Not STEP Files

**CRITICAL DECISION:** Drawings must be generated from live build123d geometry (`create_frame(cfg)`, `create_string_post(cfg)`, etc.), NOT from exported STEP files. This ensures dimensions stay in sync when parameters change.

Each drawing script follows this pattern:
```python
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand
from gib_tuners.components.frame import create_frame

gear_paths = resolve_gear_config("c13-10")
cfg = create_default_config(
    gear_json_path=gear_paths.json_path,
    config_dir=gear_paths.config_dir,
    hand=Hand.RIGHT,
)
part = create_frame(cfg, label=False)
# All dimension values come from cfg, never hard-coded
```

Run scripts with `uv run python scripts/drawings/frame.py`.

---

## MCP Server Setup

The `build123d-mcp` server is configured in `.mcp.json` (project root):

```json
{
  "mcpServers": {
    "build123d-mcp": {
      "command": "uv",
      "args": [
        "tool", "run", "--upgrade", "--python", "3.12",
        "build123d-mcp",
        "--allow-imports", "gib_tuners,dacite"
      ],
      "env": {
        "PYTHONPATH": "/app/workspaces/pzfreo/gib-tuners-mk2/src"
      }
    }
  }
}
```

**After restarting Claude Code**, verify with:
```python
# In MCP execute():
from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand
from gib_tuners.components.frame import create_frame
gear_paths = resolve_gear_config("c13-10")
cfg = create_default_config(gear_json_path=gear_paths.json_path, config_dir=gear_paths.config_dir)
part = create_frame(cfg, label=False)
show(part, "frame")
print("gib_tuners import OK")
```

---

## Coordinate Systems (DO NOT GUESS — CHECK WITH view_axes())

Always call `view_axes()` before `project_to_viewport()`. Confirmed mappings for each component:

### Frame (bbox: X=10, Y=145, Z=10)
- Z=0: mounting plate (top), Z=-10: bottom
- Y=0: one end, Y=145: other end
- **Front** (from -X, up=Z): `world_Y → page_X ×-1`, `world_Z → page_Y ×+1`
- **Top/plan** (from +Z, up=+X): `world_Y → page_X ×-1`, `world_X → page_Y ×+1`
- **End** (from +Y, up=Z): `world_X → page_X ×-1`, `world_Z → page_Y ×+1`

### String Post (bbox: X=7.5, Y=7.5, Z=14.8)
- Z=0: bottom of DD section, Z=14.8: top of cap
- Shaft axis = Z (vertical in drawing)
- **Front** (from -Y, up=Z): `world_X → page_X ×+1`, `world_Z → page_Y ×+1`

### Peg Head — IMPORTANT: ROTATE FIRST
`create_peg_head()` returns shaft along Z. Apply `part.rotate(Axis.Y, 90)` before projecting.
After rotation: shaft along +X, head at -X.
- **Front** (from -Y, up=Z): `world_X → page_X ×+1`, `world_Z → page_Y ×+1`
- **End** (from -X, up=Z): `world_Y → page_X ×+1`, `world_Z → page_Y ×+1`

---

## Key Dimensions (for reference — always read from cfg)

| Parameter | Value | Source |
|-----------|-------|--------|
| Frame outer | 10.0 mm | `cfg.frame.box_outer` |
| Wall thickness | 1.0 mm | `cfg.frame.wall_thickness` (c13-10, via tuner_config.json) |
| Total length (5-gang) | 145.0 mm | `cfg.frame.total_length` |
| Housing length | 16.2 mm | `cfg.frame.housing_length` |
| End length | 10.0 mm | `cfg.frame.end_length` |
| Tuner pitch | 27.2 mm | `cfg.frame.tuner_pitch` |
| Post bearing hole | 5.05 mm | `cfg.frame.post_bearing_hole` |
| Worm entry hole | ~7.2 mm | `cfg.frame.worm_entry_hole` |
| Peg bearing hole | 4.55 mm | `cfg.frame.peg_bearing_hole` |
| Mounting hole | 3.2 mm | `cfg.frame.mounting_hole` |
| Worm Z (c13-10) | -5.0 mm | `calculate_worm_z(cfg)` (centred) |
| Cap diameter (post) | 7.5 mm | `cfg.string_post.cap_diameter` |
| Post diameter | 6.0 mm | `cfg.string_post.post_diameter` |
| Wheel tip diameter | 7.6 mm | `cfg.gear.wheel.tip_diameter` |
| Wheel bore | 3.5 mm | `cfg.gear.wheel.bore.diameter` |
| Wheel face width | 7.7 mm | `cfg.gear.wheel.face_width` |
| Peg head ring OD | 12.5 mm | `cfg.peg_head.ring_od` |
| Peg head cap OD | 8.5 mm | `cfg.peg_head.cap_diameter` |
| Peg head shoulder | 7.0 mm | `cfg.peg_head.shoulder_diameter` |
| Gear module | M0.5 | `cfg.gear.worm.module` |
| Gear teeth | 13 | `cfg.gear.wheel.num_teeth` |

---

## What Works / What Doesn't (lessons learned)

### ✓ What works
- `view_axes()` — essential, use it before every `project_to_viewport()`
- `render_drawing(svg_path, save_to='/tmp/foo.png')` — fast preview
- `Dimension(p1, p2, side, distance, draft, label)` — clean when part is large enough
- `place_dims(specs, draft)` — auto-tiers stacked dims
- `Leader(tip, elbow, label, draft)` — keep to ≤3 per sheet
- `TechnicalDrawing()` — good title block but watch subtitle length (overflows silently)
- `lint_drawing(items)` — catches label-vs-measured errors and leader-through-text

### ✗ Known problems / workarounds

**Scale:** No native scale support. If you scale geometry with `part.scale(N)` before projecting, every Dimension fails lint's label-vs-measured check. **Workaround:** Accept lint warnings for scaled drawings, or wait for issue #147 fix.

**`set_page()` / `annotate()` not in package:** These are MCP session builtins only. Standalone scripts can't use page-bounds checking. **Workaround:** Visual check via `render_drawing()`. Issue #148 filed.

**lint_drawing() false positives for stacked dims:** Checks full bounding boxes including witness lines — flags valid stacked dimensions as overlapping. **Workaround:** Ignore `annotation_overlap` warnings that come from `place_dims()` output; fix real overlaps (leader-through-label, actual label collisions). Issue #149 filed.

**Small parts are tiny at 1:1:** String post (7.5 mm), wheel (7.6 mm) are unreadably small on A4. Need scale. Issue #147 covers this.

**`gib_tuners` not on MCP allowlist by default:** Now fixed in `.mcp.json` — but requires Claude Code restart to take effect.

---

## Issues Filed on build123d-mcp

| # | Title | Status |
|---|-------|--------|
| [#147](https://github.com/pzfreo/build123d-mcp/issues/147) | Native drawing scale (N:1) support | Open |
| [#148](https://github.com/pzfreo/build123d-mcp/issues/148) | `set_page()` / `annotate()` as package exports | Open |
| [#149](https://github.com/pzfreo/build123d-mcp/issues/149) | lint false positives from witness-line bboxes | Open |
| [#150](https://github.com/pzfreo/build123d-mcp/issues/150) | Project-local packages via PYTHONPATH + allowlist | Open |
| [#151](https://github.com/pzfreo/build123d-mcp/issues/151) | TechnicalDrawing subtitle overflow not caught by lint | Open |

---

## Current State (branch: technical-diagrams)

- Old drawing attempts removed: `scripts/drawings.py`, `scripts/freecad_drawing.py`, `src/gib_tuners/export/drawing_export.py`
- New scripts in `scripts/drawings/`: `frame.py`, `string_post.py`, `wheel.py`, `peg_head.py`
- `build123d-drafting-helpers>=0.2.0` added to `pyproject.toml` dependencies
- SVG outputs in `drawings/` (rough first pass, needs isometrics + scale + lint cleanup)
- `assembly_ga.py` and `make_pdf.py` not yet written

---

## Next Steps (in order)

1. **Restart Claude Code** so the MCP server picks up the new `.mcp.json` (gib_tuners allowlist)
2. **Verify** `gib_tuners` is importable in MCP `execute()` (test snippet above)
3. **Add isometric view** to every sheet — camera at approx `(1, -1, 0.5)` normalised, `up=(0, 0, 1)`, placed top-right of the sheet
4. **Handle scale** — decide approach once issue #147 is addressed, or use `part.scale(N)` and accept lint warnings with a `[N:1]` note in the title
5. **Write `assembly_ga.py`** — 1-gang GA showing all four components in position, centre distance annotated
6. **Write `make_pdf.py`** — assemble all SVGs into a single PDF using `pypdf` or `reportlab`
7. **Commit** everything on `technical-diagrams` branch, open PR

---

## Preferred Workflow (once gib_tuners is importable in MCP)

```
execute() in MCP session:
  → import gib_tuners component
  → build geometry
  → scale if needed (part.scale(N))
  → project_to_viewport() for each view
  → Dimension / Leader annotations
  → set_page() + annotate() (session builtins)
  → lint_drawing() — full check including page bounds
  → export() SVG + DXF

Then: render_drawing(svg_path, save_to='/tmp/preview.png') to eyeball
Then: transcribe to standalone script in scripts/drawings/
```
