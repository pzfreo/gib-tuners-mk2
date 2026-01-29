"""Full 5-gang tuner assembly.

Combines the frame with 5 tuner units, each positioned at the correct
housing location.
"""

from pathlib import Path
from typing import Optional

from build123d import (
    Compound,
    Location,
    Part,
)

from ..config.parameters import BuildConfig
from ..components.frame import create_frame
from .tuner_unit import create_tuner_unit


def create_gang_assembly(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    worm_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> dict[str, Part | dict]:
    """Create the full 5-gang tuner assembly.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        worm_step_path: Optional path to worm STEP file (for mesh rotation calculation)
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Dictionary containing:
        - 'frame': The frame Part
        - 'tuners': List of tuner component dictionaries (one per housing)
    """
    scale = config.scale

    # Create the frame
    frame = create_frame(config)

    # Get housing positions
    housing_centers = [c * scale for c in config.frame.housing_centers]

    # Create tuner units at each housing position
    tuners = []
    for i, housing_y in enumerate(housing_centers):
        # Create tuner unit (components are at origin)
        tuner_components = create_tuner_unit(
            config,
            wheel_step_path=wheel_step_path,
            worm_step_path=worm_step_path,
            include_hardware=include_hardware,
        )

        # Relocate all components to housing position
        positioned_components = {}
        for name, part in tuner_components.items():
            positioned = part.locate(Location((0, housing_y, 0)))
            positioned_components[f"tuner_{i+1}_{name}"] = positioned

        tuners.append(positioned_components)

    return {
        "frame": frame,
        "tuners": tuners,
    }


def create_gang_assembly_compound(
    config: BuildConfig,
    wheel_step_path: Optional[Path] = None,
    worm_step_path: Optional[Path] = None,
    include_hardware: bool = True,
) -> Compound:
    """Create the full 5-gang assembly as a compound shape.

    Args:
        config: Build configuration
        wheel_step_path: Optional path to wheel STEP file
        worm_step_path: Optional path to worm STEP file (for mesh rotation calculation)
        include_hardware: Whether to include washers, screws, E-clips

    Returns:
        Compound containing frame and all tuner components
    """
    assembly = create_gang_assembly(config, wheel_step_path, worm_step_path, include_hardware)

    parts = [assembly["frame"]]
    for tuner_dict in assembly["tuners"]:
        parts.extend(tuner_dict.values())

    return Compound(parts)


def create_frame_only(config: BuildConfig) -> Part:
    """Create just the frame without tuner components.

    Useful for exporting the frame geometry for machining.

    Args:
        config: Build configuration

    Returns:
        Frame Part
    """
    return create_frame(config)
