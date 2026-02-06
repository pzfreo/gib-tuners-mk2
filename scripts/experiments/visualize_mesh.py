#!/usr/bin/env python3
"""Visualize wheel-worm mesh alignment with optimal rotation.

This script demonstrates the mesh rotation calculation that aligns
wheel teeth with worm thread valleys to minimize interference.

Usage:
    python scripts/visualize_mesh.py
    python scripts/visualize_mesh.py --scale 2.0
    python scripts/visualize_mesh.py --show-tuner  # Full single tuner unit
    python scripts/visualize_mesh.py --compare     # Side-by-side comparison
"""

import argparse
import sys
import warnings
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
warnings.filterwarnings("ignore", category=DeprecationWarning)

from build123d import Align, Axis, Cylinder, Location, Part, import_step

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import FrameParams, Hand
from gib_tuners.components.wheel import load_wheel, calculate_mesh_rotation
from gib_tuners.utils.validation import find_optimal_mesh_rotation, check_wheel_worm_interference


def create_axis_markers(
    center_distance: float,
    worm_length: float = 10.0,
    wheel_height: float = 10.0,
    marker_radius: float = 0.2,
) -> dict[str, Part]:
    """Create axis marker cylinders for visualization.

    These show true axis positions (gear bounding boxes shift with rotation).
    """
    wheel_axis = Cylinder(
        radius=marker_radius,
        height=wheel_height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    worm_axis = Cylinder(
        radius=marker_radius,
        height=worm_length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    worm_axis = worm_axis.rotate(Axis.Y, 90)
    worm_axis = worm_axis.locate(Location((0, center_distance, 0)))

    return {"wheel_axis": wheel_axis, "worm_axis": worm_axis}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize wheel-worm mesh alignment")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )
    parser.add_argument(
        "--show-tuner",
        action="store_true",
        help="Show full single tuner unit instead of just wheel+worm",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Show both unrotated and rotated wheel for comparison",
    )
    return parser.parse_args()


def load_step_as_part(step_path: Path) -> Part:
    """Load a STEP file and return as Part."""
    shapes = import_step(step_path)
    if isinstance(shapes, Part):
        return shapes
    elif hasattr(shapes, "wrapped"):
        return Part(shapes.wrapped)
    elif isinstance(shapes, list) and len(shapes) > 0:
        return Part(shapes[0].wrapped)
    raise ValueError(f"Could not load Part from {step_path}")


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        return 1

    # Paths to STEP files
    project_root = Path(__file__).parent.parent
    wheel_step = project_root / "reference" / "wheel_m0.5_z13.step"
    worm_step = project_root / "reference" / "worm_m0.5_z1.step"
    gear_json = project_root / "config" / "worm_gear.json"

    if not wheel_step.exists():
        print(f"Error: Wheel STEP not found at {wheel_step}")
        return 1
    if not worm_step.exists():
        print(f"Error: Worm STEP not found at {worm_step}")
        return 1

    # Create configuration
    config = create_default_config(
        scale=args.scale,
        hand=Hand.RIGHT,
        gear_json_path=gear_json if gear_json.exists() else None,
    )

    scale = config.scale
    center_distance = config.gear.center_distance * scale
    num_teeth = config.gear.wheel.num_teeth

    print("=== Wheel-Worm Mesh Alignment Visualization ===")
    print(f"Scale: {args.scale}x")
    print(f"Center distance: {center_distance:.2f}mm")
    print(f"Wheel teeth: {num_teeth}")
    print(f"Tooth pitch angle: {360.0/num_teeth:.2f} degrees")
    print()

    if args.show_tuner:
        # Show full single tuner unit with mesh rotation
        from gib_tuners.assembly.tuner_unit import create_tuner_unit
        from gib_tuners.components.frame import create_frame

        # Create single-housing config
        single_frame = replace(config.frame, num_housings=1)
        single_config = replace(config, frame=single_frame)

        print("Building single tuner unit with mesh rotation...")

        # Create tuner unit with mesh rotation
        components = create_tuner_unit(
            single_config,
            wheel_step_path=wheel_step,
            worm_step_path=worm_step,
            include_hardware=True,
        )

        # Create frame
        frame = create_frame(single_config)
        housing_y = single_config.frame.housing_centers[0] * scale

        # Position components at housing center
        for name, part in components.items():
            positioned = part.locate(Location((0, housing_y, 0)))
            color = {
                "string_post": (0, 0.8, 0),       # Green
                "wheel": (1, 0.6, 0),             # Orange
                "peg_head": (0.7, 0.7, 0.8),      # Silver/gray
                "peg_washer": (1, 1, 0),          # Yellow
                "peg_screw": (1, 0.2, 0.2),       # Red
                "wheel_washer": (1, 1, 0),        # Yellow
                "wheel_screw": (1, 0.2, 0.2),     # Red
            }.get(name, (0.5, 0.5, 0.5))
            show_object(positioned, name=name, options={"color": color})

        show_object(frame, name="Frame", options={"color": (0.3, 0.5, 1), "alpha": 0.3})

        # Add axis markers at housing position
        # Wheel axis at (0, housing_y, worm_z) - vertical
        # Worm axis at (0, housing_y + center_distance, worm_z) - horizontal
        box_outer = single_config.frame.box_outer * scale
        worm_z = -box_outer / 2
        worm_length = single_config.gear.worm.length * scale

        markers = create_axis_markers(center_distance, worm_length=worm_length, wheel_height=12.0)
        wheel_axis = markers["wheel_axis"].locate(Location((0, housing_y, worm_z)))
        worm_axis = markers["worm_axis"].locate(Location((0, housing_y, worm_z)))
        show_object(wheel_axis, name="Wheel_axis", options={"color": (1, 0, 0)})
        show_object(worm_axis, name="Worm_axis", options={"color": (0, 0, 1)})

        # Calculate and report mesh rotation
        rotation, result = find_optimal_mesh_rotation(wheel_step, worm_step, config)
        print(f"\nMesh rotation applied: {rotation:.2f} degrees")
        print(f"Interference volume: {result.interference_volume_mm3:.4f} mm^3")
        print(f"Within tolerance: {result.within_manufacturing_tolerance}")
        print(f"Message: {result.message}")

    else:
        # Show just wheel and worm for mesh visualization
        print("Loading wheel and worm STEP files...")

        wheel = load_step_as_part(wheel_step)
        worm = load_step_as_part(worm_step)

        if scale != 1.0:
            wheel = wheel.scale(scale)
            worm = worm.scale(scale)

        # Position worm: rotate -90 Y so shaft is along X, offset by center distance in Y
        worm_positioned = worm.rotate(Axis.Y, -90)
        worm_positioned = worm_positioned.locate(Location((0, center_distance, 0)))

        # Calculate optimal mesh rotation
        print("Calculating optimal mesh rotation...")
        rotation, result = find_optimal_mesh_rotation(wheel_step, worm_step, config)
        print(f"Optimal rotation: {rotation:.2f} degrees")
        print(f"Interference volume: {result.interference_volume_mm3:.4f} mm^3")
        print(f"Within backlash tolerance: {result.within_backlash_tolerance}")
        print(f"Within manufacturing tolerance: {result.within_manufacturing_tolerance}")
        print(f"Message: {result.message}")
        print()

        if args.compare:
            # Show both unrotated and rotated wheel side by side
            # Offset in X by 25mm to clearly separate the two assemblies
            print("Showing comparison: unrotated (left, red) vs rotated (right, green)")

            offset_x = 25.0  # Separation between the two assemblies

            # LEFT SIDE: Unrotated wheel + worm (showing collision)
            # Position wheel first, then locate the assembly
            wheel_unrotated = wheel.locate(Location((-offset_x / 2, 0, 0)))
            worm_left = worm.rotate(Axis.Y, -90)
            worm_left = worm_left.locate(Location((-offset_x / 2, center_distance, 0)))

            # Left axis markers
            markers_left = create_axis_markers(center_distance)
            wheel_axis_left = markers_left["wheel_axis"].locate(Location((-offset_x / 2, 0, 0)))
            worm_axis_left = markers_left["worm_axis"].locate(Location((-offset_x / 2, 0, 0)))

            show_object(wheel_unrotated, name="Wheel_unrotated", options={"color": (1, 0.3, 0.3)})
            show_object(worm_left, name="Worm_left", options={"color": (0.6, 0.6, 0.6)})
            show_object(wheel_axis_left, name="Wheel_axis_left", options={"color": (1, 0, 0)})
            show_object(worm_axis_left, name="Worm_axis_left", options={"color": (0, 0, 1)})

            # RIGHT SIDE: Rotated wheel + worm (proper mesh)
            # Rotate wheel around its axis (at origin), then position
            wheel_rotated = wheel.rotate(Axis.Z, rotation)
            wheel_rotated = wheel_rotated.locate(Location((offset_x / 2, 0, 0)))
            worm_right = worm.rotate(Axis.Y, -90)
            worm_right = worm_right.locate(Location((offset_x / 2, center_distance, 0)))

            # Right axis markers
            markers_right = create_axis_markers(center_distance)
            wheel_axis_right = markers_right["wheel_axis"].locate(Location((offset_x / 2, 0, 0)))
            worm_axis_right = markers_right["worm_axis"].locate(Location((offset_x / 2, 0, 0)))

            show_object(wheel_rotated, name="Wheel_rotated", options={"color": (0.3, 1, 0.3)})
            show_object(worm_right, name="Worm_right", options={"color": (0.7, 0.7, 0.8)})
            show_object(wheel_axis_right, name="Wheel_axis_right", options={"color": (1, 0, 0)})
            show_object(worm_axis_right, name="Worm_axis_right", options={"color": (0, 0, 1)})

            # Check interference without rotation
            result_no_rotation = check_wheel_worm_interference(
                wheel_step, worm_step, config, mesh_rotation_deg=0.0
            )
            print(f"\nInterference without rotation: {result_no_rotation.interference_volume_mm3:.4f} mm^3")
            print(f"Interference with rotation: {result.interference_volume_mm3:.4f} mm^3")

        else:
            # Show only the optimally rotated wheel with axis markers
            wheel_rotated = wheel.rotate(Axis.Z, rotation)
            show_object(wheel_rotated, name="Wheel", options={"color": (1, 0.6, 0)})
            show_object(worm_positioned, name="Worm", options={"color": (0.7, 0.7, 0.8)})

            # Add axis markers
            markers = create_axis_markers(center_distance)
            show_object(markers["wheel_axis"], name="Wheel_axis", options={"color": (1, 0, 0)})
            show_object(markers["worm_axis"], name="Worm_axis", options={"color": (0, 0, 1)})

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
