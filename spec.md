# **Master Engineering Specification: Historic Tuner Restoration**

## **1\. System Overview**

* **Product:** 5-Gang Tuning Machine Assembly (Historic Reproduction).
* **Variants:** Right Hand (RH) and Left Hand (LH).
* **Mechanism:** Single-start Worm Drive (Sandwich Assembly).
  * **RH Unit:** Right-Hand (Clockwise) Thread.
  * **LH Unit:** Left-Hand (Counter-Clockwise) Thread.
  * *Goal:* Symmetrical tuning action (turning knobs "up" towards the headstock tip always tightens the string).
* **Manufacturing Strategy:**
  * **Frame:** Subtractive machining from **10mm² Brass Box Section**.
  * **Turned Parts:** Swiss Screw Machining (Auto-Lathe) \- **All parts including gears.**
* **Repairability:** Fully disassembleable (no soldered lids).
* **Design Constraint:** External frame geometry (outline, cutouts, mounting holes) is fixed to match historic appearance. Internal components (worm, wheel, posts) may be adjusted for function.

---

## **1a\. Parametric Build Configuration**

The build123d script shall support the following parameters:

### **Frame Parameters**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `box_outer` | 10.0mm | Outer dimension of square tube |
| `wall_thickness` | 1.0mm | Wall thickness (tolerance up to 1.1mm) |
| `total_length` | 145.0mm | Overall frame length |
| `housing_length` | 16.0mm | Length of each rigid box section |
| `num_housings` | 5 | Number of tuner positions |
| `tuner_pitch` | 27.2mm | Center-to-center spacing between adjacent tuners |

### **Tolerance Profiles**
| Profile | Hole Tolerance | Use Case |
|---------|----------------|----------|
| `production` | +0.05mm | Machined brass (final) |
| `prototype_resin` | +0.10mm | 1:1 resin print validation |
| `prototype_fdm` | +0.20mm | 2:1 FDM functional test |

### **Scale Parameter**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `scale` | 1.0 | Geometry scale factor (use 2.0 for FDM prototype) |

*Note: When `scale=2.0`, all dimensions are doubled. The script outputs both RH and LH variants at the specified scale.*

## **2\. Component A: The Reinforced Frame**

* **Material:** CZ121 Brass Box Section (10.0mm x 10.0mm x 1.0mm wall).
* **Total Length:** 145.0mm.
* **Internal Cavity:** 8.0mm x 8.0mm (10mm outer - 2×1mm walls).
* **Topology:**
  * **5x Rigid Housings:** 16mm long sections of full box profile to resist gear tension.
  * **Connectors:** Top and Side walls milled away between housings, leaving only the **Bottom Plate** (1mm thick) to connect the unit.
  * **Tuner Pitch:** 27.2mm center-to-center spacing between adjacent tuners.

### **Mounting Holes (Fixed - Historic)**

* **Quantity:** 6 holes
* **Diameter:** ø3.0mm (clearance for mushroom-head bolts)
* **Location:** Bottom plate, in the gap sections between housings

| Hole # | Y Position (from frame start) | Description |
|--------|-------------------------------|-------------|
| 1 | 4.5mm | Before Housing 1 |
| 2 | 31.7mm | Between Housing 1 & 2 |
| 3 | 58.9mm | Between Housing 2 & 3 |
| 4 | 86.1mm | Between Housing 3 & 4 |
| 5 | 113.3mm | Between Housing 4 & 5 |
| 6 | 140.5mm | After Housing 5 |

### **Housing Positions (Fixed - Historic)**

| Housing # | Center Y Position | Description |
|-----------|-------------------|-------------|
| 1 | 15.1mm | First tuner |
| 2 | 42.3mm | Second tuner |
| 3 | 69.5mm | Third tuner |
| 4 | 96.7mm | Fourth tuner |
| 5 | 123.9mm | Fifth tuner |

### **The "Sandwich" Drilling Pattern (Per Housing)**

To enable assembly without soldering:

1. **Bottom Face (Wheel Inlet):** ø8.0mm through-hole.
   * *Function:* Allows the Worm Wheel (7.0mm OD) to be inserted from underneath.
