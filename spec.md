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
| `box_outer` | 10.35mm | Outer dimension of square tube (as manufactured) |
| `wall_thickness` | 1.1mm | Wall thickness (as manufactured) |
| `total_length` | 145.0mm | Overall frame length |
| `housing_length` | 16.2mm | Length of each rigid box section |
| `end_length` | 10.0mm | Length from frame end to first/last housing center |
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

* **Material:** CZ121 Brass Box Section (10.35mm x 10.35mm x 1.1mm wall, as manufactured).
* **Total Length:** 145.0mm.
* **Internal Cavity:** 8.15mm x 8.15mm (10.35mm outer - 2×1.1mm walls).
* **End Length:** 10.0mm from frame end to first/last housing center.
* **Topology:**
  * **5x Rigid Housings:** 16.2mm long sections of full box profile to resist gear tension.
  * **Connectors:** Top and Side walls milled away between housings, leaving only the **Bottom Plate** (1.1mm thick) to connect the unit.
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
   * **Bearing Side:** ø4.0mm (peg shaft 3.8mm + 0.2mm clearance).
   * *Note:* For RH frame, entry is on left side (viewed from front). LH frame is mirrored.

## **3\. Component B: The Gear Set**

* **Constraint:** The Worm Wheel must fit through the ø8.0mm hole in the bottom of the frame.
* **Module:** **0.5**
* **Gear Ratio:** **12:1** (single-start worm, 12-tooth wheel)
* **Pressure Angle:** **25°**
* **Worm Type:** **Globoid** (improved contact pattern vs cylindrical)

### **1\. Worm (Driver) - Integral to Peg Head**

The worm thread is cast/machined as part of the peg head assembly (not a separate gear).

* **Reference geometry:** `worm_m0.5_z1.step` (for tooth profile)
* **Type:** Globoid (throat reduction 0.1mm, curvature radius 3mm)
* **Outer Diameter (tip):** **6.0mm**
* **Pitch Diameter:** 5.0mm
* **Root Diameter:** 3.75mm
* **Length:** **7mm**
* **Lead:** 1.57mm (π/2)
* **Lead Angle:** 5.7°
* **Hand:** Right (LH variant uses left-hand worm)
* **Material:** Brass (cast with peg head)

*Note: Worm STEP file provides reference geometry for machining the thread on the cast peg head shaft.*

### **2\. Worm Wheel (Driven) - Separate Part**

* **Source:** `wheel_m0.5_z12.step`
* **Teeth:** 12
* **Outer Diameter (tip):** **7.0mm**
* **Pitch Diameter:** 6.0mm
* **Root Diameter:** 4.75mm
* **Bore:** **ø3.0mm DD cut** (double-D for anti-rotation)
* **Face Width:** **6.0mm**
* **Material:** Brass

The wheel is a separate component that slides onto the string post and enables sandwich assembly.

### **DD Cut Bore Interface (Wheel Only)**

* **Wheel bore:** ø3.0mm DD cut → mates with 3.0mm DD cut on string post
* **Flat depth:** ~0.6mm (each side)
* **Across flats:** ~1.8mm

The DD cut is created by milling two parallel flats on the string post shaft.

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

The peg head, shaft, and worm thread are cast as a single brass piece, then finish-machined. This provides maximum strength and eliminates the need for a separate worm gear.

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

### **Integral Shaft + Worm (Cast as One Piece)**

The peg head, shaft, and worm thread are cast/machined as a single piece. This eliminates the weak point of a separate gear on a small shaft.

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| Peg head shoulder | 8.0mm | ~2mm | Stops shaft being pulled into frame |
| Worm thread | 6.0mm OD | 7mm | Globoid worm, integral to shaft |
| Bearing surface | 3.8mm round | ~1mm (wall) | Runs in ø4.0mm frame bearing hole |
| Screw hole | M2 tapped | 3mm deep | Retention screw at shaft end |

**Total shaft length:** ~10mm (from peg head shoulder to shaft end)

### **Worm Thread Geometry**

The worm thread is machined onto the shaft using the reference geometry from `worm_m0.5_z1.step`:

* **Type:** Globoid
* **Outer Diameter:** 6.0mm
* **Pitch Diameter:** 5.0mm
* **Root Diameter:** 3.75mm
* **Length:** 7mm
* **Lead:** 1.57mm
* **Lead Angle:** 5.7°

### **Shaft Retention**

