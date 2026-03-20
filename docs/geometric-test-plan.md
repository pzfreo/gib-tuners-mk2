# Geometric Test Plan: Proposed Additional Tests

This document describes new geometric and engineering validation tests to add to the test suite, grouped by engineering concern. Each entry describes the physical property being verified, the acceptance criterion, and the test approach.

## 1. Gear Engagement and Centre Distance

### 1.1 Worm Engagement Length vs Wheel Face Width

**What:** The worm thread must overlap the wheel's tooth face for the full face width. If the worm is shorter than the wheel, tooth contact is incomplete and load capacity drops.

**Criterion:** `worm.length >= wheel.face_width`

**Test approach:** Pure parametric check from config values. Also verify in the assembled geometry that the worm bounding box Y-extent overlaps the wheel bounding box Y-extent by at least `wheel.face_width - 0.5mm`.

### 1.2 Centre Distance Consistency (Parametric vs Geometric)

**What:** The actual Y-distance between the string post axis and peg head axis in the assembled model must match `gear.center_distance` from JSON.

**Criterion:** Measured axis-to-axis distance within 0.05mm of config CD (tighter than the current 2mm bbox-based tolerance).

**Test approach:** Instead of using bounding box centres (which are skewed by asymmetric features like the peg cap), extract the centre of cylindrical bearing faces. For the string post, use the bearing section cylinder centre. For the peg head, use the shaft bearing cylinder centre. Measure Y-distance between these two points.

### 1.3 Centre Distance Fits Within Frame Geometry

**What:** Both the post hole and worm entry hole must physically land within the housing walls, not extend beyond the frame width.

**Criterion:**
- Post axis at `housing_y - CD/2`: the post bearing hole (5.05mm) must not extend beyond the housing Y-extent (housing_center +/- housing_length/2).
- Worm axis at `housing_y + CD/2`: the worm entry hole (7.2mm) must not extend beyond the housing Y-extent.

**Test approach:** For each housing, compute the hole edge positions and verify they fall within `[housing_center - housing_length/2, housing_center + housing_length/2]`.

### 1.4 Gear Module Match

**What:** Worm and wheel modules must be identical for proper meshing.

**Criterion:** `worm.module == wheel.module` (already tested, but listed for completeness).

### 1.5 Wheel OD Fits in Cavity

**What:** The wheel tip diameter must be smaller than the internal cavity dimension so the wheel can rotate freely.

**Criterion:** `wheel.tip_diameter < frame.box_inner` with at least 0.3mm clearance.

**Test approach:** Parametric check. Also verify in assembled geometry that the wheel bounding box in X and Z stays within cavity inner walls.

## 2. Rotation and Clearance

### 2.1 Wheel Rotation Clearance (Swept Volume)

**What:** The wheel must be able to rotate through its full range without clipping the frame cavity walls at any angle. The wheel is not circular -- it has teeth -- so the tip circle may come close to cavity walls at certain orientations.

**Criterion:** At every 1-degree increment through 360 degrees, the rotated wheel must not intersect the frame solid by more than 0.01mm^3.

**Test approach:** Build a 1-gang assembly. For each rotation angle (0 to 360 in 5-degree steps for speed, then 1-degree steps near any close calls), rotate the wheel about its axis (Z-axis through the post centre), compute boolean intersection with the frame, and verify volume < 0.01mm^3.

**Simplified alternative:** Verify the wheel tip circle diameter + 2*tooth_addendum is less than the cavity dimension in both X and Z axes. This is a conservative bounding check that avoids expensive boolean operations.

### 2.2 Worm Rotation Clearance

**What:** The worm must rotate freely within the cavity. The cylindrical worm has a constant tip diameter, so it suffices to check that the worm tip circle clears the cavity in Z (vertical).

**Criterion:** `frame.box_inner - worm.tip_diameter >= 0.4mm` (0.2mm per side).

**Test approach:** Parametric check. For extra confidence, in the assembled model, rotate the peg head + worm by 90-degree increments about its axis and verify no intersection with the frame.

### 2.3 Peg Head Rotation Clearance (Cap vs Frame)

**What:** The peg head cap sits outside the frame and must not foul against adjacent housings or the frame end when rotated.

**Criterion:** The peg cap swept circle (8.5mm diameter) must not overlap with any adjacent housing structure or frame end section.

**Test approach:** Compute the peg cap centre position and verify that `cap_diameter/2` is less than the distance to the nearest frame wall or adjacent housing edge.

### 2.4 Multi-Gang Uniform Spacing

**What:** In a 5-gang assembly, all tuner-to-tuner spacings must be equal to `tuner_pitch`.

**Criterion:** For each adjacent pair of housings, the Y-distance between equivalent component centres equals `tuner_pitch` within 0.01mm.

**Test approach:** Build a 5-gang assembly. For each pair of adjacent string posts, measure Y-distance between bounding box centres. Verify all four spacings equal `tuner_pitch`.

## 3. Wall Thickness and Structural Integrity

### 3.1 Minimum Wall Around Post Bearing Hole (Top Plate)

**What:** The post bearing hole (5.05mm) is drilled through the 1.1mm top plate. The remaining annular ring of the mounting plate around the hole must have sufficient material.

**Criterion:** The frame outer dimension minus the hole diameter, divided by 2, gives the minimum wall: `(box_outer - post_bearing_hole) / 2 >= 2.0mm`. This should be at least 2mm for structural integrity.

**Test approach:** Parametric check from config values.

### 3.2 Minimum Wall Around Worm Entry Hole (Side Wall)

