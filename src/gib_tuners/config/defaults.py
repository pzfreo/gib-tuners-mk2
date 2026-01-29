"""Factory functions for creating configurations from JSON and defaults."""

import json
from pathlib import Path
from typing import Optional

from .parameters import (
    BuildConfig,
    DDCutParams,
    GearParams,
    Hand,
    ToleranceConfig,
    WheelParams,
    WormParams,
)
from .tolerances import get_tolerance


def load_gear_params(json_path: Path) -> GearParams:
    """Load gear parameters from a JSON file (e.g., 7mm-globoid.json).

    Args:
        json_path: Path to the gear JSON file

    Returns:
        GearParams populated from JSON
    """
    with open(json_path) as f:
        data = json.load(f)

    worm_data = data["worm"]
    wheel_data = data["wheel"]
    assembly_data = data["assembly"]
    features_data = data.get("features", {})
    manufacturing_data = data.get("manufacturing", {})

    # Parse worm parameters
    worm = WormParams(
        module=worm_data["module_mm"],
        num_starts=worm_data["num_starts"],
        pitch_diameter=worm_data["pitch_diameter_mm"],
        tip_diameter=worm_data["tip_diameter_mm"],
        root_diameter=worm_data["root_diameter_mm"],
        lead=worm_data["lead_mm"],
        lead_angle_deg=worm_data["lead_angle_deg"],
        length=manufacturing_data.get("worm_length_mm", 7.0),
        hand=Hand.RIGHT if worm_data.get("hand", "right") == "right" else Hand.LEFT,
        throat_reduction=worm_data.get("throat_reduction_mm", 0.1),
        throat_curvature_radius=worm_data.get("throat_curvature_radius_mm", 3.0),
    )

    # Parse wheel bore (DD cut)
    wheel_features = features_data.get("wheel", {})
    wheel_bore = DDCutParams(
        diameter=wheel_features.get("bore_diameter_mm", 3.0),
        flat_depth=0.6,  # Standard DD cut
        across_flats=1.8,
    )

    # Parse wheel parameters
    wheel = WheelParams(
        module=wheel_data["module_mm"],
        num_teeth=wheel_data["num_teeth"],
        pitch_diameter=wheel_data["pitch_diameter_mm"],
        tip_diameter=wheel_data["tip_diameter_mm"],
        root_diameter=wheel_data["root_diameter_mm"],
        face_width=manufacturing_data.get("wheel_width_mm", 6.0),
        bore=wheel_bore,
    )

    return GearParams(
        worm=worm,
        wheel=wheel,
        center_distance=assembly_data["centre_distance_mm"],
        pressure_angle_deg=assembly_data["pressure_angle_deg"],
        backlash=assembly_data["backlash_mm"],
        ratio=assembly_data["ratio"],
    )


def create_default_config(
    scale: float = 1.0,
    tolerance: str = "production",
    hand: Hand = Hand.RIGHT,
    gear_json_path: Optional[Path] = None,
) -> BuildConfig:
    """Create a BuildConfig with defaults and optional overrides.

    Args:
        scale: Geometry scale factor (1.0 for production, 2.0 for FDM prototype)
        tolerance: Tolerance profile name
        hand: LEFT or RIGHT hand variant
        gear_json_path: Optional path to gear JSON file

    Returns:
        Configured BuildConfig instance
    """
    tol_config = get_tolerance(tolerance)

    # Load gear params from JSON if provided
    if gear_json_path is not None:
        gear = load_gear_params(gear_json_path)
    else:
        gear = GearParams(worm=WormParams(), wheel=WheelParams())

    return BuildConfig(
        scale=scale,
        tolerance=tol_config,
        hand=hand,
        gear=gear,
    )
