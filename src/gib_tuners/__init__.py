"""Parametric CAD for historic guitar tuner restoration."""

from .config.parameters import (
    BuildConfig,
    FrameParams,
    GearParams,
    PegHeadParams,
    StringPostParams,
    DDCutParams,
    Hand,
)
from .config.tolerances import ToleranceProfile, TOLERANCE_PROFILES
from .config.defaults import load_gear_params, create_default_config

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
