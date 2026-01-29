"""Post and wheel partial assembly.

This assembly combines:
- String post (with DD shaft and M2 tap bore)
- Worm wheel (imported from STEP)

The wheel mates with the DD section of the post.
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Axis,
    Compound,
    Location,
    Part,
)

from ..config.parameters import BuildConfig
from ..components.string_post import create_string_post
from ..components.wheel import load_wheel, create_wheel_placeholder


def create_post_wheel_assembly(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
) -> dict[str, Part]:
    """Create a post + wheel assembly.

    The post is positioned with the bottom of the DD section at Z=0.
    The wheel is positioned to mate with the DD section.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file

    Returns:
        Dictionary of component name to Part
    """
    scale = config.scale
    post_params = config.string_post
    wheel_params = config.gear.wheel

    # Create string post - already positioned with DD at Z=0
    post = create_string_post(config)

    components = {"string_post": post}

    # Load or create wheel
    if wheel_step_path is not None and wheel_step_path.exists():
        wheel = load_wheel(wheel_step_path)
        # Scale if needed (STEP is at 1:1)
        if scale != 1.0:
            wheel = wheel.scale(scale)
    else:
        wheel = create_wheel_placeholder(config)

    # Position wheel on DD section
    # The DD section starts at Z=0 and extends to Z=dd_cut_length (6mm)
    # The wheel STEP is centered at Z=0 (extends from -3 to +3)
    # We need to shift it up so it sits at Z=0 to Z=6
    dd_length = post_params.dd_cut_length * scale
    face_width = wheel_params.face_width * scale

    # Shift wheel so its bottom is at Z=0 (center of DD section)
    # Wheel center is at Z=0 in STEP, so shift up by half the face width
    wheel_z = face_width / 2

    wheel = wheel.locate(Location((0, 0, wheel_z)))
    components["wheel"] = wheel

    return components


def create_post_wheel_compound(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
) -> Compound:
    """Create post + wheel assembly as a compound shape.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file

    Returns:
        Compound containing post and wheel
    """
    components = create_post_wheel_assembly(config, wheel_step_path)
    return Compound(list(components.values()))
