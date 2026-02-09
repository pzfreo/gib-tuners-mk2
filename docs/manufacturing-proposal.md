# Manufacturing Proposal: 10–20 Pairs of 5-Gang Tuners

**Constraint:** Frames, posts, and pegs must be brass or look like brass.

**Recommended gear profile: c13** (`config/c13/`). Cylindrical worm, M0.5, 13-tooth wheel, 20° pressure angle, profile shift +0.3. Every component falls into standard job-shop territory — no 5-axis milling, no investment casting required.

| Parameter | Value |
|-----------|-------|
| Gear module | M0.5 |
| Worm type | Cylindrical |
| Wheel teeth | 13 |
| Ratio | 13:1 |
| Pressure angle | 20° |
| Centre distance | 6.25mm |
| Wheel profile shift | +0.3 |
| Wheel rim thickness | 1.02mm |

Key advantages of c13 over earlier profiles (cyl11, bh11-cd-fx):
- **Finer pitch (M0.5 vs M0.6):** smoother feel, finer adjustment resolution
- **13:1 ratio:** higher reduction for more precise tuning
- **1.02mm rim thickness:** significantly more robust than cyl11's 0.8mm, reducing hobbing risk
- **Profile shift +0.3:** stronger tooth roots, better load distribution
- **Standard manufacturing:** all components machinable with conventional CNC and hobbing

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
5. Drill 5x worm entry holes — one side face, ø7.1mm
6. Drill + ream 5x peg bearing holes — opposite side face, ø4.55mm (H7)
7. Drill 6x ø3.0mm mounting holes in bottom plate (in gaps between housings)
8. Engrave "R" or "L" on inside surface (laser or engraving cutter)
9. Deburr all edges

**LH frame** is the same program with entry/bearing holes swapped sides. Same fixture, flip the workpiece.

**Critical tolerances:** Reamed bearing holes ±0.01mm, housing pitch 27.2mm ±0.05mm.

**Estimated cycle:** ~15–20 min per frame once fixtured.

**Recommendation:** Straightforward job-shop CNC work. Any precision machining house with 3-axis mills can do this. The box section provides outer dimensions and wall thickness for free.

---

## Component 2: String Post — Swiss Screw Machining

**Classic multi-diameter turned part. A Swiss lathe shop will barely blink at this.**

- **Material:** CZ121 brass round bar, ø8mm
- **All 200 posts are identical** (symmetric for both hands)

### Dimensions (bottom to top)

| Section | Diameter | Length |
|---------|----------|--------|
| DD cut (wheel interface) | ø3.5mm, AF 2.5mm | 7.1mm |
| Frame bearing | ø5.0mm | 1.2mm |
| Visible post | ø6.0mm | 5.5mm |
| Cap | ø7.5mm | 1.0mm |
| **Total** | | **14.8mm** |

### Operations

1. **Swiss lathe (primary):** Turn all 4 diameters, form cap fillet (0.25mm R), part off
2. **Secondary ops (transfer or bench mill):**
   - Mill 2x DD flats (0.5mm deep, forming AF 2.5mm)
   - Cross-drill ø1.5mm string hole (2.75mm from bearing shoulder)
   - Tap M2 blind hole from bottom (4mm deep)
   - Cut 3x concentric V-grooves on cap face (0.33mm wide/deep, outer ø6mm)

**Critical tolerances:** ø5.0mm bearing h7 (−0/−0.012mm), DD flats ±0.02mm.

**Estimated cycle:** ~2 min on Swiss lathe + 3–4 min secondary ops.

**Recommendation:** Send to a Swiss-lathe house. At 100–200 qty the setup cost amortises well. The DD flats and cross-hole require a secondary op station or a separate milling setup. V-grooves on the cap could be done on the lathe with a form tool. Same part regardless of gear profile.

---

## Component 3: Peg Head + Worm — CNC Lathe + Mill

**A cylindrical worm thread can be single-point cut on a standard CNC lathe. This opens up a pure-machining route, eliminating investment casting.**

- **Material:** CZ121 free-machining brass, ø14mm bar
- **Geometry source:** `reference/peghead-and-shaft.step` (ring) + cylindrical thread from worm_gear.json
- **Two variants needed:** RH worm (50–100 pcs) and LH worm (50–100 pcs)

### Key Dimensions

| Feature | Dimension |
|---------|-----------|
| Shaft (bearing section) | ø4.5mm |
| Shoulder (entry hole interface) | ø7.0mm |
| Worm pitch diameter | 6.0mm |
| Worm tip diameter | 7.0mm |
| Worm root diameter | 4.75mm |
| Worm length | 7.6mm |
| Worm thread | M0.5, single-start, lead 1.57mm |
| Cap | ø8.5mm (must be > 7.1mm entry hole) |

