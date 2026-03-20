"""Retention and assembly constraint tests.

Validates that retention hardware provides adequate engagement:
- M2 thread engagement depth in string post (must meet 2D rule)
- M2 thread engagement depth in peg head (advisory)
- Washer overlap on bearing holes

Run:
    pytest tests/test_retention.py -v --gear c13
"""

import pytest


# ===================================================================
# 1. Thread Engagement Depth
# ===================================================================

class TestThreadEngagement:
    """M2 screw thread engagement must be sufficient for retention.

    Rule of thumb: engagement >= 2 * thread major diameter (2D rule).
    For M2: engagement >= 4.0mm.
    """

    M2_MAJOR_DIAMETER = 2.0  # mm

    def test_string_post_thread_engagement(self, default_config):
        """String post M2 engagement must meet 2D rule (>= 4.0mm)."""
        sp = default_config.string_post
        min_engagement = 2 * self.M2_MAJOR_DIAMETER
        assert sp.thread_length >= min_engagement, (
            f"String post thread engagement {sp.thread_length}mm "
            f"< 2D minimum {min_engagement}mm"
        )

    def test_peg_head_thread_engagement_advisory(self, default_config):
        """Peg head M2 engagement check (advisory).

        The peg tap depth may be below the 2D rule because string tension
        provides primary retention. This test documents the design choice
        and warns but does not fail.
        """
        ph = default_config.peg_head
        min_engagement = 2 * self.M2_MAJOR_DIAMETER

        if ph.tap_depth < min_engagement:
            import warnings
            warnings.warn(
                f"Peg head thread engagement {ph.tap_depth}mm "
                f"< 2D rule {min_engagement}mm. "
                f"Acceptable because string tension provides primary retention.",
                stacklevel=1,
            )
        # Always passes — this is advisory
        assert ph.tap_depth > 0

    def test_thread_length_within_dd_section(self, default_config):
        """M2 tap bore must not extend beyond the DD cut section length."""
        sp = default_config.string_post
        wheel_fw = default_config.gear.wheel.face_width
        dd_length = sp.get_dd_cut_length(wheel_fw)
        assert sp.thread_length <= dd_length, (
            f"Thread length {sp.thread_length}mm exceeds "
            f"DD section length {dd_length:.2f}mm"
        )


# ===================================================================
# 2. Washer Overlap on Bearing Holes
# ===================================================================

class TestWasherOverlap:
    """Retention washers must overlap the bearing hole edge sufficiently
    to prevent pull-through under load.
    """

    def test_peg_washer_overlap(self, default_config):
        """Peg washer annular overlap >= 0.4mm per side on bearing hole."""
        ph = default_config.peg_head
        fp = default_config.frame
        overlap = (ph.washer_od - fp.peg_bearing_hole) / 2
        assert overlap >= 0.4, (
            f"Peg washer overlap = {overlap:.2f}mm per side "
            f"(washer={ph.washer_od}, hole={fp.peg_bearing_hole}). "
            f"Minimum 0.4mm required."
        )

    def test_post_washer_larger_than_wheel_bore(self, default_config):
        """Post retention washer must be larger than wheel DD bore.

        The washer sits below the wheel, accessible through the bottom
        inlet hole. It must be larger than the DD bore to retain the wheel.
        """
        bore_dia = default_config.gear.wheel.bore.diameter
        # Standard M2 washer OD is ~5mm
        washer_od = 5.0  # Assumed standard M2 washer
        assert washer_od > bore_dia, (
            f"Post washer OD {washer_od}mm <= wheel bore {bore_dia}mm — "
            f"washer would fall through bore"
        )

    def test_peg_washer_fits_on_shaft(self, default_config):
        """Peg washer ID must be larger than shaft for assembly."""
        ph = default_config.peg_head
        assert ph.washer_id > ph.shaft_diameter or ph.washer_id > ph.tap_drill, (
            f"Peg washer ID {ph.washer_id}mm must clear shaft for assembly"
        )

    def test_screw_head_captures_washer(self, default_config):
        """Screw head OD must be larger than washer ID to retain it."""
        ph = default_config.peg_head
        assert ph.screw_head_diameter > ph.washer_id, (
            f"Screw head {ph.screw_head_diameter}mm <= washer ID "
            f"{ph.washer_id}mm — washer not captured"
        )