2. **Top Face (Post Bearing):** ø4.2mm through-hole.
   * *Function:* Acts as the journal bearing for the String Post (4.0mm shaft).
3. **Side Faces (Worm Axle):** Asymmetric through-holes.
   * **Entry Side:** ø6.2mm (worm 6.0mm OD + 0.2mm clearance).
   * **Bearing Side:** ø2.7mm (peg shaft 2.5mm + 0.2mm clearance).
   * *Note:* For RH frame, entry is on left side (viewed from front). LH frame is mirrored.

## **3\. Component B: The Gear Set (Custom - Generated STEP Files)**

* **Constraint:** The Worm Wheel must fit through the ø8.0mm hole in the bottom of the frame.
* **Source:** Custom generated gears (STEP files from gear calculator)
* **Module:** **0.5**
* **Gear Ratio:** **12:1** (single-start worm, 12-tooth wheel)
* **Pressure Angle:** **25°**
* **Worm Type:** **Globoid** (improved contact pattern vs cylindrical)

### **1\. Worm (Driver) - Custom**

* **Source:** `worm_m0.5_z1.step`
* **Type:** Globoid (throat reduction 0.1mm, curvature radius 3mm)
* **Outer Diameter (tip):** **6.0mm**
* **Pitch Diameter:** 5.0mm
* **Root Diameter:** 3.75mm
* **Bore:** **ø2.5mm DD cut** (double-D for anti-rotation)
* **Length:** **7mm**
* **Lead:** 1.57mm (π/2)
* **Lead Angle:** 5.7°
* **Hand:** Right (LH variant uses left-hand worm)
* **Material:** Brass

### **2\. Worm Wheel (Driven) - Custom**

* **Source:** `wheel_m0.5_z12.step`
* **Teeth:** 12
* **Outer Diameter (tip):** **7.0mm**
* **Pitch Diameter:** 6.0mm
* **Root Diameter:** 4.75mm
* **Bore:** **ø3.0mm DD cut** (double-D for anti-rotation)
* **Face Width:** **6.0mm**
* **Material:** Brass

### **DD Cut Bore Interface**

Both gears use DD cut (double-D) bores for anti-rotation:

* **Worm bore:** ø2.5mm DD cut → mates with 2.5mm DD cut on peg head shaft
* **Wheel bore:** ø3.0mm DD cut → mates with 3.0mm DD cut on string post

*Note: Different bore sizes (2.5mm vs 3mm) prevent incorrect assembly.*

The DD cut is created by milling two parallel flats on a round shaft. The flat depth is typically 0.2× diameter (0.5mm for 2.5mm shaft, 0.6mm for 3mm shaft).

### **Center Distance Calculation**

* CD = (Worm PD + Wheel PD) / 2
* CD = (5.0mm + 6.0mm) / 2 = **5.5mm**

### **Assembly Parameters**

| Parameter | Value |
|-----------|-------|
| Centre Distance | 5.5mm |
| Pressure Angle | 25° |
| Backlash | 0.1mm |
| Ratio | 12:1 |

## **4\. Component C: The Peg Head Assembly**

The peg head is a cast brass finger-turn knob with an integral shaft. The custom worm gear mounts onto this shaft and is retained by an M2 screw.

### **Peg Head Geometry (from technical drawing)**

| Dimension | Value | Description |
|-----------|-------|-------------|
| Ring OD | 12.8mm | Outer diameter of peg head ring |
| Ring Bore | 9.5mm | Inner bore diameter (hollow for finger grip) |
| Ring Width | 7.8mm | Width of ring (flat-to-flat) |
| Ring Height | 8.0mm | Overall height of ring section |
| Chamfer | 1.0mm | Edge chamfer on ring faces |
| Button Diameter | ~6.0mm | Decorative end button |
| Button Height | 3.5mm | Height of decorative button |

*Note: The peg head is a ring shape with flat sides and chamfered edges, with a small decorative button on the end. The hollow bore (~9.5mm) provides finger grip for fine tuning.*

### **Integral Shaft (Cast as One Piece)**

