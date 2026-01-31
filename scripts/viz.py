#!/usr/bin/env python3
"""Visualize tuner assembly in OCP viewer.

Usage:
    python scripts/viz.py                      # 5-gang RH at 1x
    python scripts/viz.py -n 1                 # Single housing
    python scripts/viz.py -n 3 --hand left     # 3-gang LH
    python scripts/viz.py --scale 2.0          # 2x scale for prototyping
    python scripts/viz.py --no-interference    # Skip interference check
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import Location

from gib_tuners.config.defaults import create_default_config, resolve_gear_config
from gib_tuners.config.parameters import Hand, WormZMode
from gib_tuners.assembly.gang_assembly import (
    create_positioned_assembly,
    run_interference_report,
    COLOR_MAP,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize tuner assembly in OCP viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/viz.py                  # Default 5-gang RH
    python scripts/viz.py -n 1             # Single housing for fit testing
    python scripts/viz.py -n 3 --hand left # 3-gang left-hand
    python scripts/viz.py --scale 2.0      # 2x scale prototype
        """,
    )
    parser.add_argument(
        "-n", "--num-housings",
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help="Number of housings (default: 5)",
    )
    parser.add_argument(
        "--hand",
        choices=["right", "left", "both"],
        default="right",
        help="Hand variant (default: right). 'both' shows L & R side by side",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor (default: 1.0, use 2.0 for FDM prototypes)",
    )
    parser.add_argument(
        "--no-step",
        action="store_true",
        help="Use placeholder wheel instead of STEP file",
    )
    parser.add_argument(
        "--no-interference",
        action="store_true",
        help="Skip interference check",
    )
    parser.add_argument(
        "--gear",
        type=str,
        required=True,
        help="Gear config name (e.g., 'balanced'). Use --list-gears to see options.",
    )

    parser.add_argument(
        "--list-gears",
        action="store_true",
        help="List available gear configurations and exit",
    )
    worm_z_group = parser.add_mutually_exclusive_group()
    worm_z_group.add_argument(
        "--force-centered-worm",
        action="store_true",
        help="Force worm centered in frame (override globoid/hobbing auto-alignment)",
    )
    worm_z_group.add_argument(
        "--force-aligned-worm",
        action="store_true",
        help="Force worm aligned with wheel center (even for cylindrical worms)",
    )
    return parser.parse_args()


def main() -> int:
    # Handle --list-gears before argparse requires --gear
    if "--list-gears" in sys.argv:
        from gib_tuners.config.defaults import list_gear_configs
        configs = list_gear_configs()
        print("Available gear configs:", ", ".join(configs) if configs else "(none)")
        return 0

    args = parse_args()

    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed")
        print("Install with: pip install ocp-vscode")
        print("Then open VS Code with the OCP CAD Viewer extension.")
        return 1

    # Resolve gear config paths
    gear_paths = resolve_gear_config(args.gear)

    # Determine worm Z mode from CLI flags
    if args.force_centered_worm:
        worm_z_mode = WormZMode.CENTERED
    elif args.force_aligned_worm:
        worm_z_mode = WormZMode.ALIGNED
    else:
        worm_z_mode = None  # Will use config default

    # Wheel/worm STEP paths
    wheel_step = None
    worm_step = None
    if not args.no_step:
        wheel_step = gear_paths.wheel_step
        worm_step = gear_paths.worm_step
        if wheel_step is None:
            print("Warning: wheel STEP not found, using placeholder")

    gear_label = args.gear

    # Determine which hands to build
    if args.hand == "both":
        hands = [Hand.RIGHT, Hand.LEFT]
    else:
        hands = [Hand.RIGHT if args.hand == "right" else Hand.LEFT]

    print(f"=== {args.num_housings}-Gang Assembly ({args.hand.upper()}) @ {args.scale}x [{gear_label}] ===")

    assemblies = []
    for hand in hands:
        base_config = create_default_config(
            scale=args.scale,
            hand=hand,
            gear_json_path=gear_paths.json_path,
            config_dir=gear_paths.config_dir,
        )

        if worm_z_mode is not None:
            base_config = replace(
                base_config,
                gear=replace(base_config.gear, worm_z_mode=worm_z_mode),
            )

        config = replace(
            base_config,
            frame=replace(base_config.frame, num_housings=args.num_housings),
        )

        if hand == hands[0]:
            print(f"Frame length: {config.frame.total_length:.1f}mm")

        # Build assembly
        assembly = create_positioned_assembly(config, wheel_step, worm_step_path=worm_step)
        assemblies.append((hand, config, assembly))

    # Calculate offset for side-by-side display
    # LH on left (-X), RH on right (+X) so peg heads face outward
    frame_width = assemblies[0][1].frame.box_outer * args.scale
    spacing = frame_width * 4  # Double spacing to avoid clashing

    # Display all parts with colors
    for i, (hand, config, assembly) in enumerate(assemblies):
        hand_label = "RH" if hand == Hand.RIGHT else "LH"
        if len(assemblies) > 1:
            x_offset = spacing / 2 if hand == Hand.RIGHT else -spacing / 2
        else:
            x_offset = 0

        if i == 0:
            print(f"Housing centers: {[f'{y:.1f}' for y in assembly['housing_centers']]}")

        for name, part in assembly["all_parts"].items():
            # Offset part if showing both hands
            if x_offset != 0:
                part = part.move(Location((x_offset, 0, 0)))

            base_name = name.rsplit("_", 1)[0] if name != "frame" else "frame"
            color, alpha = COLOR_MAP.get(base_name, ((0.5, 0.5, 0.5), None))
            opts = {"color": color}
            if alpha is not None:
                opts["alpha"] = alpha

            display_name = f"{hand_label}_{name}" if len(assemblies) > 1 else name
            show_object(part, name=display_name, options=opts)

        # Interference report
        if not args.no_interference:
            print(f"\n{hand_label} Interference:")
            run_interference_report(assembly)

    print("\nVisualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
