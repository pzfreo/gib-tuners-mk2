"""Tests for parameter dataclasses."""

import pytest
from pathlib import Path

from gib_tuners.config.parameters import (
    BuildConfig,
    DDCutParams,
    FrameParams,
    GearParams,
    Hand,
    PegHeadParams,
    StringPostParams,
    ToleranceConfig,
    WheelParams,
    WormParams,
)
from gib_tuners.config.tolerances import TOLERANCE_PROFILES, get_tolerance
from gib_tuners.config.defaults import create_default_config, load_gear_params


class TestFrameParams:
    """Tests for FrameParams dataclass."""

    def test_default_values(self):
        """Test default frame parameters match spec."""
        params = FrameParams()
        # Box section dimensions (measured: 10x10 outer, 7.8x7.8 inner)
        assert params.box_outer == 10.0
        assert params.wall_thickness == 1.1
        assert params.total_length == 145.0
        assert params.housing_length == 16.2
        assert params.num_housings == 5
        assert params.tuner_pitch == 27.2

    def test_box_inner(self):
        """Test internal cavity calculation."""
        params = FrameParams()
        expected = 10.0 - 2 * 1.1  # 7.8
        assert abs(params.box_inner - expected) < 0.01

    def test_housing_centers(self):
        """Test housing center positions are symmetric."""
        params = FrameParams()
        centers = params.housing_centers
        assert len(centers) == 5
        # Symmetric positions: 18.1, 45.3, 72.5, 99.7, 126.9
        assert abs(centers[0] - 18.1) < 0.01
        assert abs(centers[1] - 45.3) < 0.01
        assert abs(centers[2] - 72.5) < 0.01  # Frame center
        assert abs(centers[3] - 99.7) < 0.01
        assert abs(centers[4] - 126.9) < 0.01
        # Verify symmetry: first and last are equidistant from ends
        end1 = centers[0] - params.housing_length / 2
        end2 = params.total_length - (centers[-1] + params.housing_length / 2)
        assert abs(end1 - end2) < 0.01, "Frame ends must be symmetric"

    def test_mounting_hole_positions(self):
        """Test mounting hole positions from spec."""
        params = FrameParams()
        positions = params.mounting_hole_positions
        assert len(positions) == 6
        # Symmetric end holes: 5.0 and 140.0
        expected = (5.0, 31.7, 58.9, 86.1, 113.3, 140.0)
        for actual, exp in zip(positions, expected):
            assert abs(actual - exp) < 0.01

    def test_frozen(self):
        """Test that params are immutable."""
        params = FrameParams()
        with pytest.raises(AttributeError):
            params.box_outer = 11.0


class TestDDCutParams:
    """Tests for DD cut parameters."""

    def test_default_values(self):
        """Test default DD cut parameters (updated for 7.5mm wheel)."""
        params = DDCutParams()
        assert params.diameter == 3.5
        assert params.flat_depth == 0.5
        assert params.across_flats == 2.5


class TestToleranceProfiles:
    """Tests for tolerance profiles."""

    def test_production_tolerance(self):
        """Test production tolerance values."""
        config = get_tolerance("production")
        assert config.hole_clearance == 0.05
        assert config.name == "production"

    def test_prototype_resin_tolerance(self):
        """Test resin prototype tolerance."""
        config = get_tolerance("prototype_resin")
        assert config.hole_clearance == 0.10

    def test_prototype_fdm_tolerance(self):
        """Test FDM prototype tolerance."""
        config = get_tolerance("prototype_fdm")
        assert config.hole_clearance == 0.20

    def test_invalid_profile(self):
        """Test error on invalid profile name."""
        with pytest.raises(KeyError):
            get_tolerance("invalid")


class TestBuildConfig:
    """Tests for build configuration."""

    def test_default_config(self):
        """Test default build configuration."""
        config = BuildConfig()
        assert config.scale == 1.0
        assert config.hand == Hand.RIGHT

    def test_scaled(self):
        """Test scale factor application."""
        config = BuildConfig(scale=2.0)
        assert config.scaled(10.0) == 20.0

    def test_with_tolerance(self):
        """Test tolerance application to holes."""
        config = BuildConfig(
            tolerance=ToleranceConfig(hole_clearance=0.1, name="test")
        )
        assert config.with_tolerance(4.0) == 4.1


class TestLoadGearParams:
    """Tests for loading gear parameters from JSON."""

    def test_load_from_json(self, gear_json_path):
        """Test loading gear params from JSON file validates structure and reasonable ranges.

        Actual values come from worm_gear.json which is the source of truth.
        """
        if not gear_json_path.exists():
            pytest.skip("Gear JSON file not found")

        gear = load_gear_params(gear_json_path)

        # Check worm params - verify structure and reasonable ranges
        assert gear.worm.module == 0.6  # M0.6 is fixed for this project
        assert gear.worm.num_starts == 1  # Single-start worm
        assert 5.0 <= gear.worm.pitch_diameter <= 7.0
        assert 6.0 <= gear.worm.tip_diameter <= 8.0
        assert 7.0 <= gear.worm.length <= 8.0

        # Check wheel params - verify structure and reasonable ranges
        assert gear.wheel.module == 0.6  # Must match worm module
        assert 10 <= gear.wheel.num_teeth <= 15  # Reasonable tooth count range
        assert 7.0 <= gear.wheel.tip_diameter <= 9.0
        assert 7.0 <= gear.wheel.face_width <= 8.0

        # Check assembly params - verify consistency
        assert gear.pressure_angle_deg == 20.0  # Standard pressure angle
        assert gear.ratio == gear.wheel.num_teeth  # Ratio equals wheel teeth for single-start
        # Center distance is explicitly set in JSON (may differ from (worm_pd + wheel_pd)/2 due to profile shift)
        assert 4.0 <= gear.center_distance <= 8.0, "Center distance outside reasonable range"


class TestDerivedParameters:
    """Tests for parameters derived from gear config."""

    def test_dd_cut_length_shorter_than_wheel(self, gear_json_path):
        """Test that dd_cut_length is wheel.face_width minus clearance."""
        if not gear_json_path.exists():
            pytest.skip("Gear JSON file not found")

        config = create_default_config(gear_json_path=gear_json_path)
        wheel_face_width = config.gear.wheel.face_width
        dd_cut_length = config.string_post.get_dd_cut_length(wheel_face_width)
        clearance = config.string_post.dd_cut_clearance
        assert dd_cut_length == wheel_face_width - clearance
        assert clearance == 0.5  # Bottom gap for compression clamping

    def test_worm_entry_hole_derived_from_shoulder_diameter(self, gear_json_path):
        """Test that worm_entry_hole is derived from peg shoulder diameter."""
        if not gear_json_path.exists():
            pytest.skip("Gear JSON file not found")

        config = create_default_config(gear_json_path=gear_json_path)
        expected = config.peg_head.shoulder_diameter + 0.05  # BEARING_CLEARANCE
        assert config.frame.worm_entry_hole == expected

    def test_worm_fits_through_entry_hole(self, gear_json_path):
        """Test that worm tip diameter is less than entry hole."""
        if not gear_json_path.exists():
            pytest.skip("Gear JSON file not found")

        config = create_default_config(gear_json_path=gear_json_path)
        assert config.gear.worm.tip_diameter < config.frame.worm_entry_hole