The peg head and shaft are cast/machined as a single piece. The shaft passes through the frame and carries the custom worm gear.

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| Peg head shoulder | 8.0mm | ~2mm | Stops shaft being pulled into frame |
| Worm/entry section | 6.0mm | ~7mm | Passes through entry hole, worm mounted here |
| Worm mount interface | 2.5mm DD cut | within above | Worm sits on this section, Loctited |
| Bearing surface | 2.5mm round | ~1mm (wall) | Runs in ø2.7mm frame bearing hole |
| Screw hole | M2 tapped | 3mm deep | Retention screw at shaft end |

**Total shaft length:** ~10mm (from peg head shoulder to shaft end)

### **DD Cut Shaft Interface**

The peg shaft has a 2.5mm DD cut section to mate with the worm's DD bore:

* **Shaft diameter:** 2.5mm
* **Flat depth:** ~0.5mm (each side)
* **Across flats:** ~1.5mm
* **Length:** 7mm (matches worm length)

### **Shaft Retention**

* **Pull-in prevention:** 8mm peg head shoulder cannot pass through 6.2mm entry hole
* **Pull-out prevention:** M2 × 3mm pan head screw in shaft end
  * Screw head OD: ~3.8mm (larger than 2.7mm bearing hole)
  * Screw head protrusion: ~1.3mm beyond shaft end
* **Worm retention on shaft:** Loctite on DD cut interface

### **Peg Head Assembly Sequence**

1. Cast or machine peg head with integral shaft (all sections)
2. Mill DD flats on 2.5mm shaft section
3. Slide worm onto shaft DD section, apply Loctite
4. Insert assembly through frame (worm enters 6.2mm hole, shaft exits 2.7mm hole)
5. Thread M2 × 3mm pan head screw into shaft end to retain

### **Disassembly for Repair**

1. Remove M2 screw from shaft end
2. Slide peg head + worm assembly out through entry hole
3. Replace worm or peg head as needed
4. Reassemble

### **Manufacturing Options**

**Option 1 - Investment cast:**
- Investment cast entire peg head + shaft in brass
- Finish-turn shaft to final dimensions
- Mill DD flats on shaft
- Tap M2 hole in shaft end

**Option 2 - Machined from solid:**
- Turn entire assembly from 13mm brass bar
- Mill ring shape on peg head
- Mill DD flats on shaft
- More material waste but no casting required

## **5\. Component D: The String Post (Vertical)**

* **Manufacturing:** Swiss Sliding Head Lathe (Swiss Auto) or manual lathe.
* **Stock:** 8.0mm round brass/steel bar.
* **Cap:** Decorative 7.5mm cap with chamfered edges.
* **Top Section:** 6.0mm visible post (runs in the Top Face hole).
* **Gear Interface:** 3.0mm DD cut section to mate with Worm Wheel DD bore.
* **String Hole:** ø1.5mm cross-hole, positioned 4mm from frame top.

### **String Post Dimensions (Top to Bottom)**

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| Cap | 7.5mm | 1.0mm | Decorative cap, chamfered edges |
| Visible post | 6.0mm | 5.5mm | Above frame, aesthetic |
| String hole | ø1.5mm | through | Cross-drilled, 4mm from frame top |
| Frame bearing | 4.0mm | 1.0mm | Runs in ø4.2mm top frame hole |
| Washer seat | 4.0mm | — | Washer sits here to space wheel |
| Wheel interface | 3.0mm DD cut | 6.0mm | Mates with wheel DD bore |
| Screw boss | 4.0mm round | ~2mm | Material for M2 tapped hole |
| Screw hole | M2 tapped | 3mm deep | Retention screw at shaft end |

**Total length:** ~16mm (cap to screw boss end)

### **DD Cut Shaft Interface**

The string post has a 3.0mm DD cut section to mate with the wheel's DD bore:

* **Shaft diameter:** 3.0mm
* **Flat depth:** ~0.6mm (each side)
* **Across flats:** ~1.8mm
* **Length:** 6mm (matches wheel width)

### **String Post Retention**

