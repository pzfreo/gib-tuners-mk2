# Building the Gib Tuners: A Coding Story

This project set out to create a fully parametric CAD model of a 5-gang worm-drive tuning machine for historic guitar restoration, written entirely in Python using build123d. The goal was to produce manufacturing-ready STEP files for brass components that replicate the look and feel of original 19th-century tuners while being practical to machine in small batches. Almost the entire codebase — 69 merged PRs over two weeks — was written with Claude Code as a coding partner.

## Getting the geometry right

The first challenge was simply getting parts to fit inside a 10mm brass box section. The frame, string post, worm wheel, and peg head all occupy the same tiny cavity, and every dimension is coupled. Change the gear module and the center distance shifts, which moves the worm entry hole, which changes how much wall is left for the M2 tap hole. Early on, we bounced between 10mm and 10.35mm outer dimensions and between 1.0mm and 1.1mm wall thickness before discovering that 1.1mm was non-negotiable — it's what the brass stock actually measures.

Positioning the worm-wheel mesh was fiddly. The worm sits perpendicular to the frame, spanning the full cavity width, while the wheel rotates on the string post axis below it. Getting the center distance, the mesh rotation angle (14.75°), and the Z-alignment right took several iterations with interference checking to validate each step.

## Fighting OCCT's boolean engine

The hardest technical problem was boolean fusion of the peg head. This component is built by unioning four overlapping solids: a reference STEP peg head, a core shaft, a bearing shaft, and a worm STEP imported from an external gear calculator. OCCT's boolean kernel produced degenerate zero-volume artifacts (returning `ShapeList` instead of `Solid`), phantom 734mm³ interference from disjoint compounds, and 29-nanometre non-manifold edges at worm thread termination points. We tried every OCCT healing tool available — `ShapeFix_Shape`, `ShapeFix_Solid`, `BRepBuilderAPI_Sewing`, `ShapeUpgrade_UnifySameDomain`, `BRepAlgoAPI_Defeaturing`, fuzzy booleans, STEP round-trips — and none removed the NME edges without destroying the solid. The solution was pragmatic: filter zero-volume artifacts after fusion, apply `ShapeFix_Shape` for topology repair, and classify NME edges by arc length so sub-micron artifacts are logged silently rather than triggering false warnings.

A subtler boolean bug appeared later: when the core shaft radius exactly equalled the worm root radius (2.375mm), coincident surfaces caused OCCT to consume the worm teeth during fusion, losing 70mm³ of volume. A 0.1mm undercut on the core shaft fixed it.

## The gear profile journey

The gear profile went through a full circle. We started with M0.5/13:1, switched to M0.6/10:1 for a stronger peg shaft, explored globoid worms for better meshing, then came back to cylindrical M0.5/13:1 (the c13 profile) once we found that profile shift +0.3 gave strong enough tooth roots while keeping manufacturing simple. Along the way we generated eleven distinct gear configurations, each with its own STEP files, geometry analysis, and parameter JSON. The external gear calculator tool drove the gear geometry; the CAD code had to adapt to whatever it produced.

## From CAD to workshop

Once the virtual assembly worked, the focus shifted to manufacturing tooling. We designed parametric 3D-printed jigs — a cutting jig for sawing the brass stock to length, and a two-part clamshell drilling jig for all 26 holes in a 5-gang frame. Real-world printing immediately exposed issues: M5 hardware was too large, heat-set inserts fell out of nominal-sized pockets (needed 0.3mm interference), and the frame length tolerance required a clamping plug with 4mm of travel. Each fix came from testing a physical print and feeding the result back into the parametric model.

## What worked about the process

Working with an AI coding partner on a CAD project was surprisingly effective for the exploratory, iterative style this kind of engineering demands. The parametric architecture — frozen dataclasses, derived dimensions, config-driven gear profiles — made it safe to change one parameter and have everything propagate. Interference checking after every build caught problems that would otherwise only surface at the bench. And the ability to spin up new gear profiles, jig variants, or export formats in single sessions kept the design space open rather than locking in too early.

The main friction points were spatial reasoning (positioning components in 3D required explicit coordinate checks rather than trusting intuition) and OCCT's boolean behaviour (which is genuinely unpredictable with complex imported geometry). Both were managed by building incrementally — one component at a time, one housing before five — and never moving forward until the current step was visually verified.
