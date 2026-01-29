# Prompt for Worm Gear Project: Add Mesh Alignment Analysis

## Context

When generating worm and wheel STEP files, the wheel teeth have an arbitrary starting orientation. For proper meshing visualization, the wheel needs to be rotated to align teeth with worm thread valleys.

## Feature Request

Add mesh alignment analysis to the worm gear generator that:

1. **Calculates optimal wheel rotation** to minimize interference with the worm
2. **Reports interference volume** at the optimal rotation
3. **Outputs axis markers** for visualization (thin cylinders showing true axis positions)
4. **Includes mesh data in output** (rotation angle, interference volume, tolerance status)

## Algorithm

The mesh alignment algorithm works by:

1. Testing wheel rotations from 0° to one tooth pitch (360°/num_teeth) in 1° steps
2. At each angle, computing the boolean intersection volume between wheel and worm
3. Refining around the minimum with 0.1° steps
4. Returning the angle with minimum (ideally zero) interference

Key insight: The mesh pattern repeats every tooth pitch, so we only need to search within one tooth's angular span.

## Implementation

Here's the core mesh alignment code to integrate:

```python
from dataclasses import dataclass
from build123d import Axis, Location, Part, Cylinder, Align

@dataclass
class MeshAnalysisResult:
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

    Args:
        wheel: Wheel Part centered at origin with axis along Z
        worm: Worm Part positioned at correct center distance (axis along X)
        num_teeth: Number of teeth on the wheel
        coarse_step: Step size for initial search
        fine_step: Step size for refinement

    Returns:
        Optimal rotation angle in degrees
    """
    tooth_angle = 360.0 / num_teeth
    best_rotation = 0.0
    min_interference = float("inf")

    # Coarse search
    for angle in [i * coarse_step for i in range(int(tooth_angle / coarse_step) + 1)]:
        rotated_wheel = wheel.rotate(Axis.Z, angle)
        try:
            intersection = rotated_wheel & worm
            interference = intersection.volume if hasattr(intersection, "volume") else 0
        except Exception:
            interference = 0
        if interference < min_interference:
            min_interference = interference
            best_rotation = angle

    # Fine search around best angle
    fine_range = int(coarse_step / fine_step)
    for d in range(-fine_range, fine_range + 1):
        angle = (best_rotation + d * fine_step) % tooth_angle
        rotated_wheel = wheel.rotate(Axis.Z, angle)
        try:
            intersection = rotated_wheel & worm
            interference = intersection.volume if hasattr(intersection, "volume") else 0
        except Exception:
            interference = 0
        if interference < min_interference:
            min_interference = interference
            best_rotation = angle

    return best_rotation


def find_optimal_mesh_rotation(
    wheel: Part,
    worm: Part,
    center_distance: float,
    num_teeth: int,
    backlash_tolerance_mm3: float = 1.0,
) -> MeshAnalysisResult:
    """Find optimal wheel rotation and analyze mesh quality.

    Args:
        wheel: Wheel Part centered at origin with axis along Z
        worm: Worm Part centered at origin with axis along Z
        center_distance: Distance between axes in mm
        num_teeth: Number of wheel teeth
        backlash_tolerance_mm3: Maximum acceptable interference

    Returns:
        MeshAnalysisResult with rotation and interference data
    """
    tooth_pitch = 360.0 / num_teeth

    # Position worm: rotate -90° Y (axis along X), offset by center_distance in Y
    worm_positioned = worm.rotate(Axis.Y, -90)
    worm_positioned = worm_positioned.locate(Location((0, center_distance, 0)))

    # Calculate optimal rotation
    optimal_rotation = calculate_mesh_rotation(wheel, worm_positioned, num_teeth)

    # Check interference at optimal rotation
    wheel_rotated = wheel.rotate(Axis.Z, optimal_rotation)
    try:
        intersection = wheel_rotated & worm_positioned
        interference = intersection.volume if hasattr(intersection, "volume") else 0.0
    except Exception:
        interference = 0.0

    within_tolerance = interference <= backlash_tolerance_mm3

    if interference == 0.0:
        message = "Perfect mesh - no interference"
    elif within_tolerance:
        message = f"Good mesh - {interference:.4f}mm³ interference"
    else:
        message = f"Warning - {interference:.4f}mm³ exceeds tolerance"

    return MeshAnalysisResult(
        optimal_rotation_deg=optimal_rotation,
        interference_volume_mm3=interference,
        within_tolerance=within_tolerance,
        tooth_pitch_deg=tooth_pitch,
        message=message,
    )


def create_axis_markers(center_distance: float, length: float = 10.0) -> dict[str, Part]:
    """Create axis marker cylinders for visualization.

    These show the true axis positions (important because gear bounding
    boxes shift with rotation due to asymmetric tooth positions).
    """
    wheel_axis = Cylinder(radius=0.2, height=length,
                          align=(Align.CENTER, Align.CENTER, Align.CENTER))

    worm_axis = Cylinder(radius=0.2, height=length,
                         align=(Align.CENTER, Align.CENTER, Align.CENTER))
    worm_axis = worm_axis.rotate(Axis.Y, 90)
    worm_axis = worm_axis.locate(Location((0, center_distance, 0)))

    return {"wheel_axis": wheel_axis, "worm_axis": worm_axis}
```

## Output Format

When generating gears, include mesh alignment data in the output:

```json
{
  "mesh_alignment": {
    "optimal_rotation_deg": 14.0,
    "interference_volume_mm3": 0.0,
    "within_tolerance": true,
    "tooth_pitch_deg": 27.69,
    "message": "Perfect mesh - no interference"
  }
}
```

## Visualization

When exporting STEP files or showing preview, include:

1. **Wheel** rotated by `optimal_rotation_deg` around Z axis
2. **Worm** positioned at `(0, center_distance, 0)` with axis along X
3. **Wheel axis marker** (red cylinder at origin, along Z)
4. **Worm axis marker** (blue cylinder at Y=center_distance, along X)

The axis markers are essential because gear bounding boxes appear to shift when rotated (different teeth define the box limits), but the true axes remain fixed.

## Integration Points

1. **After gear generation**: Run mesh analysis on the generated wheel and worm
2. **STEP export**: Apply optimal rotation to wheel before export, or include rotation in metadata
3. **JSON output**: Add `mesh_alignment` section to output data
4. **Visualization**: Include axis markers in preview/export

## Test Case

For a 13-tooth M0.5 wheel with 1-start worm at 5.75mm center distance:
- Expected tooth pitch: 27.69°
- Expected optimal rotation: ~14° (varies with STEP geometry)
- Expected interference: 0.0mm³ (perfect mesh)

Without rotation, typical interference is ~2mm³ (teeth collide with worm threads).
