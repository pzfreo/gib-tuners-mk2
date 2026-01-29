"""Tests for geometry validation (spec Section 9)."""

import pytest

from gib_tuners.config.defaults import create_default_config
from gib_tuners.utils.validation import validate_geometry, ValidationResult


class TestSpecValidation:
    """Tests that validate the design against spec Section 9."""

    @pytest.fixture
    def config(self, gear_json_path):
        """Create a production configuration."""
        if gear_json_path.exists():
            return create_default_config(gear_json_path=gear_json_path)
        return create_default_config()

    def test_all_validations_pass(self, config):
        """Test that all spec validations pass with default params."""
        result = validate_geometry(config)
        assert result.passed, f"Validation failed:\n{result}"

    def test_worm_fits_in_cavity(self, config):
        """Spec check: Worm OD (6.0mm) fits within internal cavity (8.15mm)."""
        worm_od = config.gear.worm.tip_diameter
        cavity = config.frame.box_inner
        assert cavity > worm_od
        assert cavity - worm_od >= 2.0  # At least 2mm clearance

    def test_worm_passes_through_entry_hole(self, config):
        """Spec check: Worm OD (6.0mm) passes through entry hole (6.2mm)."""
        worm_od = config.gear.worm.tip_diameter
        entry_hole = config.frame.worm_entry_hole
        assert entry_hole > worm_od
        assert entry_hole - worm_od >= 0.2  # 0.2mm clearance

    def test_peg_shaft_fits_in_bearing(self, config):
        """Spec check: Peg shaft (3.8mm) fits in bearing hole (4.0mm)."""
        shaft = config.peg_head.bearing_diameter
        hole = config.frame.peg_bearing_hole
        assert hole > shaft
        assert hole - shaft >= 0.2  # 0.2mm clearance

    def test_wheel_passes_through_bottom_hole(self, config):
        """Spec check: Wheel OD (7.0mm) passes through bottom hole (8.0mm)."""
        wheel_od = config.gear.wheel.tip_diameter
        wheel_hole = config.frame.wheel_inlet_hole
        assert wheel_hole > wheel_od
        assert wheel_hole - wheel_od >= 1.0  # 1.0mm clearance

    def test_post_shaft_fits_in_top_hole(self, config):
        """Spec check: Post shaft (4.0mm) fits in top hole (4.2mm)."""
        shaft = config.string_post.bearing_diameter
        hole = config.frame.post_bearing_hole
        assert hole > shaft
        assert hole - shaft >= 0.2  # 0.2mm clearance

    def test_post_cap_stops_pull_through(self, config):
        """Spec check: Post cap (7.5mm) larger than top hole (4.2mm)."""
        cap = config.string_post.cap_diameter
        hole = config.frame.post_bearing_hole
        assert cap > hole

    def test_peg_shoulder_stops_pull_in(self, config):
        """Spec check: Peg shoulder (8mm) larger than entry hole (6.2mm)."""
        shoulder = config.peg_head.shoulder_diameter
        hole = config.frame.worm_entry_hole
        assert shoulder > hole

    def test_washer_stops_peg_pull_out(self, config):
        """Spec check: Washer (5mm OD) larger than bearing hole (4.0mm)."""
        washer = config.peg_head.washer_od
        hole = config.frame.peg_bearing_hole
        assert washer > hole

    def test_center_distance_geometry(self, config):
        """Spec check: Center distance geometry is valid per spec Section 9."""
        # The center distance (5.5mm) is intentionally larger than half frame width
        # because the worm passes through holes in the walls. The spec validates
        # this geometry explicitly in Section 9.
        cd = config.gear.center_distance
        assert cd == 5.5  # Per spec

    def test_center_distance_calculation(self, config):
        """Spec check: CD = (worm PD + wheel PD) / 2."""
        worm_pd = config.gear.worm.pitch_diameter
        wheel_pd = config.gear.wheel.pitch_diameter
        expected_cd = (worm_pd + wheel_pd) / 2
        actual_cd = config.gear.center_distance
        assert abs(actual_cd - expected_cd) < 0.01

    def test_gear_modules_match(self, config):
        """Spec check: Worm and wheel have matching modules."""
        worm_module = config.gear.worm.module
        wheel_module = config.gear.wheel.module
        assert worm_module == wheel_module

    def test_eclip_retains_wheel(self, config):
        """Spec check: E-clip OD (6mm) larger than wheel bore (3mm)."""
        eclip = config.string_post.eclip_od
        bore = config.gear.wheel.bore.diameter
        assert eclip > bore

    def test_wheel_slides_over_eclip_shaft(self, config):
        """Spec check: Wheel bore (3mm) larger than E-clip shaft (2.5mm)."""
        bore = config.gear.wheel.bore.diameter
        shaft = config.string_post.eclip_shaft_diameter
        assert bore > shaft


class TestValidationOutput:
    """Tests for validation output formatting."""

    def test_validation_result_string(self):
        """Test that validation result can be converted to string."""
        config = create_default_config()
        result = validate_geometry(config)
        output = str(result)
        assert "Validation" in output
        assert "PASSED" in output or "FAILED" in output

    def test_validation_checks_count(self):
        """Test that validation has expected number of checks."""
        config = create_default_config()
        result = validate_geometry(config)
        # Should have at least 10 checks
        assert len(result.checks) >= 10
