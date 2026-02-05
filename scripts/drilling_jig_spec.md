# Drilling Jig Specification

## Overview

Two-part clamshell jig for drilling all 26 holes in a 5-gang right-hand brass tuner frame. The clamshell wraps around the frame from the top and sides (inverted U cross-section). A removable base plate closes the bottom and provides guide holes for wheel inlet drilling.

All gear-dependent dimensions (center distance, worm Z position, drill diameters, etc.) are read from the JSON file for the selected gear definition. Uses the same `--gear` argument and config loading as `build.py` (`resolve_gear_config()` + `create_default_config()`).

Example values below are for the **bh11-cd** gear profile (M0.6, 11T, CD=5.6mm, globoid worm).

## Usage

```bash
python scripts/drilling_jig.py --gear bh11-cd
python scripts/drilling_jig.py --gear balanced
python scripts/drilling_jig.py --list-gears
```

## Parts

| Part | Description |
|------|-------------|
| Clamshell | Solid block with pocket from below. Stepped M14 bushing pockets (blind M14 + smaller bore) on top and sides. Printed mounting hole guides. End walls act as end stops. Extended walls enclose side bushings with 5mm minimum rim. |
| Base plate | Flat plate with raised lip, bolted to clamshell bottom. Lip pushes frame flush against pocket ceiling. Printed guide holes for wheel inlet drilling. |

## Clamshell Dimensions (bh11-cd)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Width (X) | 40.0mm | Total external width |
| Length (Y) | 155.0mm | Frame length + 2 x 5mm end walls |
| Height (Z) | 30.9mm | 14mm top slab + 16.9mm channel depth |
| Channel width | 10.3mm | 10mm frame + 0.3mm clearance |
| Channel depth | 16.9mm | Frame height (10mm) + wall extension (6.9mm) |
| Channel length | 145.0mm | Matches frame length |
| Side wall thickness | ~14.85mm | (40 - 10.3) / 2 |
| Top slab thickness | 14.0mm | 10mm bushing engagement + 4mm structure |
| End wall thickness | 5.0mm | End stops for frame Y registration |
| Wall extension | 6.9mm | Walls extend below frame to enclose side bushings |

### Wall Extension Derivation

The wall extension ensures 5mm minimum rim below the side bushing bottom edge:

```
bushing_bottom_z = worm_z - BUSHING_OD/2 = -4.9 - 7.0 = -11.9mm
wall_extension = abs(bushing_bottom_z) - frame_outer + BUSHING_RIM
               = 11.9 - 10.0 + 5.0 = 6.9mm
channel_depth = frame_outer + wall_extension = 10.0 + 6.9 = 16.9mm
```

This is computed dynamically per gear profile.

## Base Plate Dimensions (bh11-cd)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Width (X) | 40.0mm | Matches clamshell |
| Length (Y) | 155.0mm | Matches clamshell |
| Thickness (Z) | 8.0mm | Structural base |
| Lip width (X) | 10.0mm | Matches frame outer, fits inside 10.3mm channel |
| Lip length (Y) | 145.0mm | Matches frame length |
| Lip height (Z) | 6.9mm | Matches wall extension |

The lip fits inside the clamshell pocket and pushes the frame flush against the pocket ceiling. Bolt holes are in the outer flanges (outside the lip).

## Gear Parameters (bh11-cd Profile)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Center distance | 5.6mm | Worm-to-wheel axis distance |
| CD/2 | 2.8mm | Axis offset from housing center |
| Worm Z position | -4.9mm | Aligned mode for globoid worm |
| Post axis Y offset | -CD/2 | Toward nut end (-Y) |
| Worm axis Y offset | +CD/2 | Toward bridge end (+Y) |

### Worm Z Derivation

For the bh11-cd globoid profile with virtual hobbing (aligned mode):

```
face_width = 7.6mm (wheel width)
dd_cut_length = face_width - dd_clearance = 7.6 - 0.1 = 7.5mm
bearing_length = wall_thickness + axial_play = 1.1 + 0.1 = 1.2mm
post_z_offset = -(dd_cut_length + bearing_length) = -8.7mm
worm_z = post_z_offset + face_width/2 = -8.7 + 3.8 = -4.9mm
```

## Stepped Bushing Pocket Design

Side bushing pockets use a stepped (blind pocket + bore) design to ensure structural integrity:

```
Side wall cross-section (X direction):
outer face |<-- 10mm M14 pocket -->|<-- 4.85mm bore -->| inner face
X=+/-20    |      dia 14mm         |   dia 7.05/4.05   | X=+/-5.15
```

- **Outer pocket:** dia 14mm x 10mm deep from outer wall face. M14 bushing threads into this pocket.
- **Inner bore:** Drill diameter (7.05mm for worm entry, 4.05mm for peg bearing) through remaining 4.85mm of wall to channel face.

This gives full wall containment around the M14 bushing body. Only the smaller drill bore penetrates to the channel interior.

Top face bushing pockets are through-holes (dia 14mm through 14mm top slab) since the full slab depth exceeds the 10mm bushing engagement.

## Bushing Positions (bh11-cd)

