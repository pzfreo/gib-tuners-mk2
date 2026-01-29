# gib-tuners

Parametric CAD project for historic guitar tuner restoration using build123d.

## Overview

This project generates 5-gang tuning machine assemblies (right-hand and left-hand variants) based on the engineering specification in `spec.md`. The design uses a "sandwich" assembly approach where all components can be inserted and retained without soldering.

## Installation

```bash
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Usage

### Build assemblies

```bash
# Production scale (1:1), both hands
python scripts/build_all.py --scale 1.0 --hand both

# 2x prototype for FDM printing
python scripts/build_all.py --scale 2.0 --tolerance prototype_fdm

# Just right-hand at production tolerance
python scripts/build_all.py --hand right

# Validate geometry without building
python scripts/build_all.py --validate-only
```

### Build frame only

```bash
python scripts/build_frame.py
python scripts/build_frame.py --scale 2.0 --hand left
```

### Visualize (requires OCP viewer)

```bash
python scripts/visualize.py
python scripts/visualize.py --component frame
python scripts/visualize.py --component tuner --scale 2.0
```

## Project Structure

```
gib-tuners-mk2/
├── src/gib_tuners/
│   ├── config/          # Dataclasses and parameters
│   ├── components/      # Individual parts (frame, peg_head, etc.)
│   ├── assembly/        # Assemblies (tuner unit, gang assembly)
│   ├── features/        # Reusable CAD operations
│   ├── export/          # STEP/STL export
│   └── utils/           # Mirroring, validation
├── scripts/             # CLI tools
├── tests/               # Test suite
├── reference/           # Reference STEP/DXF files
└── output/              # Generated files (gitignored)
```

## Key Files

- `spec.md` - Master engineering specification
- `7mm-globoid.json` - Gear calculator parameters
- `ARCHITECTURE.md` - Design documentation
- `CLAUDE.md` - Claude Code guidance

## Testing

```bash
pytest tests/
pytest tests/test_validation.py  # Spec Section 9 checks
```

## License

Proprietary - All rights reserved.
