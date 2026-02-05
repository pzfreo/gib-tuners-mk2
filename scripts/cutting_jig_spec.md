# Cutting Jig Specification

Cutting jig for brass frame manufacturing. Holds brass box section stock and guides saw cuts to create the frame housings and gaps.

All frame dimensions (outer size, wall thickness, housing length, pitch, etc.) are read from the JSON for the selected gear definition. Uses the same `--gear` argument and config loading as `build.py`.

## Usage

```bash
python scripts/cutting_jig.py --gear bh11-cd
python scripts/cutting_jig.py --gear balanced
python scripts/cutting_jig.py --list-gears
```

## Overview

The jig consists of two parts:
1. **Main jig body** - U-channel to hold brass, with saw guide slots (open top for saw access)
2. **Moveable end stop** - Adjustable stop with plug to secure brass

The cutting jig has an open top so the slitting saw can reach the brass. Locating plugs fit inside the brass tube's inner cavity to hold it down - one fixed at Y=0 and one on the moveable end stop at Y=frame_length.

Example values below are for the default frame parameters (10mm outer, 1.1mm wall, 5 housings, 145mm length).

## Jig Body Dimensions

| Parameter | Value | Description |
|-----------|-------|-------------|
| Length | 185mm | Frame (145mm) + end stop (10mm) + travel (30mm) |
| Width | 30mm | Provides ~9.85mm thick side walls |
| Height | 18mm | Channel (10mm) + floor (8mm) |
| Channel width | 10.3mm | Frame outer (10mm) + 0.3mm clearance |
| Channel depth | 10mm | Matches frame outer dimension |
| Floor thickness | 8mm | Solid base for rigidity |
| End stop length | 10mm | Fixed stop at Y=0 |

## Brass Frame Parameters (from config)

| Parameter | Value | Source |
|-----------|-------|--------|
| Outer dimension | 10mm | `frame.box_outer` |
| Wall thickness | 1.1mm | `frame.wall_thickness` |
| Inner dimension | 7.8mm | Derived: outer - 2 x wall |
| Frame length | 145mm | Derived: `frame.total_length` |
| Housing length | 16.2mm | `frame.housing_length` |
| Tuner pitch | 27.2mm | `frame.tuner_pitch` |
| Num housings | 5 | `frame.num_housings` |

## Saw Slots

| Parameter | Value | Description |
|-----------|-------|-------------|
| Slot width | 1mm | For slitting saw blade |
| Saw kerf | 1mm | Material removed by cut |
| Partial cut depth | 8.9mm | Leaves 1.1mm bottom wall (frame_outer - wall) |
| Full cut depth | 10mm | Cuts through entire brass (frame_outer) |

### Gap Computation

Gaps are computed dynamically from housing centers and housing length:

```
housing_centers = [18.1, 45.3, 72.5, 99.7, 126.9]  (from config)
half_housing = 16.2 / 2 = 8.1

gaps = [
    (0.0, 10.0),       # Before first housing
    (26.2, 37.2),       # Gap 1-2
    (53.4, 64.4),       # Gap 2-3
    (80.6, 91.6),       # Gap 3-4
    (107.8, 118.8),     # Gap 4-5
    (135.0, 145.0),     # After last housing
]
```

### Slot Positions (kerf-compensated)

Slots are offset by 0.5mm (half kerf) so the kerf falls into the gap regions, preserving housing dimensions.

| Slot Center | Kerf Start | Kerf End | Purpose | Depth |
|-------------|------------|----------|---------|-------|
| 9.5 | 9.0 | 10.0 | Start of H1 | 8.9mm |
| 26.7 | 26.2 | 27.2 | End of H1 | 8.9mm |
| 36.7 | 36.2 | 37.2 | Start of H2 | 8.9mm |
| 53.9 | 53.4 | 54.4 | End of H2 | 8.9mm |
| 63.9 | 63.4 | 64.4 | Start of H3 | 8.9mm |
| 81.1 | 80.6 | 81.6 | End of H3 | 8.9mm |
| 91.1 | 90.6 | 91.6 | Start of H4 | 8.9mm |
| 108.3 | 107.8 | 108.8 | End of H4 | 8.9mm |
| 118.3 | 117.8 | 118.8 | Start of H5 | 8.9mm |
| 135.5 | 135.0 | 136.0 | End of H5 | 8.9mm |
| 145.5 | 145.0 | 146.0 | Length cut | 10mm |

