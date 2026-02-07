# **Master Engineering Specification: Historic Tuner Restoration**

## **1\. System Overview**

* **Product:** 5-Gang Tuning Machine Assembly (Historic Reproduction).
* **Variants:** Right Hand (RH) and Left Hand (LH).
* **Mechanism:** Single-start Worm Drive (Sandwich Assembly).
  * **RH Unit:** Right-Hand (Clockwise) Thread.
  * **LH Unit:** Left-Hand (Counter-Clockwise) Thread.
  * *Goal:* Symmetrical tuning action (turning knobs "up" towards the headstock tip always tightens the string).
* **Manufacturing Strategy:**
  * **Frame:** Subtractive machining from **10.35mm² Brass Box Section** (1.1mm walls).
  * **Peg Head + Worm:** Investment cast as single piece, finish-machined.
  * **String Post:** Swiss Screw Machining (Auto-Lathe).
  * **Wheel:** Custom generated (separate, mates with string post).
* **Repairability:** Fully disassembleable (no soldered lids).
* **Design Constraint:** External frame geometry (outline, cutouts, mounting holes) is fixed to match historic appearance. Internal components (worm, wheel, posts) may be adjusted for function.

---

## **1a\. Parametric Build Configuration**

The build123d script shall support the following parameters:

### **Frame Parameters**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `box_outer` | 10.0mm | Outer dimension of square tube |
| `wall_thickness` | 1.1mm | Wall thickness (fixed manufacturing constraint) |
| `housing_length` | 16.2mm | Length of each rigid box section |
| `end_length` | 10.0mm | Length from frame end to first/last housing edge (symmetric) |
| `num_housings` | 5 | Number of tuner positions (1 to N) |
| `tuner_pitch` | 27.2mm | Center-to-center spacing between adjacent tuners |
| `total_length` | *computed* | = 2 * end_length + housing_length + (num_housings - 1) * pitch |

**Note:** `total_length` is computed from the other parameters, ensuring symmetric ends regardless of the number of housings.

### **Tolerance Profiles**
| Profile | Bearing Holes | Clearance Holes | Use Case |
|---------|---------------|-----------------|----------|
| `production` | +0.05mm (reamed) | +0.20mm | Machined brass, 100N rated |
| `prototype_resin` | +0.10mm | +0.20mm | 1:1 resin print validation |
| `prototype_fdm` | +0.20mm | +0.30mm | 2:1 FDM functional test |

*Bearing holes are derived: shaft diameter + bearing_clearance (0.05mm). Clearance holes: worm entry = shoulder + clearance, wheel inlet (5.1mm).*

### **Scale Parameter**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `scale` | 1.0 | Geometry scale factor (use 2.0 for FDM prototype) |

*Note: When `scale=2.0`, all dimensions are doubled. The script outputs both RH and LH variants at the specified scale.*

## **2\. Component A: The Reinforced Frame**

* **Material:** CZ121 Brass Box Section (10.0mm x 10.0mm x 1.1mm wall).
* **Total Length:** 145.0mm.
* **Internal Cavity:** 7.8mm x 7.8mm (10.0mm outer - 2×1.1mm walls).
* **End Length:** 10.0mm from frame end to first/last housing edge (symmetric ends).
* **Topology:**
  * **5x Rigid Housings:** 16.2mm long sections of full box profile to resist gear tension.
  * **Connectors:** Walls milled away between housings, leaving only the **Mounting Plate** (1.1mm thick) at Z=0 to connect the unit.
  * **Tuner Pitch:** 27.2mm center-to-center spacing between adjacent tuners.
* **Hand Identification:** "R" or "L" etched on inside surface of mounting plate (3mm tall, 0.3mm deep) near frame end at Y=2mm. Visible from below when looking into mechanism cavity.

### **Coordinate System**

