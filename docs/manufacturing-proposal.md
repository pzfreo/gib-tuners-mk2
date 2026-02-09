# Manufacturing Proposal: 10–20 Pairs of 5-Gang Tuners

**Constraint:** Frames, posts, and pegs must be brass or look like brass.

Two gear profiles are evaluated:

| Profile | Config | Worm Type | Key Difference |
|---------|--------|-----------|----------------|
| bh11-cd-fx | `config/bh11-cd-fx/` | Globoid | Higher quality mesh, complex manufacturing |
| cyl11 | `config/cyl11/` | **Cylindrical** | **Standard manufacturing, lower cost** |

**Recommendation: Use cyl11 (cylindrical) for batch production.** Every component falls into standard job-shop territory — no 5-axis milling, no investment casting required. See [Gear Profile Comparison](#gear-profile-comparison) at the end for details.

---

## Bill of Materials (per pair = 1 RH + 1 LH)

| Component | Per pair | 10 pairs | 20 pairs | Notes |
|-----------|---------|----------|----------|-------|
| Frame | 2 | 20 | 40 | 1 RH + 1 LH (mirrored) |
| Peg head + worm | 10 | 100 | 200 | 5 RH-thread + 5 LH-thread |
| Worm wheel | 10 | 100 | 200 | 5 RH-helix + 5 LH-helix |
| String post | 10 | 100 | 200 | Symmetric — identical for both hands |
| M2 x 4mm pan head screw | 20 | 200 | 400 | Peg + post retention |
| M2.5 washer (5.5mm OD) | 10 | 100 | 200 | Peg shaft retention |
| M2 washer (~5mm OD) | 10 | 100 | 200 | Post retention |
| Mounting bolts (mushroom head) | 12 | 120 | 240 | 6 per frame |

**Total custom parts: 32 per pair, 640 for 20 pairs.**

---

## Component 1: Frame — CNC Mill from Stock Box Section

**The easiest component. The stock material does most of the work.**

- **Material:** CZ121 (CW614N) free-machining brass box section, 10mm x 10mm, 1.1mm wall
- **Stock length:** 145mm per frame (cut from 1m or 2m bars)
- **Tooling cost:** Nil beyond standard cutters + one soft-jaw fixture

### Operations (single-setup on 4-axis mill or 3-axis with indexing)

1. Cut bar to 145mm (saw)
2. Mill away top + side walls between housings, leaving 5 rigid boxes connected by the 1.1mm mounting plate
3. Drill + ream 5x post bearing holes — top face, ø5.05mm (H7)
4. Drill 5x wheel inlet holes — bottom face, ø5.1mm
5. Drill 5x worm entry holes — one side face, ø7.2mm
6. Drill + ream 5x peg bearing holes — opposite side face, ø4.05mm (H7)
7. Drill 6x ø3.0mm mounting holes in bottom plate (in gaps between housings)
8. Engrave "R" or "L" on inside surface (laser or engraving cutter)
9. Deburr all edges

**LH frame** is the same program with entry/bearing holes swapped sides. Same fixture, flip the workpiece.

**Critical tolerances:** Reamed bearing holes ±0.01mm, housing pitch 27.2mm ±0.05mm.

**Estimated cycle:** ~15–20 min per frame once fixtured.

**Recommendation:** Straightforward job-shop CNC work. Any precision machining house with 3-axis mills can do this. The box section provides outer dimensions and wall thickness for free. Same frame for both gear profiles (hole positions shift by <0.2mm for the CD change; use cyl11 CD of 6.2mm).

---

## Component 2: String Post — Swiss Screw Machining

**Classic multi-diameter turned part. A Swiss lathe shop will barely blink at this.**

- **Material:** CZ121 brass round bar, ø8mm
- **All 200 posts are identical** (symmetric for both hands)

### Dimensions (bottom to top)

| Section | Diameter | Length |
|---------|----------|--------|
| DD cut (wheel interface) | ø3.4mm, AF 2.4mm | 7.1mm |
| Frame bearing | ø5.0mm | 1.2mm |
| Visible post | ø6.0mm | 5.5mm |
| Cap | ø7.5mm | 1.0mm |
| **Total** | | **14.8mm** |

### Operations

1. **Swiss lathe (primary):** Turn all 4 diameters, form cap fillet (0.25mm R), part off
2. **Secondary ops (transfer or bench mill):**
   - Mill 2x DD flats (0.5mm deep, forming AF 2.4mm)
   - Cross-drill ø1.5mm string hole (2.75mm from bearing shoulder)
   - Tap M2 blind hole from bottom (4mm deep)
   - Cut 3x concentric V-grooves on cap face (0.33mm wide/deep, outer ø6mm)

**Critical tolerances:** ø5.0mm bearing h7 (−0/−0.012mm), DD flats ±0.02mm.

**Estimated cycle:** ~2 min on Swiss lathe + 3–4 min secondary ops.

**Recommendation:** Send to a Swiss-lathe house. At 100–200 qty the setup cost amortises well. The DD flats and cross-hole require a secondary op station or a separate milling setup. V-grooves on the cap could be done on the lathe with a form tool. Same part regardless of gear profile.

---

## Component 3: Peg Head + Worm

The manufacturing approach depends heavily on the gear profile choice.

### Option A: Cylindrical worm (cyl11) — CNC Lathe + Mill (RECOMMENDED)

**A cylindrical worm thread can be single-point cut on a standard CNC lathe. This opens up a pure-machining route, eliminating investment casting.**

- **Material:** CZ121 free-machining brass, ø14mm bar
- **Geometry source:** `reference/peghead-and-shaft.step` (ring) + cylindrical thread from worm_gear.json
- **Two variants needed:** RH worm (50–100 pcs) and LH worm (50–100 pcs)

**Process (CNC lathe with live tooling, or lathe + mill):**

1. **Lathe — main profile:** Turn shaft ø4.0mm, shoulder, and outer ring envelope from ø14mm bar
2. **Mill — ring features:** Mill the offset bore (ø9.8mm, 0.25mm offset), pip, and cap using live tooling or transfer to mill
3. **Lathe — worm thread:** Single-point cut cylindrical worm, M0.6, single-start, 7.6mm long. Standard threading cycle on CNC lathe.
4. **Drill + tap:** M2 hole in shaft end, 4mm deep
5. **Finish:** Chamfer edges (0.3mm), light polish

**Critical tolerances:**
- Shaft ø4.0mm: h7 (−0/−0.012mm)
- Worm pitch diameter 5.8mm: ±0.02mm
- Cap ø8.5mm: ±0.1mm (must be > 7.2mm entry hole)

**Estimated cycle:** ~8–12 min per piece.
**Estimated cost:** £8–15 per piece (pure CNC, no casting tooling).

### Option B: Globoid worm (bh11-cd-fx) — Investment Cast + Finish Machine

**The globoid worm thread integral with a decorative ring makes it unsuitable for pure CNC at this batch size.**

- **Material:** C83600 leaded red brass (excellent castability) or CZ121
- **Geometry source:** `reference/peghead-and-shaft.step` (ring) + `config/bh11-cd-fx/worm_m0.6_z1.step` (worm)

**Process: 3D-printed wax patterns → investment casting → finish machining**

**Step 1 — Pattern Creation:**
- Export combined peg head+worm as STL from build123d at 1.015x (casting shrinkage compensation)
- Print in castable wax resin (Formlabs Castable Wax 40, 25μm layers)
- Tree 6–8 patterns per sprue
- Cost per pattern: ~£1–2 in resin, ~1–2 hrs print time per tree

**Step 2 — Investment Casting:**
- Shell-coat wax trees (ceramic slurry, 4–6 dips)
- Burnout and pour brass at ~1000°C
- Expect ±0.1–0.2mm on all features, slight surface texture on worm teeth
- **Foundry batch:** 100–200 castings is a good batch for most jewellery/instrument foundries

**Step 3 — Finish Machining (critical surfaces only):**
1. Lathe: true shaft to ø4.0mm h7 (the bearing surface)
2. Lathe or grinder: clean up globoid worm thread pitch surface (referencing STEP geometry)
3. Tap M2 hole in shaft end, 4mm deep
4. Light barrel-polish or hand-polish the decorative ring

**Estimated cost:** £15–25 per finished piece (pattern + casting + machining).

---

## Component 4: Worm Wheel

### Option A: Cylindrical (cyl11) — Standard Gear Hobbing (RECOMMENDED)

**With a cylindrical worm and no profile shift, the wheel has standard involute teeth that can be cut with an off-the-shelf M0.6 hob.**

- **Material:** Phosphor bronze PB102 (C51000) — recommended for wear; or CZ121 brass
- **Key dims:** 11 teeth, M0.6, 7.6mm OD, 7.6mm face width, ø3.5mm DD bore, no profile shift
- **Two variants:** RH-helix and LH-helix (reverse hob rotation)

**Process:**
1. Turn blank from ø10mm bar: face to 7.6mm width, bore ø3.5mm with DD flats
2. **Hob teeth** with standard M0.6 gear hob on a hobbing machine
3. Deburr tooth edges

**Alternative methods (all viable for cylindrical teeth):**
- **Wire EDM:** Cut tooth profiles from pre-bored blanks. Good accuracy, no hob needed.
- **CNC gear milling:** Single end mill, indexing each tooth gap. Slower but no special tooling.

**Rim thickness:** 0.8mm (root ø5.1mm to bore ø3.5mm). Adequate for bronze at guitar tuner loads. Use light cuts during hobbing to avoid distortion.

**Estimated cost:** £2–5 per piece (hobbed), £3–5 per piece (wire EDM).

### Option B: Globoid (bh11-cd-fx) — 5-Axis CNC from STEP

**The globoid tooth form rules out standard hobbing and wire EDM. The STEP file is the manufacturing definition.**

- **Material:** PB102 phosphor bronze or CZ121 brass
- **Geometry source:** `config/bh11-cd-fx/wheel_m0.6_z11.step`
- **Key dims:** 11 teeth, M0.6, 7.6mm OD, 7.6mm face width, ø3.5mm DD bore, profile shift +0.3

**Process:**
1. Turn blank from ø10mm bar: face to 7.6mm width, bore ø3.5mm with DD flats
2. 5-axis mill tooth profiles referencing imported STEP geometry
3. Deburr tooth edges

**Tooling:** ø0.3–0.5mm ball-nose end mill for tooth root radii. The 0.91mm rim thickness means light cuts.

**Alternative:** Investment cast from 3D-printed wax patterns. Viable if tooth accuracy tolerance is >±0.05mm.

**Estimated cost:** £8–15 per piece (5-axis CNC), or £5–10 per piece if cast.

---

## Manufacturing Strategy Summary

### Cylindrical (cyl11) — RECOMMENDED

| Component | Process | Material | Qty (20 pairs) | Est. unit cost |
|-----------|---------|----------|-----------------|----------------|
| Frame | CNC mill from box section | CZ121 brass box 10x10x1.1 | 40 | £20–30 |
| String post | Swiss lathe + secondary ops | CZ121 brass bar ø8mm | 200 | £5–8 |
| Peg head + worm | CNC lathe + live tooling | CZ121 brass bar ø14mm | 200 | £8–15 |
| Worm wheel | Gear hobbing (M0.6 hob) | PB102 phosphor bronze | 200 | £2–5 |
| Hardware | Buy-in | Stainless/brass | ~800 pcs | £0.10–0.30 ea |

### Globoid (bh11-cd-fx) — Premium option

| Component | Process | Material | Qty (20 pairs) | Est. unit cost |
|-----------|---------|----------|-----------------|----------------|
| Frame | CNC mill from box section | CZ121 brass box 10x10x1.1 | 40 | £20–30 |
| String post | Swiss lathe + secondary ops | CZ121 brass bar ø8mm | 200 | £5–8 |
| Peg head + worm | 3D wax → investment cast → finish machine | C83600 or CZ121 brass | 200 | £15–25 |
| Worm wheel | 5-axis CNC from STEP (or cast) | PB102 phosphor bronze | 200 | £8–15 |
| Hardware | Buy-in | Stainless/brass | ~800 pcs | £0.10–0.30 ea |

---

## Rough Cost Estimate (20 pairs)

### Cylindrical (cyl11) — RECOMMENDED

| | Unit cost | Qty | Subtotal |
|---|----------|-----|----------|
| Frames | £25 | 40 | £1,000 |
| String posts | £6.50 | 200 | £1,300 |
| Peg heads | £12 | 200 | £2,400 |
| Wheels | £3.50 | 200 | £700 |
| Hardware | £0.20 | 800 | £160 |
| Setup/tooling (amortised) | | | ~£800 |
| **Total** | | | **~£6,360** |
| **Per pair** | | | **~£320** |

### Globoid (bh11-cd-fx) — Premium option

| | Unit cost | Qty | Subtotal |
|---|----------|-----|----------|
| Frames | £25 | 40 | £1,000 |
| String posts | £6.50 | 200 | £1,300 |
| Peg heads | £20 | 200 | £4,000 |
| Wheels | £12 | 200 | £2,400 |
| Hardware | £0.20 | 800 | £160 |
| Setup/tooling (amortised) | | | ~£1,500 |
| **Total** | | | **~£10,400** |
| **Per pair** | | | **~£520** |

For 10 pairs: cylindrical ~£400/pair, globoid ~£650/pair.

---

## Recommended Execution Plan (Cylindrical)

### Phase 0 — Prototype Validation (before committing to batch)

1. Build 2x-scale FDM prints for fit checking (`python scripts/build.py --gear cyl11 --scale 2.0 --tolerance prototype_fdm`)
2. Build 1x-scale resin prints for dimensional validation
3. CNC 1 pilot peg head to validate lathe program and worm thread
4. Machine 2–3 pilot string posts to validate Swiss lathe program
5. Hob 2–3 pilot wheels to validate tooth mesh with pilot worm
6. CNC 1 pilot frame to validate fixturing and hole positions
7. Assemble 1 complete pilot unit — verify fit, rotation, backlash

### Phase 1 — Material Procurement

- CZ121 brass box section 10x10x1.1mm wall (~3m for 20 pairs)
- CZ121 brass bar ø8mm (~4m for 200 posts)
- CZ121 brass bar ø14mm (~4m for 200 peg heads)
- PB102 phosphor bronze bar ø10mm (~2m for 200 wheels)
- M0.6 gear hob (off-the-shelf, or verify gear shop has one)

### Phase 2 — Parallel Production

- **Stream A:** Frame machining (CNC shop, 2–3 weeks)
- **Stream B:** String post turning (Swiss lathe shop, 1–2 weeks)
- **Stream C:** Peg head turning + worm threading (CNC lathe shop, 2–3 weeks)
- **Stream D:** Wheel blanking + hobbing (gear shop, 1–2 weeks)

**Total lead time: ~3–4 weeks** (all streams in parallel, no casting bottleneck).

### Phase 3 — Assembly & QC

- Assembly per spec Section 6 (worm → wheel → post sandwich; order flexible with cylindrical)
- Function test each unit (smooth rotation, no binding, backlash check)
- Pair and package RH + LH sets

---

## Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Zero backlash with manufacturing variation | Tight spots, rough feel | Add 0.02–0.05mm backlash in JSON; verify on pilot |
| 0.8mm wheel rim thickness (cyl11) | Tooth chipping during hobbing | Light cuts, climb hobbing, proper work-holding |
| Box section wall variation | Bearing hole tolerance blown | Source measured/certified stock; verify incoming dims |
| DD fit too tight or loose | Wheel slips or won't assemble | Validate with pilot parts before full batch |
| Peg head ring complexity on CNC | Poor surface finish in bore | May need casting for ring only; worm still CNC |
| LH worm thread | Left-hand threading less common | Most CNC lathes support it; verify with shop |

---

## Brass Appearance Options

The spec calls for brass on all visible parts. For the wheels specifically:

1. **Phosphor bronze (PB102)** — Recommended. Warm golden colour, superior wear against brass worm (dissimilar metals reduce galling). Virtually indistinguishable from brass when installed. Standard in watchmaking and precision gear applications.

2. **CZ121 brass** — Same material as frame and posts. Visually identical. Slightly worse wear (brass on brass) but acceptable at guitar tuner loads (~80N string tension).

3. **Nickel silver (NS106)** — Silver-brass appearance. Only for instruments with nickel hardware. Not recommended for historic brass-look reproduction.

---

## Gear Profile Comparison

| Parameter | bh11-cd-fx (globoid) | cyl11 (cylindrical) |
|-----------|---------------------|---------------------|
| Worm type | Globoid | Cylindrical |
| Centre distance | 6.035mm | 6.2mm |
| Wheel profile shift | +0.3 | 0 (standard) |
| Wheel root diameter | 5.46mm | 5.1mm |
| Wheel rim thickness | 0.91mm | 0.8mm |
| Virtual hobbing | Yes (72 steps) | No |
| Worm manufacturing | Cast + finish machine | CNC lathe threading |
| Wheel manufacturing | 5-axis CNC or cast | Standard hobbing |
| Teeth in contact | ~2–3 simultaneous | ~1–2 (line contact) |
| Feel quality | Premium (smoother) | Good (standard) |
| Est. cost per pair | ~£520 | ~£320 |
| Lead time | 4–6 weeks | 3–4 weeks |
| Assembly order | Worm first (mandatory) | Flexible |
