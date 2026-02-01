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
| `tuner_pitch` | 27.05mm | Center-to-center spacing between adjacent tuners |
| `total_length` | *computed* | = 2 * end_length + housing_length + (num_housings - 1) * pitch |

**Note:** `total_length` is computed from the other parameters, ensuring symmetric ends regardless of the number of housings.

### **Tolerance Profiles**
| Profile | Bearing Holes | Clearance Holes | Use Case |
|---------|---------------|-----------------|----------|
| `production` | +0.05mm (reamed) | +0.20mm | Machined brass, 100N rated |
| `prototype_resin` | +0.10mm | +0.20mm | 1:1 resin print validation |
| `prototype_fdm` | +0.20mm | +0.30mm | 2:1 FDM functional test |

*Bearing holes: post bearing (4.05mm), peg bearing (4.05mm). Clearance holes: worm entry (7.05mm), wheel inlet (8.0mm).*

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
  * **Tuner Pitch:** 27.05mm center-to-center spacing between adjacent tuners.
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
| Post bearing holes | Z=0 to Z=-1.1 | Posts emerge upward (+Z) |
| "R"/"L" etching | Z=-1.1 | Inside surface of mounting plate |
| Worm entry (RH) | RIGHT side (+X) | Larger ø7.05mm hole |
| Peg bearing (RH) | LEFT side (-X) | Smaller ø4.05mm hole |
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

1. **Bottom Face (Wheel Inlet):** ø8.0mm through-hole.
   * *Function:* Allows the Worm Wheel (7.05mm OD) to be inserted from underneath.
2. **Top Face (Post Bearing):** ø4.05mm through-hole (reamed).
   * *Function:* Acts as the journal bearing for the String Post (4.0mm shaft, +0.05mm clearance).
3. **Side Faces (Worm Axle):** Asymmetric through-holes.
   * **Entry Side:** ø7.05mm (worm tip 7.0mm + 0.2mm clearance).
   * **Bearing Side:** ø4.05mm (bearing shaft 4.0mm + 0.05mm clearance, reamed).
   * *Note:* For RH frame, entry is on RIGHT side (+X). LH frame is mirrored.
   * *Retention:* Cap (8.5mm) sits against frame exterior, cannot pass through 7.05mm hole.

## **3\. Component B: The Gear Set**

* **Constraint:** The Worm Wheel must fit through the ø8.0mm hole in the bottom of the frame.
* **Module:** **0.6** (M0.6)
* **Gear Ratio:** **10:1** (single-start worm, 10-tooth wheel)
* **Pressure Angle:** **20°**
* **Worm Type:** **Cylindrical** (default) or **Globoid** (for improved contact)

*Note: Actual gear parameters are loaded from `config/<profile>/worm_gear.json`. Values below are defaults from the "balanced" profile.*

### **1\. Worm (Driver) - Integral to Peg Head**

The worm thread is cast/machined as part of the peg head assembly (not a separate gear).

* **Reference geometry:** `worm_m0.6_z1.step` (for tooth profile)
* **Type:** Cylindrical (default) or Globoid
* **Outer Diameter (tip):** **7.0mm**
* **Pitch Diameter:** 5.8mm
* **Root Diameter:** 4.3mm
* **Length:** **7.8mm** (centered in 7.8mm cavity)
* **Lead:** 1.885mm (π × module)
* **Lead Angle:** 5.9°
* **Hand:** Right (LH variant uses left-hand worm)
* **Material:** Brass (cast with peg head)

*Note: Worm STEP file provides reference geometry for machining the thread on the cast peg head shaft.*

### **2\. Worm Wheel (Driven) - Separate Part**

* **Source:** `wheel_m0.6_z10.step`
* **Teeth:** 10
* **Outer Diameter (tip):** **7.05mm**
* **Pitch Diameter:** 6.0mm
* **Root Diameter:** 4.5mm
* **Bore:** **ø3.25mm DD cut** (double-D for anti-rotation)
* **Face Width:** **7.6mm**
* **Material:** Brass

The wheel is a separate component that slides onto the string post and enables sandwich assembly.

### **DD Cut Bore Interface (Wheel Only)**

