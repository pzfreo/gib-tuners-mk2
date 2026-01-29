#!/usr/bin/env python3
"""Incremental assembly debug script.

Builds assembly components one-by-one for user verification.

Usage:
    python scripts/debug_assembly.py --step 1   # String post at origin
    python scripts/debug_assembly.py --step 2   # Post + wheel (DD alignment)
    python scripts/debug_assembly.py --step 3   # Post + wheel in single-housing frame
    python scripts/debug_assembly.py --step 4   # Add peg head
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config
from gib_tuners.config.parameters import FrameParams, Hand


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Debug assembly step by step")

    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help="Assembly step: 1=post, 2=post+wheel, 3=in frame, 4=add peg",
    )

    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Geometry scale factor (default: 1.0)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Import ocp_vscode for visualization
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed. Install with: pip install ocp-vscode")
        return 1

    from build123d import Location

    # Create configuration
    config = create_default_config(scale=args.scale, hand=Hand.RIGHT)
    scale = config.scale

    # =========================================================================
    # Step 1: String post at origin
    # =========================================================================
    if args.step >= 1:
        from gib_tuners.components.string_post import create_string_post

        post_params = config.string_post
        dd_length = post_params.dd_cut_length * scale
        bearing_h = post_params.bearing_length * scale
        post_h = post_params.post_height * scale
        cap_h = post_params.cap_height * scale

        print("=== Step 1: String post at origin ===")
        print("Post coordinate system:")
        print("  Z=0: Bottom of DD section (with M2 tap bore)")
        print("  Builds upward in +Z")
        print()

        print("Post sections (from bottom to top):")
        z = 0.0
        print(f"  DD section:     Z={z:.1f} to Z={z + dd_length:.1f}  <- wheel sits here, M2 tap bore from bottom")
        z += dd_length
        print(f"  Bearing:        Z={z:.1f} to Z={z + bearing_h:.1f}  <- sits in frame hole")
        z += bearing_h
        print(f"  Visible post:   Z={z:.1f} to Z={z + post_h:.1f}")
        z += post_h
        print(f"  Cap:            Z={z:.1f} to Z={z + cap_h:.1f}")

        post = create_string_post(config)
        show_object(post, name="string_post", options={"color": "silver"})

        if args.step == 1:
            print("\nVisualization sent to OCP viewer")
            print("Please verify the post geometry and approve before proceeding to step 2.")
            return 0

    # =========================================================================
    # Step 2: Add wheel to post (verify DD alignment)
    # =========================================================================
    if args.step >= 2:
        print("\n=== Step 2: Post + Wheel (DD alignment) ===")
        print("TODO: Implement after Step 1 is approved")
        return 0

    # =========================================================================
    # Step 3: Position in single-housing frame
    # =========================================================================
    if args.step >= 3:
        print("\n=== Step 3: Post + Wheel in frame ===")
        print("TODO: Implement after Step 2 is approved")
        return 0

    # =========================================================================
    # Step 4: Add peg head
    # =========================================================================
    if args.step >= 4:
        print("\n=== Step 4: Add peg head ===")
        print("TODO: Implement after Step 3 is approved")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