```
     PLAYER'S VIEW (looking down at installed tuner)
     ================================================

        ↑ Posts stick up into air (+Z direction)
        |
   ─────┴─────  Z=0: Mounting plate (TOP, visible from above)
   │ mechanism │     - Mounting screw holes
   │  cavity   │     - Post bearing holes (posts emerge upward)
   │    ●────→ │     - "R"/"L" etching on INSIDE (Z=-1.1 surface)
   └───────────┘  Z=-10.0: Bottom (embedded in headstock)
        |              - Wheel inlet hole ONLY (for assembly)
        ↓
     [WOOD CAVITY]

   Z-axis convention:
   - Z=0        : Mounting plate surface (visible, sits on headstock)
   - Z=-1.1     : Inside surface of mounting plate (where "R"/"L" goes)
   - Z=-8.9     : Inside surface of bottom plate
   - Z=-10.0    : Bottom surface (inside wood cavity)
```

| Item | Z Location | Notes |
|------|------------|-------|
| Mounting plate surface | Z=0 | Visible from above |
| Mounting holes | Z=0 to Z=-1.1 | Drilled through top plate |
| Post bearing holes | Z=0 to Z=-1.1 | ø = post bearing_diameter + bearing_clearance |
| "R"/"L" etching | Z=-1.1 | Inside surface of mounting plate |
| Worm entry (RH) | RIGHT side (+X) | ø = peg shoulder_diameter + bearing_clearance |
| Peg bearing (RH) | LEFT side (-X) | ø = peg shaft_diameter + bearing_clearance |
| Wheel inlet | Z=-10.0 | Bottom plate, for assembly |

### **Mounting Holes**

* **Quantity:** 6 holes
* **Diameter:** ø3.0mm (clearance for mushroom-head bolts)
* **Location:** Bottom plate, in the gap sections between housings

| Hole # | Y Position (from frame start) | Description |
|--------|-------------------------------|-------------|
| 1 | 5.0mm | Before Housing 1 (centered in 0-10mm gap) |
| 2 | 31.7mm | Between Housing 1 & 2 |
| 3 | 58.9mm | Between Housing 2 & 3 |
| 4 | 86.1mm | Between Housing 3 & 4 |
| 5 | 113.3mm | Between Housing 4 & 5 |
| 6 | 140.0mm | After Housing 5 (centered in 135-145mm gap) |

### **Housing Positions (Symmetric)**

Housing positions are calculated to ensure symmetric 10mm ends:
- First center = (total_length - (num_housings - 1) * pitch) / 2 = (145 - 108.8) / 2 = 18.1mm

| Housing # | Center Y Position | Description |
|-----------|-------------------|-------------|
| 1 | 18.1mm | First tuner |
| 2 | 45.3mm | Second tuner |
| 3 | 72.5mm | Third tuner (frame center) |
| 4 | 99.7mm | Fourth tuner |
| 5 | 126.9mm | Fifth tuner |

### **The "Sandwich" Drilling Pattern (Per Housing)**

To enable assembly without soldering:

1. **Bottom Face (Wheel Inlet):** ø5.1mm through-hole.
   * *Function:* Allows M2 washer/screw access for post retention. Wheel slides in sideways from open frame end.
2. **Top Face (Post Bearing):** bearing_diameter + bearing_clearance through-hole (reamed).
   * *Function:* Acts as the journal bearing for the String Post (5.0mm shaft, +0.05mm clearance).
3. **Side Faces (Worm Axle):** Asymmetric through-holes.
   * **Entry Side:** shoulder_diameter + bearing_clearance (shoulder must clear worm tip).
   * **Bearing Side:** shaft_diameter + bearing_clearance (reamed).
   * *Note:* For RH frame, entry is on RIGHT side (+X). LH frame is mirrored.
   * *Retention:* Cap (8.5mm) sits against frame exterior, cannot pass through entry hole.

## **3\. Component B: The Gear Set**

* **Constraint:** Wheel slides in sideways from open frame end (worm must be installed first for globoid meshing).
* **Module:** **0.6** (M0.6)
* **Pressure Angle:** **20°**

**IMPORTANT:** All gear parameters (ratio, center distance, diameters, tooth counts) are defined in `config/<profile>/worm_gear.json`. The JSON file is the **source of truth** for gear geometry. Do not hardcode gear values in code or tests—always load from the JSON.

### **1\. Worm (Driver) - Integral to Peg Head**