* **Wheel bore:** ø3.25mm DD cut → mates with 3.25mm DD cut on string post
* **Flat depth:** ~0.45mm (each side, 14% of diameter)
* **Across flats:** ~2.35mm

The DD cut is created by milling two parallel flats on the string post shaft.

### **Center Distance Calculation**

* CD = (Worm PD + Wheel PD) / 2
* CD = (5.8mm + 6.0mm) / 2 = **5.9mm**

### **Assembly Parameters**

| Parameter | Value |
|-----------|-------|
| Centre Distance | 5.9mm |
| Pressure Angle | 20° |
| Backlash | 0.0mm (configurable) |
| Ratio | 10:1 |

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
| Worm thread | 7.0mm OD / 4.0mm shaft | 7.8mm | Z = 0 to 7.8 | Centered in 7.8mm cavity |
| Bearing shaft | 4.0mm | 1.3mm | Z = 7.8 to 9.1 | Through bearing wall (1.1mm) + axial play (0.2mm) |
| M2 tap hole | 1.6mm | 4mm deep | At Z = 9.1 | Retention screw |

**Total shaft length:** 9.1mm (from Z=0 to Z=9.1)

**Key dimensions:**
- Worm (7.8mm) centered in 7.8mm cavity
- Shaft diameter (4.0mm) < worm root (4.3mm) → worm fits over shaft
- Shaft (4.0mm) fits in peg bearing hole (4.05mm) → 0.05mm clearance
- Cap (8.5mm) > worm entry hole (7.05mm) → stops push-in

### **Worm Thread Geometry**

The worm thread is imported from `config/<profile>/worm_m0.6_z1.step`:

* **Type:** Cylindrical (or Globoid per config)
* **Outer Diameter (tip):** 7.0mm
* **Pitch Diameter:** 5.8mm
* **Root Diameter:** 4.3mm (shaft must be ≤ this)
* **Shaft Diameter:** 4.0mm (0.3mm clearance inside worm)
* **Length:** 7.8mm (centered in 7.8mm cavity)
* **Lead:** 1.885mm (π × module)
* **Lead Angle:** 5.9°

### **Shaft Retention**

* **Push-in prevention:** Cap (8.5mm) sits against frame exterior, cannot pass through 7.05mm entry hole
* **Pull-out prevention:** M2 × 4mm pan head screw + washer on bearing shaft end
  * Washer: 5.5mm OD, 2.7mm ID, 0.5mm thick (larger than 4.05mm bearing hole)
  * Screw head OD: ~3.8mm (holds washer in place)
  * Total protrusion: ~1.8mm beyond shaft end

### **Peg Head Assembly Sequence**

1. Cast peg head with integral shaft (rough form)
2. Finish-turn shaft to 4.0mm bearing diameter
3. Machine worm thread (reference STEP geometry)
4. Tap M2 hole in shaft end
5. Insert assembly through frame (worm enters 7.05mm hole, shaft exits 4.05mm hole)
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
* **Cap:** Decorative 7.5mm cap with chamfered edges.
* **Top Section:** 6.0mm visible post (runs in the Top Face hole).
* **Gear Interface:** 3.5mm DD cut section to mate with Worm Wheel DD bore.
* **Retention:** M2 tap bore in bottom of DD section for nut + washer.
* **String Hole:** ø1.5mm cross-hole, centered in visible post (2.75mm from frame top).

### **String Post Dimensions (Bottom to Top)**

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| DD cut (wheel interface) | 3.25mm DD | *derived* | = `wheel.face_width` (7.5-7.6mm) |
| M2 tap bore | ø1.6mm | 4mm deep | Tapped hole in bottom of DD for retention |
| Frame bearing | 4.0mm | *derived* | = `wall_thickness + axial_play` (1.2mm) |
| Visible post | 6.0mm | 5.5mm | Above frame, aesthetic |
| String hole | ø1.5mm | through | Cross-drilled, centered in post (2.75mm from frame) |
| Cap | 7.5mm | 1.0mm | Decorative cap, chamfered edges |

**Derived lengths:**
- `bearing_length` = `wall_thickness` (1.1mm) + `post_bearing_axial_play` (0.1mm) = **1.2mm**
- `dd_cut_length` = `wheel.face_width` - `dd_cut_clearance` = **7.5mm** (balanced) or **7.5mm** (bh)

