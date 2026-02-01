# Claude Code Guidance

## Project Overview

Parametric CAD project for historic guitar tuner restoration using build123d. This generates 5-gang tuning machine assemblies (right-hand and left-hand variants) based on the engineering specification.

## Key Files

- `spec.md` - Master engineering specification (source of truth for all dimensions)
- `config/worm_gear.json` - Gear calculator parameters for worm/wheel (13T, 7.5mm wheel)
- `src/gib_tuners/config/parameters.py` - All dataclasses defining component geometry
- `src/gib_tuners/config/tolerances.py` - Tolerance profiles for different manufacturing methods

## Architecture

```
config/          - Dataclasses and parameters (no CAD operations)
components/      - Individual part geometry (frame, peg_head, string_post, wheel)
features/        - Reusable CAD operations (DD cuts, drilling patterns)
assembly/        - Combines components into assemblies
export/          - STEP/STL export utilities
utils/           - Mirroring for LH/RH, validation
```

## Conventions

- All dimensions in mm
- Frozen dataclasses for immutable parameters
- Type hints throughout
- Scale factor applied via `BuildConfig`
- RIGHT hand is the default; LEFT is a mirror

## Code Reuse (CRITICAL)

**Always start from existing working code. Never reinvent what already exists.**

Before writing new code:
1. **Check existing modules first** - Look in `assembly/`, `components/`, `utils/` for functions that do what you need
2. **Reuse assembly functions** - Use `create_positioned_assembly()` from `gang_assembly.py` instead of duplicating positioning logic
3. **Follow existing patterns** - New scripts should follow the same structure as `viz.py` and `build.py`

Key reusable functions:
- `create_positioned_assembly()` - Creates complete assembly with all parts positioned
- `create_tuner_unit()` - Single tuner components at origin
- `create_default_config()` - Config with all parameters from JSON
- `mirror_for_left_hand()` - Creates LH variant from RH geometry

**If you find yourself copying positioning math or component creation logic, STOP and use the existing assembly module instead.**

## Coordinate System

The frame uses a player's-view orientation:
- **Z=0**: Mounting plate surface (visible from above, sits on headstock)
- **Z=-box_outer**: Bottom of frame (embedded in headstock cavity)
- **+Z direction**: Where posts emerge (upward into the air)
- **RH tuner**: Worm entry on RIGHT (+X), peg bearing on LEFT (-X)
- **LH tuner**: Mirror image of RH

## Workflow Requirements

### Keeping Spec and Code in Sync (CRITICAL)

The spec and code must stay synchronized. When changing dimensions:

1. **Code is the source of truth** for what gets built
2. **spec.md documents** what the code produces
3. **Both must match** - if they diverge, update spec.md to match code

**Files that define dimensions:**
- `src/gib_tuners/config/parameters.py` - Python dataclass defaults
- `config/worm_gear.json` - Gear calculator parameters
- `spec.md` - Human-readable specification (Sections 1a, 2, 3, 5, 8)

**When changing a parameter:**
1. Update code (`parameters.py` or `worm_gear.json`)
2. Update `spec.md` sections that reference that parameter
3. Update `CLAUDE.md` Key Dimensions table if affected
4. Verify Section 8 derived dimensions still compute correctly
5. Check Section 9 validation checklist clearances

**Key cross-references in spec.md:**
| Parameter | Sections |
|-----------|----------|
| `box_outer`, `wall_thickness` | 1a, 2, 8 |
| `wheel.face_width` | 3, 5 (DD cut length must match) |
| `worm_type` | 3, 9 |
| Z coordinates | 2, 8 (must use same convention) |

**Symmetric frame ends:** The frame must have symmetric ends (10mm each). The `total_length` is computed from `num_housings`, ensuring symmetric ends regardless of the number of tuning stations:
```
total_length = 2 * end_length + housing_length + (num_housings - 1) * pitch
first_center = end_length + housing_length / 2 = 10 + 8.1 = 18.1mm
```

**Parameterized frame:** The frame supports 1 to N tuning stations via `num_housings`. All derived values (total_length, housing_centers, mounting_hole_positions) are computed automatically.

## Building

```bash
# Production scale (1:1)
python scripts/build.py --scale 1.0 --hand both

# 2x prototype for FDM printing
python scripts/build.py --scale 2.0 --tolerance prototype_fdm

# Single hand variant, STL only
python scripts/build.py --hand right --format stl

# Visualize in OCP viewer
python scripts/viz.py -n 1              # 1-gang
python scripts/viz.py                   # 5-gang (default)

# Animate worm gear mechanism
python scripts/animate.py --worm-revs 1
```

## Testing

```bash
# Run all tests
pytest tests/

# Run spec validation checks (Section 9)
pytest tests/test_validation.py

# Run with coverage
pytest --cov=src/gib_tuners tests/
```

## Reference Files

The `reference/` directory contains:
- `worm_m0.5_z1.step` - Cylindrical worm reference geometry
- `wheel_m0.5_z13.step` - 13-tooth worm wheel (7.5mm OD)
- `rhframe.step` - Reference right-hand frame geometry
- `peg.dxf`, `pegsmall.dxf` - Peg head profile references

## Incremental Assembly Workflow

**This is a complex CAD project. Work incrementally with user approval at each step.**

1. **One component at a time**: Create/fix each component in isolation. Do not move to the next until the user approves the current one.

2. **Visualize and verify**: After each change, run the debug script to visualize. Wait for user confirmation that it looks correct.

3. **Single housing first**: Work with `num_housings=1` until the single-unit assembly is approved. Only then expand to the full 5-gang.

4. **Separate debug files**: Use `scripts/experiments/debug_assembly.py` for incremental testing. Do not modify `assembly/tuner_unit.py` or `assembly/gang_assembly.py` until the positioning is verified and approved.

5. **Approval checkpoints**:
   - [ ] Frame (APPROVED)
   - [ ] String post at origin
   - [ ] Wheel mated to post (DD alignment)
   - [ ] Post+wheel positioned in single-housing frame
   - [ ] Peg head added to single-housing assembly
   - [ ] Hardware (washers, M2 nut, screw)
   - [ ] Full 5-gang assembly

6. **Do not batch changes**: Even if you think you know the fix, implement one step, show results, wait for approval.

## Key Dimensions (from spec.md)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Frame outer | 10.0mm | Square tube dimension |
| Wall thickness | 1.1mm | Tube wall (**FIXED** - manufacturing constraint) |
| Housing length | 16.2mm | Each rigid box section |
| End length | 10.0mm | Frame end to housing edge |
| Num housings | 5 (default) | Tuning stations (1 to N) |
| Tuner pitch | 27.2mm | Center-to-center spacing |
| Total length | *computed* | 145.0mm for 5 housings |
| Center distance | 5.75mm | Worm-to-wheel axis distance |
| Gear module | 0.5 | M0.5 worm drive (cylindrical or globoid) |

## Manufacturing Constraints

**Wall thickness is fixed at 1.1mm** - this is determined by the brass box section stock used in manufacturing. Never change this value.

To create axial play for rotating assemblies, we extend the shafts:
- String post bearing section = `wall_thickness + post_bearing_axial_play` (1.3mm)
- Peg head bearing section = `wall_thickness + peg_bearing_axial_play` (1.3mm)

This allows the frame to "float" between the clamping surfaces, enabling free rotation.