The worm thread is cast/machined as part of the peg head assembly (not a separate gear).

* **Reference geometry:** `config/<profile>/worm_m0.6_z1.step` (for tooth profile)
* **Parameters:** Loaded from `config/<profile>/worm_gear.json` → `worm` section
* **Hand:** Right (LH variant uses left-hand worm)
* **Material:** Brass (cast with peg head)

Key parameters from JSON:
- `tip_diameter_mm` - Outer diameter
- `pitch_diameter_mm` - For center distance calculation
- `type` - Cylindrical or globoid

*Note: Worm STEP file provides reference geometry for machining the thread on the cast peg head shaft.*

### **2\. Worm Wheel (Driven) - Separate Part**

* **Source:** `config/<profile>/wheel_m0.6_z<N>.step` (N = tooth count from JSON)
* **Parameters:** Loaded from `config/<profile>/worm_gear.json` → `wheel` section
* **Bore:** DD cut (from `features.wheel` in JSON)
* **Material:** Brass

Key parameters from JSON:
- `num_teeth` - Tooth count (determines ratio)
- `tip_diameter_mm` - Outer diameter
- `pitch_diameter_mm` - For center distance calculation
- `features.wheel.bore_diameter_mm` - DD cut bore diameter

The wheel is a separate component that slides onto the string post and enables sandwich assembly.

### **DD Cut Bore Interface (Wheel Only)**

DD cut parameters are defined in `config/<profile>/worm_gear.json` → `features.wheel`:
- `bore_diameter_mm` - Bore diameter (mates with string post DD section)
- `anti_rotation` - Type of anti-rotation feature (ddcut)

The DD cut is created by milling two parallel flats on the string post shaft.

### **Center Distance Calculation**

Center distance is defined in `config/<profile>/worm_gear.json` → `assembly.centre_distance_mm`.

Formula: CD = (Worm PD + Wheel PD) / 2 (may vary with profile shift)

### **Assembly Parameters**

All assembly parameters are loaded from `config/<profile>/worm_gear.json` → `assembly` section:
- `centre_distance_mm` - Worm-to-wheel axis distance
- `pressure_angle_deg` - Standard 20°
- `backlash_mm` - Configurable backlash
- `ratio` - Gear ratio (equals wheel tooth count for single-start worm)

## **4\. Component C: The Peg Head Assembly**

The peg head, shaft, and worm thread are cast as a single brass piece, then finish-machined. This provides maximum strength and eliminates the need for a separate worm gear.

### **Peg Head Geometry (from Onshape model)**

| Dimension | Variable | Value | Description |
|-----------|----------|-------|-------------|
| Ring OD | headouterd | 12.5mm | Outer diameter of peg head ring |
| Ring Bore | headinnerd | 9.8mm | Inner bore diameter (finger grip) |
| Ring Width | headthicknessattop | 2.4mm | Width of ring at outer edge (after face cuts) |
| Bore Offset | headinneroffset | 0.25mm | Bore center offset from ring center |
| Chamfer | smoothedges | 0.3mm | Edge chamfer on ring faces |
| Button Diameter | capd | 8.0mm | Decorative end button |
| Button Height | capl | 1.0mm | Height of decorative button |

*Note: The peg head ring is created using a revolved profile construction. The hollow bore (~9.8mm) provides finger grip for fine tuning.*

### **Ring Construction (Reference STEP)**

The peg head geometry is imported from a reference STEP file (`reference/peghead-and-shaft.step`) exported from Onshape, then combined with a new shaft and worm thread.

**Construction steps:**
1. **Import peg head STEP:** Contains ring, pip, join, cap, and shoulder
2. **Cut at Z=0:** Keep only Z ≤ 0 (peg head portion), discard original shaft
3. **Add new shaft:** 4.0mm diameter (bearing section)
4. **Add worm thread:** Import from `config/<profile>/worm_m0.6_z1.step`, position at Z=0
5. **Add M2 tap hole:** At shaft end for retention screw

**Reference STEP orientation:** Shaft along Z, peg head at Z ≤ 0
**Assembly orientation:** Rotated -90° around Y so shaft is along X, pip at -X