**Total length:** cap + post + bearing + DD = 1.0 + 5.5 + 1.2 + 7.5 = **15.2mm** (balanced)

### **DD Cut Shaft Interface**

The string post has a 3.25mm DD cut section to mate with the wheel's DD bore:

* **Shaft diameter:** 3.25mm
* **Flat depth:** 0.45mm (each side, 14% of diameter)
* **Across flats:** 2.35mm
* **Length:** = `wheel.face_width` (7.5-7.6mm, derived from gear config)

### **M2 Tap Bore Retention**

The DD section has an M2 tapped hole drilled up from the bottom:

* **Tap drill:** ø1.6mm (for M2 thread)
* **Depth:** 4mm (for standard M2 × 4mm screw)
* **Hardware:** M2 × 4mm machine screw + M2 washer (~5mm OD)

An M2 screw threads into the tap bore from below, with a washer to retain the wheel.

### **String Post Retention**

* **Pull-up prevention:** 7.5mm cap cannot pass through 4.2mm frame hole
* **Pull-down prevention:** M2 screw + washer in tap bore
  * Washer OD: ~5mm (larger than 3.5mm DD bore)
  * Screw holds washer in place
* **Wheel retention:** Bearing shoulder above wheel, M2 screw + washer below wheel

### **String Post Assembly Sequence**

1. Insert string post from above through frame (4mm bearing through ø4.2mm hole)
2. Slide wheel up from below through inlet (8mm) onto DD section
3. Place M2 washer on bottom of DD
4. Thread M2 screw into tap bore to retain wheel

## **5a. Post/Wheel/Frame Sandwich Mechanism**

The string post and wheel rotate as a unit. The frame is NOT clamped between them—instead, the frame floats with axial clearance.

### Clamping Mechanism

When the M2 retention screw is tightened:
1. Screw pulls wheel upward toward post
2. Wheel rises until it contacts the **4mm→3.25mm shoulder** on the post
3. Post shoulder (6mm→4mm) rests on frame top surface
4. Frame floats between these two reference points with axial play

### Cross-Section (Y-Z plane through post axis)

```
                    ┌─────────────────┐
                    │   POST (6mm)    │
POST SHOULDER ══════╧═════════════════╧══════  ← rests on frame top (Z=0)
─────────────────────────────────────────────  FRAME TOP SURFACE
░░░░░░░░░░░░░░░░░░░░│░░░░░░░░░░░░░░░░░░░░░░░  wall (1.1mm)
─────────────────────│───────────────────────  CAVITY CEILING (Z=-1.1)
                     │ bearing (4mm Ø)
                     │    ↕ axial_play        ← FREE GAP (frame floats here)
    ─────────────────┼───────────────────────  CLAMP SHOULDER (Z=-1.2)
                     │ DD section (3.25mm)    ↑
                ┌────┴────┐                   │ wheel pulled up by screw
                │  WHEEL  │                   │
                │         │                   │
        ────────┘         └────────           ← CAVITY FLOOR (8mm inlet hole)
                │         │
                └────┬────┘                   wheel extends through hole
                     │
                   [M2 screw from below]
```

**Note:** The wheel inlet hole (8mm) is larger than the wheel OD, allowing the wheel to extend below the frame. The wheel is NOT constrained by cavity floor—only by the clamp shoulder above and the M2 screw below.

### Parametric Constraints

| Parameter | Formula | Value |
|-----------|---------|-------|
| `wall_thickness` | design choice | 1.1mm |
| `post_bearing_axial_play` | design choice | 0.1mm |
| `wheel.face_width` | from gear config | 7.5-7.6mm |
| `dd_cut_clearance` | design choice | 0.1mm |
| `bearing_length` | `wall_thickness + axial_play` | 1.2mm |
| `dd_cut_length` | `wheel.face_width - dd_cut_clearance` | 7.4-7.5mm |

**Key points:**
- `axial_play` is a design choice (0.1mm provides free rotation)
- Wheel extends through 8mm inlet hole—no cavity floor constraint
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
   * Drill & ream **ø4.05mm** post bearing holes on Top Face (post shaft 4.0mm + 0.05mm clearance).
   * Drill **ø8.0mm** wheel inlet holes on Bottom Face.
   * Drill **ø3.0mm** mounting holes on Bottom Plate at specified Y positions.
