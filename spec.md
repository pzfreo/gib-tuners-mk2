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
   * *Function:* Allows the Worm Wheel (6.9mm OD) to be inserted from underneath.
2. **Top Face (Post Bearing):** ø4.2mm through-hole.
   * *Function:* Acts as the journal bearing for the String Post (4.0mm shaft).
3. **Side Faces (Worm Axle):** Asymmetric through-holes.
   * **Entry Side:** ø6.2mm (worm 6.0mm OD + 0.2mm clearance).
   * **Bearing Side:** ø3.2mm (peg shaft 3.0mm + 0.2mm clearance).
   * *Note:* For RH frame, entry is on left side (viewed from front). LH frame is mirrored.

## **3\. Component B: The Gear Set (Off-the-Shelf + Modification)**

* **Constraint:** The Worm Wheel must fit through the ø8.0mm hole in the bottom of the frame.
* **Source:** Off-the-shelf Module 0.5 worm gear set (AliExpress or equivalent)
* **Module:** **0.5**
* **Gear Ratio:** **12:1** (single-start worm, 12-tooth wheel)
* **Pressure Angle:** 20°

### **1\. Worm (Driver) - Off-the-Shelf**

* **Source:** Module 0.5 brass worm gear set
* **Outer Diameter:** **6.0mm**
* **Pitch Diameter:** 5.0mm (OD - 2×addendum)
* **Bore:** ø2.0mm (requires broached square keyway for shaft interface)
* **Length:** 10mm (may be cut down if needed)
* **Material:** Brass

*Note: Off-the-shelf worm is mounted on custom shaft stub that connects to cast peg head.*

### **2\. Worm Wheel (Driven) - Off-the-Shelf + Modified**

* **Source:** Module 0.5 brass worm gear set
* **Teeth:** 12
* **Outer Diameter:** **6.9mm**
* **Pitch Diameter:** 6.0mm (= module × teeth = 0.5 × 12)
* **Bore:** ø2.0mm as supplied (drill to ø3.0mm, broach 3mm square keyway)
* **Face Width:** ~5.0mm (wheel height)
* **Material:** Brass

### **Keyway Modification (Broaching) - Both Gears**

Both worm and wheel require the same modification:

1. Drill bore from ø2.0mm to **ø3.0mm**
2. Press **3mm square broach** through enlarged bore

* **Tool:** 3mm push broach
* **Equipment:** Arbor press or sturdy vice
* **Worm interface:** Mates with 3mm square section on peg head shaft
* **Wheel interface:** Mates with 3mm square section on string post

### **Center Distance Calculation**

* CD = (Worm PD + Wheel PD) / 2
* CD = (5.0mm + 6.0mm) / 2 = **5.5mm**

## **4\. Component C: The Peg Head Assembly**

The peg head is a cast brass finger-turn knob with an integral shaft. The off-the-shelf worm gear mounts onto this shaft and is retained by an M2 screw.

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

The peg head and shaft are cast/machined as a single piece. The shaft passes through the frame and carries the off-the-shelf worm gear.

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| Peg head shoulder | 8.0mm | ~2mm | Stops shaft being pulled into frame |
| Worm/entry section | 6.0mm | ~10mm | Passes through entry hole, worm mounted here |
| Worm mount keyway | 3.0mm square | within above | Broached worm sits on this section, Loctited |
| Bearing surface | 3.0mm round | ~1mm (wall) | Runs in ø3.2mm frame bearing hole |
| Screw hole | M2 tapped | 3mm deep | Retention screw at shaft end |

**Total shaft length:** ~13mm (from peg head shoulder to shaft end)

### **Worm Modification**

The off-the-shelf worm (2mm bore) must be drilled out and broached:

1. Drill worm bore from ø2.0mm to **ø3.0mm**
2. Broach **3mm square keyway** through enlarged bore
3. Worm now fits on 3mm square shaft section

### **Shaft Retention**

