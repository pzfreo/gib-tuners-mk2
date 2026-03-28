# Plan: Add Decorative Engraving to Frame Top Plate

## What
Add a simplified rope-border engraving around all 4 edges of the frame's top surface (Z=0). Based on the original vintage tuner: two thin border lines with a diagonal hatching pattern between them, ~1mm inset from the frame edge.

## Design

### Engraving geometry
- **Inset from edge:** 1.0mm (outer border line center)
- **Border band width:** ~1.5mm (outer line at 1.0mm, inner line at 2.5mm from edge)
- **Groove depth:** 0.2mm (shallow engraving into Z=0 surface)
- **Groove width:** ~0.2mm (V-groove or thin rectangular cut)
- **Rope pattern:** Diagonal hatching lines between the two borders at ~45°, spaced ~1mm apart — reads as a simplified rope/twist at this scale

### Frame top surface coordinates
- X: -5.0 to +5.0 (10mm wide)
- Y: 0 to 145.0 (for 5-gang)
- Z=0 is the top surface

### Engraving path (rectangular loop)
- Outer border: rectangle at X=[-4.0, 4.0], Y=[1.0, 144.0]
- Inner border: rectangle at X=[-2.5, 2.5], Y=[2.5, 142.5]
- Diagonal fills between borders on each of the 4 sides

### Obstacles to avoid
- Mounting holes (6 positions along centerline) — engraving goes around them since border is along the edge, not the center. No conflict.
- Post holes — also on centerline. No conflict with edge border.

## Implementation

### Step 1: Add `EngravingParams` dataclass to `parameters.py`
New frozen dataclass with:
- `inset: float = 1.0` — distance from frame edge to outer border
- `band_width: float = 1.5` — width of decorative band
- `depth: float = 0.2` — groove depth
- `groove_width: float = 0.2` — groove line width
- `hatch_spacing: float = 1.0` — diagonal line spacing
- `enabled: bool = True` — toggle engraving on/off

Add `engraving: EngravingParams` field to `FrameParams`.

### Step 2: Add `_create_engraving()` function in `frame.py`
New private function that:
1. Creates two rectangular groove loops (outer and inner borders) as thin Box cuts
2. Creates diagonal hatch lines between the borders on each of the 4 sides
3. Returns the combined engraving solid to subtract from the frame

For each border line (outer and inner):
- 4 thin Box cuts forming a rectangle (top, bottom, left, right edges)

For diagonal hatching on each side:
- Generate angled line segments between the two borders
- Each line is a thin rotated Box or extruded path
- ~45° angle, spaced by `hatch_spacing`

### Step 3: Integrate into `create_frame()`
- Call `_create_engraving()` after the text label (line ~230)
- Subtract from frame: `frame = frame - engraving`
- Before `check_shape_quality()`

### Step 4: Test and visualize
- Run `python scripts/viz.py -n 1 --gear c13` to verify single-housing appearance
- Run existing tests to confirm no regressions
- Export STEP and verify bounding box unchanged (10×145×10)

## Files modified
1. `src/gib_tuners/config/parameters.py` — add `EngravingParams` dataclass
2. `src/gib_tuners/components/frame.py` — add `_create_engraving()` and call it

## Risk
- Many small boolean cuts could slow OCCT or produce NME edges. If so, we can reduce hatch density or simplify further.
- Diagonal hatches near corners need care to avoid overlapping with the border lines.
