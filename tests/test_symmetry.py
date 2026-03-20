"""LH/RH mirror symmetry tests.

Validates that the left-hand assembly is an exact mirror of the right-hand:
- Bounding box dimensions match
- X-coordinates are negated
- Volumes are preserved

Run:
    pytest tests/test_symmetry.py -v --gear c13
"""

from dataclasses import replace

import pytest

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.utils.mirror import create_left_hand_config


# ===================================================================
# 1. Config Mirror
# ===================================================================

class TestConfigMirror:
    """Verify LH config is correctly derived from RH config."""

    def test_lh_config_hand(self, default_config):
        """LH config has Hand.LEFT."""
        lh = create_left_hand_config(default_config)
        assert lh.hand == Hand.LEFT

    def test_lh_worm_hand(self, default_config):
        """LH worm is left-hand thread."""
        lh = create_left_hand_config(default_config)
        assert lh.gear.worm.hand == Hand.LEFT

    def test_lh_preserves_dimensions(self, default_config):
        """LH config preserves all non-hand dimensions."""
        lh = create_left_hand_config(default_config)
        assert lh.frame == default_config.frame
        assert lh.string_post == default_config.string_post
        assert lh.peg_head == default_config.peg_head
        assert lh.gear.center_distance == default_config.gear.center_distance
        assert lh.gear.wheel == default_config.gear.wheel
        assert lh.scale == default_config.scale


# ===================================================================
# 2. Frame Mirror Geometry
# ===================================================================

class TestFrameMirrorGeometry:
    """Verify LH and RH frames have matching bounding box dimensions."""

    def test_frame_dimensions_match(self, gear_paths):
        """LH and RH frames have identical bounding box sizes."""
        from gib_tuners.components.frame import create_frame
        from gib_tuners.utils.mirror import mirror_for_left_hand

        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )

        rh_frame = create_frame(config)
        lh_frame = mirror_for_left_hand(rh_frame)

        rh_bb = rh_frame.bounding_box()
        lh_bb = lh_frame.bounding_box()

        # Dimensions (size) should match
        rh_size_x = rh_bb.max.X - rh_bb.min.X
        lh_size_x = lh_bb.max.X - lh_bb.min.X
        rh_size_y = rh_bb.max.Y - rh_bb.min.Y
        lh_size_y = lh_bb.max.Y - lh_bb.min.Y
        rh_size_z = rh_bb.max.Z - rh_bb.min.Z
        lh_size_z = lh_bb.max.Z - lh_bb.min.Z

        assert abs(rh_size_x - lh_size_x) < 0.01, (
            f"X size mismatch: RH={rh_size_x:.3f}, LH={lh_size_x:.3f}"
        )
        assert abs(rh_size_y - lh_size_y) < 0.01, (
            f"Y size mismatch: RH={rh_size_y:.3f}, LH={lh_size_y:.3f}"
        )
        assert abs(rh_size_z - lh_size_z) < 0.01, (
            f"Z size mismatch: RH={rh_size_z:.3f}, LH={lh_size_z:.3f}"
        )

    def test_frame_volume_preserved(self, gear_paths):
        """LH frame volume equals RH frame volume (mirror preserves volume)."""
        from gib_tuners.components.frame import create_frame
        from gib_tuners.utils.mirror import mirror_for_left_hand

        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )

        rh_frame = create_frame(config)
        lh_frame = mirror_for_left_hand(rh_frame)

        rh_vol = rh_frame.volume
        lh_vol = lh_frame.volume

        assert abs(rh_vol - lh_vol) < 0.1, (
            f"Volume mismatch: RH={rh_vol:.1f}, LH={lh_vol:.1f}"
        )

    def test_frame_x_coordinates_reflected(self, gear_paths):
        """LH frame bbox X-coordinates are negated from RH."""
        from gib_tuners.components.frame import create_frame
        from gib_tuners.utils.mirror import mirror_for_left_hand

        config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )

        rh_frame = create_frame(config)
        lh_frame = mirror_for_left_hand(rh_frame)

        rh_bb = rh_frame.bounding_box()
        lh_bb = lh_frame.bounding_box()

        # For a YZ mirror: LH.min.X = -RH.max.X, LH.max.X = -RH.min.X
        assert abs(lh_bb.min.X - (-rh_bb.max.X)) < 0.01, (
            f"LH min.X={lh_bb.min.X:.3f} != -RH max.X={-rh_bb.max.X:.3f}"
        )
        assert abs(lh_bb.max.X - (-rh_bb.min.X)) < 0.01, (
            f"LH max.X={lh_bb.max.X:.3f} != -RH min.X={-rh_bb.min.X:.3f}"
        )

        # Y and Z should be unchanged
        assert abs(lh_bb.min.Y - rh_bb.min.Y) < 0.01
        assert abs(lh_bb.max.Y - rh_bb.max.Y) < 0.01
        assert abs(lh_bb.min.Z - rh_bb.min.Z) < 0.01
        assert abs(lh_bb.max.Z - rh_bb.max.Z) < 0.01


# ===================================================================
# 3. Assembly Mirror Geometry
# ===================================================================

class TestAssemblyMirrorGeometry:
    """Verify 1-gang RH and LH assemblies have matching component sizes."""

    def test_assembly_component_sizes_match(self, gear_paths):
        """Each component's bounding box size matches between LH and RH."""
        from gib_tuners.assembly.gang_assembly import create_positioned_assembly
        from gib_tuners.utils.mirror import mirror_for_left_hand

        rh_config = create_default_config(
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )
        rh_config = replace(rh_config, frame=replace(rh_config.frame, num_housings=1))

        rh_assembly = create_positioned_assembly(
            rh_config,
            wheel_step_path=gear_paths.wheel_step,
            worm_step_path=gear_paths.worm_step,
        )

        rh_parts = rh_assembly["all_parts"]

        # Mirror each RH part and compare bbox sizes
        for name, rh_part in rh_parts.items():
            lh_part = mirror_for_left_hand(rh_part)

            rh_bb = rh_part.bounding_box()
            lh_bb = lh_part.bounding_box()

            rh_sx = rh_bb.max.X - rh_bb.min.X
            lh_sx = lh_bb.max.X - lh_bb.min.X
            rh_sy = rh_bb.max.Y - rh_bb.min.Y
            lh_sy = lh_bb.max.Y - lh_bb.min.Y
            rh_sz = rh_bb.max.Z - rh_bb.min.Z
            lh_sz = lh_bb.max.Z - lh_bb.min.Z

            assert abs(rh_sx - lh_sx) < 0.1, (
                f"{name}: X size mismatch RH={rh_sx:.2f} vs LH={lh_sx:.2f}"
            )
            assert abs(rh_sy - lh_sy) < 0.1, (
                f"{name}: Y size mismatch RH={rh_sy:.2f} vs LH={lh_sy:.2f}"
            )
            assert abs(rh_sz - lh_sz) < 0.1, (
                f"{name}: Z size mismatch RH={rh_sz:.2f} vs LH={lh_sz:.2f}"
            )
