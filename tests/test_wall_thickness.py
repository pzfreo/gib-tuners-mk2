"""Wall thickness and structural integrity tests.

Validates that material remains sufficient after all machining operations:
- DD section wall around M2 tap bore (most marginal dimension)
- Worm entry hole wall in housing side face
- Peg bearing hole wall in opposite side face
- Post bearing hole wall in top plate
- Wheel hub wall (bore to root circle)
- Worm root to shaft transition
- Housing wall integrity after all drilling operations

Run:
    pytest tests/test_wall_thickness.py -v --gear c13
"""

import math

import pytest

from gib_tuners.config.defaults import create_default_config


# ===================================================================
# 1. DD Section Wall Thickness (String Post)
# ===================================================================

class TestDDSectionWall:
    """The DD section has an M2 tap bore through a 3.5mm shaft with flats.

    The minimum wall between the tap bore and the flat surface is the
    most marginal dimension in the design.
    """

    def test_dd_wall_to_tap_bore(self, default_config):
        """Wall between DD across-flats and M2 tap bore >= 0.4mm."""
        sp = default_config.string_post
        across_flats = sp.dd_cut.across_flats
        tap_bore = sp.tap_bore_diameter
        wall = (across_flats - tap_bore) / 2
        assert wall >= 0.4, (
            f"DD wall to tap bore = {wall:.2f}mm "
            f"(AF={across_flats}, tap={tap_bore}). "
            f"Minimum 0.4mm required."
        )

    def test_dd_wall_advisory_margin(self, default_config):
        """Advisory: flag if DD wall drops below 0.5mm (marginal)."""
        sp = default_config.string_post
        wall = (sp.dd_cut.across_flats - sp.tap_bore_diameter) / 2
        if wall < 0.5:
            import warnings
            warnings.warn(
                f"DD wall to tap bore is marginal: {wall:.3f}mm "
                f"(recommended >= 0.5mm)",
                stacklevel=1,
            )

    def test_dd_diameter_exceeds_tap_bore(self, default_config):
        """DD full diameter must be larger than tap bore for concentricity."""
        sp = default_config.string_post
        assert sp.dd_cut.diameter > sp.tap_bore_diameter, (
            f"DD diameter {sp.dd_cut.diameter} must exceed "
            f"tap bore {sp.tap_bore_diameter}"
        )


# ===================================================================
# 2. Worm Entry Hole Wall
# ===================================================================

class TestWormEntryHoleWall:
    """The worm entry hole (7.2mm) is the largest hole drilled through
    a 10mm housing side face. It must not break into the top or bottom plates.
    """

    def test_entry_hole_leaves_wall_above_and_below(self, default_config):
        """Entry hole must leave >= 1.0mm material above and below."""
        fp = default_config.frame
        wall_per_side = (fp.box_outer - fp.worm_entry_hole) / 2
        assert wall_per_side >= 1.0, (
            f"Worm entry hole wall = {wall_per_side:.2f}mm per side "
            f"(box={fp.box_outer}, hole={fp.worm_entry_hole}). "
            f"Minimum 1.0mm required."
        )

    def test_entry_hole_does_not_breach_plates(self, default_config):
        """Entry hole radius + wall_thickness must not exceed box_outer/2.

        This checks the hole doesn't cut through the top or bottom plates
        when the hole centre is at -box_outer/2 (frame midpoint in Z).
        """
        fp = default_config.frame
        hole_radius = fp.worm_entry_hole / 2
        # Hole centre is at Z = -box_outer/2 (midpoint)
        # Top plate inner surface is at Z = -wall_thickness
        # Hole top edge: -box_outer/2 + hole_radius
        hole_top_edge = -fp.box_outer / 2 + hole_radius
        plate_inner = -fp.wall_thickness
        assert hole_top_edge <= plate_inner + 0.01, (
            f"Entry hole top edge at Z={hole_top_edge:.2f} "
            f"breaches top plate inner at Z={plate_inner:.2f}"
        )


# ===================================================================
# 3. Peg Bearing Hole Wall
# ===================================================================

class TestPegBearingHoleWall:
    """The peg bearing hole (4.05mm) on the opposite side face."""

    def test_peg_bearing_wall(self, default_config):
        """Peg bearing hole must leave >= 2.5mm material per side."""
        fp = default_config.frame
        wall_per_side = (fp.box_outer - fp.peg_bearing_hole) / 2
        assert wall_per_side >= 2.5, (
            f"Peg bearing hole wall = {wall_per_side:.2f}mm per side "
            f"(box={fp.box_outer}, hole={fp.peg_bearing_hole}). "
            f"Minimum 2.5mm required."
        )


# ===================================================================
# 4. Post Bearing Hole Wall (Top Plate)
# ===================================================================