* **Pull-in prevention:** 8mm peg head shoulder cannot pass through 6.2mm entry hole
* **Pull-out prevention:** M2 × 3mm pan head screw + washer in shaft end
  * Washer: ~5mm OD, 2.2mm ID, 0.5mm thick (larger than 4.0mm bearing hole)
  * Screw head OD: ~3.8mm (holds washer in place)
  * Total protrusion: ~1.8mm beyond shaft end

### **Peg Head Assembly Sequence**

1. Cast peg head with integral shaft (rough form)
2. Finish-turn shaft to 3.8mm bearing diameter
3. Machine globoid worm thread (reference STEP geometry)
4. Tap M2 hole in shaft end
5. Insert assembly through frame (worm enters 6.2mm hole, shaft exits 4.0mm hole)
6. Place washer (5mm OD) on shaft end
7. Thread M2 × 3mm pan head screw into shaft end to retain

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
* **Gear Interface:** 3.0mm DD cut section to mate with Worm Wheel DD bore.
* **Retention:** M2.5 E-clip on shaft below wheel.
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
| E-clip section | 2.5mm round | ~3mm | Wheel slides over this |
| E-clip groove | ~2.1mm | 0.4mm | DIN 6799 M2.5 E-clip seats here |

**Total length:** ~17mm (cap to shaft end)

### **DD Cut Shaft Interface**

The string post has a 3.0mm DD cut section to mate with the wheel's DD bore:

* **Shaft diameter:** 3.0mm
* **Flat depth:** ~0.6mm (each side)
* **Across flats:** ~1.8mm
* **Length:** 6mm (matches wheel width)

### **Stepped Shaft for E-clip Retention**

Below the DD section, the shaft steps down to allow wheel assembly:

* **DD section:** 3.0mm (wheel engages here)
* **Step-down:** 2.5mm round (wheel slides over this, 3mm bore > 2.5mm shaft)
* **E-clip groove:** ~2.1mm diameter, 0.4mm wide
* **E-clip:** DIN 6799 M2.5 (~6mm OD, retains wheel)

### **String Post Retention**

* **Pull-up prevention:** 7.5mm cap cannot pass through 4.2mm frame hole
* **Pull-down prevention:** E-clip at shaft end
  * E-clip OD: ~6mm (larger than 3mm DD bore)
  * Wheel sits on shoulder between 3mm DD and 2.5mm round
* **Wheel retention:** Washer above wheel, E-clip below wheel

### **String Post Assembly Sequence**

1. Insert string post down through frame (4mm shaft through ø4.2mm hole)
2. Place washer on shaft below frame
3. Slide wheel up onto 3mm DD section (slides over 2.5mm section)
4. Snap E-clip into groove to retain wheel

## **6\. Manufacturing Process (Step-by-Step)**

### **Phase 1: Frame Machining (Mill/Drill)**

1. **Cut Stock:** Cut 10.35mm Box section to 145mm.
2. **Mill Profile:** Clamp stock. Mill away the Top and Side walls in the "Gap" sections to create the 5 isolated boxes.
3. **Drill Vertical:**
   * Drill **ø4.2mm** post bearing holes on Top Face (post shaft 4.0mm + 0.2mm clearance).
   * Drill **ø8.0mm** wheel inlet holes on Bottom Face.
   * Drill **ø3.0mm** mounting holes on Bottom Plate at specified Y positions.
4. **Drill Horizontal (Asymmetric):**
   * Drill **ø6.2mm** worm entry holes on one side (worm OD 6.0mm + 0.2mm clearance).
   * Drill **ø4.0mm** peg shaft bearing holes on opposite side (shaft 3.8mm + 0.2mm clearance).
5. **Finish:** Deburr internal edges.

### **Phase 2: Wheel Production**

The wheel is manufactured from STEP file generated by gear calculator:

* **Source:** `wheel_m0.5_z12.step`
* 12 teeth, 6mm width
* ø3.0mm DD cut bore (built into STEP)

*Note: Worm is integral to peg head casting - see Phase 3.*

### **Phase 3: Peg Head + Worm Production**

Investment cast peg head with integral shaft and worm thread:

1. Investment cast peg head + shaft + rough worm form in brass
2. Finish-turn shaft to 3.8mm bearing diameter
3. Machine globoid worm thread (reference `worm_m0.5_z1.step` for geometry)
4. Tap M2 hole in shaft end

*Note: Casting the worm integral with the shaft provides maximum strength.*

