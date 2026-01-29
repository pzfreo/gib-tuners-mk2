"""String post geometry.

The string post is a stepped shaft with:
- Decorative cap (top)
- Visible post section (above frame)
- Frame bearing section
- DD cut gear interface (mates with wheel)
- E-clip retention section
- String hole (cross-drilled)
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
    - Z=0 at the bottom of the E-clip groove
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
    bearing_h = params.bearing_length * scale

    dd_length = params.dd_cut_length * scale

    eclip_shaft_d = params.eclip_shaft_diameter * scale
    eclip_shaft_h = params.eclip_shaft_length * scale
    eclip_groove_d = params.eclip_groove_diameter * scale
    eclip_groove_w = params.eclip_groove_width * scale

    string_hole_d = params.string_hole_diameter * scale
    string_hole_pos = params.string_hole_position * scale

    # Build from bottom up
    z = 0.0

    # E-clip groove (at bottom)
    groove = Cylinder(
        radius=eclip_groove_d / 2,
        height=eclip_groove_w,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    groove = groove.locate(Location((0, 0, z)))
    z += eclip_groove_w

    # E-clip shaft section
    eclip_shaft = Cylinder(
        radius=eclip_shaft_d / 2,
        height=eclip_shaft_h - eclip_groove_w,  # Already have groove width
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    eclip_shaft = eclip_shaft.locate(Location((0, 0, z)))
    z += eclip_shaft_h - eclip_groove_w

    # DD cut section
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
    string_post = groove + eclip_shaft + dd_section + bearing + post + cap

    # Cross-drill string hole
    # Position is measured from frame top, which is at z = eclip_shaft_h + dd_length + bearing_h
    frame_top_z = eclip_shaft_h + dd_length + bearing_h
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
