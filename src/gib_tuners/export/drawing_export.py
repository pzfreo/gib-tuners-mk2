"""Engineering drawing generation from build123d CAD models.

Creates orthographic views with dimensions for manufacturing documentation.
Uses build123d's native Drawing, DimensionLine/ExtensionLine, and ExportSVG/DXF.
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Drawing,
    Draft,
    ExtensionLine,
    ExportSVG,
    ExportDXF,
    Unit,
    LineType,
    Part,
    Compound,
    Vector,
)

from ..config.parameters import BuildConfig


# Standard view directions for orthographic projection
VIEWS = {
    "top": {"look_from": (0, 0, 1), "look_up": (0, 1, 0)},      # Plan view (XY plane)
    "front": {"look_from": (0, -1, 0), "look_up": (0, 0, 1)},   # Front elevation (XZ)
    "right": {"look_from": (1, 0, 0), "look_up": (0, 0, 1)},    # Right side (YZ)
    "left": {"look_from": (-1, 0, 0), "look_up": (0, 0, 1)},    # Left side (YZ)
    "bottom": {"look_from": (0, 0, -1), "look_up": (0, 1, 0)},  # Bottom view
    "iso": {"look_from": (1, -1, 1), "look_up": (0, 0, 1)},     # Isometric
}


def create_drawing(
    part: Part | Compound,
    view: str = "top",
    with_hidden: bool = True,
) -> Drawing:
    """Create a 2D drawing projection from a 3D part.

    Args:
        part: The 3D geometry to project
        view: View name from VIEWS dict (top, front, right, left, bottom, iso)
        with_hidden: Include hidden (dashed) lines

    Returns:
        Drawing object with visible_lines and hidden_lines attributes
    """
    view_config = VIEWS.get(view, VIEWS["iso"])
    return Drawing(
        part,
        look_from=view_config["look_from"],
        look_up=view_config["look_up"],
        with_hidden=with_hidden,
    )


def create_draft_settings(scale: float = 1.0) -> Draft:
    """Create draft settings scaled for the drawing.

    Args:
        scale: Drawing scale factor (e.g., 2.0 for 2:1 scale)

    Returns:
        Draft settings for dimension lines
    """
    # Base sizes for 1:1 scale, adjust for drawing scale
    base_font = 2.5
    base_arrow = 1.5

    return Draft(
        font_size=base_font / scale,
        arrow_length=base_arrow / scale,
        line_width=0.2 / scale,
        decimal_precision=2,
        display_units=False,
        unit=Unit.MM,
        extension_gap=1.0 / scale,
        pad_around_text=1.0 / scale,
    )


def export_drawing_svg(
    drawings: dict[str, Drawing],
    dimensions: list,
    output_path: Path,
    scale: float = 5.0,
    margin: float = 20.0,
) -> Path:
    """Export drawings and dimensions to SVG file.

    Args:
        drawings: Dict mapping view names to Drawing objects
        dimensions: List of ExtensionLine/DimensionLine objects
        output_path: Output file path
        scale: SVG scale factor (pixels per mm)
        margin: Margin around drawing in mm

    Returns:
        Path to written file
    """
    exporter = ExportSVG(
        unit=Unit.MM,
        scale=scale,
        margin=margin,
        line_weight=0.3,
    )

    # Add layers
    exporter.add_layer("visible", line_weight=0.5)
    exporter.add_layer("hidden", line_weight=0.25, line_type=LineType.ISO_DASH)
    exporter.add_layer("dimension", line_weight=0.2)

    # Add all drawings
    for name, drawing in drawings.items():
        exporter.add_shape(drawing.visible_lines, layer="visible")
        if drawing.hidden_lines:
            exporter.add_shape(drawing.hidden_lines, layer="hidden")

    # Add dimensions
    for dim in dimensions:
        exporter.add_shape(dim, layer="dimension")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output_path))
    return output_path


def export_drawing_dxf(
    drawings: dict[str, Drawing],
    dimensions: list,
    output_path: Path,
) -> Path:
    """Export drawings and dimensions to DXF file.

    Args:
        drawings: Dict mapping view names to Drawing objects
        dimensions: List of ExtensionLine/DimensionLine objects
        output_path: Output file path

    Returns:
        Path to written file
    """
    exporter = ExportDXF(unit=Unit.MM)

    # Add layers
    exporter.add_layer("VISIBLE", line_weight=0.5)
    exporter.add_layer("HIDDEN", line_weight=0.25, line_type=LineType.ISO_DASH)
    exporter.add_layer("DIMENSION", line_weight=0.2)

    # Add all drawings
    for name, drawing in drawings.items():
        exporter.add_shape(drawing.visible_lines, layer="VISIBLE")
        if drawing.hidden_lines:
            exporter.add_shape(drawing.hidden_lines, layer="HIDDEN")

    # Add dimensions
    for dim in dimensions:
        exporter.add_shape(dim, layer="DIMENSION")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output_path))
    return output_path


def create_frame_drawing(
    config: BuildConfig,
    output_dir: Path,
    formats: list[str] = ["svg"],
) -> list[Path]:
    """Create engineering drawing for the frame component.

    Args:
        config: Build configuration with frame parameters
        output_dir: Directory for output files
        formats: List of formats to export ("svg", "dxf")

    Returns:
        List of paths to generated files
    """
    from ..components.frame import create_frame

    frame = create_frame(config)
    draft = create_draft_settings(scale=2.0)

    # Get frame bounding box for dimension placement
    bbox = frame.bounding_box()

    # Create views
    top_view = create_drawing(frame, "top")
    front_view = create_drawing(frame, "front")

    drawings = {"top": top_view}

    # Create dimensions based on top view (XY plane projection)
    # Frame is along Y axis, so length is Y extent, width is X extent
    f = config.frame
    scale = config.scale

    # Total length dimension (along Y)
    total_length = f.total_length * scale
    half_width = (f.box_outer * scale) / 2

    dimensions = [
        # Total length (bottom edge)
        ExtensionLine(
            border=[(0, 0), (0, total_length)],
            offset=half_width + 8,
            draft=draft,
        ),
        # Box width (at first housing)
        ExtensionLine(
            border=[(-half_width, f.housing_centers[0] * scale),
                    (half_width, f.housing_centers[0] * scale)],
            offset=5,
            draft=draft,
        ),
    ]

    # Add housing center markers and pitch dimension if multiple housings
    if len(f.housing_centers) >= 2:
        y1 = f.housing_centers[0] * scale
        y2 = f.housing_centers[1] * scale
        dimensions.append(
            ExtensionLine(
                border=[(0, y1), (0, y2)],
                offset=-(half_width + 5),
                draft=draft,
                label=f"pitch {f.tuner_pitch:.1f}",
            )
        )

    # Export in requested formats
    exported = []
    for fmt in formats:
        if fmt == "svg":
            path = output_dir / "frame.svg"
            export_drawing_svg(drawings, dimensions, path)
            exported.append(path)
        elif fmt == "dxf":
            path = output_dir / "frame.dxf"
            export_drawing_dxf(drawings, dimensions, path)
            exported.append(path)

    return exported


def create_string_post_drawing(
    config: BuildConfig,
    output_dir: Path,
    formats: list[str] = ["svg"],
) -> list[Path]:
    """Create engineering drawing for the string post component.

    Args:
        config: Build configuration with string post parameters
        output_dir: Directory for output files
        formats: List of formats to export ("svg", "dxf")

    Returns:
        List of paths to generated files
    """
    from ..components.string_post import create_string_post

    post = create_string_post(config)
    draft = create_draft_settings(scale=5.0)  # Larger scale for small part

    # Create views - front shows profile, top shows circular cross-section
    front_view = create_drawing(post, "front")

    drawings = {"front": front_view}

    # Get post parameters
    p = config.string_post
    scale = config.scale

    # Get actual geometry bounds (post is vertical along Z)
    bbox = post.bounding_box()
    total_height = bbox.max.Z - bbox.min.Z

    # Post is vertical (along Z), front view shows XZ projection
    # Dimensions for key diameters and heights
    dimensions = []

    # Cap diameter (at top)
    cap_r = (p.cap_diameter * scale) / 2
    cap_top = bbox.max.Z
    cap_bottom = cap_top - p.cap_height * scale

    dimensions.append(
        ExtensionLine(
            border=[(-cap_r, cap_top), (cap_r, cap_top)],
            offset=3,
            draft=draft,
            label=f"ø{p.cap_diameter:.1f}",
        )
    )

    # Post diameter
    post_r = (p.post_diameter * scale) / 2
    post_mid = cap_bottom - (p.post_height * scale) / 2

    dimensions.append(
        ExtensionLine(
            border=[(-post_r, post_mid), (post_r, post_mid)],
            offset=5,
            draft=draft,
            label=f"ø{p.post_diameter:.1f}",
        )
    )

    # Total height
    dimensions.append(
        ExtensionLine(
            border=[(cap_r + 2, bbox.min.Z), (cap_r + 2, cap_top)],
            offset=5,
            draft=draft,
        )
    )

    # Export in requested formats
    exported = []
    for fmt in formats:
        if fmt == "svg":
            path = output_dir / "string_post.svg"
            export_drawing_svg(drawings, dimensions, path, scale=10.0)
            exported.append(path)
        elif fmt == "dxf":
            path = output_dir / "string_post.dxf"
            export_drawing_dxf(drawings, dimensions, path)
            exported.append(path)

    return exported


def create_wheel_drawing(
    config: BuildConfig,
    output_dir: Path,
    wheel_step_path: Optional[Path] = None,
    formats: list[str] = ["svg"],
) -> list[Path]:
    """Create engineering drawing for the wheel component.

    Args:
        config: Build configuration with wheel parameters
        output_dir: Directory for output files
        wheel_step_path: Path to wheel STEP file (optional)
        formats: List of formats to export ("svg", "dxf")

    Returns:
        List of paths to generated files
    """
    from ..components.wheel import load_wheel, create_wheel_placeholder

    if wheel_step_path and wheel_step_path.exists():
        wheel = load_wheel(wheel_step_path)
        if config.scale != 1.0:
            wheel = wheel.scale(config.scale)
    else:
        wheel = create_wheel_placeholder(config)

    draft = create_draft_settings(scale=5.0)

    # Create views - front shows face, right shows profile
    front_view = create_drawing(wheel, "front")
    right_view = create_drawing(wheel, "right")

    drawings = {"front": front_view}

    # Get wheel parameters
    w = config.gear.wheel
    scale = config.scale

    dimensions = []

    # Tip diameter
    tip_r = (w.tip_diameter * scale) / 2
    dimensions.append(
        ExtensionLine(
            border=[(-tip_r, 0), (tip_r, 0)],
            offset=tip_r + 3,
            draft=draft,
            label=f"ø{w.tip_diameter:.2f}",
        )
    )

    # Export in requested formats
    exported = []
    for fmt in formats:
        if fmt == "svg":
            path = output_dir / "wheel.svg"
            export_drawing_svg(drawings, dimensions, path, scale=10.0)
            exported.append(path)
        elif fmt == "dxf":
            path = output_dir / "wheel.dxf"
            export_drawing_dxf(drawings, dimensions, path)
            exported.append(path)

    return exported


def create_peg_head_drawing(
    config: BuildConfig,
    output_dir: Path,
    worm_step_path: Optional[Path] = None,
    formats: list[str] = ["svg"],
) -> list[Path]:
    """Create engineering drawing for the peg head component.

    Args:
        config: Build configuration with peg head parameters
        output_dir: Directory for output files
        worm_step_path: Path to worm STEP file (optional)
        formats: List of formats to export ("svg", "dxf")

    Returns:
        List of paths to generated files
    """
    from ..components.peg_head import create_peg_head

    try:
        peg = create_peg_head(
            config,
            worm_step_path=worm_step_path,
            worm_length=config.gear.worm.length,
        )
    except FileNotFoundError:
        print("  Warning: peg head STEP files not found, skipping")
        return []

    draft = create_draft_settings(scale=3.0)

    # Create views - front shows profile
    front_view = create_drawing(peg, "front")

    drawings = {"front": front_view}

    # Get peg parameters
    worm = config.gear.worm
    scale = config.scale

    dimensions = []

    # Worm tip diameter
    worm_r = (worm.tip_diameter * scale) / 2
    dimensions.append(
        ExtensionLine(
            border=[(-worm_r, 0), (worm_r, 0)],
            offset=worm_r + 3,
            draft=draft,
            label=f"ø{worm.tip_diameter:.2f}",
        )
    )

    # Export in requested formats
    exported = []
    for fmt in formats:
        if fmt == "svg":
            path = output_dir / "peg_head.svg"
            export_drawing_svg(drawings, dimensions, path, scale=8.0)
            exported.append(path)
        elif fmt == "dxf":
            path = output_dir / "peg_head.dxf"
            export_drawing_dxf(drawings, dimensions, path)
            exported.append(path)

    return exported
