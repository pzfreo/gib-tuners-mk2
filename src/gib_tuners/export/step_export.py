"""STEP file export utilities."""

from pathlib import Path
from typing import Union

from build123d import (
    Compound,
    Part,
    export_step as bd_export_step,
)


def export_step(
    shape: Union[Part, Compound],
    output_path: Path,
    application_name: str = "gib-tuners",
) -> None:
    """Export a shape to STEP format.

    Args:
        shape: Part or Compound to export
        output_path: Output file path (should end in .step or .stp)
        application_name: Application name for STEP header
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bd_export_step(shape, str(output_path))


def export_assembly_step(
    assembly: dict,
    output_dir: Path,
    prefix: str = "",
) -> dict[str, Path]:
    """Export an assembly to multiple STEP files.

    Creates one STEP file per component, plus an assembly file.

    Args:
        assembly: Assembly dictionary from create_gang_assembly
        output_dir: Directory for output files
        prefix: Optional prefix for filenames (e.g., "rh_" or "lh_")

    Returns:
        Dictionary mapping component names to output paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = {}

    # Export frame
    frame = assembly.get("frame")
    if frame is not None:
        frame_path = output_dir / f"{prefix}frame.step"
        export_step(frame, frame_path)
        exported["frame"] = frame_path

    # Export tuner components
    tuners = assembly.get("tuners", [])
    for i, tuner_dict in enumerate(tuners):
        for name, part in tuner_dict.items():
            # Extract component type from name (e.g., "tuner_1_string_post" -> "string_post")
            component_type = name.split("_", 2)[-1] if "_" in name else name
            component_path = output_dir / f"{prefix}tuner_{i+1}_{component_type}.step"
            export_step(part, component_path)
            exported[name] = component_path

    # Create full assembly compound and export
    all_parts = [frame] if frame is not None else []
    for tuner_dict in tuners:
        all_parts.extend(tuner_dict.values())

    if all_parts:
        assembly_compound = Compound(all_parts)
        assembly_path = output_dir / f"{prefix}assembly.step"
        export_step(assembly_compound, assembly_path)
        exported["assembly"] = assembly_path

    return exported
