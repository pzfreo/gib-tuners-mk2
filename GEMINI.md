# Gemini Code Guidance

## Project Overview

Parametric CAD project for historic guitar tuner restoration using build123d. This generates 5-gang tuning machine assemblies (right-hand and left-hand variants) based on the engineering specification.

## Key Files

- `spec.md` - Master engineering specification (source of truth for all dimensions).
- `config/worm_gear.json` - Gear calculator parameters for worm/wheel (13T, 7.5mm wheel).
- `src/gib_tuners/config/parameters.py` - All dataclasses defining component geometry.
- `src/gib_tuners/config/tolerances.py` - Tolerance profiles for different manufacturing methods.

## Architecture

- `config/` - Dataclasses and parameters (pure data, no CAD operations).
- `src/gib_tuners/components/` - Individual part geometry (frame, peg_head, string_post, wheel).
- `src/gib_tuners/features/` - Reusable CAD operations (DD cuts, drilling patterns).
- `src/gib_tuners/assembly/` - Combines components into assemblies.
- `src/gib_tuners/export/` - STEP/STL export utilities.
- `src/gib_tuners/utils/` - Mirroring for LH/RH, validation.

## Conventions

- **Units:** All dimensions are in mm.
- **Immutability:** Use frozen dataclasses for immutable parameters.
- **Typing:** Use type hints throughout the codebase.
- **Scaling:** Scale factor is applied via `BuildConfig`.
- **Handedness:** RIGHT hand is the default; LEFT is a mirror.

## Code Reuse (CRITICAL)

**Always start from existing working code. Never reinvent what already exists.**

Before writing new code:
1. **Check existing modules first:** Look in `assembly/`, `components/`, and `utils/` for functions that might already solve your problem.
2. **Reuse assembly functions:** Use `create_positioned_assembly()` from `gang_assembly.py` instead of duplicating positioning logic.
3. **Follow existing patterns:** New scripts should follow the structure of existing scripts like `viz.py` and `build.py`.

Key reusable functions:
- `create_positioned_assembly()` - Creates a complete assembly with all parts positioned.
- `create_tuner_unit()` - Creates single tuner components at the origin.
- `create_default_config()` - Creates a configuration with all parameters from JSON.
- `mirror_for_left_hand()` - Creates a LH variant from RH geometry.

**If you find yourself copying positioning math or component creation logic, STOP and use the existing assembly module instead.**

## Coordinate System

The frame uses a player's-view orientation:
- **Z=0:** Mounting plate surface (visible from above, sits on headstock).
- **Z=-box_outer:** Bottom of frame (embedded in headstock cavity).
- **+Z direction:** Where posts emerge (upward into the air).
- **RH tuner:** Worm entry on RIGHT (+X), peg bearing on LEFT (-X).
- **LH tuner:** Mirror image of RH.

## Git Workflow

- **Branching:** Every change or feature must be developed in a separate, descriptive branch (e.g., `feature/add-hardware-components` or `fix/frame-alignment`).
- **Pull Requests:** All changes must be submitted via a Pull Request (PR) for review and validation before being merged into the main branch.

## Workflow Requirements

- **Keep spec.md in sync:** When changing geometry parameters in code, always update `spec.md` to match. The spec is the source of truth.
- **Symmetric frame ends:** The frame must have symmetric ends (10mm each). `total_length` is computed from `num_housings`.
- **Parameterized frame:** The frame supports 1 to N tuning stations via `num_housings`. Derived values (`total_length`, `housing_centers`, etc.) are computed automatically.

## Building & Running

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
- `worm_m0.5_z1.step` - Cylindrical worm reference geometry.
- `wheel_m0.5_z13.step` - 13-tooth worm wheel (7.5mm OD).
- `rhframe.step` - Reference right-hand frame geometry.
- `peg.dxf`, `pegsmall.dxf` - Peg head profile references.

## Incremental Assembly Workflow

**This is a complex CAD project. Work incrementally.**

1. **One component at a time:** Create/fix each component in isolation.
2. **Visualize and verify:** After each change, run the debug script to visualize.
3. **Single housing first:** Work with `num_housings=1` until the single-unit assembly is stable.
4. **Separate debug files:** Use `scripts/experiments/debug_assembly.py` for incremental testing.
5. **Approval checkpoints:**
   - [ ] Frame
   - [ ] String post at origin
   - [ ] Wheel mated to post (DD alignment)
   - [ ] Post+wheel positioned in single-housing frame
   - [ ] Peg head added to single-housing assembly
   - [ ] Hardware (washers, M2 nut, screw)
   - [ ] Full 5-gang assembly