* **Pull-in prevention:** 8mm peg head shoulder cannot pass through 6.2mm entry hole
* **Pull-out prevention:** M2 × 3mm pan head screw in shaft end
  * Screw head OD: ~3.8mm (larger than 3.2mm bearing hole)
  * Screw head protrusion: ~1.3mm beyond shaft end
* **Worm retention on shaft:** Loctite on 3mm square keyway interface

### **Peg Head Assembly Sequence**

1. Cast or machine peg head with integral shaft (all sections)
2. Drill worm bore from 2mm to 3mm
3. Broach 3mm square keyway in worm bore
4. Slide worm onto shaft 3mm square section, apply Loctite
5. Insert assembly through frame (worm enters 6.2mm hole, shaft exits 3.2mm hole)
6. Thread M2 × 3mm pan head screw into shaft end to retain

### **Disassembly for Repair**

1. Remove M2 screw from shaft end
2. Slide peg head + worm assembly out through entry hole
3. Replace worm or peg head as needed
4. Reassemble

### **Manufacturing Options**

**Option 1 - Investment cast:**
- Investment cast entire peg head + shaft in brass
- Finish-turn shaft to final dimensions
- Tap M2 hole in shaft end

**Option 2 - Machined from solid:**
- Turn entire assembly from 13mm brass bar
- Mill ring shape on peg head
- More material waste but no casting required

## **5\. Component D: The String Post (Vertical)**

* **Manufacturing:** Swiss Sliding Head Lathe (Swiss Auto) or manual lathe.
* **Stock:** 8.0mm round brass/steel bar.
* **Cap:** Decorative 7.5mm cap with chamfered edges.
* **Top Section:** 6.0mm visible post (runs in the Top Face hole).
* **Gear Interface:** 3.0mm square section to mate with broached Worm Wheel bore.
* **String Hole:** ø1.5mm cross-hole, positioned 4mm from frame top.

### **String Post Dimensions (Top to Bottom)**

| Section | Diameter | Length | Description |
|---------|----------|--------|-------------|
| Cap | 7.5mm | 1.0mm | Decorative cap, chamfered edges |
| Visible post | 6.0mm | 5.5mm | Above frame, aesthetic |
| String hole | ø1.5mm | through | Cross-drilled, 4mm from frame top |
| Frame bearing | 4.0mm | 1.0mm | Runs in ø4.2mm top frame hole |
| Washer seat | 4.0mm | — | Washer sits here to space wheel |
| Wheel interface | 3.0mm square | 5.0mm | Mates with broached wheel bore |
| Screw boss | 4.0mm round | ~2mm | Material for M2 tapped hole |
| Screw hole | M2 tapped | 3mm deep | Retention screw at shaft end |

**Total length:** ~15mm (cap to screw boss end)

### **Wheel Bore Modification**

The off-the-shelf wheel (2mm bore) must be drilled out and broached:

1. Drill wheel bore from ø2.0mm to **ø3.0mm**
2. Broach **3mm square keyway** through enlarged bore
3. Wheel now fits on 3mm square shaft section

*Note: Both worm and wheel now use 3mm square keyways (worm for peg shaft, wheel for string post).*

### **String Post Retention**

* **Pull-up prevention:** 7.5mm cap cannot pass through 4.2mm frame hole
* **Pull-down prevention:** M2 × 3mm pan head screw in shaft end
  * Screw head OD: ~3.8mm (larger than 3mm square diagonal ~4.24mm is blocked by wheel)
  * Screw threads into 4mm round boss below 3mm square section
* **Wheel retention:** Washer above wheel, M2 screw below wheel

### **String Post Assembly Sequence**

1. Insert string post down through frame (4mm shaft through ø4.2mm hole)
2. Place washer on shaft below frame
3. Slide wheel onto 3mm square section
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
   * Drill **ø3.2mm** peg shaft bearing holes on opposite side (shaft 3.0mm + 0.2mm clearance).
5. **Finish:** Deburr internal edges.

### **Phase 2: Off-the-Shelf Gear Modification**

Both gears receive identical modification:

1. **Modify Worm Gear:**
   * Drill bore from ø2.0mm to **ø3.0mm**
   * Press **3mm square broach** through enlarged bore
   * Creates keyway for peg head shaft interface

