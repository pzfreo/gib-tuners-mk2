"""Single tuner unit assembly.

A tuner unit consists of:
- Peg head (with integral worm)
- String post
- Worm wheel
- Retention hardware (washers, M2 screws)
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Axis,
    Compound,
    Location,
    Part,
    Rotation,
)

from ..config.parameters import BuildConfig, Hand
from ..components.peg_head import create_peg_head
from ..components.string_post import create_string_post
from ..components.wheel import create_wheel_placeholder, load_wheel
from ..components.hardware import (
    create_peg_retention_washer,
    create_wheel_retention_washer,
    create_wheel_retention_screw,
    create_m2_pan_head_screw,
)


def create_tuner_unit(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> dict[str, Part]:
    """Create a single tuner unit with all components.

    Components are positioned relative to the post axis at origin:
    - Post axis is Z (vertical)
    - Worm axis is X (horizontal), offset by center distance

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Dictionary of component name to Part
    """
    scale = config.scale
    center_distance = config.gear.center_distance * scale

    # Frame dimensions for positioning
    frame = config.frame
    box_outer = frame.box_outer * scale
    wall = frame.wall_thickness * scale

    # String post dimensions
    post_params = config.string_post
    dd_h = post_params.dd_cut_length * scale
    bearing_h = post_params.bearing_length * scale

    # String post - positioned so bearing section fills the mounting plate hole
    # Post coordinate system: Z=0 at bottom of DD section, builds upward
    # Frame coordinate system: Z=0 at mounting plate top, extends into -Z
    #
    # The bearing section (from dd_h to dd_h+bearing_h in post coords)
    # should align with the mounting plate hole (from -wall to 0 in frame coords)
    # So post Z=dd_h should align with frame Z=-wall (inside of mounting plate)
    # Therefore: post_z_offset = -wall - dd_h
    # Which means: post Z=dd_h+bearing_h aligns with frame Z=0 (top surface)
    post = create_string_post(config)
    post_z_offset = -(dd_h + bearing_h)
    post = post.locate(Location((0, 0, post_z_offset)))

    components = {"string_post": post}

    # Wheel - sits on the DD cut section of the post
    if wheel_step_path is not None and wheel_step_path.exists():
        wheel = load_wheel(wheel_step_path)
        # Scale if needed (STEP is at 1:1)
        if scale != 1.0:
            wheel = wheel.scale(scale)
    else:
        wheel = create_wheel_placeholder(config)

    # Wheel sits on post DD section
    # DD section spans from post Z=0 to Z=dd_h
    # Wheel STEP is centered at Z=0, so shift up by half face width
    wheel_params = config.gear.wheel
    face_width = wheel_params.face_width * scale
    wheel_z = post_z_offset + face_width / 2
    wheel = wheel.locate(Location((0, 0, wheel_z)))
    components["wheel"] = wheel

    # Peg head - worm axis is horizontal (X), offset by center distance
    peg_head = create_peg_head(config)

    # Worm axis height is at frame center
    # Frame spans Z=0 (top) to Z=-box_outer (bottom)
    # Worm axis is centered in the cavity at Z = -box_outer / 2
    worm_z = -box_outer / 2

    # Determine X offset based on hand
    if config.hand == Hand.RIGHT:
        # Worm on negative X side
        worm_x = -center_distance
    else:
        # Worm on positive X side
        worm_x = center_distance

    peg_head = peg_head.locate(Location((worm_x, 0, worm_z)))
    components["peg_head"] = peg_head

    if include_hardware:
        # Peg retention washer - sits on bearing shaft end
        peg_washer = create_peg_retention_washer(config)
        # Position at end of peg shaft
        peg_params = config.peg_head
        worm_params = config.gear.worm
        # Shaft extends from ring center
        ring_width = peg_params.ring_width * scale
        shoulder_h = peg_params.shoulder_length * scale
        worm_length = worm_params.length * scale
        bearing_h_peg = peg_params.bearing_length * scale

        washer_x = worm_x + ring_width / 2 + shoulder_h + worm_length + bearing_h_peg
        # Rotate washer to face along X axis
        peg_washer = peg_washer.rotate(Axis.Y, 90)
        peg_washer = peg_washer.locate(Location((washer_x, 0, worm_z)))
        components["peg_washer"] = peg_washer

        # M2 screw for peg retention
        peg_screw = create_m2_pan_head_screw(config)
        peg_screw = peg_screw.rotate(Axis.Y, 90)
        peg_screw = peg_screw.locate(Location((washer_x + peg_params.washer_thickness * scale, 0, worm_z)))
        components["peg_screw"] = peg_screw

        # Wheel retention hardware (M2 washer + screw from below)
        # Washer sits below the wheel at post Z=0 (frame Z = post_z_offset)
        washer_thickness = 0.5 * scale
        wheel_washer = create_wheel_retention_washer(config)
        wheel_washer_z = post_z_offset - washer_thickness
        wheel_washer = wheel_washer.locate(Location((0, 0, wheel_washer_z)))
        components["wheel_washer"] = wheel_washer

        # M2 screw threads into tap bore from below
        wheel_screw = create_wheel_retention_screw(config)
        screw_head_h = 1.3 * scale
        wheel_screw_z = wheel_washer_z - screw_head_h
        wheel_screw = wheel_screw.locate(Location((0, 0, wheel_screw_z)))
        components["wheel_screw"] = wheel_screw

    return components


def create_tuner_unit_compound(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> Compound:
    """Create a single tuner unit as a compound shape.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Compound containing all tuner components
    """
    components = create_tuner_unit(config, wheel_step_path, include_hardware)
    return Compound(list(components.values()))