### **Integral Shaft + Worm (Combined from STEP files)**

The peg head and worm are combined from reference STEP files with a new shaft section.

| Section | Diameter | Length | Z Position | Description |
|---------|----------|--------|------------|-------------|
| Peg head | - | - | Z ≤ 0 | Imported from STEP (ring, pip, cap, shoulder) |
| Worm thread | 7.0mm OD / 4.0mm shaft | 7.6mm | Z = 0 to 7.6 | From `manufacturing.worm_length_mm` in JSON |
| Bearing shaft | 4.0mm | 1.3mm | Z = 7.6 to 8.9 | Through bearing wall (1.1mm) + axial play (0.2mm) |
| M2 tap hole | 1.6mm | 4mm deep | At Z = 8.9 | Retention screw |

**Total shaft length:** 8.9mm (from Z=0 to Z=8.9)

**Key dimensions:**
- Worm length from `manufacturing.worm_length_mm` in JSON (7.6mm)
- Shaft diameter (4.0mm) < worm root (4.3mm) → worm fits over shaft
- Shaft (4.0mm) fits in peg bearing hole (shaft + clearance) → 0.05mm clearance
- Cap (8.5mm) > worm entry hole (shoulder + clearance) → stops push-in

### **Worm Thread Geometry**

The worm thread is imported from `config/<profile>/worm_m0.6_z1.step`:

All worm parameters are loaded from `config/<profile>/worm_gear.json` → `worm` section:

* **Type:** From `worm.type` (cylindrical or globoid)
* **Outer Diameter (tip):** From `worm.tip_diameter_mm`
* **Pitch Diameter:** From `worm.pitch_diameter_mm`
* **Root Diameter:** From `worm.root_diameter_mm` (shaft must be ≤ this)
* **Shaft Diameter:** 4.0mm (fixed, must be < worm root)
* **Length:** From `manufacturing.worm_length_mm` (7.6mm)
* **Lead:** From `worm.lead_mm` (π × module)
* **Lead Angle:** From `worm.lead_angle_deg`

### **Shaft Retention**

* **Push-in prevention:** Cap (8.5mm) sits against frame exterior, cannot pass through entry hole
* **Pull-out prevention:** M2 × 4mm pan head screw + washer on bearing shaft end
  * Washer: 5.5mm OD, 2.7mm ID, 0.5mm thick (larger than peg bearing hole)
  * Screw head OD: ~3.8mm (holds washer in place)
  * Total protrusion: ~1.8mm beyond shaft end

### **Peg Head Assembly Sequence**

1. Cast peg head with integral shaft (rough form)
2. Finish-turn shaft to 4.0mm bearing diameter
3. Machine worm thread (reference STEP geometry)
4. Tap M2 hole in shaft end
5. Insert assembly through frame (worm enters entry hole, shaft exits bearing hole)
6. Place washer (5.5mm OD) on shaft end
7. Thread M2 × 4mm pan head screw into shaft end to retain

### **Disassembly for Repair**

1. Remove M2 screw from shaft end
2. Slide peg head + worm assembly out through entry hole
3. Replace entire peg head assembly if needed
4. Reassemble

### **Manufacturing**

**Investment cast + finish machine:**
1. Investment cast peg head + shaft + rough worm form in brass
2. Finish-turn shaft sections to final dimensions
3. Machine globoid worm thread (single-point or form tool)
4. Tap M2 hole in shaft end

*Note: The worm thread may be cast near-net-shape and only require cleanup, or may be machined from a plain shaft section depending on casting capability.*

## **5\. Component D: The String Post (Vertical)**

* **Manufacturing:** Swiss Sliding Head Lathe (Swiss Auto) or manual lathe.
* **Stock:** 8.0mm round brass/steel bar.
* **Cap:** Decorative 7.5mm cap with 0.25mm fillet edges and 3 concentric V-grooves (0.33mm wide/deep, outer OD 6mm).
* **Top Section:** 6.0mm visible post (runs in the Top Face hole).
* **Frame Bearing:** 5.0mm shaft (runs in ø5.05mm frame hole).
* **Gear Interface:** DD cut section (bore dia minus 0.1mm clearance) for slip-fit rotational location in wheel bore. Compression retention via M2 washer+screw.
* **Retention:** M2 tap bore in bottom of DD section for nut + washer.
* **String Hole:** ø1.5mm cross-hole, centered in visible post (2.75mm from frame top).

