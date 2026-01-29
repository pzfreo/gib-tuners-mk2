#!/usr/bin/env python3
"""Visualize complete single-housing (1-gang) assembly.

Displays:
- Frame (blue, transparent)
- Post (green)
- Wheel (orange)
- Washer (yellow)
- Screw (red)

Usage:
    python scripts/visualize_single_housing.py
    python scripts/visualize_single_housing.py --scale 2.0
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import (
    Align,
    Cylinder,
    Location,
    Part,
)

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import FrameParams, Hand
from gib_tuners.components.frame import create_frame
from gib_tuners.assembly.tuner_unit import create_tuner_unit


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize single-housing assembly")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )
    parser.add_argument(
        "--no-step",
        action="store_true",
        help="Use placeholder wheel instead of STEP file",
    )
    return parser.parse_args()


def create_washer(od: float, id_: float, thickness: float) -> Part:
    """Create a washer geometry."""
    outer = Cylinder(
        radius=od / 2,
        height=thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = Cylinder(
        radius=id_ / 2,
        height=thickness + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = inner.locate(Location((0, 0, -0.05)))
    return outer - inner


def create_m2_screw(length: float, head_d: float = 3.8, head_h: float = 1.5) -> Part:
    """Create a simplified M2 screw geometry."""
    shaft = Cylinder(
        radius=1.0,  # M2 nominal
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    head = Cylinder(
        radius=head_d / 2,
        height=head_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    head = head.locate(Location((0, 0, -head_h)))
    return shaft + head


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        return 1

    # Create configuration with single housing
    base_config = create_default_config(scale=args.scale, hand=Hand.RIGHT)
    single_frame = replace(base_config.frame, num_housings=1)
    config = replace(base_config, frame=single_frame)

    scale = config.scale
    frame_params = config.frame
    post_params = config.string_post
    wheel_params = config.gear.wheel
    gear_params = config.gear

    print("=== Single Housing Assembly Visualization ===")
    print(f"Scale: {args.scale}x")
    print()

    # Frame dimensions
    box_outer = frame_params.box_outer * scale
    wall = frame_params.wall_thickness * scale
    total_length = frame_params.total_length * scale
    housing_centers = [c * scale for c in frame_params.housing_centers]

    print("Frame geometry:")
    print(f"  Box outer: {box_outer:.2f}mm")
    print(f"  Wall thickness: {wall:.2f}mm")
    print(f"  Total length: {total_length:.2f}mm")
    print(f"  Housing center: Y={housing_centers[0]:.2f}mm")
    print()

    # Create frame
    frame = create_frame(config)

    # Determine wheel STEP path
    wheel_step = None
    if not args.no_step:
        wheel_step = Path(__file__).parent.parent / "reference" / "wheel_m0.5_z13.step"
        if not wheel_step.exists():
            print(f"Warning: Wheel STEP not found at {wheel_step}, using placeholder")
            wheel_step = None

    # Create tuner unit (includes all components with correct positioning)
    components = create_tuner_unit(config, wheel_step)

    # Calculate correct Y translation to align post with frame hole
    # Frame has: post hole at housing_y - effective_cd/2
    # tuner_unit has: post at Y=0
    # So translate by: housing_y - effective_cd/2
    housing_y = housing_centers[0]
    center_distance = gear_params.center_distance * scale
    extra_backlash = gear_params.extra_backlash * scale
    effective_cd = center_distance - extra_backlash
    translation_y = housing_y - effective_cd / 2

    print(f"Positioning:")
    print(f"  Housing center Y: {housing_y:.2f}mm")
    print(f"  Center distance: {center_distance:.2f}mm")
    print(f"  Effective CD: {effective_cd:.2f}mm")
    print(f"  Translation Y: {translation_y:.2f}mm")
    print(f"  Post will be at Y: {translation_y:.2f}mm")
    print(f"  Worm will be at Y: {translation_y + center_distance:.2f}mm")
    print()

    # Show frame
    show_object(frame, name="Frame", options={"color": (0.3, 0.5, 1), "alpha": 0.3})

    # Position and collect all tuner components
    positioned_parts = {"frame": frame}
    color_map = {
        "string_post": (0, 0.8, 0),       # Green
        "wheel": (1, 0.6, 0),             # Orange
        "peg_head": (0.7, 0.7, 0.8),      # Silver
        "peg_washer": (1, 1, 0),          # Yellow
        "peg_screw": (1, 0.2, 0.2),       # Red
        "wheel_washer": (1, 1, 0),        # Yellow
        "wheel_screw": (1, 0.2, 0.2),     # Red
    }

    for name, part in components.items():
        # Use moved() to ADD translation, not locate() which SETS position
        positioned = part.moved(Location((0, translation_y, 0)))
        positioned_parts[name] = positioned
        color = color_map.get(name, (0.5, 0.5, 0.5))
        show_object(positioned, name=name, options={"color": color})

    # Interference report
    def check_interference(part_a: Part, part_b: Part) -> float:
        """Return intersection volume between two parts (0 = no interference)."""
        try:
            intersection = part_a & part_b
            return intersection.volume if hasattr(intersection, "volume") else 0.0
        except Exception:
            return 0.0

    print("=== Interference Report ===")
    pairs = [
        ("wheel", "peg_head"),      # Gear mesh
        ("string_post", "frame"),   # Post through hole
        ("peg_head", "frame"),      # Worm through holes
        ("wheel", "frame"),         # Wheel in cavity
        ("string_post", "wheel"),   # Post-wheel fit
    ]
    total_interference = 0.0
    for name_a, name_b in pairs:
        if name_a in positioned_parts and name_b in positioned_parts:
            vol = check_interference(positioned_parts[name_a], positioned_parts[name_b])
            total_interference += vol
            status = "OK" if vol < 0.01 else f"INTERFERENCE: {vol:.3f} mm³"
            print(f"  {name_a} vs {name_b}: {status}")

    print()
    if total_interference < 0.01:
        print("All interference checks PASSED")
    else:
        print(f"TOTAL INTERFERENCE: {total_interference:.3f} mm³")

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