### Housing Sections (after cutting)

| Housing | Y Start | Y End | Length |
|---------|---------|-------|--------|
| H1 | 10.0 | 26.2 | 16.2mm |
| H2 | 37.2 | 53.4 | 16.2mm |
| H3 | 64.4 | 80.6 | 16.2mm |
| H4 | 91.6 | 107.8 | 16.2mm |
| H5 | 118.8 | 135.0 | 16.2mm |

## Fixed End Plug

Located at Y=0 on the jig, extends into brass tube to hold it down.

| Parameter | Value | Description |
|-----------|-------|-------------|
| Size | 7.7mm x 7.7mm | Fits in 7.8mm inner cavity (0.05mm clearance per side) |
| Length | 3mm | Extends into brass (Y=0 to Y=3) |
| Z position | Z=-5 | Centered in brass inner cavity |

## Moveable End Stop

Sits inside the jig channel on the channel floor, with plug extending into the brass tube.

| Parameter | Value | Description |
|-----------|-------|-------------|
| Body size (X) | 9.9mm | Fits in 10.3mm channel with clearance |
| Body size (Y) | 25mm | For rigidity |
| Body height | 10mm | Sits on channel floor (Z=-10) to jig top (Z=0) |
| Plug size | 7.7mm x 7.7mm | Fits in brass inner cavity (0.05mm clearance per side) |
| Plug length | 5mm | Extends into brass tube (in -Y direction) |
| Plug Z position | Z=-5 | Centered in brass inner cavity |
| Bolt hole | 5.5mm | M5 clearance, vertical through body |

## Hardware

| Item | Specification | Location |
|------|---------------|----------|
| Heat-set insert | M5, 6.4mm OD | Jig floor at Y=157.5mm |
| Bolt | M5 | Through end stop, channel floor, into insert |
| Bolt clearance hole | 5.5mm | Through channel floor at Y=157.5mm |

## Coordinate System

- **Y=0**: Fixed end stop face (brass butts against this)
- **Y=145**: Frame end (moveable end stop position)
- **Z=0**: Jig top surface (brass sits flush)
- **Z=-10**: Channel floor (brass bottom)
- **Z=-18**: Jig bottom

## Manufacturing Notes

1. Jig is designed for 3D printing (FDM/SLA)
2. Heat-set insert installed from jig bottom
3. Partial cuts (8.9mm) leave bottom wall for rigidity during cutting
4. Full cut at Y=145.5 separates frame from waste stock

## Files

- `cutting_jig.py` - Parametric CAD script (reads gear definition JSON via --gear)
- `output/cutting_jig_prototype.step` - Jig body geometry
- `output/cutting_jig_end_stop.step` - End stop geometry

## Comparison: Cutting Jig vs Drilling Jig

| Feature | Cutting Jig | Drilling Jig |
|---------|-------------|--------------|
| Top | Open (saw access) | Closed (clamshell with drill bushings) |
| Brass hold-down | Internal plugs (7.7mm) | Clamshell pocket + base plate lip |
| Y location | Fixed plug + moveable end stop | Pocket end walls (fixed) |
| Z location | Plugs in brass inner cavity | Lip pushes frame against ceiling |
| Channel depth | 10mm (frame height) | 16.9mm (extended for bushing enclosure) |
| Config | --gear (reads JSON) | --gear (reads JSON) |
| Hardware | M5 heat-set + bolt | 15x M14 bushings + 4x M5 |