### **String Post Dimensions (Bottom to Top)**

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| DD cut (wheel interface) | bore_dia - `dd_shaft_clearance` | *derived* | = `wheel.face_width` - `dd_cut_clearance` |
| M2 tap bore | ø1.6mm | 4mm deep | Tapped hole in bottom of DD for retention |
| Frame bearing | 5.0mm | *derived* | = `wall_thickness + axial_play` (1.2mm) |
| Visible post | 6.0mm | 5.5mm | Above frame, aesthetic |
| String hole | ø1.5mm | through | Cross-drilled, centered in post (2.75mm from frame) |
| Cap | 7.5mm | 1.0mm | 0.25mm fillet top/bottom, 3× V-grooves (0.33mm, outer OD 6mm) |

**Derived lengths:**
- `bearing_length` = `wall_thickness` (1.1mm) + `post_bearing_axial_play` (0.1mm) = **1.2mm**
- `dd_cut_length` = `wheel.face_width` - `dd_cut_clearance` (e.g. 7.6 - 0.5 = **7.1mm**)

**Total length:** cap + post + bearing + DD = 1.0 + 5.5 + 1.2 + dd_cut_length (e.g. **14.8mm**)

### **DD Cut Shaft Interface**

The string post DD cut section provides rotational location in the wheel's DD bore. The shaft DD is undersized by `dd_shaft_clearance` (0.1mm) for a slip fit; compression from the M2 washer+screw provides retention force. DD bore dimensions are loaded from `features.wheel.bore_diameter_mm` in `worm_gear.json`:

* **Bore diameter:** from JSON `bore_diameter_mm` (e.g. 3.5mm)
* **Shaft diameter:** bore_diameter - `dd_shaft_clearance` (e.g. 3.4mm)
* **Flat depth:** 0.5mm (each side)
* **Shaft across flats:** bore AF - `dd_shaft_clearance` (e.g. 2.4mm)
* **Length:** = `wheel.face_width` - `dd_cut_clearance` (e.g. 7.6 - 0.5 = 7.1mm)
* **Bottom gap:** `dd_cut_clearance` (0.5mm) — compression travel for washer clamping

### **M2 Tap Bore Retention**

The DD section has an M2 tapped hole drilled up from the bottom:

* **Tap drill:** ø1.6mm (for M2 thread)
* **Depth:** 4mm (for standard M2 × 4mm screw)
* **Hardware:** M2 × 4mm machine screw + M2 washer (~5mm OD)

An M2 screw threads into the tap bore from below, with a washer to retain the wheel.

### **String Post Retention**

* **Pull-up prevention:** 7.5mm cap cannot pass through 5.05mm frame hole
* **Pull-down prevention:** M2 screw + washer in tap bore
  * Washer OD: ~5mm (larger than DD bore from JSON)
  * Screw holds washer in place
* **Wheel retention:** Bearing shoulder above wheel, M2 screw + washer below wheel

### **String Post Assembly Sequence**

**Assembly Constraints:**
- Worm MUST be installed first (required for globoid meshing, recommended for cylindrical)
- Wheel OD (from JSON) cannot fit through post bearing hole - insert separately

1. Install peg head (worm) first - secure with M2 screw + washer
2. Slide wheel sideways into cavity from open frame end (meshes with worm)
3. Insert string post from above through bearing hole (ø5.05mm)
4. DD section engages wheel bore, creating the sandwich
5. Tap M2 thread into post (stronger with wheel supporting the DD section)
6. Thread M2 screw + washer through bottom hole (ø5.1mm) into tap bore

## **5a. Post/Wheel/Frame Sandwich Mechanism**

The string post and wheel rotate as a unit. The frame is NOT clamped between them—instead, the frame floats with axial clearance.

