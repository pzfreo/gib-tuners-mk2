"""5-gang frame geometry.

The frame is machined from 10.35mm square brass tube. It consists of:
- 5 rigid housings (full box profile)
- Connectors between housings (bottom plate only)
- Mounting holes in the bottom plate
- Sandwich drilling pattern per housing
"""

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import BuildConfig, Hand


def create_frame(config: BuildConfig) -> Part:
    """Create the 5-gang frame geometry.

    The frame is oriented with:
    - X: Width direction (side-to-side)
    - Y: Length direction (along frame, 145mm)
    - Z: Height direction (top-to-bottom)

    Origin is at the center of the frame cross-section at Y=0.

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
    outer_box = Box(
        box_outer, total_length, box_outer,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    # Create internal cavity (hollow tube)
    inner_box = Box(
        box_inner, total_length + 2, box_inner,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    inner_box = inner_box.locate(Location((0, -1, wall)))

    frame = outer_box - inner_box

    # Get housing center positions
    housing_centers = [c * scale for c in frame_params.housing_centers]

    # Mill away top and side walls between housings (leave only bottom plate)
    # This creates the characteristic frame shape
    for i in range(len(housing_centers) - 1):
        y_start = housing_centers[i] + housing_length / 2
        y_end = housing_centers[i + 1] - housing_length / 2
        gap_length = y_end - y_start

        if gap_length > 0:
            # Remove top wall in gap
            top_cut = Box(
                box_inner, gap_length, wall + 0.1,
                align=(Align.CENTER, Align.MIN, Align.MIN),
            )
            top_cut = top_cut.locate(Location((0, y_start, box_outer - wall)))
            frame = frame - top_cut

            # Remove side walls in gap (both sides)
            side_cut = Box(
                wall + 0.1, gap_length, box_inner,
                align=(Align.MIN, Align.MIN, Align.MIN),
            )
            # Right side (+X)
            side_cut_r = side_cut.locate(Location((box_outer / 2 - wall, y_start, wall)))
            frame = frame - side_cut_r
            # Left side (-X)
            side_cut_l = side_cut.locate(Location((-box_outer / 2, y_start, wall)))
            frame = frame - side_cut_l

    # Also remove walls before first housing and after last housing
    first_housing_start = housing_centers[0] - housing_length / 2
    last_housing_end = housing_centers[-1] + housing_length / 2

    # Before first housing
    if first_housing_start > 0:
        gap_length = first_housing_start
        # Top
        top_cut = Box(
            box_inner, gap_length, wall + 0.1,
            align=(Align.CENTER, Align.MIN, Align.MIN),
        )
        top_cut = top_cut.locate(Location((0, 0, box_outer - wall)))
        frame = frame - top_cut
        # Sides
        side_cut = Box(
            wall + 0.1, gap_length, box_inner,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        side_cut_r = side_cut.locate(Location((box_outer / 2 - wall, 0, wall)))
        frame = frame - side_cut_r
        side_cut_l = side_cut.locate(Location((-box_outer / 2, 0, wall)))
        frame = frame - side_cut_l

    # After last housing
    if last_housing_end < total_length:
        gap_start = last_housing_end
        gap_length = total_length - gap_start
        # Top
        top_cut = Box(
            box_inner, gap_length, wall + 0.1,
            align=(Align.CENTER, Align.MIN, Align.MIN),
        )
        top_cut = top_cut.locate(Location((0, gap_start, box_outer - wall)))
        frame = frame - top_cut
        # Sides
        side_cut = Box(
            wall + 0.1, gap_length, box_inner,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        side_cut_r = side_cut.locate(Location((box_outer / 2 - wall, gap_start, wall)))
        frame = frame - side_cut_r
        side_cut_l = side_cut.locate(Location((-box_outer / 2, gap_start, wall)))
        frame = frame - side_cut_l

    # Drill mounting holes in bottom plate
    mounting_positions = [p * scale for p in frame_params.mounting_hole_positions]
    mounting_hole_d = config.with_tolerance(frame_params.mounting_hole) * scale

    for y_pos in mounting_positions:
        hole = Cylinder(
            radius=mounting_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        hole = hole.locate(Location((0, y_pos, -0.1)))
        frame = frame - hole

    # Drill sandwich pattern for each housing
    center_distance = config.gear.center_distance * scale

    for housing_y in housing_centers:
        # Post bearing hole (top) - Z axis, from top
        post_hole_d = config.with_tolerance(frame_params.post_bearing_hole) * scale
        post_hole = Cylinder(
            radius=post_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        post_hole = post_hole.locate(Location((0, housing_y, box_outer - wall - 0.1)))
        frame = frame - post_hole

        # Wheel inlet hole (bottom) - Z axis, from bottom
        wheel_hole_d = config.with_tolerance(frame_params.wheel_inlet_hole) * scale
        wheel_hole = Cylinder(
            radius=wheel_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        wheel_hole = wheel_hole.locate(Location((0, housing_y, -0.1)))
        frame = frame - wheel_hole

        # Worm entry and bearing holes (sides) - X axis
        # Entry is larger (worm OD + clearance)
        # Bearing is smaller (peg shaft + clearance)
        worm_entry_d = config.with_tolerance(frame_params.worm_entry_hole) * scale
        peg_bearing_d = config.with_tolerance(frame_params.peg_bearing_hole) * scale

        worm_z = box_outer / 2  # Centered in box height

        # Determine side based on hand
        if config.hand == Hand.RIGHT:
            # Entry on left (-X), bearing on right (+X)
            entry_x = -box_outer / 2 - 0.1
            bearing_x = box_outer / 2 - wall - 0.1
        else:
            # Entry on right (+X), bearing on left (-X)
            entry_x = box_outer / 2 - wall - 0.1
            bearing_x = -box_outer / 2 - 0.1

        # Entry hole (larger, for worm)
        entry_hole = Cylinder(
            radius=worm_entry_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        entry_hole = entry_hole.rotate(Axis.Y, 90)
        if config.hand == Hand.RIGHT:
            entry_hole = entry_hole.locate(Location((entry_x, housing_y, worm_z)))
        else:
            entry_hole = entry_hole.locate(Location((entry_x, housing_y, worm_z)))
        frame = frame - entry_hole

        # Bearing hole (smaller, for peg shaft)
        bearing_hole = Cylinder(
            radius=peg_bearing_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        bearing_hole = bearing_hole.rotate(Axis.Y, 90)
        if config.hand == Hand.RIGHT:
            bearing_hole = bearing_hole.locate(Location((bearing_x, housing_y, worm_z)))
        else:
            bearing_hole = bearing_hole.locate(Location((bearing_x, housing_y, worm_z)))
        frame = frame - bearing_hole

    return frame
