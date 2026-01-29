"""Tests for frame geometry generation."""

import pytest

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand


class TestFrameGeometry:
    """Tests for frame creation.

    Note: These tests require build123d to be installed.
    """

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return create_default_config()

    def test_frame_creation(self, config):
        """Test that frame can be created without errors."""
        try:
            from gib_tuners.components.frame import create_frame
        except ImportError:
            pytest.skip("build123d not installed")

        frame = create_frame(config)
        assert frame is not None

    def test_frame_scaled(self, config):
        """Test frame creation at 2x scale."""
        try:
            from gib_tuners.components.frame import create_frame
        except ImportError:
            pytest.skip("build123d not installed")

        scaled_config = create_default_config(scale=2.0)
        frame = create_frame(scaled_config)
        assert frame is not None

    def test_left_hand_frame(self):
        """Test left-hand frame creation."""
        try:
            from gib_tuners.components.frame import create_frame
            from gib_tuners.utils.mirror import create_left_hand_config
        except ImportError:
            pytest.skip("build123d not installed")

        rh_config = create_default_config()
        lh_config = create_left_hand_config(rh_config)

        assert lh_config.hand == Hand.LEFT
        frame = create_frame(lh_config)
        assert frame is not None


class TestStringPostGeometry:
    """Tests for string post creation."""

    def test_string_post_creation(self, production_config):
        """Test that string post can be created."""
        try:
            from gib_tuners.components.string_post import create_string_post
        except ImportError:
            pytest.skip("build123d not installed")

        post = create_string_post(production_config)
        assert post is not None

    def test_string_post_total_length(self, production_config):
        """Test string post total length calculation."""
        params = production_config.string_post
        expected = (
            params.cap_height +
            params.post_height +
            params.bearing_length +
            params.dd_cut_length +
            params.eclip_shaft_length
        )
        assert abs(params.total_length - expected) < 0.01


class TestPegHeadGeometry:
    """Tests for peg head creation."""

    def test_peg_head_creation(self, production_config):
        """Test that peg head can be created."""
        try:
            from gib_tuners.components.peg_head import create_peg_head
        except ImportError:
            pytest.skip("build123d not installed")

        peg_head = create_peg_head(production_config)
        assert peg_head is not None


class TestDDCutFeature:
    """Tests for DD cut feature."""

    def test_dd_cut_bore_creation(self, production_config):
        """Test DD cut bore creation."""
        try:
            from gib_tuners.features.dd_cut import create_dd_cut_bore
        except ImportError:
            pytest.skip("build123d not installed")

        params = production_config.gear.wheel.bore
        bore = create_dd_cut_bore(params, 6.0)
        assert bore is not None

    def test_dd_cut_shaft_creation(self, production_config):
        """Test DD cut shaft creation."""
        try:
            from gib_tuners.features.dd_cut import create_dd_cut_shaft
        except ImportError:
            pytest.skip("build123d not installed")

        params = production_config.string_post.dd_cut
        shaft = create_dd_cut_shaft(params, 6.0)
        assert shaft is not None
