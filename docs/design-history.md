# Design History: Gib Tuners Mk2

## Phase 1: Foundation (Jan 29, 2026)

**PR #1 — Initial parametric frame**
- Established coordinate system: Z=0 at mounting plate, frame extends into -Z
- Parametric 1–N housing support with symmetric 10mm ends
- RH default: worm entry on +X, peg bearing on -X; LH is mirror

**PR #2 — String post redesign & 7.5mm wheel**
- Replaced E-clip groove retention with M2 tap bore from bottom (screw retention)
- Adopted 7.5mm OD wheel, 13-tooth, M0.5, 5.75mm center distance
- Frame set to 10x10x1mm box section
- Added DD (double-D) section on string post for wheel engagement

**PR #3 — Peg head construction & gear consistency**
- Peg head built by importing reference STEP, cutting at Z=0, adding new 3.5mm shaft
- Worm positioned butted against shoulder at Z=0
- Shaft: worm(7.8mm) + gap(0.2mm) + bearing wall(1.0mm) + clearance(0.1mm) = 9.1mm
- Frame adjusted to 10.35mm outer, 1.1mm wall

**PR #5 — Worm-wheel mesh positioning**
- Post/wheel axis at Y=0, worm axis at Y=+5.75mm (center distance)
- Worm centered in 8.15mm cavity with 0.175mm clearance each side

**PR #7 — Mesh rotation optimization**
- 14.75° worm rotation eliminates gear mesh interference at assembly Z-offset

**PR #9 — Frame dimensions corrected**
- Reverted to 10mm box outer, 1mm wall (eliminated all 1-gang interference)

## Phase 2: Gear Profile Evolution (Jan 30 – Feb 1, 2026)

**PR #13 — Globoid worm support**
- Added Z-axis alignment modes: AUTO (centered for cylindrical, aligned for globoid)
- New enums: WormType (CYLINDRICAL, GLOBOID), WormZMode (AUTO, CENTERED, ALIGNED)

**PR #16 — Bearing tolerances tightened for string tension**
- Bearing clearance reduced from +0.2mm to +0.05mm (reamed holes)
- Post bearing: 4.2→4.05mm, peg bearing: 4.0→3.85mm
- Reduced post tilt under 100N load from ~11° to ~3°

**PR #17 — Switch to M0.6 balanced profile**
- Gear module M0.5→M0.6, ratio 13:1→10:1
- Peg shaft increased 3.5→4.0mm for stronger M2 tap wall (0.95→1.2mm)
- All bearing holes now derived from component dimensions + 0.05mm clearance
- Switched to M2.5 washer with M2 screw (3x better peg retention, 0.25→0.75mm overlap)

**PR #20 — Axial play & retention mechanism**
- Post bearing axial play: 0.2mm (frame floats between clamping surfaces)
- Peg bearing axial play: 0.2mm
- DD cut clearance: 0.1mm (M2 screw clamps wheel to shoulder)
- Wall thickness declared fixed manufacturing constraint at 1.1mm

**PR #25 — Tighter post bearing play**
- Post bearing axial play reduced 0.2→0.1mm, bearing length 1.3→1.2mm

## Phase 3: Manufacturing Refinement (Feb 1–2, 2026)

**PR #27 — Wall thickness fixed at 1.1mm**
- Corrected from 1.0mm — this is the brass box section stock dimension, non-negotiable

**PR #31 — M2 tap depth optimized**
- Reduced M2 tap from 4mm to 3mm depth
- Improved worm wall thickness: 0.59→0.75mm (safety factor 8.1x→10.9x)
- String tension pulls worm into frame, so screw just holds in place when unloaded

**PR #32 — Wheel inlet hole redesigned**
- Reduced from 8mm to 5.1mm (4.9mm M2 washer + 0.2mm tolerance)
- Key insight: wheel enters sideways from open frame end, not through bottom hole
- Assembly order: Worm first → Wheel (sideways) → Post (DD engages wheel bore)

**PR #34 — BH11-CD gear configuration**
- M0.6 globoid worm, 11-tooth, hobbed profile

## Phase 4: Jig Design (Feb 4–6, 2026)

**PR #35 — Cutting jig**
- U-channel (10.3x10mm) with saw guide slots and kerf compensation
- Fixed locating plug + moveable end stop with M5 heat-set inserts

**PR #39 — Drilling jig**
- 2-part clamshell for drilling all 26 holes in an N-gang frame
- M14 stepped bushing pockets with 5mm minimum rim
- Dynamic wall extension per gear profile

