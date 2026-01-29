#!/usr/bin/env python3
"""Regenerate worm and wheel STEP files from gear calculator JSON.

Run this when worm_gear.json parameters change.
Requires: pip install wormgear
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GEAR_JSON = PROJECT_ROOT / "config" / "worm_gear.json"
REFERENCE_DIR = PROJECT_ROOT / "reference"


def main() -> int:
    if not GEAR_JSON.exists():
        print(f"Error: {GEAR_JSON} not found")
        return 1

    REFERENCE_DIR.mkdir(exist_ok=True)

    print(f"Regenerating gears from {GEAR_JSON.name}...")
    print(f"Output directory: {REFERENCE_DIR}\n")

    # Generate both worm and wheel in one run (more efficient, also generates mesh alignment)
    result = subprocess.run(
        ["wormgear", str(GEAR_JSON), "-o", str(REFERENCE_DIR)],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Error generating gears")
        return 1

    print("\nDone. Files updated in reference/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
