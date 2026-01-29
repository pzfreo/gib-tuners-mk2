"""Configuration dataclasses and parameter definitions."""

from .parameters import (
    BuildConfig,
    FrameParams,
    GearParams,
    PegHeadParams,
    StringPostParams,
    DDCutParams,
    Hand,
)
from .tolerances import ToleranceProfile, TOLERANCE_PROFILES
from .defaults import load_gear_params, create_default_config

__all__ = [
    "BuildConfig",
    "FrameParams",
    "GearParams",
    "PegHeadParams",
    "StringPostParams",
    "DDCutParams",
    "Hand",
    "ToleranceProfile",
    "TOLERANCE_PROFILES",
    "load_gear_params",
    "create_default_config",
]
