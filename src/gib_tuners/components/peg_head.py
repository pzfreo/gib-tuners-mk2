"""Peg head assembly geometry.

The peg head is constructed by combining:
1. Reference peg head STEP (ring, pip, cap, shoulder) - cut at Z=0
2. New shaft sized to fit inside worm root
3. Reference worm STEP positioned at Z=0 (butted against shoulder)
4. M2 tap hole at shaft end

Structure (from peg head toward bearing end):
- Peg head (Z ≤ 0): ring, pip, join, cap, shoulder from STEP
- Worm (Z = 0 to 7.8): butted against shoulder, 0.1mm clearance each side
- Shaft gap (Z = 7.8 to 8.0): to frame cavity end
- Bearing shaft (Z = 8.0 to 9.0): through bearing wall
- Extension (Z = 9.0 to 9.1): beyond frame for washer clearance
- M2 tap hole at Z = 9.1

Total shaft: 9.1mm from shoulder to end
"""

from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Part,
    import_step,
)

from ..config.parameters import BuildConfig

# Reference STEP file locations
REFERENCE_DIR = Path(__file__).parent.parent.parent.parent / "reference"
PEG_HEAD_STEP = REFERENCE_DIR / "peghead-and-shaft.step"
WORM_STEP = REFERENCE_DIR / "worm_m0.5_z1.step"

# Current worm STEP length (until regenerated at target length)
WORM_STEP_LENGTH = 7.0


def create_peg_head(config: BuildConfig, include_worm: bool = True) -> Part:
    """Create the peg head assembly geometry.

    Combines peg head STEP, new shaft, and worm STEP.

    The peg head is oriented with:
    - Shaft axis along Z (before rotation for assembly)
    - Peg head at Z ≤ 0, shaft/worm at Z > 0

    For assembly, rotate -90° around Y to align shaft with X axis.

    Args:
        config: Build configuration
        include_worm: If True, includes worm thread geometry

    Returns:
        Peg head Part

    Raises:
        FileNotFoundError: If reference STEP files are not found
    """
    if not PEG_HEAD_STEP.exists():
        raise FileNotFoundError(
            f"Peg head STEP not found: {PEG_HEAD_STEP}\n"
            "Please ensure peghead-and-shaft.step is in the reference/ directory."
        )

    params = config.peg_head
    scale = config.scale

    # Import peg head and cut at Z=0 (keep Z ≤ 0)
    peg_head_full = import_step(PEG_HEAD_STEP)

    keep_box = Box(20, 20, 30, align=(Align.CENTER, Align.CENTER, Align.MAX))
    keep_box = keep_box.locate(Location((0, 0, 0)))
    peg_head = peg_head_full & keep_box

    # Get shaft dimensions from params
    shaft_dia = params.shaft_diameter
    shaft_length = params.shaft_length  # Computed property: 9.1mm

    # Create new shaft
    new_shaft = Cylinder(
        radius=shaft_dia / 2,
        height=shaft_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    new_shaft = new_shaft.locate(Location((0, 0, 0)))  # Bottom at Z=0

    # Combine peg head and shaft
    result = peg_head + new_shaft

    # Add worm if requested and STEP exists
    if include_worm and WORM_STEP.exists():
        worm = import_step(WORM_STEP)
        # Worm STEP is centered at origin, shift so bottom is at Z=0
        worm_half = WORM_STEP_LENGTH / 2
        worm_positioned = worm.locate(Location((0, 0, worm_half)))
        result = result + worm_positioned

    # Add M2 tap hole at shaft end
    tap_hole = Cylinder(
        radius=params.tap_drill / 2,
        height=params.tap_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    tap_hole = tap_hole.locate(Location((0, 0, shaft_length)))
    result = result - tap_hole

    # Rotate for assembly orientation (shaft along X, pip at -X)
    result = result.rotate(Axis.Y, -90)

    # Apply scale if needed
    if scale != 1.0:
        result = result.scale(scale)

    return result


def create_peg_head_simplified(config: BuildConfig) -> Part:
    """Create peg head without worm detail for quick visualization.

    Args:
        config: Build configuration

    Returns:
        Simplified peg head Part
    """
    return create_peg_head(config, include_worm=False)
