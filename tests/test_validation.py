"""Tests for geometry validation (spec Section 9)."""

from pathlib import Path

import pytest

from gib_tuners.config.defaults import create_default_config
from gib_tuners.utils.validation import (
    validate_geometry,
    ValidationResult,
    check_wheel_worm_interference,
    find_optimal_mesh_rotation,
)


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
        """Spec check: Peg shaft (3.5mm) fits in bearing hole (4.0mm)."""
        shaft = config.peg_head.shaft_diameter
        hole = config.frame.peg_bearing_hole
        assert hole > shaft
        assert hole - shaft >= 0.2  # 0.2mm clearance

    def test_wheel_passes_through_bottom_hole(self, config):
        """Spec check: Wheel OD (7.5mm) passes through bottom hole (8.0mm)."""
        wheel_od = config.gear.wheel.tip_diameter
        wheel_hole = config.frame.wheel_inlet_hole
        assert wheel_hole > wheel_od
        assert wheel_hole - wheel_od >= 0.5  # 0.5mm clearance

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

    def test_peg_cap_stops_push_in(self, config):
        """Spec check: Peg cap (8mm) larger than entry hole (6.2mm)."""
        cap = config.peg_head.cap_diameter
        hole = config.frame.worm_entry_hole
        assert cap > hole

    def test_washer_stops_peg_pull_out(self, config):
        """Spec check: Washer (5mm OD) larger than bearing hole (4.0mm)."""
        washer = config.peg_head.washer_od
        hole = config.frame.peg_bearing_hole
        assert washer > hole

    def test_center_distance_geometry(self, config):
        """Spec check: Center distance geometry is valid per spec Section 9."""
        # The center distance (5.75mm) is intentionally larger than half frame width
        # because the worm passes through holes in the walls. The spec validates
        # this geometry explicitly in Section 9.
        cd = config.gear.center_distance
        assert cd == 5.75  # Per spec (updated for 13-tooth wheel)

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

    def test_m2_thread_fits_through_dd_bore(self, config):
        """Spec check: M2 thread (1.6mm tap) passes through DD across-flats (2.5mm)."""
        tap_bore = config.string_post.tap_bore_diameter
        across_flats = config.gear.wheel.bore.across_flats
        assert across_flats > tap_bore

    def test_washer_retains_wheel(self, config):
        """Spec check: M2 washer (~5mm OD) larger than DD bore (3.5mm)."""
        # Assume ~5mm washer OD for M2
        washer_od = 5.0
        bore = config.gear.wheel.bore.diameter
        assert washer_od > bore


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


class TestWheelWormInterference:
    """Tests for wheel-worm mesh interference checking."""

    @pytest.fixture
    def wheel_step_path(self, reference_dir: Path) -> Path:
        """Return path to wheel STEP file."""
        return reference_dir / "wheel_m0.5_z13.step"

    @pytest.fixture
    def worm_step_path(self, reference_dir: Path) -> Path:
        """Return path to worm STEP file."""
        return reference_dir / "worm_m0.5_z1.step"

    def test_interference_check_with_missing_files(self, production_config):
        """Test that interference check handles missing files gracefully."""
        result = check_wheel_worm_interference(
            wheel_step_path=Path("/nonexistent/wheel.step"),
            worm_step_path=Path("/nonexistent/worm.step"),
            config=production_config,
        )
        assert not result.within_backlash_tolerance
        assert "Could not load" in result.message

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("reference/wheel_m0.5_z13.step").exists(),
        reason="STEP files not available"
    )
    def test_interference_check_loads_step_files(
        self, wheel_step_path, worm_step_path, production_config
    ):
        """Test that interference check can load STEP files."""
        if not wheel_step_path.exists() or not worm_step_path.exists():
            pytest.skip("STEP files not available")

        result = check_wheel_worm_interference(
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            config=production_config,
        )
        # Should not contain "Could not load" error
        assert "Could not load" not in result.message

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("reference/wheel_m0.5_z13.step").exists(),
        reason="STEP files not available"
    )
    def test_optimal_mesh_rotation_is_deterministic(
        self, wheel_step_path, worm_step_path, production_config
    ):
        """Test that mesh rotation calculation gives same result each run."""
        if not wheel_step_path.exists() or not worm_step_path.exists():
            pytest.skip("STEP files not available")

        # Run calculation twice
        rotation1, _ = find_optimal_mesh_rotation(
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            config=production_config,
        )
        rotation2, _ = find_optimal_mesh_rotation(
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            config=production_config,
        )
        # Should get same result
        assert abs(rotation1 - rotation2) < 0.01, (
            f"Mesh rotation not deterministic: {rotation1}° vs {rotation2}°"
        )

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("reference/wheel_m0.5_z13.step").exists(),
        reason="STEP files not available"
    )
    def test_optimal_rotation_within_tooth_pitch(
        self, wheel_step_path, worm_step_path, production_config
    ):
        """Test that optimal rotation is within one tooth pitch angle."""
        if not wheel_step_path.exists() or not worm_step_path.exists():
            pytest.skip("STEP files not available")

        rotation, _ = find_optimal_mesh_rotation(
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            config=production_config,
        )
        num_teeth = production_config.gear.wheel.num_teeth
        tooth_angle = 360.0 / num_teeth  # ~27.69° for 13 teeth

        assert 0 <= rotation < tooth_angle, (
            f"Rotation {rotation}° should be in [0, {tooth_angle}°)"
        )

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("reference/wheel_m0.5_z13.step").exists(),
        reason="STEP files not available"
    )
    def test_interference_within_tolerance(
        self, wheel_step_path, worm_step_path, production_config
    ):
        """Test that optimized mesh has interference within tolerance."""
        if not wheel_step_path.exists() or not worm_step_path.exists():
            pytest.skip("STEP files not available")

        rotation, result = find_optimal_mesh_rotation(
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            config=production_config,
        )
        # At minimum, should be within manufacturing tolerance
        assert result.within_manufacturing_tolerance, (
            f"Interference {result.interference_volume_mm3:.4f}mm³ exceeds tolerance. "
            f"Rotation: {rotation}°. Message: {result.message}"
        )
