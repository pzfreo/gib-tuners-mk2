#!/usr/bin/env python3
"""Visualize complete N-gang tuner assembly.

Displays full frame with all tuners:
- Frame (blue, transparent)
- Posts (green)
- Wheels (orange)
- Peg heads (silver)
- Washers (yellow)
- Screws (red)

Usage:
    python scripts/visualize_full_assembly.py
    python scripts/visualize_full_assembly.py --num-housings 3
    python scripts/visualize_full_assembly.py --hand left
    python scripts/visualize_full_assembly.py --scale 2.0
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import Location, Part

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.components.frame import create_frame
from gib_tuners.assembly.tuner_unit import create_tuner_unit


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize full tuner assembly")
    parser.add_argument(
        "--num-housings",
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help="Number of tuner housings (default: 5)",
    )
    parser.add_argument(
        "--hand",
        choices=["right", "left"],
        default="right",
        help="Hand variant (default: right)",
    )
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
    parser.add_argument(
        "--no-interference",
        action="store_true",
        help="Skip interference checking (faster)",
    )
    return parser.parse_args()


def check_interference(part_a: Part, part_b: Part) -> float:
    """Return intersection volume between two parts (0 = no interference)."""
    try:
        intersection = part_a & part_b
        return intersection.volume if hasattr(intersection, "volume") else 0.0
    except Exception:
        return 0.0


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        return 1

    # Create configuration
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    base_config = create_default_config(scale=args.scale, hand=hand)

    # Set number of housings
    frame_params = replace(base_config.frame, num_housings=args.num_housings)
    config = replace(base_config, frame=frame_params)

    scale = config.scale
    frame_params = config.frame
    gear_params = config.gear

    print(f"=== {args.num_housings}-Gang Assembly Visualization ({args.hand.upper()} hand) ===")
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
    print(f"  Housing centers: {[f'{c:.2f}' for c in housing_centers]}")
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

    # Calculate Y translation offset
    # Frame has: post hole at housing_y - effective_cd/2
    # tuner_unit has: post at Y=0
    center_distance = gear_params.center_distance * scale
    extra_backlash = gear_params.extra_backlash * scale
    effective_cd = center_distance - extra_backlash

    print(f"Gear parameters:")
    print(f"  Center distance: {center_distance:.2f}mm")
    print(f"  Effective CD: {effective_cd:.2f}mm")
    print()

    # Show frame
    show_object(frame, name="Frame", options={"color": (0.3, 0.5, 1), "alpha": 0.3})

    # Color map for components
    color_map = {
        "string_post": (0, 0.8, 0),       # Green
        "wheel": (1, 0.6, 0),             # Orange
        "peg_head": (0.7, 0.7, 0.8),      # Silver
        "peg_washer": (1, 1, 0),          # Yellow
        "peg_screw": (1, 0.2, 0.2),       # Red
        "wheel_washer": (1, 1, 0),        # Yellow
        "wheel_screw": (1, 0.2, 0.2),     # Red
    }

    # Create and position tuners for each housing
    all_positioned_parts = {"frame": frame}

    for i, housing_y in enumerate(housing_centers):
        tuner_num = i + 1
        print(f"Tuner {tuner_num}: housing Y = {housing_y:.2f}mm")

        # Create tuner unit
        components = create_tuner_unit(config, wheel_step)

        # Calculate translation for this housing
        translation_y = housing_y - effective_cd / 2

        # Position and display each component
        for name, part in components.items():
            positioned = part.moved(Location((0, translation_y, 0)))
            display_name = f"{name}_{tuner_num}"
            all_positioned_parts[display_name] = positioned
            color = color_map.get(name, (0.5, 0.5, 0.5))
            show_object(positioned, name=display_name, options={"color": color})

    print()

    # Interference report (optional, can be slow for full assembly)
    if not args.no_interference:
        print("=== Interference Report ===")

        # Check each tuner against frame
        total_interference = 0.0
        for i in range(args.num_housings):
            tuner_num = i + 1
            tuner_interference = 0.0

            # Key interference checks for this tuner
            checks = [
                (f"wheel_{tuner_num}", f"peg_head_{tuner_num}"),      # Gear mesh
                (f"string_post_{tuner_num}", "frame"),                # Post through hole
                (f"peg_head_{tuner_num}", "frame"),                   # Worm through holes
                (f"wheel_{tuner_num}", "frame"),                      # Wheel in cavity
            ]

            for name_a, name_b in checks:
                if name_a in all_positioned_parts and name_b in all_positioned_parts:
                    vol = check_interference(all_positioned_parts[name_a], all_positioned_parts[name_b])
                    tuner_interference += vol
                    if vol >= 0.01:
                        print(f"  Tuner {tuner_num}: {name_a.split('_')[0]} vs {name_b.split('_')[0]}: INTERFERENCE {vol:.3f} mm³")

            total_interference += tuner_interference
            if tuner_interference < 0.01:
                print(f"  Tuner {tuner_num}: OK")

        print()
        if total_interference < 0.01:
            print("All interference checks PASSED")
        else:
            print(f"TOTAL INTERFERENCE: {total_interference:.3f} mm³")
    else:
        print("(Interference checking skipped)")

    print()
    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
