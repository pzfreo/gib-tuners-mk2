#!/usr/bin/env python3
"""Peg head with worm - exact dimensions per user spec."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build123d import import_step, Box, Align, Location, Cylinder

PEG_STEP = Path(__file__).parent.parent / "reference" / "peghead-and-shaft.step"
WORM_STEP = Path(__file__).parent.parent / "reference" / "worm_m0.5_z1.step"

# Worm: 7.8mm (0.1mm clearance each side in 8mm cavity)
WORM_LENGTH = 7.0      # Current worm STEP length
TARGET_WORM = 7.8      # Desired length (regenerate STEP file)

# Shaft extends beyond worm:
# - 0.2mm to meet frame cavity end
# - 1.0mm through bearing wall
# - 0.1mm beyond frame for washer clearance
SHAFT_BEYOND_WORM = 0.2 + 1.0 + 0.1  # = 1.3mm

# Shaft
SHAFT_DIA = 3.5        # Fits worm root (3.75mm)

# M2 tap
TAP_DRILL = 1.6
TAP_DEPTH = 4.0


def main() -> int:
    try:
        from ocp_vscode import show_object
    except ImportError:
        print("Error: ocp-vscode not installed")
        return 1

    peg = import_step(PEG_STEP)
    worm = import_step(WORM_STEP)

    # Keep Z <= 0 (peg head, cap, shoulder)
    keep_box = Box(20, 20, 30, align=(Align.CENTER, Align.CENTER, Align.MAX))
    keep_box = keep_box.locate(Location((0, 0, 0)))
    peg_head = peg & keep_box

    # Shaft length = worm + extension
    shaft_length = TARGET_WORM + SHAFT_BEYOND_WORM  # 7.8 + 1.3 = 9.1mm

    print(f"Worm: {TARGET_WORM}mm (current STEP is {WORM_LENGTH}mm), Z = 0 to {TARGET_WORM}")
    print(f"Shaft beyond worm: {SHAFT_BEYOND_WORM}mm (0.2 gap + 1.0 wall + 0.1 clearance)")
    print(f"Total shaft: {SHAFT_DIA}mm dia, Z = 0 to {shaft_length}")

    new_shaft = Cylinder(
        radius=SHAFT_DIA / 2,
        height=shaft_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    new_shaft = new_shaft.locate(Location((0, 0, 0)))

    # Worm at Z=0 (using current 7mm STEP for visualization)
    worm_half = WORM_LENGTH / 2
    worm_positioned = worm.locate(Location((0, 0, worm_half)))

    print(f"(Visualization uses {WORM_LENGTH}mm worm, regenerate at {TARGET_WORM}mm)")

    # M2 tap hole at end
    tap_hole = Cylinder(
        radius=TAP_DRILL / 2,
        height=TAP_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    tap_hole = tap_hole.locate(Location((0, 0, shaft_length)))
    print(f"M2 tap: {TAP_DRILL}mm dia, {TAP_DEPTH}mm deep at Z={shaft_length}")

    # Combine
    combined = peg_head + new_shaft + worm_positioned - tap_hole

    bb = combined.bounding_box()
    print(f"\nCombined: Z = {bb.min.Z:.1f} to {bb.max.Z:.1f}")

    show_object(combined, name="Peg_with_worm", options={"color": (0.8, 0.6, 0.2)})

    # Show original offset
    show_object(peg.locate(Location((20, 0, 0))), name="Original",
                options={"color": (0.5, 0.5, 0.5), "alpha": 0.5})

    return 0


if __name__ == "__main__":
    sys.exit(main())
