"""Sandwich drilling pattern for frame housings.

Each housing has a specific pattern of holes that enables the sandwich assembly:
- Top: Post bearing hole
- Bottom: Wheel inlet hole
- Side (entry): Worm entry hole (larger)
- Side (bearing): Peg shaft bearing hole (smaller)

Note: The actual drilling is done in frame.py. This module provides
utilities for calculating hole positions and creating drilling cylinders.
"""

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import BuildConfig, Hand


def create_drilling_cylinder(
    diameter: float,
    depth: float,
    position: tuple[float, float, float],
    axis: Axis,
) -> Part:
    """Create a drilling cylinder at a position along an axis.

    Args:
        diameter: Hole diameter
        depth: Drilling depth
        position: (x, y, z) position of hole center
        axis: Axis along which to drill

    Returns:
        Cylinder Part for boolean subtraction
    """
    cyl = Cylinder(
        radius=diameter / 2,
        height=depth,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # Rotate to align with axis
    if axis == Axis.X:
        cyl = cyl.rotate(Axis.Y, 90)
    elif axis == Axis.Y:
        cyl = cyl.rotate(Axis.X, 90)
    # Z is default, no rotation needed

    cyl = cyl.locate(Location(position))
    return cyl


def calculate_worm_axis_offset(config: BuildConfig) -> float:
    """Calculate the worm axis offset from post axis.

    Args:
        config: Build configuration

    Returns:
        Offset in mm (positive = towards entry side)
    """
    return config.gear.center_distance * config.scale


def calculate_hole_positions(
    config: BuildConfig,
    housing_center_y: float,
) -> dict[str, tuple[float, float, float]]:
    """Calculate positions for all holes in a housing.

    Args:
        config: Build configuration
        housing_center_y: Y position of the housing center

    Returns:
        Dictionary mapping hole name to (x, y, z) position
    """
    frame = config.frame
    scale = config.scale
    box_outer = frame.box_outer * scale

    # Post axis at X=0, worm axis offset by center distance
    center_distance = config.gear.center_distance * scale

    # Worm axis height (centered in box)
    worm_z = box_outer / 2

    # Determine entry side based on hand
    if config.hand == Hand.RIGHT:
        entry_x = -box_outer / 2  # Left side
        bearing_x = box_outer / 2  # Right side
    else:
        entry_x = box_outer / 2  # Right side
        bearing_x = -box_outer / 2  # Left side

    return {
        "post_top": (0, housing_center_y, box_outer),  # Top of frame
        "wheel_bottom": (0, housing_center_y, 0),  # Bottom of frame
        "worm_entry": (entry_x, housing_center_y, worm_z),
        "peg_bearing": (bearing_x, housing_center_y, worm_z),
    }