* **Pull-up prevention:** 7.5mm cap cannot pass through 4.2mm frame hole
* **Pull-down prevention:** M2 × 3mm pan head screw in shaft end
  * Screw head OD: ~3.8mm
  * Screw threads into 4mm round boss below DD section
* **Wheel retention:** Washer above wheel, M2 screw below wheel

### **String Post Assembly Sequence**

1. Insert string post down through frame (4mm shaft through ø4.2mm hole)
2. Place washer on shaft below frame
3. Slide wheel onto 3mm DD cut section
4. Thread M2 × 3mm pan head screw into shaft end to retain wheel

## **6\. Manufacturing Process (Step-by-Step)**

### **Phase 1: Frame Machining (Mill/Drill)**

1. **Cut Stock:** Cut 10mm Box section to 145mm.
2. **Mill Profile:** Clamp stock. Mill away the Top and Side walls in the "Gap" sections to create the 5 isolated boxes.
3. **Drill Vertical:**
   * Drill **ø4.2mm** post bearing holes on Top Face (post shaft 4.0mm + 0.2mm clearance).
   * Drill **ø8.0mm** wheel inlet holes on Bottom Face.
   * Drill **ø3.0mm** mounting holes on Bottom Plate at specified Y positions.
4. **Drill Horizontal (Asymmetric):**
   * Drill **ø6.2mm** worm entry holes on one side (worm OD 6.0mm + 0.2mm clearance).
   * Drill **ø2.7mm** peg shaft bearing holes on opposite side (shaft 2.5mm + 0.2mm clearance).
5. **Finish:** Deburr internal edges.

### **Phase 2: Custom Gear Production**

Gears are manufactured from STEP files generated by gear calculator:

1. **Worm:** `worm_m0.5_z1.step`
   * Globoid profile, 7mm length
   * ø2.5mm DD cut bore (built into STEP)

2. **Worm Wheel:** `wheel_m0.5_z12.step`
   * 12 teeth, 6mm width
   * ø3.0mm DD cut bore (built into STEP)

*Note: DD cut bores are generated in the STEP files - no post-machining required.*

### **Phase 3: Peg Head & Shaft Production**

**Option A - Investment cast (recommended):**
1. Investment cast peg head + shaft in brass
2. Finish-turn shaft sections to final dimensions
3. Mill DD flats on 2.5mm shaft section (7mm long)
4. Tap M2 hole in shaft end

**Option B - Machined from solid:**
1. Turn entire peg head + shaft from 13mm brass bar
2. Mill ring shape on peg head
3. Mill DD flats on 2.5mm shaft section
4. Tap M2 hole in shaft end

### **Phase 4: String Post Production**

1. Turn from **8mm brass/steel bar:**
   * 7.5mm cap (1mm high, chamfered)
   * 6mm visible post (5.5mm high)
   * 4mm frame bearing section (1mm, through frame)
   * 3mm DD cut gear interface (6mm, for wheel)
   * 4mm round screw boss (2mm, for M2 thread)
2. Mill DD flats on 3mm shaft section
3. Cross-drill ø1.5mm string hole (4mm from frame top)
4. Tap M2 hole in shaft end (3mm deep)

### **Phase 5: Assembly (The "Sandwich" Logic)**

1. **Insert Peg Head Assembly:** Slide **Peg Head + Worm** through **Entry Hole** (ø6.2mm). The ø2.5mm shaft passes through opposite **Bearing Hole** (ø2.7mm).
2. **Secure Peg Head:** Thread **M2 × 3mm pan head screw** into peg shaft end.
3. **Insert Post:** Slide **String Post** down through **Top Hole** (ø4.2mm).
4. **Place Washer:** Add washer on post shaft below frame to space wheel.
5. **Insert Wheel:** Slide **Worm Wheel** through **Bottom Hole** (ø8mm) onto post's 3mm DD section.
6. **Secure Post:** Thread **M2 × 3mm pan head screw** into post shaft end to retain wheel.
7. **Complete:** Both peg head and string post secured with M2 screws.

## **7\. The Left Hand (LH) Variant**

