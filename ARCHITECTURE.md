# Architecture Documentation

## System Overview

This project generates parametric CAD models for historic 5-gang guitar tuning machines. The design uses a "sandwich" assembly approach where all components can be inserted and retained without soldering.

## Component Hierarchy

```
GangAssembly (5 tuners)
├── Frame (single piece)
│   ├── 5x Rigid Housings (full box profile)
│   ├── 4x Connectors (bottom plate only)
│   └── 6x Mounting Holes
│
└── 5x TunerUnit
    ├── PegHead (cast with integral worm)
    │   ├── Ring head (finger grip)
    │   ├── Shaft (3.8mm bearing surface)
    │   ├── Worm thread (globoid, integral)
    │   └── M2 retention screw + washer
    │
    ├── StringPost (Swiss screw machined)
    │   ├── Decorative cap (7.5mm)
    │   ├── Visible post (6.0mm)
    │   ├── Frame bearing (4.0mm)
    │   ├── DD cut interface (3.0mm)
    │   ├── E-clip groove (2.5mm shaft)
    │   └── String hole (1.5mm cross-drilled)
    │
    └── WormWheel (separate, mates with post)
        ├── 12 teeth, M0.5
        ├── DD cut bore (3.0mm)
        └── 6.0mm face width
```

## Data Flow

```
7mm-globoid.json ──┐
                   │
spec.md ───────────┼──► parameters.py ──► components/*.py ──► assembly/*.py ──► export/
                   │         │
tolerances.py ─────┘         │
                             ▼
                      features/*.py
                    (DD cuts, drilling)
```

## Design Decisions

### 1. Frozen Dataclasses

All parameter classes are frozen (`@dataclass(frozen=True)`) to ensure:
- Thread safety
- Hashability for caching
- Clear separation between configuration and CAD operations

### 2. Tolerance Profiles

Three profiles support the manufacturing workflow:
- `production`: +0.05mm holes for machined brass
- `prototype_resin`: +0.10mm for 1:1 resin validation prints
- `prototype_fdm`: +0.20mm for 2:1 FDM functional tests

### 3. Scale Factor

The `BuildConfig.scale` parameter allows generating enlarged prototypes:
- Scale 1.0: Production dimensions
- Scale 2.0: Double-size for FDM printing (easier to print, test fit)

All dimensions are multiplied by scale except tolerances.

### 4. Left/Right Hand Mirroring

The LH variant is a geometric mirror of RH, with:
- Mirrored frame geometry
- Left-hand worm thread (counter-clockwise)
- Left-hand wheel helix

This ensures symmetrical tuning action on the instrument.

### 5. Sandwich Assembly

The design enables full disassembly without soldering:

1. **Peg Head**: Retained by shoulder (pull-in) and M2 screw+washer (pull-out)
2. **String Post**: Retained by cap (pull-up) and E-clip (pull-down)
3. **Wheel**: Slides onto DD cut, retained by E-clip below

### 6. DD Cut Interface

Double-D cuts provide anti-rotation between wheel and string post:
- 3.0mm nominal diameter
- 0.6mm flat depth each side
- 1.8mm across flats

## Frame Geometry

The frame is machined from 10.35mm square brass tube:

```
         ┌─────────────────────────────────────────────────────────────┐
         │  Housing 1    Housing 2    Housing 3    Housing 4    Housing 5  │
         │    15.1mm      42.3mm       69.5mm       96.7mm      123.9mm    │
         │  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐    │
  Side ──│  │       │   │       │   │       │   │       │   │       │    │── Side
         │  └───────┘   └───────┘   └───────┘   └───────┘   └───────┘    │
         │      ○           ○           ○           ○           ○        │
         │    4.5mm      31.7mm      58.9mm      86.1mm     113.3mm  140.5mm│
         └─────────────────────────────────────────────────────────────┘
                                  Bottom Plate
                              (mounting holes shown)
```

### Per-Housing Drilling Pattern

```
                    Top (ø4.2mm post bearing)
                           │
                    ┌──────┴──────┐
                    │             │
    Entry ──────────│    ○        │────────── Bearing
    (ø6.2mm)        │    │        │           (ø4.0mm)
                    │    │5.5mm   │
                    │    ▼        │
                    └──────┬──────┘
                           │
                    Bottom (ø8.0mm wheel inlet)
```

## Validation (Spec Section 9)

Automated checks verify:
- Component clearances (worm fits in cavity, wheel fits through hole)
- Retention geometry (caps larger than holes)
- Center distance calculation
- Gear mesh compatibility (module, pressure angle)

## File Outputs

```
output/
├── rh/
│   ├── frame.step
│   ├── peg_head.step
│   ├── string_post.step
│   ├── wheel.step
│   └── assembly.step
└── lh/
    ├── frame.step
    ├── peg_head.step
    ├── string_post.step
    ├── wheel.step
    └── assembly.step
```