All Y values from frame start (Y=0). Housing centers: 18.1, 45.3, 72.5, 99.7, 126.9mm.

### Post Bearing Bushings (top face, M14, dia 4.05mm bore)

Drill vertically from above through the mounting plate.

| # | X (mm) | Y (mm) | Bore |
|---|--------|--------|------|
| PB1 | 0 | 15.3 | dia 4.05mm |
| PB2 | 0 | 42.5 | dia 4.05mm |
| PB3 | 0 | 69.7 | dia 4.05mm |
| PB4 | 0 | 96.9 | dia 4.05mm |
| PB5 | 0 | 124.1 | dia 4.05mm |

Y = housing_center - CD/2. Adjacent spacing = 27.2mm.

### Worm Entry Bushings (right wall, M14 stepped, dia 7.05mm bore)

Drill horizontally from +X side through housing wall.

| # | Y (mm) | Z (mm) | Bore |
|---|--------|--------|------|
| WE1 | 20.9 | -4.9 | dia 7.05mm |
| WE2 | 48.1 | -4.9 | dia 7.05mm |
| WE3 | 75.3 | -4.9 | dia 7.05mm |
| WE4 | 102.5 | -4.9 | dia 7.05mm |
| WE5 | 129.7 | -4.9 | dia 7.05mm |

Y = housing_center + CD/2. Z = worm axis position.

### Peg Bearing Bushings (left wall, M14 stepped, dia 4.05mm bore)

Drill horizontally from -X side. Same Y,Z positions as worm entry.

| # | Y (mm) | Z (mm) | Bore |
|---|--------|--------|------|
| PeB1 | 20.9 | -4.9 | dia 4.05mm |
| PeB2 | 48.1 | -4.9 | dia 4.05mm |
| PeB3 | 75.3 | -4.9 | dia 4.05mm |
| PeB4 | 102.5 | -4.9 | dia 4.05mm |
| PeB5 | 129.7 | -4.9 | dia 4.05mm |

## Printed Guide Holes

### Mounting Holes (top face, dia 3.0mm)

Drill vertically from above through the mounting plate at gap positions.

| # | X (mm) | Y (mm) |
|---|--------|--------|
| MH1 | 0 | 5.0 |
| MH2 | 0 | 31.7 |
| MH3 | 0 | 58.9 |
| MH4 | 0 | 86.1 |
| MH5 | 0 | 113.3 |
| MH6 | 0 | 140.0 |

### Wheel Inlet Holes (base plate, dia 5.1mm)

Drill vertically from below through housing bottom wall.

| # | X (mm) | Y (mm) |
|---|--------|--------|
| WI1 | 0 | 15.3 |
| WI2 | 0 | 42.5 |
| WI3 | 0 | 69.7 |
| WI4 | 0 | 96.9 |
| WI5 | 0 | 124.1 |

Y positions match post bearing holes (at post axis).

## Bushing Clearance (bh11-cd)

| Check | Value | Status |
|-------|-------|--------|
| Top bushing pitch | 27.2mm | 13.2mm gap between M14 bodies |
| Side bushing pitch | 27.2mm | 13.2mm gap between M14 bodies |
| Side bushing Z span | +2.1 to -11.9mm | Fully enclosed by extended walls (wall bottom at -16.9mm) |
| Rim below side bushings | 5.0mm | -16.9 - (-11.9) = 5.0mm minimum rim |
| Rim above side bushings | 2.1mm into 14mm top slab | Bushing top at Z=+2.1, contained within top slab |
| Side wall X containment | 10mm M14 pocket in 14.85mm wall | 4.85mm solid wall behind bushing (bore only) |
| Top slab thickness | 14.0mm | Exceeds 10mm bushing engagement |

## Fastener Layout

### Base Plate to Clamshell (4x M3)

| Bolt | X (mm) | Y (mm) | Notes |
|------|--------|--------|-------|
| B1 | +12.6 | 5.0 | Right flange, near front |
| B2 | +12.6 | 140.0 | Right flange, near rear |
| B3 | -12.6 | 5.0 | Left flange, near front |
| B4 | -12.6 | 140.0 | Left flange, near rear |

- Clamshell: M3 heat-set inserts (dia 5.0mm x 4.0mm deep) in wall bottom faces
- Base plate: M3 clearance holes (dia 3.4mm) with counterbore (dia 5.5mm x 3.5mm deep) from below

Bolt X positions are centered in the outer flanges (outside the base plate lip).

## Coordinate System (bh11-cd)

Same as frame code (`frame.py`):

```
Z = +14.0   Top of clamshell (drill entry for top holes)
Z =  0.0    Pocket ceiling / frame mounting plate (Z=0 datum)
Z = -4.9    Worm/peg axis (side bushing centers)
Z = -10.0   Frame bottom
Z = -16.9   Wall bottoms / pocket opening / lip bottom
Z = -16.9   Base plate top surface
Z = -24.9   Base plate bottom surface

Y = -5.0    Clamshell front face
Y =  0.0    Frame start / pocket start (front end stop)
Y = 145.0   Frame end / pocket end (rear end stop)
Y = 150.0   Clamshell rear face

X = -20.0   Clamshell left face (peg bearing bushings enter from here)
X = -5.15   Left channel wall
X =  0.0    Frame/channel center
X = +5.15   Right channel wall
X = +20.0   Clamshell right face (worm entry bushings enter from here)
```