**PR #41 — Hardware downsized M5→M3**
- Bolt clearance 5.5→3.4mm, insert OD 6.4→5.0mm
- Heat-set insert depth matched to actual insert height (4mm)

**PR #43 — Prototype drilling mode**
- Prototype: simple through-holes, 30mm wide, 8mm slab (for marking positions)
- Production: M14 stepped bushing pockets, 40mm wide, 14mm slab

**PR #44 — Heat-set insert interference fit**
- Pocket diameter reduced 5.0→4.7mm (0.3mm interference for knurling grip)
- Inserts were falling out at nominal 5.0mm

**PR #46 — Clamping plug end stop**
- Cavity extended 4mm past nominal frame length
- 10x10mm plug seats in channel, accommodates up to 4mm length variation

## Phase 5: String Post Detail & DD Fit (Feb 6–7, 2026)

**PR #47 — String post cap detail**
- Added 0.25mm fillet to cap top and bottom edges
- 3 decorative concentric V-grooves on cap top (0.33x0.33mm, outer OD 6mm)
- String post bearing increased 4.0→5.0mm; frame hole auto-derives to 5.05mm

**PR #50 — BH11-CD-FX gear profile**
- Positive profile shift (+0.3), worm relief groove
- Center distance 5.6→6.2mm, shallower teeth, stronger roots

**PR #54 — DD slip fit for compression retention**
- DD shaft undersized 0.1mm for slip fit (3.4/2.4mm AF vs 3.5/2.5mm bore)
- Bottom gap increased 0.1→0.5mm for compression travel
- Wheel positioned in clamped state: top against bearing shoulder, gap at bottom
- Washer+screw now clamps wheel via compression, not tight interference

## Phase 6: C13 Gear Profile (Feb 9, 2026)

**PR #55 — Three new gear profiles with manufacturing proposal**
- c11: Cylindrical, 25° pressure angle (standard)
- cyl11: Cylindrical, 20° pressure angle (optimized for batch production)
- trim: Globoid with virtual hobbing (premium option)
- Recommended CZ121 brass (machining), PB102 phosphor bronze (wheels)

**PR #57 — C13 adopted as preferred profile**
- M0.5, 13-tooth, 20° pressure angle, cylindrical worm
- Centre distance 6.25mm
- 1.02mm rim thickness (vs 0.8mm for cyl11) — more robust for hobbing
- Profile shift +0.3 for stronger tooth roots

**PR #58 — C13 shaft diameter override**
- Peg shaft set to 4.5mm (matches c13 worm root diameter for smooth transition)

**PR #60 — Manufacturing proposal rewritten for c13**
- Single recommended path (removed globoid A/B options)
- Finer pitch M0.5 = smoother feel, 13:1 ratio = finer tuning resolution

## Phase 7: Final Refinements (Feb 9–11, 2026)

**PR #62 — C13-10 configuration & core shaft fix**
- C13 gears with 1.0mm wall thickness and 7.7mm gear width for manufactured frames
- Core shaft undercut 0.1mm to prevent coincident surfaces eating worm teeth

**PR #64 — Decorative frame engraving**
- Rope-border inspired engraving on top plate
- Two border grooves (1mm and 2mm from edge) with 45° diagonal hatching
- Chevron pattern where short-end diagonals meet at centerline

**PR #65 — Swept worm peg head**
- Regenerated c13-10 STEP files from swept worm tool (cleaner geometry vs 36-section loft)
- Relief groove at bearing end filled for stronger M2 tap region
- Washer clearance (0.1mm) added to shaft protrusion beyond frame wall

## Key Design Decisions Summary

| Decision | Early | Final |
|----------|-------|-------|
| Gear module | M0.5 → M0.6 → **M0.5 (c13)** | Back to finer pitch |
| Gear ratio | 13:1 → 10:1 → **13:1 (c13)** | Back to finer resolution |
| Worm type | Cylindrical → Globoid → **Cylindrical** | Simpler manufacturing |
| Frame box | 10→10.35→**10mm**, wall 1.0→**1.1mm** | Stock dimension fixed |
| Peg shaft | 3.5→4.0→**4.5mm** | Matches worm root |
| Retention | E-clip → **M2 screw + compression DD** | Simpler assembly |
| Wheel entry | Through bottom hole → **Sideways from open end** | Smaller hole, stronger frame |
| Bearing clearance | +0.2mm → **+0.05mm** | Tighter for string load |
| Jig hardware | M5 → **M3** | Proportionate to jig size |
| Jig insert fit | Nominal → **0.3mm interference** | Knurling needs grip |
