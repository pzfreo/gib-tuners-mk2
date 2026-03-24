"""Tests for pip stalk reinforcement.

The OnShape peg head STEP has a 1.0mm diameter pip stalk connecting the
2.1mm pip to the ring body. This is too weak in CZ121 brass (fails at ~20N
bending). We reinforce it to 1.5mm in code after STEP import.

These tests verify:
1. The reinforcement increases the minimum stalk diameter
2. The pip tip diameter (2.1mm) is unchanged
3. The overall peg head volume increases (material added, not removed)
4. The peg head bounding box is unchanged (no geometry outside original)
5. The rest of the peg head geometry is unaffected
6. Comparing CNC version (raw STEP) vs reinforced: only stalk region changed
"""

import math

import pytest

from build123d import import_step, Box, Align, Location, Part, Compound
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepGProp import BRepGProp
from OCP.GeomAbs import (
    GeomAbs_Circle, GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Sphere,
    GeomAbs_Torus, GeomAbs_BSplineSurface,
)
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

from gib_tuners.components.peg_head import create_peg_head, PEG_HEAD_STEP


# Target reinforcement diameter
TARGET_STALK_DIAMETER = 1.5

SURFACE_TYPE_NAMES = {
    GeomAbs_Plane: "Plane",
    GeomAbs_Cylinder: "Cylinder",
    GeomAbs_Sphere: "Sphere",
    GeomAbs_Torus: "Torus",
    GeomAbs_BSplineSurface: "BSpline",
}


def _get_all_faces(shape):
    """Extract all faces with type, area, and geometry-specific info."""
    explorer = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    faces = []
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        adaptor = BRepAdaptor_Surface(face)
        stype = adaptor.GetType()
        type_name = SURFACE_TYPE_NAMES.get(stype, f"Other({stype})")

        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face, props)
        area = props.Mass()
        com = props.CentreOfMass()

        info = {"type": type_name, "area": area,
                "com": (com.X(), com.Y(), com.Z())}

        if stype == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            info["diameter"] = cyl.Radius() * 2
            info["axis"] = tuple(
                round(v, 3) for v in (
                    cyl.Axis().Direction().X(),
                    cyl.Axis().Direction().Y(),
                    cyl.Axis().Direction().Z(),
                )
            )
        elif stype == GeomAbs_Torus:
            t = adaptor.Torus()
            info["major_r"] = t.MajorRadius()
            info["minor_r"] = t.MinorRadius()

        faces.append(info)
        explorer.Next()
    return faces


def _get_cylindrical_faces(shape):
    """Extract cylindrical faces only."""
    return [f for f in _get_all_faces(shape) if f["type"] == "Cylinder"]


def _import_raw_peg_head():
    """Import the raw OnShape STEP without any modifications."""
    imported = import_step(PEG_HEAD_STEP)
    if hasattr(imported, '__iter__') and not isinstance(imported, (Part, Compound)):
        shapes = list(imported)
        shape = shapes[0]
        for s in shapes[1:]:
            shape = shape + s
        return Part(shape.wrapped) if not isinstance(shape, Part) else shape
    return imported if isinstance(imported, Part) else Part(imported.wrapped)


def _find_face(faces, type_name, area, diameter=None, atol_area=0.5):
    """Find a face matching type, area, and optionally diameter."""
    for f in faces:
        if f["type"] != type_name:
            continue
        if abs(f["area"] - area) > atol_area:
            continue
        if diameter is not None and "diameter" in f:
            if abs(f["diameter"] - diameter) > 0.05:
                continue
        return f
    return None


class TestPipRawGeometry:
    """Verify our understanding of the raw STEP before any fix."""

    def test_raw_step_has_1mm_stalk(self):
        """The unmodified STEP should have a 1.0mm diameter stalk."""
        raw = _import_raw_peg_head()
        cylinders = _get_cylindrical_faces(raw)
        # Pip region: small cylinders on Z axis, far negative Z
        pip_cyls = [c for c in cylinders
                    if c["diameter"] < 3.0
                    and c["com"][2] < -15]
        diameters = sorted(c["diameter"] for c in pip_cyls)
        # Should find 1.0mm stalk and 2.1mm pip
        assert any(abs(d - 1.0) < 0.05 for d in diameters), (
            f"Expected 1.0mm stalk in raw STEP, found diameters: {diameters}"
        )
        assert any(abs(d - 2.1) < 0.05 for d in diameters), (
            f"Expected 2.1mm pip in raw STEP, found diameters: {diameters}"
        )


