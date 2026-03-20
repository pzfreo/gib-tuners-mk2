# Engineering Validation Tests: Summary for Engineers

This document describes the geometric and physical validation tests applied to the parametric tuner model. It is written for engineers evaluating the design, not for software developers. All tests operate on the 3D solid model or the parametric configuration and verify that the design meets manufacturing and functional requirements.

The test suite currently contains **114 tests** across 10 test modules. All pass on the c13 gear profile.

---

## What is Being Tested

The CAD model generates a 5-gang worm-drive tuning machine assembly from parametric inputs. The test suite verifies that:

- Components fit together with correct clearances
- No two solid parts occupy the same space
- Gear geometry is consistent and meshes correctly
- Rotating components clear the frame at all angles
- Wall thicknesses are sufficient after all machining operations
- Retention hardware provides adequate engagement and overlap
- The assembly can be physically built in the intended sequence
- LH and RH variants are exact mirrors of each other

The tests fall into six categories: **clearance and fit**, **gear engagement**, **rotation clearance**, **wall thickness and structural integrity**, **retention hardware**, and **LH/RH symmetry**.

---

## 1. Clearance and Fit

These verify that shafts fit through their respective holes with the designed bearing clearance, and that retention features (caps, washers) are larger than the holes they must not pass through.

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Post bearing in frame | 5.0mm shaft through 5.05mm hole | 0.05mm diametral clearance |
| Peg shaft in bearing hole | 4.0mm shaft through 4.05mm hole | 0.05mm diametral clearance |
| Worm tip through entry | Worm OD through entry hole | Entry hole > worm OD + 0.04mm |
| DD shaft in wheel bore | Post DD (2.4mm AF) in wheel DD (2.5mm AF) | 0.1mm across-flats clearance |
| M2 tap through DD bore | 1.6mm tap drill inside 2.5mm AF | Tap drill < across-flats |
| Washer through wheel inlet | 4.9mm washer through 5.1mm hole | 0.2mm clearance |
| Post cap vs bearing hole | 7.5mm cap, 5.05mm hole | Cap cannot pull through |
| Peg cap vs entry hole | 8.5mm cap, 7.2mm entry | Cap prevents push-in |
| Washer vs peg bearing | 5.5mm washer, 4.05mm hole | Washer prevents pull-out |

### Component Position Tests

These build the full 3D assembly and measure bounding box positions to verify that components are placed at the correct coordinates.

| Check | What is verified | Tolerance |
|-------|-----------------|-----------|
| Frame centre | Bounding box centre matches expected (X~0, Y~total_length/2, Z~-box_outer/2) | 0.5mm |
| String post Y-position | Post at housing_y - CD/2 | 0.5mm |
| Wheel Y-position | Wheel co-axial with post | 1.0mm |
| Peg head Y-position | Peg at housing_y + CD/2 | 2.0mm (asymmetric cap shifts bbox) |
| Peg head Z-position | Peg shaft at worm axis height | 2.0mm |

### Component Containment Tests

These verify that internal parts stay within the frame cavity boundaries.

| Check | What is verified | Tolerance |
|-------|-----------------|-----------|
| Wheel X-extent | Wheel bbox within +/- half cavity width | 0.1mm |
| Wheel Z-extent | Wheel below mounting plate ceiling, above frame floor | 0.1mm |

### Pairwise Non-Intersection (Interference Check)

Every pair of solid components in the assembly is tested for geometric interference using boolean intersection. If the intersection volume exceeds the threshold, the test fails.

| Pair type | Threshold | Rationale |
|-----------|-----------|-----------|
| General pairs | 0.01 mm^3 | Components must not occupy the same space |
| Gear mesh (wheel + peg/worm) | 0.1 mm^3 | Tiny contact volume acceptable at theoretical mesh point |
| Intentional overlaps (DD shaft in wheel, hardware on shafts) | Skipped | These are designed to mate |

For a 5-gang assembly, pairwise interference is checked across all housings. Total interference must remain below 0.5 mm^3.

### Boolean Operation Verification

These confirm that machining operations (drilling, milling, DD cutting) actually remove material from the solid model.

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Frame drilling | Drilled frame volume < solid box volume | >30% volume reduction (cavity + all holes) |
| DD flat cuts | DD flats remove positive volume from cylindrical shaft | Flat depth > 0, removal > 0.1mm^3 |

### Frame Geometry Tests

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Z-orientation | Mounting plate at Z=0, bottom at Z=-10mm | Within 0.01mm |
| Wheel inlet holes | At least 5 holes penetrate the bottom face (one per housing) | Face count at Z=-box_outer >= 5 |

