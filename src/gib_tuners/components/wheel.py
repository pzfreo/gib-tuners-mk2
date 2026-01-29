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
    Axis,
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


def calculate_mesh_rotation(
    wheel: Part,
    worm: Part,
    num_teeth: int,
    coarse_step: float = 1.0,
    fine_step: float = 0.1,
) -> float:
    """Find wheel rotation that minimizes collision with worm.

    Uses iterative collision minimization to find the optimal wheel rotation
    angle that aligns wheel teeth with worm thread valleys.

    Args:
        wheel: Wheel Part (centered at origin, Z-axis rotation)
        worm: Worm Part (positioned for mesh testing)
        num_teeth: Number of teeth on the wheel (determines tooth pitch angle)
        coarse_step: Step size in degrees for initial search (default 1.0°)
        fine_step: Step size in degrees for refinement (default 0.1°)

    Returns:
        Optimal rotation angle in degrees
    """
    tooth_angle = 360.0 / num_teeth  # ~27.69° for 13 teeth

    best_rotation = 0.0
    min_interference = float("inf")

    # Coarse search: test rotations in coarse_step increments within one tooth pitch
    coarse_angles = [i * coarse_step for i in range(int(tooth_angle / coarse_step) + 1)]
    for angle in coarse_angles:
        rotated_wheel = wheel.rotate(Axis.Z, angle)
        try:
            intersection = rotated_wheel & worm
            interference = intersection.volume if hasattr(intersection, "volume") else 0
        except Exception:
            # Boolean operation failed - treat as no interference
            interference = 0

        if interference < min_interference:
            min_interference = interference
            best_rotation = angle

    # Fine search: refine around best angle with fine_step increments
    fine_range = int(coarse_step / fine_step)
    fine_angles = [
        best_rotation + (d - fine_range) * fine_step
        for d in range(2 * fine_range + 1)
    ]
    for angle in fine_angles:
        # Keep angle within [0, tooth_angle) range
        normalized_angle = angle % tooth_angle
        rotated_wheel = wheel.rotate(Axis.Z, normalized_angle)
        try:
            intersection = rotated_wheel & worm
            interference = intersection.volume if hasattr(intersection, "volume") else 0
        except Exception:
            interference = 0

        if interference < min_interference:
            min_interference = interference
            best_rotation = normalized_angle

    return best_rotation


def calculate_mesh_rotation_analytical(
    num_teeth: int,
    lead: float,
    z_offset: float = 0.0,
) -> tuple[float, float]:
    """Calculate optimal wheel rotation analytically.

    For a worm gear mesh, the optimal wheel rotation aligns a tooth valley
    with the worm thread at the contact point. This is derived from:
    1. Base alignment: 180° / num_teeth (centers a valley at mesh point)
    2. Z-offset correction: when axes are at different Z heights, the contact
       point shifts along the worm helix

    Args:
        num_teeth: Number of wheel teeth
        lead: Worm lead in mm (axial advance per revolution = π × module × num_starts)
        z_offset: wheel_axis_z - worm_axis_z in mm (positive = wheel higher)

    Returns:
        Tuple of (rotation_plus, rotation_minus) in degrees for both sign options.
        Test both to determine which gives less interference for your geometry.
    """
    # Base alignment: center a tooth valley at the mesh point
    base = 180.0 / num_teeth

    # Z-offset correction: shift along worm helix
    # When wheel is higher than worm, contact shifts along worm thread
    # This is equivalent to a rotation of (z_offset / lead) × 360° on the worm
    # which requires (z_offset / lead) × (360° / num_teeth) wheel rotation to compensate
    z_correction = 0.0
    if z_offset != 0.0:
        z_correction = (z_offset / lead) * (360.0 / num_teeth)

    # Normalize to [0, tooth_pitch)
    tooth_pitch = 360.0 / num_teeth
    rotation_plus = (base + z_correction) % tooth_pitch
    rotation_minus = (base - z_correction) % tooth_pitch

    return (rotation_plus, rotation_minus)


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
