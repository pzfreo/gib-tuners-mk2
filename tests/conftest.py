"""Pytest configuration and fixtures."""

import json
from pathlib import Path

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gib_tuners.config.defaults import create_default_config, load_gear_params, resolve_gear_config
from gib_tuners.config.parameters import BuildConfig, Hand


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def gear_paths():
    """Return gear config paths (uses balanced config)."""
    return resolve_gear_config("balanced")


@pytest.fixture
def gear_json_path(gear_paths) -> Path:
    """Return path to gear JSON file."""
    return gear_paths.json_path


@pytest.fixture
def config_dir(gear_paths) -> Path:
    """Return path to gear config directory."""
    return gear_paths.config_dir


@pytest.fixture
def reference_dir(project_root: Path) -> Path:
    """Return path to reference files directory."""
    return project_root / "reference"


@pytest.fixture
def default_config(gear_paths) -> BuildConfig:
    """Create a default build configuration (uses balanced gear config)."""
    return create_default_config(
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )


@pytest.fixture
def production_config(gear_paths) -> BuildConfig:
    """Create a production build configuration with gear JSON."""
    return create_default_config(
        scale=1.0,
        tolerance="production",
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )


@pytest.fixture
def prototype_config(gear_paths) -> BuildConfig:
    """Create a 2x prototype configuration."""
    return create_default_config(
        scale=2.0,
        tolerance="prototype_fdm",
        hand=Hand.RIGHT,
        gear_json_path=gear_paths.json_path,
        config_dir=gear_paths.config_dir,
    )
