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

import math
from typing import Optional

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
from ..config.defaults import calculate_worm_z
from ..utils.validation import check_shape_quality


def _create_engraving(config: BuildConfig) -> Optional[Part]:
    """Create decorative border engraving geometry to subtract from frame top.

    Pattern: two rectangular border grooves (outer and inner) with diagonal
    hatching between them on all 4 sides. Simplified rope motif.

    Returns None if engraving is disabled.
    """
    frame_params = config.frame
    eng = frame_params.engraving
    if not eng.enabled:
        return None

    scale = config.scale
    box_outer = frame_params.box_outer * scale
    total_length = frame_params.total_length * scale
    half_w = box_outer / 2

    inset = eng.inset * scale
    band = eng.band_width * scale
    depth = eng.depth * scale
    gw = eng.groove_width * scale
    spacing = eng.hatch_spacing * scale

    # Border line positions (distance from center)
    ox = half_w - inset          # outer border X (±4.0 at 1:1)
    ix = half_w - inset - band   # inner border X (±2.5 at 1:1)
    oy0 = inset                  # outer border Y min (1.0)
    oy1 = total_length - inset   # outer border Y max (144.0)
    iy0 = inset + band           # inner border Y min (2.5)
    iy1 = total_length - inset - band  # inner border Y max (142.5)

    cuts: list[Part] = []

    def line_h(length: float, x: float, y: float) -> None:
        """Add a horizontal groove line (along X)."""
        b = Box(length, gw, depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MAX))
        cuts.append(b.locate(Location((x, y, 0.05))))

    def line_v(length: float, x: float, y: float) -> None:
        """Add a vertical groove line (along Y)."""
        b = Box(gw, length, depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MAX))
        cuts.append(b.locate(Location((x, y, 0.05))))

    def diagonal(cx: float, cy: float, angle: float) -> None:
        """Add a diagonal hatch line at the given center and angle."""
        diag_len = band * math.sqrt(2)
        b = Box(diag_len, gw, depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MAX))
        b = b.rotate(Axis.Z, angle)
        cuts.append(b.locate(Location((cx, cy, 0.05))))

    # --- Outer border rectangle (4 lines) ---
    line_h(2 * ox + gw, 0, oy0)   # bottom
    line_h(2 * ox + gw, 0, oy1)   # top
    line_v(oy1 - oy0, -ox, (oy0 + oy1) / 2)  # left
    line_v(oy1 - oy0, ox, (oy0 + oy1) / 2)   # right

    # --- Inner border rectangle (4 lines) ---
    line_h(2 * ix + gw, 0, iy0)   # bottom
    line_h(2 * ix + gw, 0, iy1)   # top
    line_v(iy1 - iy0, -ix, (iy0 + iy1) / 2)  # left
    line_v(iy1 - iy0, ix, (iy0 + iy1) / 2)   # right

    # --- Diagonal hatching: long sides (left and right) ---
    band_cx_left = -(ox + ix) / 2   # center of left band
    band_cx_right = (ox + ix) / 2   # center of right band

    y = iy0 + spacing / 2
    while y < iy1:
        diagonal(band_cx_left, y, 45)
        diagonal(band_cx_right, y, -45)
        y += spacing

    # --- Diagonal hatching: short sides (bottom and top) ---
    # Mirrored along long axis (Y): left half at 45°, right half at -45°
    band_cy_bottom = (oy0 + iy0) / 2
    band_cy_top = (oy1 + iy1) / 2

    # Generate left half positions, then mirror for right half
    left_xs: list[float] = []
    x = -ix + spacing / 2
    while x < 0:
        left_xs.append(x)
        x += spacing

    for xp in left_xs:
        diagonal(xp, band_cy_bottom, 45)
        diagonal(xp, band_cy_top, 45)
        # Mirror to right half
        diagonal(-xp, band_cy_bottom, -45)
        diagonal(-xp, band_cy_top, -45)

    # Fuse all cuts into one solid for a single boolean subtraction
    result = cuts[0]
    for c in cuts[1:]:
        result = result + c

    return result