### Cross-Section (X-Z plane at a side bushing Y position)

```
Z=+14  +------------------------------------------+
       |              TOP SLAB (14mm)              |
Z=0    +--------+                       +----------+  <- pocket ceiling
       |        |      pocket           |          |
       |  LEFT  |    (10.3mm wide)      |  RIGHT   |
       |  WALL  |                       |  WALL    |
       | [bore] |   *bushing center     | [bore]   |  <- Z=-4.9
       |  4.05  |      frame (10mm)     |  7.05    |
Z=-10  |        |  +-----------------+  |          |  <- lip top / frame bottom
       |  5mm   |  |   BASE LIP      |  |  5mm     |
       |  rim   |  |   (6.9mm tall)   |  |  rim     |
Z=-16.9+--------+  |                 |  +----------+  <- wall bottom / lip bottom
       +-----------+                 +-------------+
       |           +-----------------+             |
       |           BASE PLATE (8mm)                |
Z=-24.9+-----------+-----------------+-------------+
```

## Drilling Workflow

### Step 1: Top and Side Holes (clamshell only, no base plate)

1. Place clamshell upside down on bench (pocket opening facing up)
2. Drop brass frame into pocket (mounting plate faces down into pocket ceiling)
3. Flip clamshell right-side up (frame held by gravity + pocket fit)
4. Drill 5x post bearing holes through top bushings (dia 4.05mm, vertical)
5. Drill 6x mounting holes through top guides (dia 3.0mm, vertical)
6. Clamp jig on side, drill 5x worm entry holes through right wall bushings (dia 7.05mm, horizontal)
7. Flip, drill 5x peg bearing holes through left wall bushings (dia 4.05mm, horizontal)

### Step 2: Bottom Holes (with base plate)

8. Bolt base plate to clamshell bottom (4x M3 bolts)
9. Flip jig upside down
10. Drill 5x wheel inlet holes through base plate guides (dia 5.1mm, vertical)

## Hardware BOM (bh11-cd)

| Item | Qty | Description |
|------|-----|-------------|
| M14 drill bushing, dia 4.05mm bore | 10 | Post bearing (5) + peg bearing (5) |
| M14 drill bushing, dia 7.05mm bore | 5 | Worm entry |
| M3 socket head cap screw (5.5mm head) | 4 | Base plate attachment (through 8mm plate + 6.9mm lip clearance) |
| M3 heat-set insert (dia 5.0mm x 4.0mm) | 4 | In clamshell wall bottoms |

Note: Bushing bore diameters are config-dependent. Values above are for bh11-cd. Use `--gear` to see values for other profiles.

## Manufacturing Notes

- **3D printing (FDM/SLA):** Print clamshell with top face down for best bushing pocket surface finish. Print base plate flat (lip facing up).
- **Bushing installation:** M14 bushings thread into blind pockets from the outer face. For 3D-printed jigs, tap the holes with an M14 tap, or print slightly undersized (13.8mm) for press-fit with Loctite.
- **Stepped pockets:** The blind M14 pocket seats the bushing. The smaller bore behind it guides the drill into the frame. This design keeps the full M14 body enclosed in wall material.
- **Drill bushing bore clearance:** The bushing bore should be 0.05-0.1mm larger than the drill bit for free spinning. Bushing bores listed above are the nominal drill diameters.
- **Air gap:** Between bushing bore exit and brass frame face, there is approximately 4.85mm of unsupported drill length (side walls) or 4mm (top slab). Acceptable for guided drilling and reaming.

## Handedness

This jig is for **right-hand** frames only:
- Worm entry bushings on **+X** (right) wall
- Peg bearing bushings on **-X** (left) wall

A left-hand variant would swap these sides. This can be added as a parameter in a future revision.

## Config Profiles

| Profile | CD (mm) | Worm Z (mm) | Wall Extension (mm) | Worm Bore |
|---------|---------|-------------|---------------------|-----------|
| bh11-cd | 5.6 | -4.9 | 6.9 | dia 7.05mm |
| balanced | 5.9 | -5.0 | 7.0 | dia 7.05mm |

## Comparison with Cutting Jig

| Aspect | Cutting Jig | Drilling Jig |
|--------|------------|--------------|
| Purpose | Saw cuts for housings/gaps | Drill all 26 holes |
| Parts | Body + moveable end stop | Clamshell + base plate (with lip) |
| Frame hold-down | Internal plugs in cavity | Clamshell pocket + base plate lip |
| End stops | Fixed plug + moveable stop | Pocket end walls (fixed) |
| Precision features | Saw guide slots (1mm wide) | M14 stepped bushing pockets |
| Channel width | 10.3mm | 10.3mm (same) |
| Channel depth | 10.0mm | 16.9mm (extended for bushing enclosure) |
| Hardware | M3 heat-set + bolt | 15x M14 bushings + 4x M3 |
| Config | Gear-profile driven (--gear) | Gear-profile driven (--gear) |