### Clamping Mechanism

When the M2 retention screw is tightened:
1. Screw pulls wheel upward toward post
2. Wheel rises until it contacts the **5mm→3.5mm shoulder** on the post
3. Post shoulder (6mm→5mm) rests on frame top surface
4. Frame floats between these two reference points with axial play

### Cross-Section (Y-Z plane through post axis)

```
                    ┌─────────────────┐
                    │   POST (6mm)    │
POST SHOULDER ══════╧═════════════════╧══════  ← rests on frame top (Z=0)
─────────────────────────────────────────────  FRAME TOP SURFACE
░░░░░░░░░░░░░░░░░░░░│░░░░░░░░░░░░░░░░░░░░░░░  wall (1.1mm)
─────────────────────│───────────────────────  CAVITY CEILING (Z=-1.1)
                     │ bearing (5mm Ø)
                     │    ↕ axial_play        ← FREE GAP (frame floats here)
    ─────────────────┼───────────────────────  CLAMP SHOULDER (Z=-1.2)
                     │ DD section (3.5mm)     ↑
                ┌────┴────┐                   │ wheel pulled up by screw
                │  WHEEL  │                   │
                │         │                   │
        ────────┴─────────┴────────           ← CAVITY FLOOR (5.1mm inlet hole)
                     │
                   [M2 screw + washer from below]
```

**Note:** Wheel sits in cavity (wheel OD from JSON > 5.1mm inlet hole). The 5.1mm inlet hole provides access for M2 screw + washer to retain the post. Wheel is constrained by clamp shoulder above and cavity floor below.

### Parametric Constraints

| Parameter | Formula | Value |
|-----------|---------|-------|
| `wall_thickness` | design choice | 1.1mm |
| `post_bearing_axial_play` | design choice | 0.1mm |
| `wheel.face_width` | from gear config | 7.5-7.6mm |
| `dd_shaft_clearance` | design choice | 0.1mm |
| `dd_cut_clearance` | design choice | 0.5mm |
| `bearing_length` | `wall_thickness + axial_play` | 1.2mm |
| `dd_cut_length` | `wheel.face_width - dd_cut_clearance` | 7.1-7.2mm |

**Key points:**
- `axial_play` is a design choice (0.1mm provides free rotation)
- Wheel sits in cavity (wheel OD from JSON > 5.1mm hole); enters sideways from open frame end
- DD cut is 0.1mm shorter than wheel to ensure screw clamps wheel to shoulder
- Bearing length > wall thickness ensures axial play exists

### Why This Works

- **Axial play** allows free rotation without binding
- **Bearing section > wall** positions the clamp shoulder inside cavity
- **DD cut = wheel width** ensures full anti-rotation engagement
- **Frame floats** on the bearing with clearance, never clamped

## **6\. Manufacturing Process (Step-by-Step)**

### **Phase 1: Frame Machining (Mill/Drill)**

1. **Cut Stock:** Cut 10.0mm Box section to 145mm.
2. **Mill Profile:** Clamp stock. Mill away the Top and Side walls in the "Gap" sections to create the 5 isolated boxes.
3. **Drill Vertical:**
   * Drill & ream post bearing holes on Top Face (bearing_diameter + bearing_clearance).
   * Drill **ø5.1mm** wheel inlet holes on Bottom Face (M2 washer access).
   * Drill **ø3.0mm** mounting holes on Bottom Plate at specified Y positions.
4. **Drill Horizontal (Asymmetric):**
   * Drill worm entry holes on one side (shoulder_diameter + bearing_clearance).
   * Drill & ream peg shaft bearing holes on opposite side (shaft_diameter + bearing_clearance).
5. **Finish:** Deburr internal edges.

### **Phase 2: Wheel Production**

The wheel is manufactured from STEP file generated by gear calculator:

* **Source:** `config/<profile>/wheel_m0.6_z<N>.step` (N = tooth count from JSON)
* Tooth count and width from `worm_gear.json`
* DD cut bore from `features.wheel.bore_diameter_mm` (built into STEP)

*Note: Worm is integral to peg head casting - see Phase 3.*