4. **Drill Horizontal (Asymmetric):**
   * Drill **ø7.05mm** worm entry holes on one side (worm OD 7.0mm + 0.2mm clearance).
   * Drill & ream **ø4.05mm** peg shaft bearing holes on opposite side (shaft 4.0mm + 0.05mm clearance).
5. **Finish:** Deburr internal edges.

### **Phase 2: Wheel Production**

The wheel is manufactured from STEP file generated by gear calculator:

* **Source:** `config/<profile>/wheel_m0.6_z10.step`
* 10 teeth, 7.6mm width
* ø3.25mm DD cut bore (built into STEP)

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
   * 7.5mm cap (1mm high, chamfered)
   * 6mm visible post (5.5mm high)
   * 4mm frame bearing section (1.2mm, through frame + axial play)
   * 3.25mm DD cut gear interface (7.5mm, matches wheel width)
   * M2 tap bore (~4mm deep, for screw retention)
2. Mill DD flats on 3.25mm shaft section
3. Tap M2 hole in bottom
4. Cross-drill ø1.5mm string hole (2.75mm from frame top)

### **Phase 5: Assembly (The "Sandwich" Logic)**

1. **Insert Peg Head Assembly:** Slide **Peg Head + Worm** through **Entry Hole** (ø7.05mm). The ø4.0mm shaft passes through opposite **Bearing Hole** (ø4.05mm).
2. **Secure Peg Head:** Place **5.5mm washer** on shaft end, thread **M2 × 4mm pan head screw** to retain.
3. **Insert Post:** Slide **String Post** from above through **Top Hole** (ø4.05mm).
4. **Insert Wheel:** Slide **Worm Wheel** up through **Bottom Hole** (ø8mm) onto post's 3.25mm DD section.
5. **Place Post Washer:** Add **M2 washer** (~5mm OD) on bottom of DD section.
6. **Secure Wheel:** Thread **M2 × 4mm screw** into post tap bore to retain wheel.
7. **Complete:** Peg head secured with M2 screw + washer, wheel secured with M2 screw + washer.

## **7\. The Left Hand (LH) Variant**

* **Geometry:** The LH Frame is a **Mirror Image** of the RH Frame.  
* **Functional Inversion:**  
  * **Worm:** Uses **Left-Hand (CCW) Thread**.  
  * **Wheel:** Uses **Left-Hand Helix**.  
  * **Result:** Turning the knob in the *symmetrical* direction relative to the headstock produces the *same* tensioning result (tightening). This mimics high-end historic instruments.

## **8\. Derived Dimensions for Manufacture**

* **Center Distance (CD):** Distance from Worm Axis to Post Axis.
  * CD = (Pitch Dia Worm + Pitch Dia Wheel) / 2
  * CD = (5.8mm + 6.0mm) / 2 = **5.9mm**.
* **Vertical Alignment:** (using Section 2 coordinate system: Z=0 at mounting plate)
  * Internal Cavity: Z = -1.1mm (ceiling) to Z = -8.9mm (floor), height = 7.8mm.
  * Worm Axis Height: **Z = -5.0mm** (Centered in cavity).
  * Worm Clearance: 7.8mm cavity - 7.0mm worm OD = **0.8mm total** (0.4mm top/bottom).
  * Wheel Pitch Plane: **Z = -5.0mm** (Must align with worm).
* **Horizontal Hole Offset:**
  * Post Axis (top/bottom holes): X = 0 (centered on frame width).
  * Worm Axis (side holes): Offset from post axis by **5.9mm** (= center distance).
  * *Note:* Frame is 10.0mm wide, internal cavity is 7.8mm. Worm axis at X = 5.9mm from post axis places the side holes off-center.

### **Y-Axis Offset for Worm/Wheel Engagement**

The worm and wheel axes are offset from the housing center along Y to achieve proper center distance while centering the mechanism within each housing. This also provides a preload mechanism where string tension takes up backlash.

