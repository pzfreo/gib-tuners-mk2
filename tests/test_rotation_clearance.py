"""Rotation clearance and multi-gang spacing tests.

Validates that rotating components have sufficient clearance:
- Wheel can rotate 360 degrees without hitting frame cavity walls
- Worm can rotate freely within the cavity
- Peg cap doesn't foul adjacent housings or frame ends
- Multi-gang tuner spacing is uniform

Run:
    pytest tests/test_rotation_clearance.py -v --gear c13
"""

import math
from dataclasses import replace

import pytest

from gib_tuners.config.defaults import create_default_config, calculate_worm_z


# ===================================================================
# 1. Wheel Rotation Clearance (Parametric)
# ===================================================================

class TestWheelRotationClearance:
    """The wheel must rotate 360 degrees without clipping the frame cavity.

    The wheel has teeth so tip circle varies. The conservative check is
    that the tip diameter fits within the cavity (already checked in
    test_gear_engagement). Here we add a geometric swept-volume check.
    """

    def test_wheel_tip_circle_clears_cavity_x(self, default_config):
        """Wheel tip circle must fit within cavity X dimension."""
        wheel_od = default_config.gear.wheel.tip_diameter
        cavity = default_config.frame.box_inner
        assert wheel_od < cavity, (
            f"Wheel tip {wheel_od}mm >= cavity width {cavity}mm in X"
        )

    def test_wheel_tip_circle_clears_cavity_z(self, default_config):
        """Wheel tip circle must fit within cavity Z dimension.

        Cavity height = box_inner (same as width for square tube).
        """
        wheel_od = default_config.gear.wheel.tip_diameter
        cavity_height = default_config.frame.box_inner
        assert wheel_od < cavity_height, (
            f"Wheel tip {wheel_od}mm >= cavity height {cavity_height}mm in Z"
        )

    def test_wheel_rotation_geometric(self, gear_paths):
        """Rotate the wheel at 45-degree increments and check no intersection
        with the frame exceeds tolerance.
        """
        from gib_tuners.assembly.gang_assembly import (
            create_positioned_assembly,
            check_interference,
        )
        from build123d import Axis, Location

        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        config = replace(config, frame=replace(config.frame, num_housings=1))

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
        )

        frame = assembly["frame"]
        wheel = assembly["all_parts"]["wheel_1"]

        # Get wheel centre for rotation axis
        wb = wheel.bounding_box()
        wheel_cx = (wb.min.X + wb.max.X) / 2
        wheel_cy = (wb.min.Y + wb.max.Y) / 2
        wheel_cz = (wb.min.Z + wb.max.Z) / 2

        failures = []
        # Test at 45-degree increments (8 positions covers all quadrants)
        for angle_deg in range(0, 360, 45):
            if angle_deg == 0:
                continue  # Already at default position

            # Rotate wheel about its Z axis (post axis)
            rotated = wheel.rotate(
                Axis((wheel_cx, wheel_cy, wheel_cz), (0, 0, 1)),
                angle_deg,
            )
            vol = check_interference(rotated, frame)
            if vol >= 0.05:
                failures.append(
                    f"  {angle_deg}°: intersection = {vol:.3f} mm³"
                )

        assert not failures, (
            "Wheel-frame intersection at rotation angles:\n"
            + "\n".join(failures)
        )


# ===================================================================
# 2. Worm Rotation Clearance
# ===================================================================

class TestWormRotationClearance:
    """The worm must rotate freely within the cavity. For a cylindrical
    worm, the tip diameter is constant so a parametric check suffices.
    """

    def test_worm_clearance_per_side(self, default_config):
        """Worm must have >= 0.2mm clearance per side in cavity."""
        worm_od = default_config.gear.worm.tip_diameter
        cavity = default_config.frame.box_inner
        clearance_per_side = (cavity - worm_od) / 2
        assert clearance_per_side >= 0.2, (
            f"Worm clearance = {clearance_per_side:.2f}mm per side "
            f"(cavity={cavity}, worm_od={worm_od}). "
            f"Minimum 0.2mm required."
        )

    def test_worm_clears_top_and_bottom_plates(self, default_config):
        """Worm centred at -box_outer/2 must not touch top or bottom plates."""
        fp = default_config.frame
        worm_od = default_config.gear.worm.tip_diameter
        worm_z = -fp.box_outer / 2  # Centred in frame

        worm_top = worm_z + worm_od / 2
        worm_bottom = worm_z - worm_od / 2

        plate_ceiling = -fp.wall_thickness
        plate_floor = -(fp.box_outer - fp.wall_thickness)

        assert worm_top <= plate_ceiling, (
            f"Worm top edge Z={worm_top:.2f} exceeds cavity ceiling {plate_ceiling:.2f}"
        )
        assert worm_bottom >= plate_floor, (
            f"Worm bottom edge Z={worm_bottom:.2f} below cavity floor {plate_floor:.2f}"
        )


