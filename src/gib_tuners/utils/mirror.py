"""Left-hand / right-hand mirroring utilities.

The LH variant is a geometric mirror of the RH assembly.
"""

from typing import TYPE_CHECKING

from ..config.parameters import BuildConfig, GearParams, Hand, WormParams

if TYPE_CHECKING:
    from build123d import Compound, Part


def mirror_for_left_hand(shape: "Part | Compound") -> "Part | Compound":
    """Mirror a shape for left-hand variant.

    Mirrors about the YZ plane (X=0), which flips the entry/bearing
    hole sides.

    Args:
        shape: RH shape to mirror

    Returns:
        LH mirrored shape
    """
    from build123d import Plane
    return shape.mirror(Plane.YZ)


def create_left_hand_config(rh_config: BuildConfig) -> BuildConfig:
    """Create a left-hand configuration from a right-hand one.

    Changes:
    - hand: RIGHT -> LEFT
    - worm.hand: RIGHT -> LEFT

    Args:
        rh_config: Right-hand build configuration

    Returns:
        Left-hand build configuration
    """
    # Create new worm params with left hand
    lh_worm = WormParams(
        module=rh_config.gear.worm.module,
        num_starts=rh_config.gear.worm.num_starts,
        pitch_diameter=rh_config.gear.worm.pitch_diameter,
        tip_diameter=rh_config.gear.worm.tip_diameter,
        root_diameter=rh_config.gear.worm.root_diameter,
        lead=rh_config.gear.worm.lead,
        lead_angle_deg=rh_config.gear.worm.lead_angle_deg,
        length=rh_config.gear.worm.length,
        hand=Hand.LEFT,
        throat_reduction=rh_config.gear.worm.throat_reduction,
        throat_curvature_radius=rh_config.gear.worm.throat_curvature_radius,
    )

    # Create new gear params with LH worm
    lh_gear = GearParams(
        worm=lh_worm,
        wheel=rh_config.gear.wheel,
        center_distance=rh_config.gear.center_distance,
        pressure_angle_deg=rh_config.gear.pressure_angle_deg,
        backlash=rh_config.gear.backlash,
        ratio=rh_config.gear.ratio,
    )

    return BuildConfig(
        scale=rh_config.scale,
        tolerance=rh_config.tolerance,
        hand=Hand.LEFT,
        frame=rh_config.frame,
        gear=lh_gear,
        peg_head=rh_config.peg_head,
        string_post=rh_config.string_post,
    )
