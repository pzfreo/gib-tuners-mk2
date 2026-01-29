"""5-gang frame geometry.

The frame is machined from 10.35mm square brass tube. It consists of:
- 5 rigid housings (full box profile)
- Connectors between housings (mounting plate only)
- Mounting holes in the mounting plate (top, Z=0)
- Sandwich drilling pattern per housing

Coordinate System:
- X: Width direction (side-to-side)
- Y: Length direction (along frame, 145mm)
- Z: Height direction
  - Z=0: Mounting plate surface (visible from above, sits on headstock)
  - Z=-box_outer: Bottom of frame (inside wood cavity)
  - Posts emerge upward in +Z direction
"""

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Part,
    Plane,
    Text,
    extrude,
)

from ..config.parameters import BuildConfig, Hand


def create_frame(config: BuildConfig) -> Part:
    """Create the 5-gang frame geometry.

    The frame is oriented with:
    - X: Width direction (side-to-side)
    - Y: Length direction (along frame, 145mm)
    - Z: Height direction (mounting plate at Z=0, frame extends into -Z)

    Origin is at the center of the mounting plate surface at Y=0.
    The mounting plate (top) is at Z=0, visible when installed.
    The frame extends downward into the headstock cavity (negative Z).

    Args:
        config: Build configuration

    Returns:
        Frame Part
    """
    frame_params = config.frame
    scale = config.scale

    # Scaled dimensions
    box_outer = frame_params.box_outer * scale
    wall = frame_params.wall_thickness * scale
    total_length = frame_params.total_length * scale
    housing_length = frame_params.housing_length * scale
    box_inner = frame_params.box_inner * scale

    # Start with full-length box tube
    # Z=0 (top/mounting plate) to Z=-box_outer (bottom)
    outer_box = Box(
        box_outer, total_length, box_outer,
        align=(Align.CENTER, Align.MIN, Align.MAX),  # MAX aligns top at Z=0
    )

    # Create internal cavity (hollow tube)
    inner_box = Box(
        box_inner, total_length + 2, box_inner,
        align=(Align.CENTER, Align.MIN, Align.MAX),
    )
    inner_box = inner_box.locate(Location((0, -1, -wall)))  # Offset down by wall thickness

    frame = outer_box - inner_box

    # Get housing center positions
    housing_centers = [c * scale for c in frame_params.housing_centers]

    # Mill away everything below mounting plate between housings and at ends
    # This leaves only the mounting plate (wall thickness) as connector
    first_housing_start = housing_centers[0] - housing_length / 2
    last_housing_end = housing_centers[-1] + housing_length / 2

    def mill_gap(y_start: float, y_end: float) -> None:
        """Remove all material below mounting plate in a gap region."""
        nonlocal frame
        gap_length = y_end - y_start
        if gap_length <= 0:
            return
        # Cut full width, from bottom of mounting plate to bottom of frame
        cut = Box(
            box_outer + 0.2, gap_length, box_outer - wall + 0.1,
            align=(Align.CENTER, Align.MIN, Align.MAX),
        )
        cut = cut.locate(Location((0, y_start, -wall)))
        frame = frame - cut

    # Before first housing
    if first_housing_start > 0:
        mill_gap(0, first_housing_start)

    # Between housings
    for i in range(len(housing_centers) - 1):
        y_start = housing_centers[i] + housing_length / 2
        y_end = housing_centers[i + 1] - housing_length / 2
        mill_gap(y_start, y_end)

    # After last housing
    if last_housing_end < total_length:
        mill_gap(last_housing_end, total_length)

    # Drill mounting holes in mounting plate (from Z=0 down through wall)
    mounting_positions = [p * scale for p in frame_params.mounting_hole_positions]
    mounting_hole_d = config.with_tolerance(frame_params.mounting_hole) * scale

    for y_pos in mounting_positions:
        hole = Cylinder(
            radius=mounting_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Drill from just above Z=0 down through mounting plate
        hole = hole.rotate(Axis.X, 180)  # Point downward
        hole = hole.locate(Location((0, y_pos, 0.1)))
        frame = frame - hole

    # Drill sandwich pattern for each housing
    center_distance = config.gear.center_distance * scale

    for housing_y in housing_centers:
        # Post bearing hole (top/mounting plate) - Z axis, from top
        # Posts emerge upward through this hole
        post_hole_d = config.with_tolerance(frame_params.post_bearing_hole) * scale
        post_hole = Cylinder(
            radius=post_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        post_hole = post_hole.rotate(Axis.X, 180)  # Point downward
        post_hole = post_hole.locate(Location((0, housing_y, 0.1)))
        frame = frame - post_hole

        # Wheel inlet hole (bottom) - Z axis, from bottom
        wheel_hole_d = config.with_tolerance(frame_params.wheel_inlet_hole) * scale
        wheel_hole = Cylinder(
            radius=wheel_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Start below bottom surface (-box_outer - 0.1) and drill upward through wall
        wheel_hole = wheel_hole.locate(Location((0, housing_y, -box_outer - 0.1)))
        frame = frame - wheel_hole

        # Worm entry and bearing holes (sides) - X axis
        # Entry is larger (worm OD + clearance)
        # Bearing is smaller (peg shaft + clearance)
        worm_entry_d = config.with_tolerance(frame_params.worm_entry_hole) * scale
        peg_bearing_d = config.with_tolerance(frame_params.peg_bearing_hole) * scale

        worm_z = -box_outer / 2  # Centered in box height (negative Z)

        # Determine side based on hand
        if config.hand == Hand.RIGHT:
            # RH: Entry on RIGHT (+X), bearing on LEFT (-X)
            entry_x = box_outer / 2 - wall - 0.1
            bearing_x = -box_outer / 2 - 0.1
        else:
            # LH: Entry on LEFT (-X), bearing on RIGHT (+X)
            entry_x = -box_outer / 2 - 0.1
            bearing_x = box_outer / 2 - wall - 0.1

        # Entry hole (larger, for worm)
        entry_hole = Cylinder(
            radius=worm_entry_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        entry_hole = entry_hole.rotate(Axis.Y, 90)
        entry_hole = entry_hole.locate(Location((entry_x, housing_y, worm_z)))
        frame = frame - entry_hole

        # Bearing hole (smaller, for peg shaft)
        bearing_hole = Cylinder(
            radius=peg_bearing_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        bearing_hole = bearing_hole.rotate(Axis.Y, 90)
        bearing_hole = bearing_hole.locate(Location((bearing_x, housing_y, worm_z)))
        frame = frame - bearing_hole

    # Etch "L" or "R" on inside surface of mounting plate to identify hand
    # Visible when looking from below (into the mechanism cavity)
    letter = "R" if config.hand == Hand.RIGHT else "L"
    text_height = 3.0 * scale  # 3mm tall text
    etch_depth = 0.3 * scale  # 0.3mm deep etch

    # Position between frame end and first mounting hole
    # First mounting hole is at end_length/2 = 5mm, so put text at ~2mm
    text_y = 2.0 * scale

    # Create text flat on XY plane, extrude upward, position on inside of mounting plate
    text_sketch = Text(letter, font_size=text_height, align=(Align.CENTER, Align.CENTER))
    text_solid = extrude(text_sketch, etch_depth)
    # Rotate 90 deg around Z so text reads along Y axis (frame length direction)
    text_solid = text_solid.rotate(Axis.Z, -90)
    # Move text so it cuts into inside surface of mounting plate (at Z=-wall)
    text_solid = text_solid.locate(Location((0, text_y, -wall)))
    frame = frame - text_solid

    return frame
