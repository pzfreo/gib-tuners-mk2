# Claude Code Guidance

## Project Overview

Parametric CAD project for historic guitar tuner restoration using build123d. This generates 5-gang tuning machine assemblies (right-hand and left-hand variants) based on the engineering specification.

## Key Files

- `spec.md` - Master engineering specification (source of truth for all dimensions)
- `7mm-globoid.json` - Gear calculator parameters for worm/wheel
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

## Building

```bash
# Production scale (1:1)
python scripts/build_all.py --scale 1.0 --hand both

# 2x prototype for FDM printing
python scripts/build_all.py --scale 2.0 --tolerance prototype_fdm

# Single hand variant
python scripts/build_all.py --hand right

# Visualize in OCP viewer
python scripts/visualize.py
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
- `worm_m0.5_z1.step` - Globoid worm reference geometry
- `wheel_m0.5_z12.step` - 12-tooth worm wheel
- `rhframe.step` - Reference right-hand frame geometry
- `peg.dxf`, `pegsmall.dxf` - Peg head profile references

## Key Dimensions (from spec.md)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Frame outer | 10.35mm | Square tube dimension |
| Wall thickness | 1.1mm | Tube wall |
| Total length | 145.0mm | Frame length |
| Tuner pitch | 27.2mm | Center-to-center spacing |
| Center distance | 5.5mm | Worm-to-wheel axis distance |
| Gear module | 0.5 | M0.5 globoid worm drive |
