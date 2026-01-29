#!/usr/bin/env python3
"""Regenerate worm and wheel STEP files from gear calculator JSON.

Run this when 7.5mm-cyl.json parameters change.
Requires: pip install wormgear
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GEAR_JSON = PROJECT_ROOT / "7.5mm-cyl.json"
REFERENCE_DIR = PROJECT_ROOT / "reference"


def main() -> int:
    if not GEAR_JSON.exists():
        print(f"Error: {GEAR_JSON} not found")
        return 1

    REFERENCE_DIR.mkdir(exist_ok=True)

    print(f"Regenerating gears from {GEAR_JSON.name}...\n")

    # Generate worm
    print("=== Worm ===")
    result = subprocess.run(
        ["wormgear", str(GEAR_JSON), "--worm-only", "-o", str(REFERENCE_DIR)],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error generating worm")
        return 1

    # Generate wheel
    print("\n=== Wheel ===")
    result = subprocess.run(
        ["wormgear", str(GEAR_JSON), "--wheel-only", "-o", str(REFERENCE_DIR)],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error generating wheel")
        return 1

    print("\nDone. STEP files updated in reference/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