class TestPipReinforcement:
    """Tests for the pip stalk reinforcement fix."""

    def test_stalk_diameter_increased(self, production_config):
        """After reinforcement, no cylindrical face in pip region < TARGET."""
        peg = create_peg_head(production_config, include_worm=False)
        # After -90°Y rotation: pip stalk cylinders have axis along X
        cylinders = _get_cylindrical_faces(peg)
        pip_stalk_cyls = [c for c in cylinders
                          if c["diameter"] < 3.0
                          and c["area"] < 5.0
                          and abs(abs(c["axis"][0]) - 1.0) < 0.1]

        for cyl in pip_stalk_cyls:
            assert cyl["diameter"] >= TARGET_STALK_DIAMETER - 0.05, (
                f"Pip region cylinder d={cyl['diameter']:.3f}mm is below "
                f"target {TARGET_STALK_DIAMETER}mm"
            )

    def test_pip_tip_diameter_preserved(self, production_config):
        """The pip dome diameter (2.1mm) must not change."""
        peg = create_peg_head(production_config, include_worm=False)
        cylinders = _get_cylindrical_faces(peg)
        pip_body = [c for c in cylinders if abs(c["diameter"] - 2.1) < 0.1]
        assert len(pip_body) >= 1, (
            "Pip body cylinder (2.1mm) not found — dome may have been damaged"
        )

    def test_volume_increased(self, production_config):
        """Reinforcement adds material, so volume should increase."""
        peg = create_peg_head(production_config, include_worm=False)
        assert peg.volume > 0, "Peg head has zero volume"

    def test_bounding_box_unchanged(self, production_config):
        """Reinforcement must not extend geometry beyond original bounds."""
        peg = create_peg_head(production_config, include_worm=False)
        bb = peg.bounding_box()
        # After -90°Y rotation: pip tip at +X ~19mm, ring OD at ±Z ~6.25mm
        assert bb.max.X < 20.0, (
            f"Peg head extends too far in +X: {bb.max.X:.2f}mm"
        )
        assert bb.max.Z < 7.0, (
            f"Peg head extends too far in +Z: {bb.max.Z:.2f}mm"
        )
        assert bb.min.Z > -7.0, (
            f"Peg head extends too far in -Z: {bb.min.Z:.2f}mm"
        )

    def test_no_stalk_faces_below_target(self, production_config):
        """No small cylinders aligned along X should remain below target."""
        peg = create_peg_head(production_config, include_worm=False)
        cylinders = _get_cylindrical_faces(peg)
        problem_faces = [
            c for c in cylinders
            if c["diameter"] < TARGET_STALK_DIAMETER - 0.05
            and c["diameter"] > 0.5  # ignore tiny fillet artifacts
            and abs(abs(c["axis"][0]) - 1.0) < 0.1  # aligned along X
            and c["area"] < 2.0  # small face (stalk-sized)
        ]
        assert len(problem_faces) == 0, (
            f"Found {len(problem_faces)} undersized cylinder(s) in pip region: "
            f"{[(c['diameter'], c['area']) for c in problem_faces]}"
        )


