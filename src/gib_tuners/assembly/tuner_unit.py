"""Single tuner unit assembly.

A tuner unit consists of:
- Peg head (with integral worm)
- String post
- Worm wheel
- Retention hardware (washers, E-clip, screw)
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
    create_wheel_eclip,
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

    # String post - positioned with bottom of E-clip groove at Z=0
    # Adjust so frame bearing sits at frame wall level
    post = create_string_post(config)
    # Post total length from params
    post_params = config.string_post
    eclip_h = post_params.eclip_shaft_length * scale
    dd_h = post_params.dd_cut_length * scale
    bearing_h = post_params.bearing_length * scale

    # Position post so bearing section is at frame wall
    # Frame bottom is at Z=0, frame top at Z=box_outer
    # Top hole is at Z = box_outer - wall
    # Post bearing should sit in this hole
    post_z_offset = -(eclip_h + dd_h)  # Move down so bearing aligns with frame top
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

    # Wheel sits on post, centered on DD section
    # DD section starts at Z = eclip_h (above E-clip shaft)
    wheel_z = post_z_offset + eclip_h
    wheel = wheel.locate(Location((0, 0, wheel_z)))
    components["wheel"] = wheel

    # Peg head - worm axis is horizontal (X), offset by center distance
    peg_head = create_peg_head(config)

    # Worm axis height is at frame center (Z = box_outer / 2)
    worm_z = box_outer / 2

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

        # M2 screw
        screw = create_m2_pan_head_screw(config)
        screw = screw.rotate(Axis.Y, 90)
        screw = screw.locate(Location((washer_x + peg_params.washer_thickness * scale, 0, worm_z)))
        components["peg_screw"] = screw

        # Wheel E-clip - sits in groove below wheel
        eclip = create_wheel_eclip(config)
        eclip_z = post_z_offset  # At bottom of post
        eclip = eclip.locate(Location((0, 0, eclip_z)))
        components["wheel_eclip"] = eclip

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