# ===================================================================
# 3. Peg Cap Rotation Clearance
# ===================================================================

class TestPegCapClearance:
    """The peg head cap sits outside the frame. When rotated, it must
    not foul against adjacent housing structures or the frame end.
    """

    def test_peg_cap_clears_adjacent_housing(self, default_config):
        """Peg cap swept circle must not overlap the next housing.

        The peg cap centre is at housing_y + CD/2 on the side face.
        The next housing starts at (housing_y + pitch) - housing_length/2.
        The cap must not reach that boundary.
        """
        fp = default_config.frame
        cd = default_config.gear.center_distance
        cap_radius = default_config.peg_head.cap_diameter / 2

        if fp.num_housings < 2:
            pytest.skip("Need >= 2 housings for adjacency check")

        centers = fp.housing_centers
        for i in range(len(centers) - 1):
            peg_y = centers[i] + cd / 2
            next_housing_edge = centers[i + 1] - fp.housing_length / 2

            # Gap between cap edge and next housing
            gap = next_housing_edge - (peg_y + cap_radius)
            assert gap >= 0, (
                f"Peg cap at housing {i+1} overlaps housing {i+2}: "
                f"cap edge Y={peg_y + cap_radius:.2f}, "
                f"next housing Y={next_housing_edge:.2f}, "
                f"gap={gap:.2f}mm"
            )

    def test_peg_cap_clears_frame_end(self, default_config):
        """Last peg cap must not extend beyond frame end."""
        fp = default_config.frame
        cd = default_config.gear.center_distance
        cap_radius = default_config.peg_head.cap_diameter / 2

        last_peg_y = fp.housing_centers[-1] + cd / 2
        cap_edge = last_peg_y + cap_radius
        assert cap_edge <= fp.total_length, (
            f"Last peg cap edge Y={cap_edge:.2f} exceeds "
            f"frame end Y={fp.total_length:.2f}"
        )

    def test_first_peg_cap_clears_frame_start(self, default_config):
        """First peg cap must not extend before frame start.

        The peg is at housing_y + CD/2, so cap_y - radius should be >= 0.
        Since CD/2 is positive, this is unlikely to fail but worth checking.
        """
        fp = default_config.frame
        cd = default_config.gear.center_distance
        cap_radius = default_config.peg_head.cap_diameter / 2

        first_peg_y = fp.housing_centers[0] + cd / 2
        cap_start = first_peg_y - cap_radius
        assert cap_start >= 0, (
            f"First peg cap start Y={cap_start:.2f} before frame start"
        )


# ===================================================================
# 4. Multi-Gang Uniform Spacing
# ===================================================================

class TestMultiGangSpacing:
    """In a 5-gang assembly, all tuner-to-tuner spacings must equal
    tuner_pitch.
    """

    def test_housing_center_spacing(self, default_config):
        """Verify all inter-housing spacings equal tuner_pitch."""
        fp = default_config.frame
        centers = fp.housing_centers
        if len(centers) < 2:
            pytest.skip("Need >= 2 housings for spacing check")

        for i in range(len(centers) - 1):
            spacing = centers[i + 1] - centers[i]
            assert abs(spacing - fp.tuner_pitch) < 0.01, (
                f"Spacing between housing {i+1} and {i+2}: "
                f"{spacing:.3f}mm != pitch {fp.tuner_pitch}mm"
            )

    def test_assembly_component_spacing(self, gear_paths):
        """In a 5-gang assembly, string post Y-spacings match tuner_pitch."""
        from gib_tuners.assembly.gang_assembly import create_positioned_assembly

        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        # Use default 5 housings

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
        )

        parts = assembly["all_parts"]
        pitch = config.frame.tuner_pitch * config.scale

        # Get Y positions of all string posts
        post_ys = []
        for i in range(1, config.frame.num_housings + 1):
            key = f"string_post_{i}"
            if key not in parts:
                continue
            bb = parts[key].bounding_box()
            post_ys.append((bb.min.Y + bb.max.Y) / 2)

        assert len(post_ys) >= 2, "Need >= 2 posts for spacing check"

        for i in range(len(post_ys) - 1):
            spacing = post_ys[i + 1] - post_ys[i]
            assert abs(spacing - pitch) < 0.5, (
                f"Post {i+1} to {i+2} spacing: {spacing:.2f}mm "
                f"!= pitch {pitch:.2f}mm"
            )
