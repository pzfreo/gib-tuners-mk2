#!/usr/bin/env python3
"""Visualize complete N-gang tuner assembly.

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

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.assembly.gang_assembly import (
    create_positioned_assembly,
    run_interference_report,
    COLOR_MAP,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize full tuner assembly")
    parser.add_argument("-n", "--num-housings", type=int, default=5, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--hand", choices=["right", "left"], default="right")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--no-step", action="store_true", help="Use placeholder wheel")
    parser.add_argument("--no-interference", action="store_true", help="Skip interference check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed")
        return 1

    # Config
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    base_config = create_default_config(scale=args.scale, hand=hand)
    config = replace(base_config, frame=replace(base_config.frame, num_housings=args.num_housings))

    # Wheel STEP path
    wheel_step = None
    if not args.no_step:
        wheel_step = Path(__file__).parent.parent / "reference" / "wheel_m0.5_z13.step"
        if not wheel_step.exists():
            wheel_step = None

    print(f"=== {args.num_housings}-Gang Assembly ({args.hand.upper()}) @ {args.scale}x ===")
    print(f"Frame length: {config.frame.total_length:.1f}mm")

    # Build assembly
    assembly = create_positioned_assembly(config, wheel_step)

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
