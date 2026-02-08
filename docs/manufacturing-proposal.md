# Manufacturing Proposal: 10–20 Pairs of 5-Gang Tuners

**Gear profile:** bh11-cd-fx (globoid worm, M0.6, 11:1 ratio)
**Constraint:** Frames, posts, and pegs must be brass or look like brass.

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

**Recommendation:** Straightforward job-shop CNC work. Any precision machining house with 3-axis mills can do this. The box section provides outer dimensions and wall thickness for free.

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

**Recommendation:** Send to a Swiss-lathe house. At 100–200 qty the setup cost amortises well. The DD flats and cross-hole require a secondary op station or a separate milling setup. V-grooves on the cap could be done on the lathe with a form tool.

---

## Component 3: Peg Head + Worm — Investment Cast + Finish Machine

**This is the most complex and expensive component. The globoid worm thread integral with a decorative ring makes it unsuitable for pure CNC at this batch size.**

- **Material:** C83600 leaded red brass (excellent castability) or CZ121
- **Geometry source:** `reference/peghead-and-shaft.step` (ring) + `config/bh11-cd-fx/worm_m0.6_z1.step` (worm)
- **Two variants needed:** RH worm (50–100 pcs) and LH worm (50–100 pcs)

### Recommended process: 3D-printed wax patterns → investment casting → finish machining

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

### Why not full CNC?

The ring has a 9.8mm offset bore (finger grip), complex revolved profile, pip, and cap. Machining this from ø14mm bar on a 5-axis mill would work but at ~3x the per-piece cost and enormous material waste. Investment casting gets the complex ring near-net-shape, and you only machine the precision functional surfaces.

### Alternative: CNC + assembled worm

Machine the peg head (ring + shaft) as a turned/milled part, and press-fit or silver-solder a separately-made worm onto the shaft. This decouples the two hard problems but adds an assembly step and a potential failure mode. The spec explicitly wants integral worm for strength — stick with casting.

**Estimated cost:** £15–25 per finished piece (pattern + casting + machining).

---

## Component 4: Worm Wheel — 5-Axis CNC from STEP

**The globoid tooth form rules out standard hobbing and wire EDM. The STEP file is the manufacturing definition.**

- **Material:** Phosphor bronze PB102 (C51000) — **recommended over brass**
  - Excellent wear against brass worm (dissimilar metals reduce galling)
  - Colour is close to brass (warm golden-bronze) — satisfies "looks like brass"
  - Superior fatigue life for gear teeth at M0.6 scale
  - If pure brass colour is essential: use CZ121 brass instead
- **Geometry source:** `config/bh11-cd-fx/wheel_m0.6_z11.step`
- **Key dims:** 11 teeth, M0.6, 7.6mm OD, 7.6mm face width, ø3.5mm DD bore, profile shift +0.3
- **Two variants:** RH-helix (from STEP) and LH-helix (mirror)

### Process

1. Turn blank from ø10mm bar: face to 7.6mm width, bore ø3.5mm with DD flats
2. 5-axis mill tooth profiles referencing imported STEP geometry
3. Deburr tooth edges

**Tooling:** ø0.3–0.5mm ball-nose end mill for tooth root radii. The 0.91mm rim thickness (per geometry analysis) means light cuts to avoid distortion.

### Alternative: Investment cast from 3D-printed patterns

- Print wheel STEP at 25μm resolution in castable wax
- Cast in phosphor bronze
- Pro: No 5-axis mill needed, good for the globoid form
- Con: Tooth profile accuracy may suffer; each pattern is consumed (no re-use)
- **Verdict:** Viable if tooth accuracy tolerance is >±0.05mm. Worth testing with a pilot batch.

**Estimated cost:** £8–15 per piece (5-axis CNC), or £5–10 per piece if cast.

---

## Manufacturing Strategy Summary

| Component | Process | Material | Qty (20 pairs) | Est. unit cost |
|-----------|---------|----------|-----------------|----------------|
| Frame | CNC mill from box section | CZ121 brass box 10x10x1.1 | 40 | £20–30 |
| String post | Swiss lathe + secondary ops | CZ121 brass bar ø8mm | 200 | £5–8 |
| Peg head + worm | 3D wax → investment cast → finish machine | C83600 or CZ121 brass | 200 | £15–25 |
| Worm wheel | 5-axis CNC from STEP (or cast pilot) | PB102 phosphor bronze | 200 | £8–15 |
| Hardware | Buy-in | Stainless/brass | ~800 pcs | £0.10–0.30 ea |

---

## Rough Cost Estimate

### 20 pairs

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

For 10 pairs, setup costs don't halve, so expect ~£600–700 per pair.

---

## Recommended Execution Plan

### Phase 0 — Prototype Validation (before committing to batch)

1. Build 2x-scale FDM prints for fit checking (`python scripts/build.py --gear bh11-cd-fx --scale 2.0 --tolerance prototype_fdm`)
2. Build 1x-scale resin prints for dimensional validation
3. Cast 2–3 pilot peg heads from resin patterns to validate casting process
4. Machine 2–3 pilot string posts to validate Swiss lathe program
5. CNC 1 pilot frame to validate fixturing and hole positions

### Phase 1 — Material Procurement

- CZ121 brass box section 10x10x1.1mm wall (source from metal stockholder, ~3m needed for 20 pairs)
- CZ121 brass bar ø8mm (source ~4m for 200 posts + offcuts)
- PB102 phosphor bronze bar ø10mm (~2m for 200 wheels)
- Formlabs Castable Wax 40 resin (1–2L for 200 peg head patterns)

### Phase 2 — Parallel Production

- **Stream A:** Frame machining (CNC shop, 2–3 weeks)
- **Stream B:** String post turning (Swiss lathe shop, 1–2 weeks)
- **Stream C:** Peg head pattern printing → casting → finish machining (4–6 weeks, longest lead)
- **Stream D:** Wheel machining (5-axis shop, 2–3 weeks)

### Phase 3 — Assembly & QC

- Assembly per spec Section 6 (worm → wheel → post sandwich)
- Function test each unit (smooth rotation, no binding, backlash check)
- Pair and package RH + LH sets

---

## Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Globoid worm accuracy from casting | Poor mesh, rough feel | Finish-machine worm thread; run pilot batch first |
| 0.91mm wheel rim thickness | Tooth breakage during machining | Light cuts, proper work-holding, consider casting instead |
| Box section wall variation | Bearing hole tolerance blown | Source measured/certified stock; verify incoming dimensions |
| DD fit too tight or loose | Wheel slips or won't assemble | Validate with pilot parts before full batch |
| LH worm pattern | Mirror STEP may have geometry issues | Validate LH mirror in build123d before printing patterns |

---

## Brass Appearance Options

The spec already calls for brass on all visible parts. For the wheels specifically:

1. **Phosphor bronze (PB102)** — Recommended. Warm golden colour, superior wear. Virtually indistinguishable from brass when installed. This is what high-end watchmakers use for similar worm wheels.

2. **CZ121 brass** — Same material as frame and posts. Visually identical. Slightly worse wear characteristics (brass on brass) but acceptable at the low loads of guitar tuners.

3. **Nickel silver (NS106)** — Silver-brass appearance. Would only suit instruments with nickel hardware. Not recommended for a historic brass-look reproduction.
