"""Peg head assembly geometry.

The peg head is cast as a single piece with (from outside to inside frame):
- Decorative button (outside)
- Ring head (finger grip with hollow bore)
- Cap (sits against frame, stops push-in)
- Entry shaft (passes through worm entry hole)
- Integral worm thread (in cavity)
- Bearing shaft (through peg bearing hole on opposite side)
- M2 tapped hole for retention screw

Note: The worm thread geometry is complex (globoid) and should be
imported from the reference STEP file for actual manufacturing.
This module creates a simplified representation for assembly visualization.
"""

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import BuildConfig, Hand


def create_peg_head(config: BuildConfig, include_worm_detail: bool = False) -> Part:
    """Create the peg head assembly geometry.

    The peg head is oriented with:
    - Worm axis along X (horizontal)
    - Button/ring on the left (-X), outside frame
    - Shaft extending right (+X), into frame

    Args:
        config: Build configuration
        include_worm_detail: If True, creates detailed worm geometry (slow).
                           If False, creates simplified cylindrical representation.

    Returns:
        Peg head Part
    """
    params = config.peg_head
    worm = config.gear.worm
    scale = config.scale

    # Scaled dimensions - ring
    ring_od = params.ring_od * scale
    ring_bore = params.ring_bore * scale
    ring_width = params.ring_width * scale

    # Button
    button_d = params.button_diameter * scale
    button_h = params.button_height * scale

    # Cap (stop against frame)
    cap_d = params.cap_diameter * scale
    cap_h = params.cap_length * scale

    # Entry shaft (through worm entry hole)
    entry_d = params.entry_shaft_diameter * scale
    entry_h = params.entry_shaft_length * scale

    # Worm
    worm_od = worm.tip_diameter * scale
    worm_length = worm.length * scale

    # Bearing shaft
    bearing_d = params.bearing_diameter * scale
    bearing_h = params.bearing_length * scale

    # Build from left to right (negative X to positive X)
    # Ring head is centered at X=0 for positioning

    # Button (leftmost, outside)
    button = Cylinder(
        radius=button_d / 2,
        height=button_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    button = button.rotate(Axis.Y, -90)  # Align along X axis
    button = button.locate(Location((-ring_width / 2 - button_h, 0, 0)))

    # Ring head - simplified as a cylinder with bore
    ring_outer = Cylinder(
        radius=ring_od / 2,
        height=ring_width,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    ring_outer = ring_outer.rotate(Axis.Y, 90)  # Align along X

    ring_inner = Cylinder(
        radius=ring_bore / 2,
        height=ring_width + 2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    ring_inner = ring_inner.rotate(Axis.Y, 90)

    ring = ring_outer - ring_inner

    # Cap (sits against frame, stops push-in)
    x_pos = ring_width / 2
    cap = Cylinder(
        radius=cap_d / 2,
        height=cap_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cap = cap.rotate(Axis.Y, 90)
    cap = cap.locate(Location((x_pos, 0, 0)))
    x_pos += cap_h

    # Entry shaft (through worm entry hole in frame wall)
    entry_shaft = Cylinder(
        radius=entry_d / 2,
        height=entry_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    entry_shaft = entry_shaft.rotate(Axis.Y, 90)
    entry_shaft = entry_shaft.locate(Location((x_pos, 0, 0)))
    x_pos += entry_h

    # Worm section (simplified as cylinder)
    worm_section = Cylinder(
        radius=worm_od / 2,
        height=worm_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    worm_section = worm_section.rotate(Axis.Y, 90)
    worm_section = worm_section.locate(Location((x_pos, 0, 0)))
    x_pos += worm_length

    # Bearing shaft (through peg bearing hole on opposite side)
    bearing_shaft = Cylinder(
        radius=bearing_d / 2,
        height=bearing_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bearing_shaft = bearing_shaft.rotate(Axis.Y, 90)
    bearing_shaft = bearing_shaft.locate(Location((x_pos, 0, 0)))
    x_pos += bearing_h

    # Screw hole (M2 tapped, simplified as cylinder)
    screw_hole_d = 1.6 * scale  # M2 tap drill
    screw_hole_depth = params.screw_length * scale

    screw_hole = Cylinder(
        radius=screw_hole_d / 2,
        height=screw_hole_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    screw_hole = screw_hole.rotate(Axis.Y, -90)  # Point into shaft
    screw_hole = screw_hole.locate(Location((x_pos, 0, 0)))

    # Combine all parts
    peg_head = button + ring + cap + entry_shaft + worm_section + bearing_shaft
    peg_head = peg_head - screw_hole

    return peg_head


def create_peg_head_simplified(config: BuildConfig) -> Part:
    """Create a simplified peg head for quick visualization.

    This is faster than the full geometry and useful for assembly checks.

    Args:
        config: Build configuration

    Returns:
        Simplified peg head Part
    """
    return create_peg_head(config, include_worm_detail=False)
