# Non-Manifold Edge (NME) Healing

## What are Non-Manifold Edges?

A non-manifold edge is an edge shared by more than two faces. In a valid solid (manifold), every edge is shared by exactly two faces. NMEs make geometry ambiguous for CNC toolpath generation and can cause issues in downstream CAD/CAM software.

## Why NMEs occur in this project

The peg head component is built by boolean-fusing four overlapping solids:

1. Peg head reference STEP (ring, pip, cap, shoulder)
2. Core shaft cylinder
3. Bearing shaft cylinder
4. Worm reference STEP

These parts have overlapping boundaries by design (0.1mm overlap for reliable boolean fusion). OCCT's boolean engine produces 4 non-manifold edges at the worm thread termination points (where the helical thread surface intersects the flat end-faces of the worm). These are ~29nm arc-length circular arcs — numerical noise from the boolean kernel, far below any manufacturing tolerance.

## The healing pipeline

### _heal_shape() in peg_head.py

The `_heal_shape()` function applies two operations:

1. **ShapeList consolidation** — filters out zero-volume degenerate artifacts that OCCT's boolean engine produces alongside the main solid
2. **ShapeFix_Shape** — repairs topology issues (shell orientation, wire defects)

```python
from OCP.ShapeFix import ShapeFix_Shape

fixer = ShapeFix_Shape(shape)
fixer.SetPrecision(0.01)
fixer.Perform()
healed = fixer.Shape()
```

### check_shape_quality() in validation.py

The quality checker distinguishes between:
- **Significant NMEs** (>1 micron arc length) — raises a warning, indicates a real topology problem
- **Degenerate NMEs** (sub-micron arc length) — logged as info only, harmless boolean kernel artifacts

This prevents false alarms from the ~29nm thread termination artifacts while still catching genuine problems.

## Where healing is applied

In `src/gib_tuners/components/peg_head.py`, `_heal_shape()` is called at two points:

1. **After the 4-part fusion** (peg head + core shaft + bearing shaft + worm) — consolidates ShapeList result and fixes topology
2. **After the tap hole subtraction** — handles any artifacts from the boolean cut

## Known residual NMEs

4 degenerate NME edges (~29nm arc length each) persist after healing. These are at:
- Z=0.65mm (worm thread start) — 2 edges
- Z=6.95mm (worm thread end) — 2 edges

These are intrinsic to OCCT's boolean kernel when fusing worm thread geometry and cannot be removed by any standard OCCT healing approach (ShapeFix_Shape, ShapeFix_Solid, BRepBuilderAPI_Sewing, ShapeUpgrade_UnifySameDomain, BRepAlgoAPI_Defeaturing, fuzzy boolean) without destroying solid geometry.

At 29nm, these are:
- 3,400x smaller than the tightest manufacturing tolerance (0.1mm)
- Invisible to any CNC toolpath generator
- Correctly handled by the STL export pipeline (pymeshfix)

## How to verify

Build the peg head and check that no NME **warning** appears:

```bash
python scripts/build.py --gear c13 --hand right --format step --components peg_head
```

The build output should not show "non-manifold edges detected" warnings. The 4 degenerate NMEs are logged silently in the ShapeQualityResult issues list but do not trigger warnings.

```python
from gib_tuners.utils.validation import check_shape_quality

result = check_shape_quality(peg_head_part, "peg_head")
# result.non_manifold_edges == 4 (degenerate, sub-micron)
# No warning is emitted for degenerate edges
```
