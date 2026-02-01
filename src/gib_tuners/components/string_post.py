"""String post geometry.

The string post is a stepped shaft with (from bottom to top):
- DD cut gear interface (mates with wheel) with M2 tap bore from bottom
- Frame bearing section
- Visible post section (above frame)
- Decorative cap (top)
- String hole (cross-drilled)

Assembly: Post inserted from above, wheel slides up from below onto DD section,
M2 washer and nut thread onto the tap bore to retain wheel.
"""

from build123d import (
    Align,
    Axis,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import BuildConfig
from ..features.dd_cut import create_dd_cut_shaft


def create_string_post(config: BuildConfig) -> Part:
    """Create the string post geometry.

    The post is oriented along the Z axis with:
    - Z=0 at the bottom of the DD section (with M2 tap bore)
    - Positive Z going up toward the cap

    Args:
        config: Build configuration

    Returns:
        String post Part
    """
    params = config.string_post
    scale = config.scale

    # Scaled dimensions
    cap_d = params.cap_diameter * scale
    cap_h = params.cap_height * scale

    post_d = params.post_diameter * scale
    post_h = params.post_height * scale

    bearing_d = params.bearing_diameter * scale
    # bearing_length and dd_cut_length are derived from frame and wheel params
    wall_thickness = config.frame.wall_thickness
    wheel_face_width = config.gear.wheel.face_width
    bearing_h = params.get_bearing_length(wall_thickness) * scale
    dd_length = params.get_dd_cut_length(wheel_face_width) * scale

    # M2 tap bore: 1.6mm pilot hole diameter, thread_length deep
    tap_bore_d = 1.6 * scale  # M2 tap drill size
    tap_bore_depth = params.thread_length * scale

    string_hole_d = params.string_hole_diameter * scale
    string_hole_pos = params.string_hole_position * scale

    # Build from bottom up
    z = 0.0

    # DD cut section (mates with wheel) - starts at Z=0
    dd_params = params.dd_cut
    dd_section = create_dd_cut_shaft(dd_params, dd_length, scale)
    dd_section = dd_section.locate(Location((0, 0, z)))
    z += dd_length

    # Frame bearing section
    bearing = Cylinder(
        radius=bearing_d / 2,
        height=bearing_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bearing = bearing.locate(Location((0, 0, z)))
    z += bearing_h

    # Visible post section
    post = Cylinder(
        radius=post_d / 2,
        height=post_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    post = post.locate(Location((0, 0, z)))
    z += post_h

    # Cap
    cap = Cylinder(
        radius=cap_d / 2,
        height=cap_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cap = cap.locate(Location((0, 0, z)))

    # Combine all sections
    string_post = dd_section + bearing + post + cap

    # M2 tap bore - drilled up from bottom into DD section
    tap_bore = Cylinder(
        radius=tap_bore_d / 2,
        height=tap_bore_depth + 0.1,  # Slightly deeper for clean cut
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    tap_bore = tap_bore.locate(Location((0, 0, -0.1)))
    string_post = string_post - tap_bore

    # Cross-drill string hole
    # Position is measured from frame top, which is at z = dd_length + bearing_h
    frame_top_z = dd_length + bearing_h
    hole_z = frame_top_z + string_hole_pos

    string_hole = Cylinder(
        radius=string_hole_d / 2,
        height=cap_d + 2,  # Through the post
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    string_hole = string_hole.rotate(Axis.X, 90)
    string_hole = string_hole.locate(Location((0, 0, hole_z)))
    string_post = string_post - string_hole

    return string_post
