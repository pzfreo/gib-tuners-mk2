"""Peg head assembly geometry.

The peg head is constructed by combining:
1. Reference peg head STEP (ring, pip, cap, shoulder) - cut at Z=0
2. Reference worm STEP positioned at Z=0 (butted against shoulder)
3. Bearing shaft beyond the worm
4. M2 tap hole at shaft end

Structure (from peg head toward bearing end):
- Head: decorative ring with finger grip (from STEP)
- Cap: sits outside frame, prevents push-in (from STEP)
- Shoulder: fits inside worm entry hole (from STEP)
- Worm: threaded section (from worm STEP, length from gear config)
- Bearing shaft: generated beyond worm end (4.0mm diameter)
- M2 tap hole: 4mm deep from shaft end (extends into worm)

"""

from pathlib import Path
from typing import Optional

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
from ..utils.validation import check_shape_quality


def _to_part(shape) -> Part:
    """Ensure shape is a Part."""
    if isinstance(shape, Part):
        return shape
    elif hasattr(shape, 'wrapped'):
        return Part(shape.wrapped)
    return shape

# Reference STEP file locations
REFERENCE_DIR = Path(__file__).parent.parent.parent.parent / "reference"
PEG_HEAD_STEP = REFERENCE_DIR / "peghead7mm.step"

# Default worm STEP (used if not provided via config)
DEFAULT_WORM_STEP = REFERENCE_DIR / "worm_m0.5_z1.step"
DEFAULT_WORM_LENGTH = 7.8


def create_peg_head(
    config: BuildConfig,
    include_worm: bool = True,
    worm_step_path: Optional[Path] = None,
    worm_length: Optional[float] = None,
) -> Part:
    """Create the peg head assembly geometry.

    Combines peg head STEP, new shaft, and worm STEP.

    The peg head is oriented with:
    - Shaft axis along Z (before rotation for assembly)
    - Peg head at Z ≤ 0, shaft/worm at Z > 0

    For assembly, rotate -90° around Y to align shaft with X axis.

    Args:
        config: Build configuration
        include_worm: If True, includes worm thread geometry
        worm_step_path: Path to worm STEP file (uses default if None)
        worm_length: Worm length in mm (uses config.peg_head.worm_length if None)

    Returns:
        Peg head Part

    Raises:
        FileNotFoundError: If reference STEP files are not found
    """
    if not PEG_HEAD_STEP.exists():
        raise FileNotFoundError(
            f"Peg head STEP not found: {PEG_HEAD_STEP}\n"
            "Please ensure peghead7mm.step is in the reference/ directory."
        )

    params = config.peg_head
    scale = config.scale

    # Use provided worm path/length or fall back to defaults
    worm_step = worm_step_path if worm_step_path is not None else DEFAULT_WORM_STEP
    worm_len = worm_length if worm_length is not None else params.worm_length

    # Import peg head and cut at Z=0 (keep Z ≤ 0)
    peg_head_imported = import_step(PEG_HEAD_STEP)
    # import_step returns ShapeList; fuse into single Part if multiple shapes
    if hasattr(peg_head_imported, '__iter__') and not isinstance(peg_head_imported, Part):
        peg_head_full = peg_head_imported[0]
        for shape in peg_head_imported[1:]:
            peg_head_full = peg_head_full + shape
    else:
        peg_head_full = peg_head_imported

    # Cut peg head at Z=0 (keep Z ≤ 0)
    keep_box = Box(20, 20, 30, align=(Align.CENTER, Align.CENTER, Align.MAX))
    keep_box = keep_box.locate(Location((0, 0, 0)))
    peg_head = _to_part(peg_head_full & keep_box)

    # Get shaft dimensions from params
    shaft_dia = params.shaft_diameter
    wall_thickness = config.frame.wall_thickness
    bearing_wall = params.get_bearing_wall(wall_thickness)

    # Total length from Z=0 to shaft end (for tap hole positioning)
    total_shaft_length = worm_len + bearing_wall

    # Add worm if requested and STEP exists
    if include_worm and worm_step.exists():
        # Import worm
        worm_imported = import_step(worm_step)
        if hasattr(worm_imported, '__iter__') and not isinstance(worm_imported, Part):
            worm = _to_part(worm_imported[0])
        else:
            worm = _to_part(worm_imported)
        # Worm STEP is centered at origin, shift so bottom is at Z=0
        worm_half = worm_len / 2
        worm_positioned = worm.locate(Location((0, 0, worm_half)))

        # Create bearing shaft starting at worm end
        bearing_shaft = Cylinder(
            radius=shaft_dia / 2,
            height=bearing_wall,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        bearing_shaft = bearing_shaft.locate(Location((0, 0, worm_len)))

        # Fuse all parts using regular union
        result = peg_head + worm_positioned + bearing_shaft
    else:
        # No worm: create full shaft from Z=0 to end
        full_shaft = Cylinder(
            radius=shaft_dia / 2,
            height=total_shaft_length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        full_shaft = full_shaft.locate(Location((0, 0, 0)))
        result = peg_head + full_shaft

    # Add M2 tap hole at shaft end
    tap_hole = Cylinder(
        radius=params.tap_drill / 2,
        height=params.tap_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    tap_hole = tap_hole.locate(Location((0, 0, total_shaft_length)))
    result = result - tap_hole

    # Rotate for assembly orientation (pip at +X, shaft at -X)
    # -90° around Y: +Z → -X, -Z → +X
    # So: peg head (Z<0) → +X (outside), shaft (Z>0) → -X (through frame)
    result = result.rotate(Axis.Y, -90)

    # Apply scale if needed
    if scale != 1.0:
        result = result.scale(scale)

    # Check shape quality (warns if non-manifold edges detected)
    check_shape_quality(result, "peg_head")

    return result


def create_peg_head_simplified(
    config: BuildConfig,
    worm_step_path: Optional[Path] = None,
    worm_length: Optional[float] = None,
) -> Part:
    """Create peg head without worm detail for quick visualization.

    Args:
        config: Build configuration
        worm_step_path: Path to worm STEP file (uses default if None)
        worm_length: Worm length in mm (uses config.peg_head.worm_length if None)

    Returns:
        Simplified peg head Part
    """
    return create_peg_head(
        config,
        include_worm=False,
        worm_step_path=worm_step_path,
        worm_length=worm_length,
    )
