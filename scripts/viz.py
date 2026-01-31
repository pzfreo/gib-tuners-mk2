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
        choices=["right", "left"],
        default="right",
        help="Hand variant (default: right)",
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
        default=None,
        help="Gear config name (e.g., 'balanced'). Looks in config/<name>/",
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

    # Config
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    base_config = create_default_config(
        scale=args.scale,
        hand=hand,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )

    # Determine worm Z mode from CLI flags
    if args.force_centered_worm:
        worm_z_mode = WormZMode.CENTERED
    elif args.force_aligned_worm:
        worm_z_mode = WormZMode.ALIGNED
    else:
        worm_z_mode = base_config.gear.worm_z_mode  # AUTO (from JSON hints)

    config = replace(
        base_config,
        frame=replace(base_config.frame, num_housings=args.num_housings),
        gear=replace(base_config.gear, worm_z_mode=worm_z_mode),
    )

    # Wheel STEP path (from gear config)
    wheel_step = None
    worm_step = None
    if not args.no_step:
        wheel_step = gear_paths.wheel_step
        worm_step = gear_paths.worm_step
        if wheel_step is None:
            print("Warning: wheel STEP not found, using placeholder")

    gear_label = args.gear or "default"
    print(f"=== {args.num_housings}-Gang Assembly ({args.hand.upper()}) @ {args.scale}x [{gear_label}] ===")
    print(f"Frame length: {config.frame.total_length:.1f}mm")

    # Build assembly
    assembly = create_positioned_assembly(config, wheel_step, worm_step_path=worm_step)

    print(f"Housing centers: {[f'{y:.1f}' for y in assembly['housing_centers']]}")

    # Display all parts with colors
    for name, part in assembly["all_parts"].items():
        base_name = name.rsplit("_", 1)[0] if name != "frame" else "frame"
        color, alpha = COLOR_MAP.get(base_name, ((0.5, 0.5, 0.5), None))
        opts = {"color": color}
        if alpha is not None:
            opts["alpha"] = alpha
        show_object(part, name=name, options=opts)

    # Interference report
    if not args.no_interference:
        print()
        run_interference_report(assembly)

    print("\nVisualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
