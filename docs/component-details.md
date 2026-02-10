# Component Details — 5-Gang Instrument Tuning Machines

All dimensions in **mm** | Tolerances in brackets where critical

**Config: c13-10** 

---

## Overview

One tuner set = 1 RH (right-hand) + 1 LH (left-hand) assembly.
Each assembly has **5 tuning stations**.
LH is a mirror of RH.

### Parts per assembly

| Part | Qty | Material | Identical LH/RH? |
|------|-----|----------|-------------------|
| Frame | 1 | Brass (CZ121) | No — mirrored |
| String post | 5 | Brass (CZ121) | Yes — same part |
| Peg head + worm | 5 | Brass (CZ121) | thread direction L & R|
| Worm wheel | 5 | Phosphor bronze (PB102) | helix direction L & R|
| M2 x 4mm pan head screw | 10 | Stainless steel | Yes |
| M2.5 washer (5.5mm OD) | 5 | Stainless steel | Yes |
| M2 washer (~5mm OD) | 5 | Stainless steel | Yes |

### Hardware (buy, not manufactured)

| Item | Size | Qty per assembly |
|------|------|------------------|
| Pan head screw | M2 x 3mm | 10 (5 peg + 5 post) |
| Washer (peg retention) | M2.5 (ID 2.7, OD 5.5, t=0.5) | 5 |
| Washer (post retention) | M2 (ID ~2.2, OD ~5.0, t=0.5) | 5 |
| Mounting bolt | M3 mushroom head | 6 |

---

## 1. Frame

Square brass tube with machined openings. 5 rigid box sections connected by a flat mounting plate (top wall).

### Dimensions

| Parameter | Value |
|-----------|-------|
| Cross-section (outer) | 10.0 x 10.0 |
| Wall thickness | 1.0 |
| Internal cavity | 8.0 x 8.0 |
| Total length | 145.0 |
| Housing length | 16.2 (each box section) |
| End length | 10.0 (solid ends, each side) |
| Tuner pitch | 27.2 (centre-to-centre) |
| Number of housings | 5 |

### Holes (5 of each, one per housing)

| Hole | Face | Diameter | Tolerance |
|------|------|----------|-----------|
| Post bearing | Top | 5.05 | H7 (reamed) |
| Wheel inlet | Bottom | 5.1 | +0.1 |
| Worm entry | Right side (RH) | 7.05 | +0.1 |
| Peg bearing | Left side (RH) | 4.55 | H7 (reamed) |
| Mounting | Bottom plate | 3.0 | +0.1 |

Mounting holes: 6 total, in gaps between housings and at ends.

**LH frame:** Worm entry and peg bearing holes swap sides.

---

## 2. String Post

Turned brass part. Multi-diameter shaft with cap on top. **Same part for RH and LH.**

### Sections (top to bottom)

| Section | Diameter | Length | Notes |
|---------|----------|--------|-------|
| Cap | 7.5 | 1.0 | Fillet 0.25R top+bottom, 0.3 chamfer |
| Visible post | 6.0 | 5.5 | String hole here |
| Frame bearing | 5.0 (h7) | 1.1 | Passes through top wall |
| DD section | 3.5 / AF 2.5 | 7.2 | Wheel interface |
| **Total** | | **14.8** | |

### Features

| Feature | Detail |
|---------|--------|
| String hole | 1.5 dia, cross-drilled, 2.75 from bearing shoulder |
| DD flats | 2 flats, 0.5 deep, across-flats = 2.5 |
| M2 tap hole | Bottom of DD, 1.6 drill, 4.0 deep |
| Cap grooves | 3 concentric V-grooves, 0.33 wide x 0.33 deep, outer at 6.0 dia |



---

## 3. Peg Head + Worm

Decorative ring with integral worm shaft. **RH and LH have opposite thread direction.**

### Key dimensions

| Feature | Dimension |
|---------|-----------|
| Ring outer diameter | 12.5 |
| Ring bore | 9.8 (offset 0.25 from centre) |
| Cap diameter | 8.5 |
| Cap length | 1.0 |
| Shoulder diameter | 7.0 |
| Shaft diameter | 4.5 (h7) |

### Worm thread

| Parameter | Value |
|-----------|-------|
| Module | 0.5 |
| Type | Cylindrical |
| Starts | 1 |
| Pitch diameter | 6.0 |
| Tip diameter | 7.0 |
| Root diameter | 4.75 |
| Lead (axial advance per rev) | 1.571 |
| Lead angle | 4.76 deg |
| Worm length | 7.7 |
| Pressure angle | 20 deg |

### Shaft sections (from ring outward)

| Section | Diameter | Length | Notes |
|---------|----------|--------|-------|
| Worm | 7.0 tip / 4.75 root | 7.7 | Threaded |
| Bearing | 4.5 (h7) | 1.2 | Passes through frame wall |
| **Total shaft** | | **8.9** | |

### Features

| Feature | Detail |
|---------|--------|
| M2 tap hole | End of shaft, 1.6 drill, 3.0 deep |
| Pip (decorative) | 2.1 dia x 1.2 long, on ring face |
| Edge chamfer | 0.3 all edges |

Worm thread is integral to the peg shaft. No pins or setscrews used. Shaft must be concentric to worm pitch diameter within 0.01mm.


## 4. Worm Wheel

Gear with DD bore. **RH and LH have opposite helix direction.**

### Dimensions

| Parameter | Value |
|-----------|-------|
| Module | 0.5 |
| Number of teeth | 13 |
| Pitch diameter | 6.5 |
| Tip diameter | 7.6 |
| Root diameter | 5.55 |
| Face width | 7.7 |
| Profile shift | +0.3 |
| Pressure angle | 20 deg |

**Tip reduction (0.2): Tooth tips shortened 0.2mm to prevent interference with
  worm root. Already applied — the 7.6 tip diameter includes this reduction.**

### Bore (DD cut)

| Parameter | Value |
|-----------|-------|
| Bore diameter | 3.5 |
| Across flats | 2.5 |
| Flat depth | 0.5 (each side) |


---

## 5. Assembly — Gear Mesh

| Parameter | Value |
|-----------|-------|
| Centre distance | 6.25 |
| Gear ratio | 13:1 |
| Worm axis to wheel axis | 90 deg, offset 6.25 |
| Worm Z position (in frame) | -5.0 (below frame top) |

---

## 7. Critical Tolerances

| Feature | Tolerance | Why |
|---------|-----------|-----|
| Post bearing dia (5.0) | h7 (-0 / -0.012) | Must rotate freely in frame |
| Peg shaft dia (4.5) | h7 (-0 / -0.012) | Must rotate freely in frame |
| Frame bearing holes | H7 (+0.012 / +0) | Match shaft tolerances |
| DD flats (post + wheel) | +/- 0.02 | Anti-rotation fit |
| Housing pitch (27.2) | +/- 0.05 | Alignment across 5 stations |
| Worm pitch diameter (6.0) | +/- 0.02 | Gear mesh quality |
| Centre distance (6.25) | +/- 0.02 | Gear mesh quality |

---

## 8. File List


| File | Description |
|------|-------------|
| `frame_rh_5gang.step` | Right-hand frame |
| `frame_lh_5gang.step` | Left-hand frame |
| `string_post.step` | String post (same for both hands) |
| `peg_head_rh.step` | Peg head + worm, right-hand thread |
| `peg_head_lh.step` | Peg head + worm, left-hand thread |
| `wheel_rh.step` | Worm wheel, right-hand helix |
| `wheel_lh.step` | Worm wheel, left-hand helix |

STL versions also available (same names, `.stl` extension).