**Process (CNC lathe with live tooling, or lathe + mill):**

1. **Lathe — main profile:** Turn shaft ø4.5mm, shoulder, and outer ring envelope from ø14mm bar
2. **Mill — ring features:** Mill the offset bore (ø9.8mm, 0.25mm offset), pip, and cap using live tooling or transfer to mill
3. **Lathe — worm thread:** Single-point cut cylindrical worm, M0.5, single-start, 7.6mm long. Standard threading cycle on CNC lathe.
4. **Drill + tap:** M2 hole in shaft end, 4mm deep
5. **Finish:** Chamfer edges (0.3mm), light polish

**Critical tolerances:**
- Shaft ø4.5mm: h7 (−0/−0.012mm)
- Worm pitch diameter 6.0mm: ±0.02mm
- Cap ø8.5mm: ±0.1mm (must be > 7.1mm entry hole)

**Estimated cycle:** ~8–12 min per piece.
**Estimated cost:** £8–15 per piece (pure CNC, no casting tooling).

---

## Component 4: Worm Wheel — Standard Gear Hobbing

**With a cylindrical worm, the wheel has involute teeth that can be cut with an off-the-shelf M0.5 hob.**

- **Material:** Phosphor bronze PB102 (C51000) — recommended for wear; or CZ121 brass
- **Key dims:** 13 teeth, M0.5, 7.6mm OD, 7.6mm face width, ø3.5mm DD bore, profile shift +0.3
- **Two variants:** RH-helix and LH-helix (reverse hob rotation)

**Process:**
1. Turn blank from ø10mm bar: face to 7.6mm width, bore ø3.5mm with DD flats
2. **Hob teeth** with standard M0.5 gear hob on a hobbing machine (set hob for +0.3 profile shift)
3. Deburr tooth edges

**Alternative methods (all viable for cylindrical teeth):**
- **Wire EDM:** Cut tooth profiles from pre-bored blanks. Good accuracy, no hob needed.
- **CNC gear milling:** Single end mill, indexing each tooth gap. Slower but no special tooling.

**Rim thickness:** 1.02mm (root ø5.55mm to bore ø3.5mm). Robust for bronze at guitar tuner loads. Comfortable margin for hobbing.

**Estimated cost:** £2–5 per piece (hobbed), £3–5 per piece (wire EDM).

---

## Manufacturing Strategy Summary

| Component | Process | Material | Qty (20 pairs) | Est. unit cost |
|-----------|---------|----------|-----------------|----------------|
| Frame | CNC mill from box section | CZ121 brass box 10x10x1.1 | 40 | £20–30 |
| String post | Swiss lathe + secondary ops | CZ121 brass bar ø8mm | 200 | £5–8 |
| Peg head + worm | CNC lathe + live tooling | CZ121 brass bar ø14mm | 200 | £8–15 |
| Worm wheel | Gear hobbing (M0.5 hob) | PB102 phosphor bronze | 200 | £2–5 |
| Hardware | Buy-in | Stainless/brass | ~800 pcs | £0.10–0.30 ea |

---

## Rough Cost Estimate (20 pairs)

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

For 10 pairs: ~£400/pair.

---

## Recommended Execution Plan

### Phase 0 — Prototype Validation (before committing to batch)

1. Build 2x-scale FDM prints for fit checking (`python scripts/build.py --gear c13 --scale 2.0 --tolerance prototype_fdm`)
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
- M0.5 gear hob (off-the-shelf, or verify gear shop has one)

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
| Box section wall variation | Bearing hole tolerance blown | Source measured/certified stock; verify incoming dims |
| DD fit too tight or loose | Wheel slips or won't assemble | Validate with pilot parts before full batch |
| Peg head ring complexity on CNC | Poor surface finish in bore | May need casting for ring only; worm still CNC |
| LH worm thread | Left-hand threading less common | Most CNC lathes support it; verify with shop |
| M0.5 hob availability | Delays if not in stock | Source early; M0.5 is standard metric, widely available |

---

## Brass Appearance Options

The spec calls for brass on all visible parts. For the wheels specifically:

1. **Phosphor bronze (PB102)** — Recommended. Warm golden colour, superior wear against brass worm (dissimilar metals reduce galling). Virtually indistinguishable from brass when installed. Standard in watchmaking and precision gear applications.

2. **CZ121 brass** — Same material as frame and posts. Visually identical. Slightly worse wear (brass on brass) but acceptable at guitar tuner loads (~80N string tension).

3. **Nickel silver (NS106)** — Silver-brass appearance. Only for instruments with nickel hardware. Not recommended for historic brass-look reproduction.
