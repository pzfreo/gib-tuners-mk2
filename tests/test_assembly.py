"""Tests for assembly interference checks."""

from dataclasses import replace
from pathlib import Path

import pytest

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.assembly import (
    AssemblyInterferenceError,
    create_positioned_assembly,
    run_interference_report,
)


class TestAssemblyInterference:
    """Tests for assembly interference checking.

    Uses gear_paths fixture from conftest.py (parameterized via --gear option).
    """

    def test_single_housing_no_interference(self, gear_paths):
        """Test that a single-housing assembly has no interference."""
        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        config = replace(config, frame=replace(config.frame, num_housings=1))

        # Should not raise
        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
            check_interference=True,
        )

        # Verify interference results are included
        assert "interference" in assembly
        # Small interference expected from gear mesh (zero backlash)
        assert assembly["interference"]["total"] < 0.1

    def test_five_housing_no_interference(self, gear_paths):
        """Test that a 5-housing assembly has no interference."""
        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        # Default is 5 housings

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
            check_interference=True,
        )

        # 5 housings with small gear mesh interference each
        assert assembly["interference"]["total"] < 0.5

    def test_interference_report_keys(self, gear_paths):
        """Test that interference report contains expected keys."""
        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        config = replace(config, frame=replace(config.frame, num_housings=1))

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
            check_interference=False,  # Don't raise, just build
        )

        results = run_interference_report(assembly, verbose=False)

        # Should have keys for each check type
        assert "total" in results
        assert "tuner_1_gear_mesh" in results
        assert "tuner_1_post_in_hole" in results
        assert "tuner_1_worm_in_hole" in results
        assert "tuner_1_wheel_in_cavity" in results

    def test_check_interference_false_no_validation(self, gear_paths):
        """Test that check_interference=False skips validation."""
        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        config = replace(config, frame=replace(config.frame, num_housings=1))

        assembly = create_positioned_assembly(
            config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
            check_interference=False,
        )

        # Should not have interference key when not checked
        assert "interference" not in assembly