---

## 2. Gear Engagement and Centre Distance

These tests validate that the worm and wheel mesh correctly and that the centre distance is consistent throughout the assembly.

### Worm Engagement

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Worm length vs face width | Worm thread length >= wheel face width | Full tooth contact across entire face |
| Worm axis Z-alignment | Worm axis Z-position aligns with wheel centre Z | Offset < half wheel height (geometric, from assembled model) |

The worm is integral to the peg head casting, so the geometric check verifies that the worm axis (computed from config) falls within the wheel's Z-extent in the assembled model. This ensures the thread covers the full tooth face.

### Centre Distance

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Effective CD consistency | Assembly effective_cd matches config CD minus extra_backlash | Within 0.01mm |
| Post Y-position from assembly | String post bbox centre Y matches expected housing_y - CD/2 | Within 0.5mm |
| Post hole within housing | Post bearing hole Y-position within housing Y-extent | For all 5 housings |
| Worm entry within housing | Worm entry hole edges within housing Y-extent | For all 5 housings |
| CD in reasonable range | Centre distance from JSON within 4-8mm | Sanity check |
| CD vs pitch diameters | CD consistent with (worm_PD + wheel_PD) / 2 | Within 1mm (profile shift) |

### Wheel in Cavity

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Wheel OD vs cavity width | wheel.tip_diameter < frame.box_inner | >= 0.3mm clearance |
| Wheel OD vs cavity (diagonal) | Wheel fits even on square cavity diagonal | OD < box_inner (always true for circle in square) |

---

## 3. Rotation Clearance

These tests verify that all rotating components can turn freely without fouling the frame or adjacent parts.

### Wheel Rotation

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Tip circle vs cavity X | Wheel tip diameter < cavity width | Parametric |
| Tip circle vs cavity Z | Wheel tip diameter < cavity height | Parametric |
| Swept volume (geometric) | Wheel rotated at 45-degree increments, boolean intersection with frame | < 0.05 mm^3 at every angle |

The geometric swept-volume test builds a 1-gang assembly, then rotates the wheel solid about its axis (the string post Z-axis) at 45-degree increments through 360 degrees. At each position, the boolean intersection volume with the frame is computed. This catches cases where individual teeth might clip the cavity wall even though the tip circle fits.

### Worm Rotation

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Clearance per side | (cavity - worm_OD) / 2 | >= 0.2mm per side |
| Clears top and bottom plates | Worm top edge below cavity ceiling, bottom edge above cavity floor | Worm centred at -box_outer/2 |

For a cylindrical worm the tip diameter is constant, so a parametric check is sufficient. The test verifies the worm centred at frame midpoint does not touch the inner surfaces of the top or bottom plates.

### Peg Cap Clearance

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Clears adjacent housing | Cap swept circle does not overlap the next housing | Gap >= 0 for all adjacent pairs |
| Clears frame end (last peg) | Last peg cap edge does not extend beyond frame total_length | cap_y + radius <= total_length |
| Clears frame start (first peg) | First peg cap edge does not extend before Y=0 | cap_y - radius >= 0 |

The peg head cap (8.5mm diameter) sits outside the frame on the worm entry side. When rotated, it sweeps a circle. These tests verify the swept circle does not intrude into the next housing or beyond the frame ends. This matters because the connector sections between housings have their side walls milled away and the cap must not catch on the remaining structure.

### Multi-Gang Spacing

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Housing centre spacing | All inter-housing Y-spacings equal tuner_pitch | Within 0.01mm (parametric) |
| Assembly component spacing | String post Y-spacings in 5-gang assembly match tuner_pitch | Within 0.5mm (geometric, from bbox) |

---

## 4. Wall Thickness and Structural Integrity

These tests verify that sufficient material remains after all machining operations (drilling, milling, DD cutting). Wall thickness failures can lead to part breakage under string tension or during assembly.

### DD Section (Most Marginal)

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Wall to tap bore | (across_flats - tap_bore_diameter) / 2 | >= 0.4mm **(currently 0.45mm)** |
| Advisory margin | Warn if wall drops below 0.5mm | Warning only (currently fires) |
| Diameter exceeds tap bore | DD full diameter > tap drill diameter | Concentricity requirement |

The DD section of the string post is the most structurally marginal dimension in the entire design. A 3.5mm shaft has two 0.5mm flats milled off it (leaving 2.5mm across flats), and a 1.6mm M2 tap bore runs axially through the centre. The remaining wall between the flat surface and the tap bore is only **0.45mm** — just 0.05mm above the hard minimum of 0.4mm.

