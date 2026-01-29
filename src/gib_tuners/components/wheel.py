"""Worm wheel handling.

The wheel geometry comes from a generated STEP file (wheel_m0.5_z13.step).
This module provides functions to:
- Load the wheel from STEP
- Modify the bore (e.g., apply DD cut)
- Scale for prototyping
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Align,
    Compound,
    Cylinder,
    Location,
    Part,
    import_step,
)

from ..config.parameters import BuildConfig
from ..features.dd_cut import create_dd_cut_bore


def load_wheel(step_path: Path) -> Part:
    """Load wheel geometry from a STEP file.

    Args:
        step_path: Path to the wheel STEP file

    Returns:
        Wheel Part

    Raises:
        FileNotFoundError: If STEP file doesn't exist
    """
    if not step_path.exists():
        raise FileNotFoundError(f"Wheel STEP file not found: {step_path}")

    shapes = import_step(step_path)

    # import_step can return various types depending on STEP content
    if isinstance(shapes, Part):
        return shapes
    elif hasattr(shapes, "wrapped"):
        # Solid, Compound, or other Shape subclass
        return Part(shapes.wrapped)
    elif isinstance(shapes, list) and len(shapes) > 0:
        return Part(shapes[0].wrapped)
    else:
        raise ValueError(f"No valid geometry found in {step_path}")


def modify_wheel_bore(
    wheel: Part,
    config: BuildConfig,
    current_bore_diameter: Optional[float] = None,
) -> Part:
    """Modify the wheel bore to have a DD cut.

    If the wheel already has a round bore, this creates the DD cut.
    If the wheel STEP already has a DD bore, this is a no-op.

    Args:
        wheel: Wheel Part to modify
        config: Build configuration
        current_bore_diameter: Current bore diameter if known (for removal)

    Returns:
        Wheel with DD cut bore
    """
    wheel_params = config.gear.wheel
    dd_params = wheel_params.bore
    face_width = wheel_params.face_width * config.scale

    # Create DD cut bore
    dd_bore = create_dd_cut_bore(dd_params, face_width + 0.2, config.scale)

    # The bore should be centered in the wheel
    dd_bore = dd_bore.locate(Location((0, 0, -0.1)))

    # If we need to first remove an existing round bore
    if current_bore_diameter is not None:
        # Add back a cylinder to fill the existing bore
        fill = Cylinder(
            radius=current_bore_diameter * config.scale / 2,
            height=face_width,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        wheel = wheel + fill

    # Cut the DD bore
    wheel = wheel - dd_bore

    return wheel


def create_wheel_placeholder(config: BuildConfig) -> Part:
    """Create a placeholder wheel for when STEP file is unavailable.

    This creates a simple cylinder with DD bore for testing.
    The wheel is centered at Z=0 to match STEP file conventions.

    Args:
        config: Build configuration

    Returns:
        Placeholder wheel Part
    """
    wheel_params = config.gear.wheel
    scale = config.scale

    tip_d = wheel_params.tip_diameter * scale
    face_width = wheel_params.face_width * scale

    # Basic cylinder centered at Z=0
    wheel = Cylinder(
        radius=tip_d / 2,
        height=face_width,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # Add DD bore (centered)
    dd_bore = create_dd_cut_bore(wheel_params.bore, face_width + 0.2, scale)
    wheel = wheel - dd_bore

    return wheel
