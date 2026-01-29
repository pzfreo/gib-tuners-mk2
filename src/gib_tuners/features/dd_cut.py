"""Double-D (DD) cut operations for anti-rotation interfaces.

DD cuts create two parallel flats on a round shaft or bore to prevent rotation.
Used for the wheel-to-post interface.
"""

from build123d import (
    Align,
    Box,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import DDCutParams


def create_dd_cut_bore(
    params: DDCutParams,
    length: float,
    scale: float = 1.0,
) -> Part:
    """Create a DD cut bore (negative space for boolean subtraction).

    The bore is centered at the origin, extending along the Z axis.

    Args:
        params: DD cut parameters (diameter, flat_depth, across_flats)
        length: Length of the bore
        scale: Scale factor to apply

    Returns:
        Part representing the DD bore volume (for subtraction)
    """
    d = params.diameter * scale
    across_flats = params.across_flats * scale
    h = length * scale

    # Start with a cylinder
    bore = Cylinder(radius=d / 2, height=h, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Create boxes to cut the flats
    flat_height = h

    # Cut flat on +X side
    flat_box = Box(d, d, flat_height, align=(Align.MIN, Align.CENTER, Align.MIN))
    flat_box = flat_box.locate(Location((across_flats / 2, 0, 0)))
    bore = bore - flat_box

    # Cut flat on -X side
    flat_box2 = Box(d, d, flat_height, align=(Align.MAX, Align.CENTER, Align.MIN))
    flat_box2 = flat_box2.locate(Location((-across_flats / 2, 0, 0)))
    bore = bore - flat_box2

    return bore


def create_dd_cut_shaft(
    params: DDCutParams,
    length: float,
    scale: float = 1.0,
) -> Part:
    """Create a DD cut shaft section (positive geometry).

    The shaft is centered at the origin, extending along the Z axis.

    Args:
        params: DD cut parameters (diameter, flat_depth, across_flats)
        length: Length of the DD section
        scale: Scale factor to apply

    Returns:
        Part representing the DD shaft section
    """
    d = params.diameter * scale
    across_flats = params.across_flats * scale
    h = length * scale

    # Start with a cylinder
    shaft = Cylinder(radius=d / 2, height=h, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Create boxes to cut the flats (same as bore, just on a shaft)
    flat_box = Box(d, d, h, align=(Align.MIN, Align.CENTER, Align.MIN))
    flat_box = flat_box.locate(Location((across_flats / 2, 0, 0)))
    shaft = shaft - flat_box

    flat_box2 = Box(d, d, h, align=(Align.MAX, Align.CENTER, Align.MIN))
    flat_box2 = flat_box2.locate(Location((-across_flats / 2, 0, 0)))
    shaft = shaft - flat_box2

    return shaft
