"""Standard hardware components.

Simple geometry for screws, washers, and E-clips used in the assembly.
These are for visualization and assembly verification, not manufacturing.
"""

from build123d import (
    Align,
    Cylinder,
    Location,
    Part,
)

from ..config.parameters import BuildConfig


def create_washer(
    outer_diameter: float,
    inner_diameter: float,
    thickness: float,
    scale: float = 1.0,
) -> Part:
    """Create a simple washer.

    Args:
        outer_diameter: Outer diameter
        inner_diameter: Inner diameter (hole)
        thickness: Washer thickness
        scale: Scale factor

    Returns:
        Washer Part
    """
    od = outer_diameter * scale
    id_ = inner_diameter * scale
    t = thickness * scale

    outer = Cylinder(radius=od / 2, height=t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(radius=id_ / 2, height=t + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = inner.locate(Location((0, 0, -0.05)))

    return outer - inner


def create_peg_retention_washer(config: BuildConfig) -> Part:
    """Create the washer used to retain the peg head.

    5mm OD, 2.2mm ID, 0.5mm thick (from spec).

    Args:
        config: Build configuration

    Returns:
        Washer Part
    """
    params = config.peg_head
    return create_washer(
        outer_diameter=params.washer_od,
        inner_diameter=params.washer_id,
        thickness=params.washer_thickness,
        scale=config.scale,
    )


def create_eclip(
    outer_diameter: float,
    inner_diameter: float,
    thickness: float = 0.6,
    scale: float = 1.0,
) -> Part:
    """Create a simplified E-clip representation.

    This is a simplified disc shape for visualization.
    Actual E-clips have a C-shape opening.

    Args:
        outer_diameter: Outer diameter
        inner_diameter: Shaft diameter (determines inner opening)
        thickness: Clip thickness
        scale: Scale factor

    Returns:
        E-clip Part (simplified)
    """
    od = outer_diameter * scale
    id_ = inner_diameter * scale
    t = thickness * scale

    outer = Cylinder(radius=od / 2, height=t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(radius=id_ / 2, height=t + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = inner.locate(Location((0, 0, -0.05)))

    return outer - inner


def create_wheel_eclip(config: BuildConfig) -> Part:
    """Create the E-clip used to retain the wheel on the string post.

    DIN 6799 M2.5 (~6mm OD) from spec.

    Args:
        config: Build configuration

    Returns:
        E-clip Part
    """
    params = config.string_post
    return create_eclip(
        outer_diameter=params.eclip_od,
        inner_diameter=params.eclip_groove_diameter,
        thickness=0.6,
        scale=config.scale,
    )


def create_pan_head_screw(
    thread_diameter: float,
    length: float,
    head_diameter: float,
    head_height: float,
    scale: float = 1.0,
) -> Part:
    """Create a simplified pan head screw.

    Args:
        thread_diameter: Nominal thread diameter
        length: Screw length (excluding head)
        head_diameter: Head diameter
        head_height: Head height
        scale: Scale factor

    Returns:
        Screw Part
    """
    td = thread_diameter * scale
    l = length * scale
    hd = head_diameter * scale
    hh = head_height * scale

    # Shank
    shank = Cylinder(radius=td / 2, height=l, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Head
    head = Cylinder(radius=hd / 2, height=hh, align=(Align.CENTER, Align.CENTER, Align.MIN))
    head = head.locate(Location((0, 0, l)))

    return shank + head


def create_m2_pan_head_screw(config: BuildConfig) -> Part:
    """Create the M2 pan head screw for peg retention.

    Args:
        config: Build configuration

    Returns:
        Screw Part
    """
    params = config.peg_head
    return create_pan_head_screw(
        thread_diameter=2.0,
        length=params.screw_length,
        head_diameter=3.8,
        head_height=1.3,
        scale=config.scale,
    )
