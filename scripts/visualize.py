#!/usr/bin/env python3
"""Visualize the tuner assembly in OCP viewer.

Usage:
    python scripts/visualize.py
    python scripts/visualize.py --component frame
    python scripts/visualize.py --scale 2.0
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import Hand
from gib_tuners.config.tolerances import TOLERANCE_PROFILES


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visualize tuner assembly")

    parser.add_argument(
        "--component",
        choices=["frame", "peg_head", "string_post", "wheel", "tuner", "assembly"],
        default="assembly",
        help="Component to visualize (default: assembly)",
    )

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
        "--gear-json",
        type=Path,
        default=Path("7mm-globoid.json"),
        help="Path to gear parameters JSON",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show, show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        print("Then open VS Code with the OCP CAD Viewer extension.")
        return 1

    # Determine gear JSON path
    gear_json_path = args.gear_json if args.gear_json.exists() else None

    # Create configuration
    hand = Hand.RIGHT if args.hand == "right" else Hand.LEFT
    config = create_default_config(
        scale=args.scale,
        tolerance=args.tolerance,
        hand=hand,
        gear_json_path=gear_json_path,
    )

    if hand == Hand.LEFT:
        from gib_tuners.utils.mirror import create_left_hand_config
        config = create_left_hand_config(config)

    print(f"Building {args.component} at scale {args.scale}x...")

    # STEP file path for wheel geometry
    project_root = Path(__file__).parent.parent
    wheel_step = project_root / "reference" / "wheel_m0.5_z13.step"

    # Build requested component
    if args.component == "frame":
        from gib_tuners.components.frame import create_frame
        shape = create_frame(config)
        show_object(shape, name="frame")

    elif args.component == "peg_head":
        from gib_tuners.components.peg_head import create_peg_head
        shape = create_peg_head(config)
        show_object(shape, name="peg_head")

    elif args.component == "string_post":
        from gib_tuners.components.string_post import create_string_post
        shape = create_string_post(config)
        show_object(shape, name="string_post")

    elif args.component == "wheel":
        from gib_tuners.components.wheel import create_wheel_placeholder
        shape = create_wheel_placeholder(config)
        show_object(shape, name="wheel")

    elif args.component == "tuner":
        from gib_tuners.assembly.tuner_unit import create_tuner_unit
        components = create_tuner_unit(config, wheel_step)
        for name, part in components.items():
            show_object(part, name=name)

    elif args.component == "assembly":
        from gib_tuners.assembly.gang_assembly import create_gang_assembly
        assembly = create_gang_assembly(config, wheel_step)
        show_object(assembly["frame"], name="frame")
        for i, tuner_dict in enumerate(assembly["tuners"]):
            for name, part in tuner_dict.items():
                show_object(part, name=name)

    print("Visualization sent to OCP viewer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