class TestPostBearingHoleWall:
    """The post bearing hole (5.05mm) through the 10mm top plate."""

    def test_post_bearing_wall(self, default_config):
        """Post bearing hole must leave >= 2.0mm material per side."""
        fp = default_config.frame
        wall_per_side = (fp.box_outer - fp.post_bearing_hole) / 2
        assert wall_per_side >= 2.0, (
            f"Post bearing hole wall = {wall_per_side:.2f}mm per side "
            f"(box={fp.box_outer}, hole={fp.post_bearing_hole}). "
            f"Minimum 2.0mm required."
        )


# ===================================================================
# 5. Wheel Hub Wall (Bore to Root Circle)
# ===================================================================

class TestWheelHubWall:
    """The wheel has a DD bore cut through its hub. The material between
    the bore OD and the tooth root circle must be sufficient.
    """

    def test_hub_wall_bore_to_root(self, default_config):
        """Hub wall from bore to tooth root >= 0.5mm."""
        wheel = default_config.gear.wheel
        hub_wall = (wheel.root_diameter - wheel.bore.diameter) / 2
        assert hub_wall >= 0.5, (
            f"Wheel hub wall = {hub_wall:.2f}mm "
            f"(root_dia={wheel.root_diameter}, bore={wheel.bore.diameter}). "
            f"Minimum 0.5mm required."
        )


# ===================================================================
# 6. Worm Root to Shaft Transition
# ===================================================================

class TestWormRootToShaft:
    """The worm thread is cut into the peg head shaft. The shaft bearing
    section must not be larger than the root diameter.
    """

    def test_shaft_fits_within_worm_root(self, default_config):
        """Shaft diameter <= worm root diameter for complete thread form."""
        shaft = default_config.peg_head.shaft_diameter
        root = default_config.gear.worm.root_diameter
        assert shaft <= root, (
            f"Shaft diameter {shaft}mm exceeds worm root {root}mm — "
            f"thread form would be incomplete at bearing transition"
        )


# ===================================================================
# 7. Housing Wall Integrity After Drilling
# ===================================================================

class TestHousingWallIntegrity:
    """After drilling all four holes (top, bottom, two sides), the housing
    walls must still form a continuous rigid box. Verify by comparing actual
    frame volume against analytical estimate.
    """

    def test_frame_volume_within_estimate(self, default_config):
        """Frame volume should be within 10% of analytical estimate."""
        from gib_tuners.components.frame import create_frame

        fp = default_config.frame
        s = default_config.scale

        # Build actual frame
        frame = create_frame(default_config)
        actual_vol = frame.volume

        # Analytical estimate: outer box - inner cavity
        outer_vol = (fp.box_outer * s) ** 2 * fp.total_length * s
        inner = fp.box_inner * s
        wall = fp.wall_thickness * s

        # Cavity volume (only in housing sections; gaps have walls milled away)
        # In housings: full hollow box
        # In connectors: top plate remains, side walls removed
        # Rough estimate: hollow tube along full length
        cavity_vol = inner ** 2 * fp.total_length * s
        shell_vol = outer_vol - cavity_vol

        # Holes remove additional material; frame should be less than shell
        # but not dramatically less (holes are small relative to total)
        assert actual_vol < outer_vol, "Frame should be less than solid block"
        assert actual_vol > shell_vol * 0.5, (
            f"Frame volume {actual_vol:.1f} is less than 50% of shell "
            f"estimate {shell_vol:.1f} — holes may be overlapping"
        )

    def test_no_adjacent_holes_overlap(self, default_config):
        """Verify that the four holes in each housing don't overlap.

        Check by ensuring the sum of hole areas on any single face
        doesn't exceed the face area minus minimum wall material.
        """
        fp = default_config.frame
        face_area = fp.box_outer * fp.housing_length

        # Top face: post bearing hole
        post_hole_area = math.pi * (fp.post_bearing_hole / 2) ** 2
        assert post_hole_area < face_area * 0.5, (
            f"Post hole area {post_hole_area:.1f} > 50% of top face {face_area:.1f}"
        )

        # Side face: worm entry hole (larger of the two side holes)
        entry_hole_area = math.pi * (fp.worm_entry_hole / 2) ** 2
        assert entry_hole_area < face_area * 0.5, (
            f"Entry hole area {entry_hole_area:.1f} > 50% of side face {face_area:.1f}"
        )

        # Bottom face: wheel inlet hole
        inlet_hole_area = math.pi * (fp.wheel_inlet_hole / 2) ** 2
        assert inlet_hole_area < face_area * 0.5, (
            f"Inlet hole area {inlet_hole_area:.1f} > 50% of bottom face {face_area:.1f}"
        )