```
     HOUSING (16.2mm along Y)
     ========================

     Y=0 end (toward nut/bridge)              Y=145 end
     String pulls this way ←
       |                                           |
       |    POST        WORM                       |
       |      │   5.9mm    │                       |
       |      │<---------->│                       |
       |      ●            ●                       |
       |   -2.95mm     +2.95mm                     |
       |      from housing center                  |
       |                                           |

     String tension pulls post toward -Y.
     Post pivots at top bearing, wheel (at bottom) swings +Y into worm.
```

| Item | Y Position | Notes |
|------|------------|-------|
| Housing center | housing_y | Computed from frame parameters |
| Post axis | housing_y - CD/2 | Offset toward -Y (nut end) by 2.95mm |
| Worm axis | housing_y + CD/2 | Offset toward +Y (bridge end) by 2.95mm |
| Center distance | 5.9mm | Between worm and wheel axes |
| Extra backlash | configurable | Parameter for additional play beyond gear design |

**Preload mechanism:** String tension pulls the string post toward -Y (toward the nut/bridge). The post pivots at its top bearing, causing the wheel (at the bottom of the post) to swing toward +Y, pushing into the worm and taking up backlash.

**Both RH and LH variants:** Use the same offset directions (post toward -Y, worm toward +Y from housing center).

---

## **9\. Geometry Validation Checklist**

Before manufacturing, verify:

- [x] Worm OD (7.0mm) fits within internal cavity height (7.8mm) ✓ 0.8mm clearance
- [x] Worm OD (7.0mm) passes through entry hole (7.05mm) ✓ 0.2mm clearance
- [x] Peg head shaft (4.0mm) fits in bearing hole (4.05mm) ✓ 0.05mm clearance (reamed)
- [x] Wheel OD (7.05mm) passes through bottom hole (8.0mm) ✓ 0.8mm clearance
- [x] Post shaft (4.0mm) fits in top bearing hole (4.05mm) ✓ 0.05mm clearance (reamed)
- [x] Post cap (7.5mm) stops pull-through top hole (4.05mm) ✓
- [x] Peg head cap (8.5mm) stops pull-in through entry hole (7.05mm) ✓
- [x] M2 screw + washer (5.5mm OD) stops peg pull-out through bearing hole (4.05mm) ✓
- [x] Center distance (5.9mm) fits within frame geometry ✓
- [x] Sandwich assembly sequence verified ✓
- [x] Worm integral to peg head casting ✓
- [x] 3.25mm DD cut bore in wheel (for string post) ✓
- [x] M2 thread (2mm) passes through wheel DD across-flats (2.35mm) ✓
- [x] M2 washer (5mm OD) retains wheel (larger than 3.25mm DD bore) ✓
- [x] Custom wheel STEP file generated ✓

### **Gear Mesh Validation**

| Parameter | Worm | Wheel | Check |
|-----------|------|-------|-------|
| Module | 0.6 | 0.6 | ✓ Match |
| Pitch Diameter | 5.8mm | 6.0mm | — |
| Center Distance | — | — | 5.9mm ✓ |
| Pressure Angle | 20° | 20° | ✓ Match |
| Worm Type | Cylindrical or Globoid | — | Configurable |

### **Hardware List (per tuner)**

| Item | Specification | Qty |
|------|---------------|-----|
| Peg head + worm | Cast brass, integral worm (cylindrical or globoid), 4.0mm shaft | 1 |
| Worm wheel | Custom STEP, M0.6, 10T, 7.05mm OD, 3.25mm DD bore | 1 |
| Peg retention screw | M2 × 4mm pan head | 1 |
| Peg retention washer | 5.5mm OD, 2.7mm ID, 0.5mm thick | 1 |
| Post retention screw | M2 × 4mm pan head | 1 |
| Post retention washer | M2 washer (~5mm OD, ~2.2mm ID) | 1 |

### **Source Files**

| File | Description |
|------|-------------|
| `reference/peghead-and-shaft.step` | Complete peg head + shaft reference geometry (from Onshape) |
| `config/<profile>/worm_m0.6_z1.step` | Worm reference geometry (for machining cast shaft) |
| `config/<profile>/wheel_m0.6_z10.step` | 10-tooth worm wheel (separate part) |
| `config/<profile>/worm_gear.json` | Gear calculator parameters |