def create_frame(config: BuildConfig, label: bool = True) -> Part:
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
    # Worm and wheel axes are offset from housing center by center_distance/2
    # to achieve proper mesh while centering the mechanism in the housing.
    # Post axis is offset toward -Y (string tension pulls this way)
    # Worm axis is offset toward +Y (wheel swings into worm under load)
    center_distance = config.gear.center_distance * scale
    extra_backlash = config.gear.extra_backlash * scale
    effective_cd = center_distance - extra_backlash

    # Y offsets from housing center
    post_y_offset = -effective_cd / 2  # Post toward -Y (nut/bridge end)
    worm_y_offset = effective_cd / 2   # Worm toward +Y

    for housing_y in housing_centers:
        # Calculate actual Y positions for this housing
        post_y = housing_y + post_y_offset
        worm_y = housing_y + worm_y_offset

        # Post bearing hole (top/mounting plate) - Z axis, from top
        # Posts emerge upward through this hole
        post_hole_d = config.with_tolerance(frame_params.post_bearing_hole) * scale
        post_hole = Cylinder(
            radius=post_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        post_hole = post_hole.rotate(Axis.X, 180)  # Point downward
        post_hole = post_hole.locate(Location((0, post_y, 0.1)))
        frame = frame - post_hole

        # Wheel inlet hole (bottom) - Z axis, from bottom
        wheel_hole_d = config.with_tolerance(frame_params.wheel_inlet_hole) * scale
        wheel_hole = Cylinder(
            radius=wheel_hole_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Start below bottom surface (-box_outer - 0.1) and drill upward through wall
        wheel_hole = wheel_hole.locate(Location((0, post_y, -box_outer - 0.1)))
        frame = frame - wheel_hole

        # Worm entry and bearing holes (sides) - X axis
        # Entry is larger (worm OD + clearance)
        # Bearing is smaller (peg shaft + clearance)
        worm_entry_d = config.with_tolerance(frame_params.worm_entry_hole) * scale
        peg_bearing_d = config.with_tolerance(frame_params.peg_bearing_hole) * scale

        worm_z = calculate_worm_z(config)  # Position based on gear configuration

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
        entry_hole = entry_hole.locate(Location((entry_x, worm_y, worm_z)))
        frame = frame - entry_hole

        # Bearing hole (smaller, for peg shaft)
        bearing_hole = Cylinder(
            radius=peg_bearing_d / 2,
            height=wall + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        bearing_hole = bearing_hole.rotate(Axis.Y, 90)
        bearing_hole = bearing_hole.locate(Location((bearing_x, worm_y, worm_z)))
        frame = frame - bearing_hole

    # Etch "L" or "R" on inside surface of mounting plate to identify hand
    # Visible when looking from below (into the mechanism cavity)
    if label:
        letter = "R" if config.hand == Hand.RIGHT else "L"
        text_height = 3.0 * scale  # 3mm tall text
        etch_depth = 0.3 * scale  # 0.3mm deep etch

        # Position between frame end and first mounting hole
        # First mounting hole is at end_length/2 = 5mm, so put text at ~2mm
        text_y = 2.0 * scale

        # Create text flat on XY plane, extrude upward, position on inside of mounting plate
        # Text is on the underside, so mirror it in X so it reads correctly from below
        text_sketch = Text(letter, font_size=text_height, align=(Align.CENTER, Align.CENTER))
        text_solid = extrude(text_sketch, etch_depth)
        # Mirror in X so text reads correctly when viewed from below (-Z direction)
        text_solid = text_solid.mirror(Plane.YZ)
        # Rotate 90 deg around Z so text reads along Y axis (frame length direction)
        text_solid = text_solid.rotate(Axis.Z, -90)
        # Move text so it cuts into inside surface of mounting plate (at Z=-wall)
        text_solid = text_solid.locate(Location((0, text_y, -wall)))
        frame = frame - text_solid

    # Add decorative engraving to top plate
    engraving = _create_engraving(config)
    if engraving is not None:
        frame = frame - engraving

    # Check shape quality (warns if non-manifold edges detected)
    check_shape_quality(frame, "frame")

    return frame