### Worm Entry Hole

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Wall above and below hole | (box_outer - entry_hole) / 2 | >= 1.0mm per side |
| Does not breach plates | Hole top edge below top plate inner surface | Hole at frame midpoint Z |

The worm entry hole (7.2mm) is the largest hole drilled through a 10mm housing side face, leaving only 1.4mm per side. The test verifies the hole does not break through into the top or bottom plates.

### Other Hole Walls

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Peg bearing hole wall | (box_outer - 4.05mm) / 2 | >= 2.5mm per side |
| Post bearing hole wall | (box_outer - 5.05mm) / 2 | >= 2.0mm per side |

### Gear Component Walls

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Wheel hub (bore to root) | (root_diameter - bore_diameter) / 2 | >= 0.5mm |
| Worm root to shaft | shaft_diameter <= worm.root_diameter | Thread form complete at transition |

The wheel hub wall check verifies there is enough material between the DD bore and the base of the teeth. The worm root check ensures the bearing shaft diameter does not exceed the thread root — otherwise the thread form would be incomplete where the worm transitions to the bearing section.

### Housing Integrity After Drilling

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Frame volume vs analytical | Actual frame volume > 50% of hollow shell estimate | Holes not overlapping |
| Hole area vs face area | Each hole area < 50% of its face area | No single hole dominates a face |

These catch the case where two holes drilled from different faces might break through into each other inside the housing, creating an unintended passage and weakening the structure.

---

## 5. Retention Hardware

These tests verify that the M2 screws and washers provide adequate mechanical retention for the peg head and string post assemblies.

### Thread Engagement

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| String post M2 engagement | thread_length >= 2 * M2 diameter (2D rule) | >= 4.0mm **(currently 4.0mm — at minimum)** |
| Peg head M2 engagement | tap_depth vs 2D rule | Advisory warning **(currently 3.0mm, below 4.0mm rule)** |
| Thread within DD section | thread_length <= dd_cut_length | Thread does not extend beyond DD |

The 2D rule of thumb states that thread engagement should be at least twice the major diameter for reliable retention in brass. The string post meets this exactly at 4.0mm. The peg head is below the rule at 3.0mm, but this is acceptable because string tension provides the primary retention force for the peg — the screw only prevents the peg from sliding out when no string is installed.

### Washer Overlap

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Peg washer overlap | (washer_OD - bearing_hole) / 2 | >= 0.4mm per side |
| Post washer vs bore | Standard M2 washer OD > wheel DD bore | Washer cannot fall through bore |
| Washer fits on shaft | Washer ID clears shaft for assembly | Assembly constraint |
| Screw captures washer | Screw head OD > washer ID | Washer retained by screw |

---

## 6. LH/RH Mirror Symmetry

These tests verify that the left-hand variant is an exact geometric mirror of the right-hand variant, with no dimensional distortion introduced by the mirroring process.

### Configuration

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| LH hand setting | LH config has Hand.LEFT | Exact |
| LH worm hand | LH worm is left-hand thread | Exact |
| Dimension preservation | All non-hand dimensions identical (frame, post, peg, CD, wheel) | Exact |

### Frame Geometry

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Bounding box sizes match | RH and LH frame X, Y, Z extents identical | Within 0.01mm |
| Volume preserved | Mirror does not change frame volume | Within 0.1 mm^3 |
| X-coordinates reflected | LH min.X = -RH max.X, LH max.X = -RH min.X | Within 0.01mm |
| Y, Z unchanged | Mirror does not affect Y or Z coordinates | Within 0.01mm |

### Assembly Components

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| All component sizes match | Each mirrored component has same bbox dimensions as RH original | Within 0.1mm per axis |

This tests every component in a 1-gang assembly (frame, string post, wheel, peg head, washers, screws) to verify that the YZ-plane mirror preserves all dimensions.

---

## 7. Gear Mesh Validation (with STEP Files)

When reference STEP files for the worm and wheel are available, more detailed mesh checks are performed using boolean operations on the imported gear geometry.

| Check | What is verified | Acceptance |
|-------|-----------------|------------|
| Mesh interference volume | Boolean intersection of positioned worm and wheel | Within manufacturing tolerance |
| Optimal mesh rotation | Wheel rotation angle that minimises interference | Deterministic (repeatable) and within one tooth pitch (0 to 360/num_teeth degrees) |
| Interference at optimal rotation | Residual interference after rotation optimisation | Within backlash or manufacturing tolerance |

