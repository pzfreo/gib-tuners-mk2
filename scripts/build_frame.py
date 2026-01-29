#!/usr/bin/env python3
"""Build just the frame for quick iteration.

Usage:
    python scripts/build_frame.py
    python scripts/build_frame.py --scale 2.0 --hand left
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.config.tolerances import TOLERANCE_PROFILES
from gib_tuners.components.frame import create_frame
from gib_tuners.export.step_export import export_step
from gib_tuners.utils.mirror import create_left_hand_config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Build frame only")

    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )

    parser.add_argument(
        "--tolerance",
        choices=list(TOLERANCE_PROFILES.keys()),
        default="production",
        help="Tolerance profile (default: production)",
    )

    parser.add_argument(
        "--hand",
        choices=["right", "left"],
        default="right",
        help="Which hand variant (default: right)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: output/{hand}/frame.step)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Create configuration
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    config = create_default_config(
        scale=args.scale,
        tolerance=args.tolerance,
        hand=hand,
    )

    if hand == Hand.LEFT:
        config = create_left_hand_config(config)

    print(f"Building {args.hand.upper()} frame at scale {args.scale}x...")

    frame = create_frame(config)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = Path("output") / args.hand / "frame.step"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Exporting to {output_path}...")
    export_step(frame, output_path)

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