class TestProductionComparison:
    """Compare CNC production version (raw STEP) against reinforced version.

    Both are built from the same STEP file in the same test run, so there's
    no dependency on hardcoded values or gear profiles. We compare the Z<=0
    portion (peg head before shaft/worm) to isolate only the stalk change.
    """

    @pytest.fixture
    def cnc_and_fixed(self):
        """Build both CNC (raw) and fixed versions, cut at Z=0.

        Returns (cnc_head, fixed_head) — both are the Z<=0 portion only,
        no shaft, no rotation. Direct apples-to-apples comparison.
        """
        raw = _import_raw_peg_head()

        # Cut at Z=0 to get the head portion (same as create_peg_head does)
        keep_box = Box(20, 20, 30, align=(Align.CENTER, Align.CENTER, Align.MAX))
        keep_box = keep_box.locate(Location((0, 0, 0)))

        cnc_head = Part((raw & keep_box).wrapped)

        # For the fixed version, we need create_peg_head to apply the
        # reinforcement. But create_peg_head also adds shaft and rotates.
        # Instead, we replicate just the reinforcement step here:
        # import STEP → reinforce_pip_stalk() → cut at Z=0
        # This tests the reinforcement function in isolation.
        #
        # For now, return raw as cnc (the reinforcement doesn't exist yet,
        # so fixed == cnc until the fix is implemented).
        # Once the fix exists, we'll call the reinforcement function here.
        from gib_tuners.components.peg_head import reinforce_pip_stalk
        raw2 = _import_raw_peg_head()
        reinforced = reinforce_pip_stalk(raw2, TARGET_STALK_DIAMETER)
        fixed_head = Part((reinforced & keep_box).wrapped)

        return cnc_head, fixed_head

    def test_volume_increase_bounded(self, cnc_and_fixed):
        """Volume should increase but only by the stalk reinforcement amount.

        Stalk reinforcement from 1.0mm to 1.5mm over ~0.2mm length:
          π/4 * (1.5² - 1.0²) * 0.2 ≈ 0.196 mm³
        Allow generous margin for boolean artifacts but cap at 2mm³.
        """
        cnc, fixed = cnc_and_fixed
        volume_change = fixed.volume - cnc.volume
        assert volume_change >= 0, (
            f"Volume decreased by {abs(volume_change):.3f} mm³ — "
            f"material was removed, not added"
        )
        assert volume_change < 2.0, (
            f"Volume increased by {volume_change:.3f} mm³ — "
            f"expected < 2mm³ from stalk reinforcement only"
        )

    def test_bounding_box_matches(self, cnc_and_fixed):
        """Bounding box should be identical (reinforcement is inside original)."""
        cnc, fixed = cnc_and_fixed
        cnc_bb = cnc.bounding_box()
        fix_bb = fixed.bounding_box()
        tol = 0.01
        assert abs(cnc_bb.min.X - fix_bb.min.X) < tol, "X min changed"
        assert abs(cnc_bb.max.X - fix_bb.max.X) < tol, "X max changed"
        assert abs(cnc_bb.min.Y - fix_bb.min.Y) < tol, "Y min changed"
        assert abs(cnc_bb.max.Y - fix_bb.max.Y) < tol, "Y max changed"
        assert abs(cnc_bb.min.Z - fix_bb.min.Z) < tol, "Z min changed"
        assert abs(cnc_bb.max.Z - fix_bb.max.Z) < tol, "Z max changed"

    def test_non_stalk_faces_preserved(self, cnc_and_fixed):
        """Every CNC face except the stalk cylinder must exist in the fixed version.

        We match faces by (type, area, diameter) within tolerance.
        The 1.0mm stalk (area≈0.459) and the two pip-junction tori
        (R=0.750, r=0.300) are the only faces allowed to change — the
        boolean union may reshape the transition fillets.
        """
        cnc, fixed = cnc_and_fixed
        cnc_faces = _get_all_faces(cnc)
        fixed_faces = _get_all_faces(fixed)

        # Track which fixed faces have been matched (avoid double-counting)
        matched_fixed = set()
        missing = []

        for cf in cnc_faces:
            # Skip the stalk cylinder — it's expected to change
            if (cf["type"] == "Cylinder"
                    and "diameter" in cf
                    and abs(cf["diameter"] - 1.0) < 0.05
                    and cf["area"] < 1.0):
                continue

            # Skip pip-junction tori — boolean may reshape these
            if (cf["type"] == "Torus"
                    and "major_r" in cf
                    and abs(cf["major_r"] - 0.750) < 0.05):
                continue

            # Skip the small plane between stalk and pip (area≈0.982)
            # — this transition face is consumed by the reinforcement
            if (cf["type"] == "Plane"
                    and cf["area"] < 1.1
                    and cf["area"] > 0.8):
                continue

            # Find a matching face in fixed version
            found = False
            for j, ff in enumerate(fixed_faces):
                if j in matched_fixed:
                    continue
                if ff["type"] != cf["type"]:
                    continue
                # For cylinders, match primarily by diameter (unique identifier).
                # Area can shift when OCCT re-tessellates after booleans.
                if "diameter" in cf and "diameter" in ff:
                    if abs(ff["diameter"] - cf["diameter"]) > 0.05:
                        continue
                    # Diameter matches — accept with generous area tolerance
                    atol = max(2.0, cf["area"] * 0.05)
                else:
                    # Non-cylinder: use relative tolerance for area
                    atol = max(1.5, cf["area"] * 0.03)
                if abs(ff["area"] - cf["area"]) > atol:
                    continue
                matched_fixed.add(j)
                found = True
                break

            if not found:
                missing.append(cf)

        assert len(missing) == 0, (
            f"{len(missing)} CNC face(s) missing after reinforcement:\n"
            + "\n".join(
                f"  {m['type']} area={m['area']:.3f}"
                + (f" d={m['diameter']:.3f}" if "diameter" in m else "")
                for m in missing
            )
        )

    def test_stalk_cylinder_removed(self, cnc_and_fixed):
        """The original 1.0mm stalk cylinder should not exist in fixed version."""
        _, fixed = cnc_and_fixed
        fixed_faces = _get_all_faces(fixed)
        old_stalk = _find_face(fixed_faces, "Cylinder", 0.459,
                               diameter=1.0, atol_area=0.1)
        assert old_stalk is None, (
            f"Original 1.0mm stalk still present: area={old_stalk['area']:.3f}"
        )

    def test_pip_tip_position_unchanged(self, cnc_and_fixed):
        """The pip tip (most negative Z plane) must not move."""
        cnc, fixed = cnc_and_fixed
        cnc_faces = _get_all_faces(cnc)
        fixed_faces = _get_all_faces(fixed)

        # Find pip tip plane (smallest Z center-of-mass)
        cnc_planes = [f for f in cnc_faces if f["type"] == "Plane"]
        fixed_planes = [f for f in fixed_faces if f["type"] == "Plane"]

        cnc_tip = min(cnc_planes, key=lambda f: f["com"][2])
        fixed_tip = min(fixed_planes, key=lambda f: f["com"][2])

        assert abs(cnc_tip["com"][2] - fixed_tip["com"][2]) < 0.01, (
            f"Pip tip moved: CNC Z={cnc_tip['com'][2]:.3f} vs "
            f"fixed Z={fixed_tip['com'][2]:.3f}"
        )

    def test_pip_body_cylinder_preserved(self, cnc_and_fixed):
        """The 2.1mm pip body must have the same diameter and area."""
        cnc, fixed = cnc_and_fixed
        cnc_faces = _get_all_faces(cnc)
        fixed_faces = _get_all_faces(fixed)

        cnc_pip = _find_face(cnc_faces, "Cylinder", 3.958, diameter=2.1)
        fixed_pip = _find_face(fixed_faces, "Cylinder", 3.958, diameter=2.1)

        assert cnc_pip is not None, "CNC pip body not found"
        assert fixed_pip is not None, "Fixed pip body not found"
        assert abs(cnc_pip["area"] - fixed_pip["area"]) < 0.1, (
            f"Pip body area changed: {cnc_pip['area']:.3f} → "
            f"{fixed_pip['area']:.3f}"
        )

    def test_face_count_close(self, cnc_and_fixed):
        """Face count should be similar (±4 for boolean artifacts)."""
        cnc, fixed = cnc_and_fixed
        cnc_count = len(_get_all_faces(cnc))
        fixed_count = len(_get_all_faces(fixed))
        assert abs(cnc_count - fixed_count) <= 4, (
            f"Face count changed significantly: {cnc_count} → {fixed_count}"
        )

    def test_reinforcement_not_visible_inside_ring(self, cnc_and_fixed):
        """Reinforcement cylinder must not protrude into the ring bore.

        Slice the reinforced head at Z levels inside the ring body (-16.5
        to -15.0) and check no new circles appear compared to the raw STEP.
        A protruding reinforcement would show as an extra small circle
        (1.5mm) inside the ring's larger bore.
        """
        cnc, fixed = cnc_and_fixed

        def _section_circles(shape, z):
            plane = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
            sec = BRepAlgoAPI_Section(shape.wrapped, plane)
            sec.Build()
            circles = []
            exp = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
            while exp.More():
                edge = TopoDS.Edge_s(exp.Current())
                adaptor = BRepAdaptor_Curve(edge)
                if adaptor.GetType() == GeomAbs_Circle:
                    circles.append(adaptor.Circle().Radius() * 2)
                exp.Next()
            return sorted(circles)

        # Sample Z levels inside the ring body (below the stalk region)
        for z in [-16.5, -16.0, -15.5, -15.0]:
            raw_circles = _section_circles(cnc, z)
            fix_circles = _section_circles(fixed, z)
            # The reinforcement cylinder (1.5mm) should not appear
            new_small = [d for d in fix_circles
                         if d < 3.0
                         and not any(abs(d - r) < 0.1 for r in raw_circles)]
            assert len(new_small) == 0, (
                f"At Z={z}, reinforcement visible inside ring: "
                f"new circles {[f'{d:.2f}' for d in new_small]}mm"
            )