2. **Modify Worm Wheel:**
   * Drill bore from ø2.0mm to **ø3.0mm**
   * Press **3mm square broach** through enlarged bore
   * Creates keyway for string post interface

*Note: Using the same 3mm broach for both gears simplifies tooling.*

### **Phase 3: Peg Head & Shaft Production**

**Option A - Investment cast (recommended):**
1. Investment cast peg head + shaft in brass
2. Finish-turn shaft sections to final dimensions
3. Mill 3mm square keyway on shaft
4. Tap M2 hole in shaft end

**Option B - Machined from solid:**
1. Turn entire peg head + shaft from 13mm brass bar
2. Mill ring shape on peg head
3. Mill 3mm square keyway on shaft
4. Tap M2 hole in shaft end

### **Phase 4: String Post Production**

1. Turn from **8mm brass/steel bar:**
   * 7.5mm cap (1mm high, chamfered)
   * 6mm visible post (5.5mm high)
   * 4mm frame bearing section (1mm, through frame)
   * 3mm square gear interface (5mm, for wheel)
   * 4mm round screw boss (2mm, for M2 thread)
2. Cross-drill ø1.5mm string hole (4mm from frame top)
3. Tap M2 hole in shaft end (3mm deep)

### **Phase 5: Assembly (The "Sandwich" Logic)**

1. **Insert Peg Head Assembly:** Slide **Peg Head + Worm** through **Entry Hole** (ø6.2mm). The ø3.0mm shaft passes through opposite **Bearing Hole** (ø3.2mm).
2. **Secure Peg Head:** Thread **M2 × 3mm pan head screw** into peg shaft end.
3. **Insert Post:** Slide **String Post** down through **Top Hole** (ø4.2mm).
4. **Place Washer:** Add washer on post shaft below frame to space wheel.
5. **Insert Wheel:** Slide **Worm Wheel** through **Bottom Hole** (ø8mm) onto post's 3mm square section.
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
- [x] Peg head shaft (3.0mm) fits in bearing hole (3.2mm) ✓ 0.2mm clearance
- [x] Wheel OD (6.9mm) passes through bottom hole (8.0mm) ✓ 1.1mm clearance
- [x] Post shaft (4.0mm) fits in top bearing hole (4.2mm) ✓ 0.2mm clearance
- [x] Post cap (7.5mm) stops pull-through top hole (4.2mm) ✓
- [x] Peg head shoulder (8mm) stops pull-in through entry hole (6.2mm) ✓
- [x] M2 screw head (3.8mm) stops peg pull-out through bearing hole (3.2mm) ✓
- [x] Center distance (5.5mm) fits within frame geometry ✓
- [x] Sandwich assembly sequence verified ✓
- [x] 3mm square broach keyway for worm bore ✓
- [x] 3mm square broach keyway for wheel bore ✓
- [x] M2 tappable in 4mm round post boss (below 3mm square) ✓
- [ ] Off-the-shelf gears sourced and verified

### **Gear Mesh Validation**

| Parameter | Worm | Wheel | Check |
|-----------|------|-------|-------|
| Module | 0.5 | 0.5 | ✓ Match |
| Pitch Diameter | 5.0mm | 6.0mm | — |
| Center Distance | — | — | 5.5mm ✓ |
| Pressure Angle | 20° | 20° | ✓ Match |

### **Hardware List (per tuner)**

| Item | Specification | Qty |
|------|---------------|-----|
| Worm gear | Module 0.5, 6.0mm OD, brass, drill/broach to 3mm sq | 1 |
| Worm wheel | Module 0.5, 12T, 6.9mm OD, brass, drill/broach to 3mm sq | 1 |
| Peg retention screw | M2 × 3mm pan head | 1 |
| Post retention screw | M2 × 3mm pan head | 1 |
| Washer | ~4mm ID, spacing wheel on post | 1 |
| Loctite | Blue 242 (removable) | — |
| 3mm square broach | For both worm and wheel bores | — |