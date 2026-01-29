"""Worm-Wheel Mesh Alignment Module

This module provides functions for calculating optimal wheel rotation to achieve
proper mesh alignment with a worm, and for checking interference between the gears.

Usage:
    from mesh_alignment import find_optimal_mesh_rotation, check_interference, create_axis_markers

    # Calculate optimal rotation
    rotation_deg, interference_mm3 = find_optimal_mesh_rotation(
        wheel=wheel_part,
        worm=worm_part,
        center_distance=5.75,
        num_teeth=13,
    )

    # Apply rotation to wheel
    wheel_aligned = wheel.rotate(Axis.Z, rotation_deg)

    # Create visualization helpers
    markers = create_axis_markers(center_distance=5.75, worm_length=7.8)

Dependencies:
    - build123d
    - OCP (OpenCASCADE Python bindings)
"""

from dataclasses import dataclass
from typing import Tuple, Optional

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
)


@dataclass
class MeshAnalysisResult:
    """Results from mesh alignment analysis."""
    optimal_rotation_deg: float
    interference_volume_mm3: float
    within_tolerance: bool
    tooth_pitch_deg: float
    message: str


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

    The algorithm searches within one tooth pitch (360°/num_teeth) since
    the mesh pattern repeats every tooth.

    Args:
        wheel: Wheel Part centered at origin with axis along Z
        worm: Worm Part positioned at correct center distance (axis along X)
        num_teeth: Number of teeth on the wheel
        coarse_step: Step size in degrees for initial search (default 1.0°)
        fine_step: Step size in degrees for refinement (default 0.1°)

    Returns:
        Optimal rotation angle in degrees (0 to tooth_pitch)
    """
    tooth_angle = 360.0 / num_teeth

    best_rotation = 0.0
    min_interference = float("inf")

    # Coarse search: test rotations in coarse_step increments
    coarse_angles = [i * coarse_step for i in range(int(tooth_angle / coarse_step) + 1)]
    for angle in coarse_angles:
        rotated_wheel = wheel.rotate(Axis.Z, angle)
        try:
            intersection = rotated_wheel & worm
            interference = intersection.volume if hasattr(intersection, "volume") else 0
        except Exception:
            interference = 0

        if interference < min_interference:
            min_interference = interference
            best_rotation = angle

    # Fine search: refine around best angle
    fine_range = int(coarse_step / fine_step)
    fine_angles = [
        best_rotation + (d - fine_range) * fine_step
        for d in range(2 * fine_range + 1)
    ]
    for angle in fine_angles:
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


def check_interference(
    wheel: Part,
    worm: Part,
    rotation_deg: float = 0.0,
) -> float:
    """Check intersection volume between wheel and worm.

    Args:
        wheel: Wheel Part centered at origin with axis along Z
        worm: Worm Part positioned at correct center distance
        rotation_deg: Rotation to apply to wheel before checking

    Returns:
        Intersection volume in mm³
    """
    if rotation_deg != 0.0:
        wheel = wheel.rotate(Axis.Z, rotation_deg)

    try:
        intersection = wheel & worm
        return intersection.volume if hasattr(intersection, "volume") else 0.0
    except Exception:
        return 0.0


def find_optimal_mesh_rotation(
    wheel: Part,
    worm: Part,
    center_distance: float,
    num_teeth: int,
    backlash_tolerance_mm3: float = 1.0,
) -> MeshAnalysisResult:
    """Find optimal wheel rotation and analyze mesh quality.

    This is the main entry point for mesh analysis. It:
    1. Positions the worm at the correct center distance
    2. Calculates optimal wheel rotation
    3. Measures final interference
    4. Reports whether mesh is within tolerance

    Args:
        wheel: Wheel Part centered at origin with axis along Z
        worm: Worm Part centered at origin with axis along Z (will be rotated)
        center_distance: Distance between wheel and worm axes in mm
        num_teeth: Number of teeth on the wheel
        backlash_tolerance_mm3: Maximum acceptable interference volume

    Returns:
        MeshAnalysisResult with rotation, interference, and status
    """
    tooth_pitch = 360.0 / num_teeth

    # Position worm: rotate -90° Y so axis is along X, offset by center_distance in Y
    worm_positioned = worm.rotate(Axis.Y, -90)
    worm_positioned = worm_positioned.locate(Location((0, center_distance, 0)))

    # Calculate optimal rotation
    optimal_rotation = calculate_mesh_rotation(
        wheel=wheel,
        worm=worm_positioned,
        num_teeth=num_teeth,
    )

    # Check interference at optimal rotation
    interference = check_interference(
        wheel=wheel,
        worm=worm_positioned,
        rotation_deg=optimal_rotation,
    )

    # Also check interference without rotation for comparison
    interference_unrotated = check_interference(
        wheel=wheel,
        worm=worm_positioned,
        rotation_deg=0.0,
    )

    within_tolerance = interference <= backlash_tolerance_mm3

    if interference == 0.0:
        message = "Perfect mesh - no interference detected"
    elif within_tolerance:
        message = f"Good mesh - interference {interference:.4f}mm³ within tolerance"
    else:
        message = f"Warning - interference {interference:.4f}mm³ exceeds tolerance"

    if interference_unrotated > 0 and interference < interference_unrotated:
        message += f" (reduced from {interference_unrotated:.4f}mm³ without rotation)"

    return MeshAnalysisResult(
        optimal_rotation_deg=optimal_rotation,
        interference_volume_mm3=interference,
        within_tolerance=within_tolerance,
        tooth_pitch_deg=tooth_pitch,
        message=message,
    )


def create_axis_markers(
    center_distance: float,
    worm_length: float = 10.0,
    wheel_height: float = 10.0,
    marker_radius: float = 0.2,
) -> dict[str, Part]:
    """Create axis marker cylinders for visualization.

    These thin cylinders mark the true axis positions of the wheel and worm,
    which is helpful because gear bounding boxes shift with rotation.

    Args:
        center_distance: Distance between wheel and worm axes
        worm_length: Length of worm axis marker
        wheel_height: Length of wheel axis marker
        marker_radius: Radius of marker cylinders

    Returns:
        Dictionary with 'wheel_axis' and 'worm_axis' Parts
    """
    # Wheel axis: vertical (Z) at origin
    wheel_axis = Cylinder(
        radius=marker_radius,
        height=wheel_height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # Worm axis: horizontal (X) at Y=center_distance
    worm_axis = Cylinder(
        radius=marker_radius,
        height=worm_length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    worm_axis = worm_axis.rotate(Axis.Y, 90)
    worm_axis = worm_axis.locate(Location((0, center_distance, 0)))

    return {
        "wheel_axis": wheel_axis,
        "worm_axis": worm_axis,
    }


def print_mesh_report(
    result: MeshAnalysisResult,
    center_distance: float,
    num_teeth: int,
) -> str:
    """Generate a human-readable mesh analysis report.

    Args:
        result: MeshAnalysisResult from find_optimal_mesh_rotation
        center_distance: Center distance used
        num_teeth: Number of wheel teeth

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 50,
        "WORM-WHEEL MESH ANALYSIS REPORT",
        "=" * 50,
        "",
        "Gear Parameters:",
        f"  Wheel teeth:      {num_teeth}",
        f"  Tooth pitch:      {result.tooth_pitch_deg:.2f}°",
        f"  Center distance:  {center_distance:.2f}mm",
        "",
        "Mesh Alignment:",
        f"  Optimal rotation: {result.optimal_rotation_deg:.2f}°",
        f"  Interference:     {result.interference_volume_mm3:.4f}mm³",
        f"  Within tolerance: {'Yes' if result.within_tolerance else 'NO'}",
        "",
        f"Status: {result.message}",
        "=" * 50,
    ]
    return "\n".join(lines)


# Example usage when run directly
if __name__ == "__main__":
    from pathlib import Path
    from build123d import import_step

    # Example with STEP files
    wheel_path = Path("wheel_m0.5_z13.step")
    worm_path = Path("worm_m0.5_z1.step")

    if wheel_path.exists() and worm_path.exists():
        wheel = import_step(wheel_path)
        worm = import_step(worm_path)

        if hasattr(wheel, "wrapped"):
            wheel = Part(wheel.wrapped)
        if hasattr(worm, "wrapped"):
            worm = Part(worm.wrapped)

        result = find_optimal_mesh_rotation(
            wheel=wheel,
            worm=worm,
            center_distance=5.75,
            num_teeth=13,
        )

        report = print_mesh_report(result, center_distance=5.75, num_teeth=13)
        print(report)
    else:
        print("STEP files not found. Place wheel and worm STEP files in current directory.")