* **Geometry:** The LH Frame is a **Mirror Image** of the RH Frame.  
* **Functional Inversion:**  
  * **Worm:** Uses **Left-Hand (CCW) Thread**.  
  * **Wheel:** Uses **Left-Hand Helix**.  
  * **Result:** Turning the knob in the *symmetrical* direction relative to the headstock produces the *same* tensioning result (tightening). This mimics high-end historic instruments.

## **8\. Derived Dimensions for Manufacture**

* **Center Distance (CD):** Distance from Worm Axis to Post Axis.
  * CD = (Pitch Dia Worm + Pitch Dia Wheel) / 2
  * CD = (5.0mm + 6.0mm) / 2 = **5.5mm**.
* **Vertical Alignment:**
  * Internal Cavity: Z = 1.0mm (floor) to Z = 9.0mm (ceiling), height = 8.0mm.
  * Worm Axis Height: **Z = 5.0mm** (Centered in box and cavity).
  * Worm Clearance: 8.0mm cavity - 6.0mm worm OD = **2.0mm total** (1.0mm top/bottom).
  * Wheel Pitch Plane: **Z = 5.0mm** (Must align with worm).
* **Horizontal Hole Offset:**
  * Post Axis (top/bottom holes): X = 0 (centered on frame width).
  * Worm Axis (side holes): Offset from post axis by **5.5mm** (= center distance).
  * *Note:* Frame is 10mm wide, internal cavity is 8mm. Worm axis at X = 5.5mm from post axis places the side holes off-center.

---

## **9\. Geometry Validation Checklist**

Before manufacturing, verify:

- [x] Worm OD (6.0mm) fits within internal cavity height (8.0mm) ✓ 2.0mm clearance
- [x] Worm OD (6.0mm) passes through entry hole (6.2mm) ✓ 0.2mm clearance
- [x] Peg head shaft (2.5mm) fits in bearing hole (2.7mm) ✓ 0.2mm clearance
- [x] Wheel OD (7.0mm) passes through bottom hole (8.0mm) ✓ 1.0mm clearance
- [x] Post shaft (4.0mm) fits in top bearing hole (4.2mm) ✓ 0.2mm clearance
- [x] Post cap (7.5mm) stops pull-through top hole (4.2mm) ✓
- [x] Peg head shoulder (8mm) stops pull-in through entry hole (6.2mm) ✓
- [x] M2 screw head (3.8mm) stops peg pull-out through bearing hole (2.7mm) ✓
- [x] Center distance (5.5mm) fits within frame geometry ✓
- [x] Sandwich assembly sequence verified ✓
- [x] 2.5mm DD cut bore in worm (for peg shaft) ✓
- [x] 3.0mm DD cut bore in wheel (for string post) ✓
- [x] M2 tappable in 4mm round post boss (below 3mm DD) ✓
- [x] Custom gear STEP files generated ✓

### **Gear Mesh Validation**

| Parameter | Worm | Wheel | Check |
|-----------|------|-------|-------|
| Module | 0.5 | 0.5 | ✓ Match |
| Pitch Diameter | 5.0mm | 6.0mm | — |
| Center Distance | — | — | 5.5mm ✓ |
| Pressure Angle | 25° | 25° | ✓ Match |
| Worm Type | Globoid | — | Improved contact |

### **Hardware List (per tuner)**

| Item | Specification | Qty |
|------|---------------|-----|
| Worm gear | Custom, M0.5, 6.0mm OD, globoid, 2.5mm DD bore | 1 |
| Worm wheel | Custom, M0.5, 12T, 7.0mm OD, 3.0mm DD bore | 1 |
| Peg retention screw | M2 × 3mm pan head | 1 |
| Post retention screw | M2 × 3mm pan head | 1 |
| Washer | ~4mm ID, spacing wheel on post | 1 |
| Loctite | Blue 242 (removable) | — |

### **Source Files**

| File | Description |
|------|-------------|
| `worm_m0.5_z1.step` | Globoid worm, RH thread |
| `wheel_m0.5_z12.step` | 12-tooth worm wheel |
| `7mm-globoid.json` | Gear calculator parameters |