### **Phase 4: String Post Production**

1. Turn from **8mm brass/steel bar:**
   * 7.5mm cap (1mm high, chamfered)
   * 6mm visible post (5.5mm high)
   * 4mm frame bearing section (1mm, through frame)
   * 3mm DD cut gear interface (6mm, for wheel)
   * 2.5mm round section (~3mm, for E-clip)
   * E-clip groove (2.1mm dia, 0.4mm wide)
2. Mill DD flats on 3mm shaft section
3. Cross-drill ø1.5mm string hole (4mm from frame top)

### **Phase 5: Assembly (The "Sandwich" Logic)**

1. **Insert Peg Head Assembly:** Slide **Peg Head + Worm** through **Entry Hole** (ø6.2mm). The ø3.8mm shaft passes through opposite **Bearing Hole** (ø4.0mm).
2. **Secure Peg Head:** Place **5mm washer** on shaft end, thread **M2 × 3mm pan head screw** to retain.
3. **Insert Post:** Slide **String Post** down through **Top Hole** (ø4.2mm).
4. **Place Post Washer:** Add washer on post shaft below frame to space wheel.
5. **Insert Wheel:** Slide **Worm Wheel** up through **Bottom Hole** (ø8mm) onto post's 3mm DD section.
6. **Secure Wheel:** Snap **M2.5 E-clip** into groove on shaft end.
7. **Complete:** Peg head secured with M2 screw + washer, wheel secured with E-clip.

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
  * *Note:* Frame is 10.35mm wide, internal cavity is 8.15mm. Worm axis at X = 5.5mm from post axis places the side holes off-center.

---

## **9\. Geometry Validation Checklist**

Before manufacturing, verify:

- [x] Worm OD (6.0mm) fits within internal cavity height (8.15mm) ✓ 2.15mm clearance
- [x] Worm OD (6.0mm) passes through entry hole (6.2mm) ✓ 0.2mm clearance
- [x] Peg head shaft (3.8mm) fits in bearing hole (4.0mm) ✓ 0.2mm clearance
- [x] Wheel OD (7.0mm) passes through bottom hole (8.0mm) ✓ 1.0mm clearance
- [x] Post shaft (4.0mm) fits in top bearing hole (4.2mm) ✓ 0.2mm clearance
- [x] Post cap (7.5mm) stops pull-through top hole (4.2mm) ✓
- [x] Peg head shoulder (8mm) stops pull-in through entry hole (6.2mm) ✓
- [x] M2 screw + washer (5mm OD) stops peg pull-out through bearing hole (4.0mm) ✓
- [x] Center distance (5.5mm) fits within frame geometry ✓
- [x] Sandwich assembly sequence verified ✓
- [x] Worm integral to peg head casting ✓
- [x] 3.0mm DD cut bore in wheel (for string post) ✓
- [x] Wheel slides over 2.5mm section (3mm bore > 2.5mm shaft) ✓
- [x] E-clip (6mm OD) retains wheel (larger than 3mm DD bore) ✓
- [x] Custom wheel STEP file generated ✓

### **Gear Mesh Validation**

| Parameter | Worm | Wheel | Check |
|-----------|------|-------|-------|
| Module | 0.5 | 0.5 | ✓ Match |
| Pitch Diameter | 5.0mm | 6.0mm | — |
| Center Distance | — | — | 5.5mm ✓ |
| Pressure Angle | 25° | 25° | ✓ Match |
| Worm Type | Globoid (integral) | — | Improved contact |

### **Hardware List (per tuner)**

| Item | Specification | Qty |
|------|---------------|-----|
| Peg head + worm | Cast brass, integral globoid worm, 3.8mm shaft | 1 |
| Worm wheel | Custom STEP, M0.5, 12T, 7.0mm OD, 3.0mm DD bore | 1 |
| Peg retention screw | M2 × 3mm pan head | 1 |
| Peg retention washer | 5mm OD, 2.2mm ID, 0.5mm thick | 1 |
| Wheel retention E-clip | DIN 6799 M2.5 (~6mm OD) | 1 |
| Post spacing washer | ~4mm ID, spacing wheel on post | 1 |

### **Source Files**

| File | Description |
|------|-------------|
| `worm_m0.5_z1.step` | Globoid worm reference geometry (for machining cast shaft) |
| `wheel_m0.5_z12.step` | 12-tooth worm wheel (separate part) |
| `7mm-globoid.json` | Gear calculator parameters |