### **Phase 3: Peg Head + Worm Production**

Investment cast peg head with integral shaft and worm thread:

1. Investment cast peg head + shaft + rough worm form in brass
2. Finish-turn shaft to 4.0mm bearing diameter
3. Machine worm thread (reference `config/<profile>/worm_m0.6_z1.step` for geometry)
4. Tap M2 hole in shaft end

*Note: Casting the worm integral with the shaft provides maximum strength.*

### **Phase 4: String Post Production**

1. Turn from **8mm brass/steel bar:**
   * 7.5mm cap (1mm high, 0.25mm fillet, 3× V-grooves)
   * 6mm visible post (5.5mm high)
   * 5mm frame bearing section (1.2mm, through frame + axial play)
   * DD cut gear interface (bore_dia - 0.1mm clearance, slip fit in wheel bore)
   * M2 tap bore (~4mm deep, for screw retention)
2. Mill DD flats on shaft section (undersized for slip fit)
3. Tap M2 hole in bottom
4. Cross-drill ø1.5mm string hole (2.75mm from frame top)

### **Phase 5: Assembly (The "Sandwich" Logic)**

**Assembly order: Worm → Wheel → Post** (worm must be in place first for globoid meshing).

1. **Install Peg Head (Worm):** Slide **Peg Head + Worm** through **Entry Hole**. The ø4.0mm shaft passes through opposite **Bearing Hole**.
2. **Secure Peg Head:** Place **5.5mm washer** on shaft end, thread **M2 × 3mm pan head screw** to retain.
3. **Insert Wheel:** Slide **Worm Wheel** sideways into cavity from open frame end. Wheel OD (from JSON) cannot fit through post bearing hole - must insert separately.
4. **Insert Post:** Slide **String Post** from above through **Top Hole**. DD section engages wheel bore.
5. **Tap Post:** Drill and tap M2 hole in post (stronger with wheel supporting DD section).
6. **Secure Post:** Thread **M2 × 3mm screw + washer** through **Bottom Hole** (ø5.1mm) into post tap bore.
7. **Complete:** Peg head secured with M2 screw + washer, post secured with M2 screw + washer.

## **7\. The Left Hand (LH) Variant**

* **Geometry:** The LH Frame is a **Mirror Image** of the RH Frame.  
* **Functional Inversion:**  
  * **Worm:** Uses **Left-Hand (CCW) Thread**.  
  * **Wheel:** Uses **Left-Hand Helix**.  
  * **Result:** Turning the knob in the *symmetrical* direction relative to the headstock produces the *same* tensioning result (tightening). This mimics high-end historic instruments.

## **8\. Derived Dimensions for Manufacture**

* **Center Distance (CD):** Distance from Worm Axis to Post Axis.
  * Loaded from `config/<profile>/worm_gear.json` → `assembly.centre_distance_mm`
  * Formula: CD = (Pitch Dia Worm + Pitch Dia Wheel) / 2 (may vary with profile shift)
* **Vertical Alignment:** (using Section 2 coordinate system: Z=0 at mounting plate)
  * Internal Cavity: Z = -1.1mm (ceiling) to Z = -8.9mm (floor), height = 7.8mm.
  * Worm Axis Height: **Z = -5.0mm** (Centered in cavity).
  * Worm Clearance: 7.8mm cavity - 7.0mm worm OD = **0.8mm total** (0.4mm top/bottom).
  * Wheel Pitch Plane: **Z = -5.0mm** (Must align with worm).
* **Horizontal Hole Offset:**
  * Post Axis (top/bottom holes): X = 0 (centered on frame width).
  * Worm Axis (side holes): Offset from post axis by **CD** (= `assembly.centre_distance_mm` from JSON).
  * *Note:* Frame is 10.0mm wide, internal cavity is 7.8mm. Worm axis at X = CD from post axis places the side holes off-center.

### **Y-Axis Offset for Worm/Wheel Engagement**

The worm and wheel axes are offset from the housing center along Y to achieve proper center distance while centering the mechanism within each housing. This also provides a preload mechanism where string tension takes up backlash.