---

## 8. Spec Section 9 Validation

A consolidated validation function checks all items from the engineering specification Section 9 checklist:

- Worm OD fits within cavity (7.8mm) with >= 0.4mm clearance
- Worm passes through entry hole
- All shaft/hole clearances correct
- Centre distance within 4-8mm range
- CD consistent with pitch diameter calculation (within 1mm, allowing for profile shift)
- Gear modules match (worm and wheel)
- M2 thread fits through DD bore
- Washer retains wheel

The validation produces a structured pass/fail report with at least 10 individual checks.

---

## Coordinate System Reference

All geometric tests use the player's-view coordinate system defined in the specification:

```
Z=0         Mounting plate (top, visible surface)
Z=-1.1      Inside surface of top plate (cavity ceiling)
Z=-8.9      Inside surface of bottom plate (cavity floor)
Z=-10.0     Bottom surface (inside headstock cavity)

X=0         Frame centreline (post axis)
+X          Worm entry side (RH variant)
-X          Peg bearing side (RH variant)

Y=0         Frame start
Y=145       Frame end (5-gang)
```

Post axis is at `housing_y - CD/2` (toward Y=0).
Worm axis is at `housing_y + CD/2` (toward Y=145).

---

## Known Marginal Dimensions

These parameters are within tolerance but have minimal margin. The test suite flags them with advisory warnings. Any parameter changes should be checked against these:

| Dimension | Current value | Minimum acceptable | Margin | Test advisory |
|-----------|--------------|-------------------|--------|---------------|
| DD section wall (AF to tap bore) | 0.45mm | 0.40mm | 0.05mm | Warning fires |
| Worm cavity clearance (per side) | 0.4mm | 0.2mm | 0.2mm | Passes |
| Post bearing clearance | 0.05mm | 0.04mm | 0.01mm | Passes |
| Peg bearing clearance | 0.05mm | 0.04mm | 0.01mm | Passes |
| Peg tap engagement (M2) | 3.0mm | 4.0mm (2D rule) | -1.0mm (below rule of thumb) | Warning fires |
| String post tap engagement (M2) | 4.0mm | 4.0mm (2D rule) | 0.0mm (at minimum) | Passes |
| Peg washer overlap | 0.475mm | 0.40mm | 0.075mm | Passes |

The two advisory warnings that fire during a test run are:
1. **DD wall thickness** — 0.45mm is marginal; recommended >= 0.5mm
2. **Peg tap depth** — 3.0mm is below the 2D rule of 4.0mm; acceptable because string tension provides primary retention

---

## Test Execution

All tests run via pytest. The full suite takes approximately 45 minutes due to expensive 3D boolean operations in the assembly and interference tests.

```bash
# Full suite (114 tests, ~45 min)
pytest tests/ -v --gear c13

# Fast parametric checks only (~30 sec)
pytest tests/test_wall_thickness.py tests/test_retention.py tests/test_parameters.py tests/test_validation.py -v

# Gear engagement and rotation clearance (~5 min)
pytest tests/test_gear_engagement.py tests/test_rotation_clearance.py -v --gear c13

# LH/RH symmetry (~3 min)
pytest tests/test_symmetry.py -v --gear c13

# Assembly interference (slow, builds full 3D assemblies, ~15 min)
pytest tests/test_assembly_validation.py tests/test_assembly.py -v --gear c13

# Frame and component geometry (~2 min)
pytest tests/test_frame.py -v
```

The `--gear` flag selects the gear profile. The default is `c13-10` (M0.5, 13-tooth, cylindrical worm). Different profiles may have different clearances and should each be validated independently.

### Test Modules

| Module | Tests | Type | Time |
|--------|-------|------|------|
| `test_parameters.py` | 17 | Parametric (no CAD) | Fast |
| `test_validation.py` | 17 | Parametric + STEP mesh | Medium |
| `test_wall_thickness.py` | 11 | Parametric + frame build | Medium |
| `test_retention.py` | 7 | Parametric | Fast |
| `test_gear_engagement.py` | 7 | Parametric + assembly build | Medium |
| `test_rotation_clearance.py` | 10 | Parametric + assembly build | Medium |
| `test_symmetry.py` | 7 | Assembly build + mirror | Medium |
| `test_frame.py` | 10 | Component build | Medium |
| `test_assembly_validation.py` | 16 | Full assembly + boolean ops | Slow |
| `test_assembly.py` | 4 | Full assembly + STEP export | Slow |