**What:** The worm entry hole (7.2mm) is drilled through a 10mm x 10mm side face. The remaining material above and below the hole is critical for frame rigidity.

**Criterion:** `(box_outer - worm_entry_hole) / 2 >= 1.0mm`. The hole must leave at least 1mm of material above and below.

**Test approach:** Parametric check. Also verify geometrically that the hole doesn't break through the top or bottom plates by checking `worm_entry_hole/2 + wall_thickness <= box_outer/2`.

### 3.3 Minimum Wall Around Peg Bearing Hole (Opposite Side Wall)

**What:** The peg bearing hole (4.05mm) on the opposite side wall. This is a smaller hole so less critical, but should still be checked.

**Criterion:** `(box_outer - peg_bearing_hole) / 2 >= 2.5mm`.

**Test approach:** Parametric check.

### 3.4 DD Section Wall Thickness (String Post)

**What:** The DD section of the string post has an M2 tapped hole (1.6mm drill) running axially through a 3.5mm diameter shaft with 0.5mm flats cut into it. The minimum wall between the tap bore and the flat surface is critical.

**Criterion:** `(dd_cut.across_flats - tap_bore_diameter) / 2 >= 0.4mm`. Currently: (2.5 - 1.6) / 2 = 0.45mm. This is marginal.

**Test approach:** Parametric check. Flag a warning if wall drops below 0.5mm.

### 3.5 DD Section Wall Thickness (Wheel Bore)

**What:** The wheel has a DD bore (3.5mm diameter with 0.5mm flats). The minimum wall between the DD bore flat and the wheel root circle determines whether the wheel hub is structurally sound.

**Criterion:** `(wheel.root_diameter - wheel.bore.diameter) / 2 >= 0.5mm`. The hub wall from bore OD to tooth root must have sufficient material.

**Test approach:** Parametric check from gear JSON values.

### 3.6 Worm Thread Root to Shaft Core

**What:** The worm thread is cut into the peg head shaft. The root diameter defines the remaining core. The shaft bearing section must not be larger than the root diameter or the thread form would be incomplete at the bearing transition.

**Criterion:** `peg_head.shaft_diameter <= worm.root_diameter`. Currently 4.0mm <= 4.3mm.

**Test approach:** Parametric check.

### 3.7 Housing Wall Integrity After All Drilling

**What:** Each housing has four holes drilled through it (top, bottom, two sides). After all boolean operations, the housing walls must still form a continuous rigid box. No two holes should overlap or break through into each other.

**Criterion:** Build a single-housing frame and verify it has at least 6 distinct face groups (top, bottom, 4 sides minus holes). Verify the frame volume is within expected range (solid box minus expected hole volumes minus cavity).

**Test approach:** Build the frame, compute volume, compare against analytical estimate. The analytical volume = outer_box - inner_cavity - holes. If the actual volume is less than expected by more than 5%, a hole is cutting through a wall.

## 4. Retention and Assembly Constraints

### 4.1 Screw Thread Engagement Depth (String Post)

**What:** The M2 screw into the string post tap bore must have sufficient thread engagement for reliable retention under string tension.

**Criterion:** `thread_length >= 2 * thread_major_diameter`. For M2: engagement >= 4mm (2 * 2.0mm). Currently 4.0mm -- exactly at minimum.

**Test approach:** Parametric check.

### 4.2 Screw Thread Engagement Depth (Peg Head)

**What:** The M2 screw into the peg head tap bore.

**Criterion:** `peg_head.tap_depth >= 2 * 2.0mm = 4.0mm`. Currently 3.0mm -- below the 2D rule of thumb. Flag as a note (acceptable because string tension provides the primary retention force for the peg, not the screw).

**Test approach:** Parametric check with advisory warning.

### 4.3 Washer Coverage Over Bearing Hole

**What:** Retention washers must overlap the bearing hole edge sufficiently to prevent pull-through under load.

**Criterion:**
- Peg washer: `(washer_od - peg_bearing_hole) / 2 >= 0.5mm`. Currently (5.5 - 4.05) / 2 = 0.725mm.
- Post washer: washer OD > wheel bore diameter.

**Test approach:** Parametric check.

## 5. LH/RH Symmetry

### 5.1 Mirror Geometry Verification

**What:** The LH assembly must be an exact mirror of the RH assembly. All bounding box dimensions must match; only X-coordinates should be negated.

**Criterion:** For each component, `LH.bbox.size == RH.bbox.size` within 0.01mm. LH component X-centres should equal `-1 * RH component X-centres`.

**Test approach:** Build both RH and LH 1-gang assemblies. Compare bounding box dimensions for each part. Verify X-coordinate reflection.

## Priority Order for Implementation

1. **3.4 DD section wall thickness** -- most critical, currently marginal at 0.45mm
2. **1.2 Centre distance (geometric)** -- tighten the existing 2mm tolerance test
3. **3.2 Wall around worm entry hole** -- large hole in small section
4. **2.1 Wheel rotation clearance** -- functional correctness
5. **1.1 Worm engagement length** -- gear performance
6. **3.7 Housing wall integrity** -- structural validation
7. **1.3 CD fits within housing** -- layout check
8. **2.4 Multi-gang spacing** -- manufacturing accuracy
9. **4.1-4.3 Retention checks** -- assembly robustness
10. **5.1 LH/RH symmetry** -- variant correctness
11. **2.2-2.3 Worm and peg rotation** -- less critical (mostly parametric)
12. **3.1, 3.3, 3.5, 3.6** -- supplementary wall checks