```
     HOUSING (16.2mm along Y)
     ========================

     Y=0 end (toward nut/bridge)              Y=145 end
     String pulls this way ←
       |                                           |
       |    POST        WORM                       |
       |      │    CD      │                       |
       |      │<---------->│                       |
       |      ●            ●                       |
       |   -CD/2       +CD/2                       |
       |      from housing center                  |
       |                                           |

     String tension pulls post toward -Y.
     Post pivots at top bearing, wheel (at bottom) swings +Y into worm.
```

| Item | Y Position | Notes |
|------|------------|-------|
| Housing center | housing_y | Computed from frame parameters |
| Post axis | housing_y - CD/2 | Offset toward -Y (nut end) |
| Worm axis | housing_y + CD/2 | Offset toward +Y (bridge end) |
| Center distance (CD) | from JSON | `assembly.centre_distance_mm` in worm_gear.json |
| Extra backlash | configurable | Parameter for additional play beyond gear design |

**Preload mechanism:** String tension pulls the string post toward -Y (toward the nut/bridge). The post pivots at its top bearing, causing the wheel (at the bottom of the post) to swing toward +Y, pushing into the worm and taking up backlash.

**Both RH and LH variants:** Use the same offset directions (post toward -Y, worm toward +Y from housing center).

---

## **9\. Geometry Validation Checklist**

Before manufacturing, verify (values loaded from `worm_gear.json`):

- [x] Worm OD fits within internal cavity height (7.8mm) with clearance
- [x] Worm OD passes through entry hole with clearance
- [x] Peg head shaft (4.0mm) fits in bearing hole (shaft + clearance) ✓ 0.05mm clearance (reamed)
- [x] Wheel OD enters sideways from open frame end (worm first for globoid) ✓
- [x] Post shaft (5.0mm) fits in top bearing hole (5.05mm) ✓ 0.05mm clearance (reamed)
- [x] Post cap (7.5mm) stops pull-through top hole (5.05mm) ✓
- [x] Peg head cap (8.5mm) stops pull-in through entry hole ✓
- [x] M2 screw + washer (5.5mm OD) stops peg pull-out through bearing hole ✓
- [x] Center distance (from JSON) fits within frame geometry ✓
- [x] Sandwich assembly sequence verified ✓
- [x] Worm integral to peg head casting ✓
- [x] DD cut bore in wheel (from JSON) for string post ✓
- [x] M2 thread passes through wheel DD across-flats ✓
- [x] M2 washer retains wheel (larger than DD bore) ✓
- [x] Custom wheel STEP file generated ✓

### **Gear Mesh Validation**

All gear parameters are validated from `config/<profile>/worm_gear.json`:

| Parameter | Check |
|-----------|-------|
| Module | Worm and wheel must match (0.6) |
| Center Distance | Loaded from `assembly.centre_distance_mm` |
| Pressure Angle | Standard 20° |
| Ratio | Equals `wheel.num_teeth` for single-start worm |
| Worm Type | From `worm.type` (cylindrical or globoid) |

### **Hardware List (per tuner)**

| Item | Specification | Qty |
|------|---------------|-----|
| Peg head + worm | Cast brass, integral worm (type from JSON), 4.0mm shaft | 1 |
| Worm wheel | Custom STEP from `config/<profile>/`, M0.6, params from JSON | 1 |
| Peg retention screw | M2 × 4mm pan head | 1 |
| Peg retention washer | 5.5mm OD, 2.7mm ID, 0.5mm thick | 1 |
| Post retention screw | M2 × 4mm pan head | 1 |
| Post retention washer | M2 washer (~5mm OD, ~2.2mm ID) | 1 |

### **Source Files**

| File | Description |
|------|-------------|
| `reference/peghead-and-shaft.step` | Complete peg head + shaft reference geometry (from Onshape) |
| `config/<profile>/worm_m0.6_z1.step` | Worm reference geometry (for machining cast shaft) |
| `config/<profile>/wheel_m0.6_z<N>.step` | Worm wheel (N = tooth count from JSON) |
| `config/<profile>/worm_gear.json` | **Source of truth** for all gear parameters |