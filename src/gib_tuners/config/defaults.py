"""Factory functions for creating configurations from JSON and defaults."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .parameters import (
    BuildConfig,
    DDCutParams,
    FrameParams,
    GearParams,
    Hand,
    PegHeadParams,
    StringPostParams,
    ToleranceConfig,
    WheelParams,
    WormParams,
    WormType,
    WormZMode,
)
from .tolerances import get_tolerance

# Directory paths
CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"
REFERENCE_DIR = Path(__file__).parent.parent.parent.parent / "reference"

# Default gear parameters JSON - single source of truth for gear geometry
DEFAULT_GEAR_JSON = CONFIG_DIR / "worm_gear.json"

# Bearing hole clearance (tight fit, can be reamed at assembly if needed)
BEARING_CLEARANCE = 0.05  # 0.025mm per side


@dataclass
class GearConfigPaths:
    """Paths for a gear configuration."""
    json_path: Path              # worm_gear.json
    config_dir: Optional[Path]   # Config directory (None for legacy root config)
    wheel_step: Optional[Path]   # wheel STEP if exists
    worm_step: Optional[Path]    # worm STEP if exists


def resolve_gear_config(gear_name: Optional[str] = None) -> GearConfigPaths:
    """Resolve gear config paths from name.

    Args:
        gear_name: Config name (e.g., 'balanced') or None for default

    Returns:
        GearConfigPaths with all resolved paths

    Raises:
        FileNotFoundError if config doesn't exist
    """
    if gear_name is None:
        # Default: root config/worm_gear.json (balanced M0.6 config)
        wheel_step = REFERENCE_DIR / "wheel_m0.6_z10.step"
        worm_step = REFERENCE_DIR / "worm_m0.6_z1.step"
        return GearConfigPaths(
            json_path=DEFAULT_GEAR_JSON,
            config_dir=None,
            wheel_step=wheel_step if wheel_step.exists() else None,
            worm_step=worm_step if worm_step.exists() else None,
        )

    config_dir = CONFIG_DIR / gear_name
    json_path = config_dir / "worm_gear.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Gear config not found: {json_path}")

    # Check for STEP files in config dir (named by module/teeth)
    wheel_step = None
    worm_step = None
    for f in config_dir.glob("wheel_*.step"):
        wheel_step = f
        break
    for f in config_dir.glob("worm_*.step"):
        worm_step = f
        break

    return GearConfigPaths(
        json_path=json_path,
        config_dir=config_dir,
        wheel_step=wheel_step,
        worm_step=worm_step,
    )


def list_gear_configs() -> list:
    """List available gear configurations.

    Returns:
        List of config directory names that contain worm_gear.json
    """
    configs = []
    if CONFIG_DIR.exists():
        for item in CONFIG_DIR.iterdir():
            if item.is_dir() and (item / "worm_gear.json").exists():
                configs.append(item.name)
    return sorted(configs)


def load_tuner_config(config_dir: Optional[Path]) -> dict:
    """Load tuner config overrides from tuner_config.json.

    This allows per-gear-config overrides for frame, string_post, and peg_head
    parameters that may need to change with different gear designs.

    Args:
        config_dir: Config directory containing tuner_config.json

    Returns:
        Dict with frame/string_post/peg_head overrides, or empty dict if not found

    Example tuner_config.json:
        {
            "frame": {"box_outer": 12.0},
            "string_post": {"bearing_diameter": 4.5},
            "peg_head": {"shaft_diameter": 4.5}
        }
    """
    if config_dir is None:
        return {}
    config_path = config_dir / "tuner_config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


def requires_worm_alignment(config: "BuildConfig") -> bool:
    """Check if worm must align with wheel center (globoid or virtual hobbing).

    Returns True if:
    - worm.worm_type == GLOBOID, or
    - gear.virtual_hobbing == True

    When True, the worm Z-position should match the wheel center for proper meshing.
    """
    return (
        config.gear.worm.worm_type == WormType.GLOBOID or
        config.gear.virtual_hobbing
    )


def calculate_worm_z(config: "BuildConfig") -> float:
    """Calculate worm Z position based on gear configuration.

    Args:
        config: Build configuration with gear and frame parameters

    Returns:
        Z-coordinate for worm axis position

    Positioning logic (in order of precedence):
    1. If worm_z_mode == CENTERED: center in frame
    2. If worm_z_mode == ALIGNED: align with wheel center
    3. If worm_z_mode == AUTO: auto-detect based on globoid/virtual_hobbing
    """
    scale = config.scale
    box_outer = config.frame.box_outer * scale
    worm_z_mode = config.gear.worm_z_mode

    # Check explicit overrides first
    if worm_z_mode == WormZMode.CENTERED:
        return -box_outer / 2

    if worm_z_mode == WormZMode.ALIGNED:
        # Calculate wheel_z
        post_params = config.string_post
        gear_params = config.gear
        dd_h = post_params.dd_cut_length * scale
        bearing_h = post_params.bearing_length * scale
        post_z_offset = -(dd_h + bearing_h)
        face_width = gear_params.wheel.face_width * scale
        return post_z_offset + face_width / 2

    # AUTO mode: detect based on worm type and virtual_hobbing
    if requires_worm_alignment(config):
        # Aligned: calculate wheel_z
        post_params = config.string_post
        gear_params = config.gear
        dd_h = post_params.dd_cut_length * scale
        bearing_h = post_params.bearing_length * scale
        post_z_offset = -(dd_h + bearing_h)
        face_width = gear_params.wheel.face_width * scale
        return post_z_offset + face_width / 2

    # Default: centered in frame
    return -box_outer / 2


def load_mesh_alignment(module: float, config_dir: Optional[Path] = None) -> dict:
    """Load mesh alignment data from wormgear optimizer output.

    Checks for data in this order:
    1. config_dir/geometry_analysis_m{module}.json (new format, nested)
    2. config_dir/mesh_alignment.json (old format)
    3. reference/mesh_alignment_m{module}.json (legacy fallback)

    Args:
        module: Gear module in mm (e.g., 0.6)
        config_dir: Optional config directory to check first

    Returns:
        Dict with optimal_rotation_deg, tooth_pitch_deg, etc., or empty dict if not found
    """
    # Check config directory first
    if config_dir:
        # New format: geometry_analysis_m{module}.json with nested mesh_alignment
        geometry_json = config_dir / f"geometry_analysis_m{module}.json"
        if geometry_json.exists():
            with open(geometry_json) as f:
                data = json.load(f)
                # New format has mesh_alignment nested
                if "mesh_alignment" in data:
                    return data["mesh_alignment"]
                return data

        # Old format: mesh_alignment.json at root level
        mesh_json = config_dir / "mesh_alignment.json"
        if mesh_json.exists():
            with open(mesh_json) as f:
                return json.load(f)

    # Fall back to reference directory
    # Check new format first
    geometry_json = REFERENCE_DIR / f"geometry_analysis_m{module}.json"
    if geometry_json.exists():
        with open(geometry_json) as f:
            data = json.load(f)
            if "mesh_alignment" in data:
                return data["mesh_alignment"]
            return data

    # Legacy format
    mesh_json = REFERENCE_DIR / f"mesh_alignment_m{module}.json"
    if mesh_json.exists():
        with open(mesh_json) as f:
            return json.load(f)
    return {}


def load_gear_params(json_path: Path, config_dir: Optional[Path] = None) -> GearParams:
    """Load gear parameters from a JSON file (e.g., config/worm_gear.json).

    Args:
        json_path: Path to the gear JSON file
        config_dir: Optional config directory for mesh alignment lookup

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

    # Parse worm type
    worm_type_str = worm_data.get("type", "cylindrical")
    worm_type = WormType.GLOBOID if worm_type_str == "globoid" else WormType.CYLINDRICAL

    # Parse virtual hobbing flag
    virtual_hobbing = manufacturing_data.get("virtual_hobbing", False)

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
        worm_type=worm_type,
        throat_reduction=worm_data.get("throat_reduction_mm", 0.1),
        throat_curvature_radius=worm_data.get("throat_curvature_radius_mm", 3.0),
    )

    # Parse wheel bore (DD cut) - updated for 7.5mm wheel
    wheel_features = features_data.get("wheel", {})
    bore_diameter = wheel_features.get("bore_diameter_mm", 3.5)
    # Calculate DD parameters: flat_depth ~14% of diameter, across_flats = diameter - 2*flat_depth
    flat_depth = round(bore_diameter * 0.14, 1)  # ~0.5mm for 3.5mm bore
    across_flats = round(bore_diameter - 2 * flat_depth, 1)  # ~2.5mm for 3.5mm bore
    wheel_bore = DDCutParams(
        diameter=bore_diameter,
        flat_depth=flat_depth,
        across_flats=across_flats,
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

    # Load base mesh rotation from mesh_alignment JSON (wormgear optimizer output)
    # This is the optimal rotation for Z-aligned axes; will be adjusted for Z-offset in create_default_config
    module = worm_data["module_mm"]
    mesh_alignment = load_mesh_alignment(module, config_dir)
    mesh_rotation_base = mesh_alignment.get("optimal_rotation_deg", 0.0)

    return GearParams(
        worm=worm,
        wheel=wheel,
        center_distance=assembly_data["centre_distance_mm"],
        pressure_angle_deg=assembly_data["pressure_angle_deg"],
        backlash=assembly_data["backlash_mm"],
        ratio=assembly_data["ratio"],
        mesh_rotation_deg=mesh_rotation_base,
        virtual_hobbing=virtual_hobbing,
    )


def create_default_config(
    scale: float = 1.0,
    tolerance: str = "production",
    hand: Hand = Hand.RIGHT,
    gear_json_path: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> BuildConfig:
    """Create a BuildConfig with defaults and optional overrides.

    Derives dependent parameters from gear and component configs:
    - dd_cut_length = wheel.face_width (they are the same)
    - worm_entry_hole = peg_head.shoulder_diameter + BEARING_CLEARANCE
    - peg_bearing_hole = peg_head.shaft_diameter + BEARING_CLEARANCE
    - post_bearing_hole = string_post.bearing_diameter + BEARING_CLEARANCE

    Args:
        scale: Geometry scale factor (1.0 for production, 2.0 for FDM prototype)
        tolerance: Tolerance profile name
        hand: LEFT or RIGHT hand variant
        gear_json_path: Optional path to gear JSON file (defaults to config/worm_gear.json)
        config_dir: Optional config directory for mesh alignment lookup

    Returns:
        Configured BuildConfig instance

    Raises:
        ValueError: If worm tip diameter exceeds entry hole size
    """
    tol_config = get_tolerance(tolerance)

    # Load gear params from JSON (use default if not specified)
    if gear_json_path is None:
        gear_json_path = DEFAULT_GEAR_JSON

    if gear_json_path.exists():
        gear = load_gear_params(gear_json_path, config_dir)
    else:
        # Fallback to hardcoded defaults if JSON not found
        gear = GearParams(worm=WormParams(), wheel=WheelParams())

    # Load tuner config overrides (allows per-gear-config customization)
    tuner_overrides = load_tuner_config(config_dir)
    frame_overrides = tuner_overrides.get("frame", {})
    string_post_overrides = tuner_overrides.get("string_post", {})
    peg_head_overrides = tuner_overrides.get("peg_head", {})

    # Create component params first (needed to derive frame hole sizes)
    # Use default wall_thickness from FrameParams for bearing dimensions
    default_wall = frame_overrides.get("wall_thickness", FrameParams().wall_thickness)

    # Derive StringPostParams - bearing_length must match frame wall_thickness
    # Apply any overrides from tuner_config.json
    string_post_kwargs = {
        "dd_cut": gear.wheel.bore,
        "dd_cut_length": gear.wheel.face_width,
        "bearing_length": default_wall,
    }
    string_post_kwargs.update(string_post_overrides)
    string_post = StringPostParams(**string_post_kwargs)

    # Derive PegHeadParams - bearing_wall must match frame wall_thickness
    # Apply any overrides from tuner_config.json
    peg_head_kwargs = {
        "worm_length": gear.worm.length,
        "bearing_wall": default_wall,
    }
    peg_head_kwargs.update(peg_head_overrides)
    peg_head = PegHeadParams(**peg_head_kwargs)

    # Derive FrameParams with bearing holes from component dimensions + clearance
    # All bearing holes use BEARING_CLEARANCE for tight fit (can be reamed if needed)
    worm_entry_hole = peg_head.shoulder_diameter + BEARING_CLEARANCE
    peg_bearing_hole = peg_head.shaft_diameter + BEARING_CLEARANCE
    post_bearing_hole = string_post.bearing_diameter + BEARING_CLEARANCE

    frame_kwargs = {
        "worm_entry_hole": worm_entry_hole,
        "peg_bearing_hole": peg_bearing_hole,
        "post_bearing_hole": post_bearing_hole,
    }
    frame_kwargs.update(frame_overrides)
    frame = FrameParams(**frame_kwargs)

    # Validate: worm must fit through entry hole during assembly
    if gear.worm.tip_diameter >= worm_entry_hole:
        raise ValueError(
            f"Worm tip diameter ({gear.worm.tip_diameter}mm) must be less than "
            f"worm entry hole ({worm_entry_hole}mm)"
        )

    # Calculate Z-offset correction for mesh rotation
    # The mesh_alignment JSON gives optimal rotation for Z-aligned axes (worm and wheel at same Z).
    # In the actual assembly, the wheel and worm may be at different Z heights, so we need to correct.
    #
    # When worm is aligned with wheel (globoid, virtual_hobbing, or force-aligned),
    # z_offset = 0 and no correction is needed.
    #
    # When worm is centered in frame (cylindrical, no hobbing),
    # we calculate the Z offset and apply helix geometry correction.
    dd_h = string_post.dd_cut_length
    bearing_h = string_post.bearing_length
    face_width = gear.wheel.face_width
    box_outer = frame.box_outer
    lead = gear.worm.lead
    ratio = gear.ratio
    lead_angle_rad = math.radians(gear.worm.lead_angle_deg)

    post_z_offset = -(dd_h + bearing_h)
    wheel_z = post_z_offset + face_width / 2
    worm_z_centered = -box_outer / 2

    # Determine if worm will be aligned with wheel or centered
    # Check mode first, then auto-detect
    worm_z_mode = gear.worm_z_mode
    worm_aligned = (
        worm_z_mode == WormZMode.ALIGNED or
        (worm_z_mode == WormZMode.AUTO and (
            gear.worm.worm_type == WormType.GLOBOID or gear.virtual_hobbing
        ))
    )

    if worm_aligned:
        # Worm and wheel at same Z, no correction needed
        z_offset = 0.0
    else:
        # Worm centered in frame, calculate offset
        z_offset = wheel_z - worm_z_centered

    # Convert Z offset to wheel rotation using lead angle geometry
    effective_axial_shift = z_offset * math.tan(lead_angle_rad)
    z_correction_deg = (effective_axial_shift / lead) * 360.0 / ratio

    # Apply correction to get final mesh rotation
    final_mesh_rotation = gear.mesh_rotation_deg + z_correction_deg

    # Create updated gear params with corrected rotation
    gear = GearParams(
        worm=gear.worm,
        wheel=gear.wheel,
        center_distance=gear.center_distance,
        pressure_angle_deg=gear.pressure_angle_deg,
        backlash=gear.backlash,
        extra_backlash=gear.extra_backlash,
        ratio=gear.ratio,
        mesh_rotation_deg=final_mesh_rotation,
        virtual_hobbing=gear.virtual_hobbing,
        worm_z_mode=gear.worm_z_mode,
    )

    return BuildConfig(
        scale=scale,
        tolerance=tol_config,
        hand=hand,
        gear=gear,
        frame=frame,
        string_post=string_post,
        peg_head=peg_head,
    )
