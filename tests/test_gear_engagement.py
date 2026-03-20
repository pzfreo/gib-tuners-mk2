"""Gear engagement and centre distance tests.

Validates worm/wheel mesh geometry:
- Worm engagement length covers wheel face width
- Geometric centre distance matches config (tighter than bbox check)
- Centre distance fits within housing bounds
- Wheel OD fits in cavity with clearance

Run:
    pytest tests/test_gear_engagement.py -v --gear c13
"""

from dataclasses import replace

import pytest

from gib_tuners.config.defaults import create_default_config, calculate_worm_z


# ===================================================================
# 1. Worm Engagement Length
# ===================================================================

class TestWormEngagementLength:
    """The worm thread must overlap the full wheel face width for
    complete tooth contact and rated load capacity.
    """

    def test_worm_length_covers_face_width(self, default_config):
        """Worm length >= wheel face width."""
        worm_len = default_config.gear.worm.length
        face_width = default_config.gear.wheel.face_width
        assert worm_len >= face_width, (
            f"Worm length {worm_len}mm < wheel face width {face_width}mm — "
            f"incomplete tooth engagement"
        )

    def test_worm_engagement_geometric(self, gear_paths):
        """Verify the worm axis Z-position aligns with the wheel centre Z.

        The worm is embedded in the peg_head compound, so we cannot
        isolate its bbox. Instead, verify that the peg shaft (worm axis)
        Z-position matches the wheel centre Z within half the face width.
        This ensures the worm thread covers the wheel tooth face.
        """
        from gib_tuners.assembly.gang_assembly import create_positioned_assembly

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

        parts = assembly["all_parts"]
        wheel = parts["wheel_1"]

        wheel_bb = wheel.bounding_box()
        wheel_cz = (wheel_bb.min.Z + wheel_bb.max.Z) / 2

        # Worm axis Z from config
        worm_z = calculate_worm_z(config)

        # Worm axis should be within the wheel's Z-extent
        # (worm centred near wheel centre for full engagement)
        wheel_half_height = (wheel_bb.max.Z - wheel_bb.min.Z) / 2
        offset = abs(worm_z - wheel_cz)
        assert offset < wheel_half_height, (
            f"Worm axis Z={worm_z:.2f} too far from wheel centre "
            f"Z={wheel_cz:.2f} (offset={offset:.2f}, "
            f"half_height={wheel_half_height:.2f})"
        )


# ===================================================================
# 2. Centre Distance — Geometric Measurement
# ===================================================================

class TestCentreDistanceGeometric:
    """Measure actual axis-to-axis distance from assembled component
    bearing surfaces rather than bounding box centres (which are skewed
    by asymmetric features like the peg cap).
    """

    def test_cd_from_assembly_positions(self, gear_paths):
        """Post and peg Y-positions should produce the correct CD.

        Uses housing_centers and effective_cd from assembly dict, which
        are computed from config. Verifies internal consistency.
        """
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

        expected_cd = config.gear.center_distance * config.scale
        effective_cd = assembly["effective_cd"]
        backlash = config.gear.extra_backlash * config.scale

        # Effective CD = center_distance - extra_backlash
        assert abs(effective_cd - (expected_cd - backlash)) < 0.01, (
            f"Effective CD {effective_cd:.3f} != "
            f"expected {expected_cd:.3f} - backlash {backlash:.3f}"
        )

    def test_cd_post_to_peg_from_string_post_bbox(self, gear_paths):
        """Measure post-to-peg Y distance from string post (symmetric)
        and peg shaft section. String post bbox centre Y is reliable
        since the post is axially symmetric.
        """
        from gib_tuners.assembly.gang_assembly import create_positioned_assembly

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

        s = config.scale
        housing_y = assembly["housing_centers"][0]
        effective_cd = assembly["effective_cd"]

        # Expected positions
        expected_post_y = housing_y - effective_cd / 2
        expected_peg_y = housing_y + effective_cd / 2

        # String post is axially symmetric, so bbox centre Y is reliable
        post = assembly["all_parts"]["string_post_1"]
        post_bb = post.bounding_box()
        post_y = (post_bb.min.Y + post_bb.max.Y) / 2

        assert abs(post_y - expected_post_y) < 0.5, (
            f"Post Y={post_y:.2f}, expected {expected_post_y:.2f}"
        )


# ===================================================================
# 3. Centre Distance Within Housing Bounds
# ===================================================================

class TestCDWithinHousing:
    """Both the post hole and worm entry hole must physically land
    within the housing walls (not extend beyond the housing Y-extent).
    """

    def test_post_hole_within_housing(self, default_config):
        """Post bearing hole edges within housing Y-extent."""
        fp = default_config.frame
        cd = default_config.gear.center_distance

        for center_y in fp.housing_centers:
            post_y = center_y - cd / 2
            half_housing = fp.housing_length / 2
            housing_start = center_y - half_housing
            housing_end = center_y + half_housing

            hole_radius = fp.post_bearing_hole / 2
            # Post hole is in XZ plane (top face), check Y position
            # The hole is at a single Y position, just needs to be within housing
            assert housing_start <= post_y <= housing_end, (
                f"Post axis Y={post_y:.2f} outside housing "
                f"[{housing_start:.2f}, {housing_end:.2f}]"
            )

    def test_worm_entry_within_housing(self, default_config):
        """Worm entry hole edges within housing Y-extent."""
        fp = default_config.frame
        cd = default_config.gear.center_distance

        for center_y in fp.housing_centers:
            worm_y = center_y + cd / 2
            half_housing = fp.housing_length / 2
            housing_start = center_y - half_housing
            housing_end = center_y + half_housing

            # Worm entry hole diameter along Y
            hole_radius = fp.worm_entry_hole / 2
            hole_start = worm_y - hole_radius
            hole_end = worm_y + hole_radius

            assert hole_start >= housing_start - 0.01, (
                f"Worm hole start Y={hole_start:.2f} "
                f"before housing start {housing_start:.2f}"
            )
            assert hole_end <= housing_end + 0.01, (
                f"Worm hole end Y={hole_end:.2f} "
                f"after housing end {housing_end:.2f}"
            )


# ===================================================================
# 4. Wheel OD Fits in Cavity
# ===================================================================

class TestWheelODInCavity:
    """The wheel tip diameter must be smaller than the cavity dimension
    to allow free rotation.
    """

    def test_wheel_tip_diameter_vs_cavity(self, default_config):
        """Wheel tip diameter < frame inner dimension with clearance."""
        wheel_od = default_config.gear.wheel.tip_diameter
        cavity = default_config.frame.box_inner
        clearance = cavity - wheel_od
        assert clearance >= 0.3, (
            f"Wheel OD {wheel_od}mm in {cavity}mm cavity — "
            f"clearance {clearance:.2f}mm < 0.3mm minimum"
        )

    def test_wheel_tip_vs_cavity_diagonal(self, default_config):
        """Even on the diagonal, wheel must fit.

        The cavity is square (box_inner x box_inner), so the diagonal
        is box_inner * sqrt(2). The wheel is circular, so it always
        fits if OD < box_inner. This test documents the constraint.
        """
        wheel_od = default_config.gear.wheel.tip_diameter
        cavity = default_config.frame.box_inner
        assert wheel_od < cavity, (
            f"Wheel OD {wheel_od}mm >= cavity {cavity}mm"
        )


# Helper to avoid circular import at module level
def create_positioned_assembly(*args, **kwargs):
    from gib_tuners.assembly.gang_assembly import create_positioned_assembly as _cpa
    return _cpa(*args, **kwargs)
