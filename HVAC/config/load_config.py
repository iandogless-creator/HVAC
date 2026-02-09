"""
load_config.py
--------------

HVACgooee — Global Configuration Loader (v1)

Responsibilities (LOCKED)
-------------------------
- Load application configuration ONCE at startup
- Return an immutable config object
- Perform no calculations
- No GUI imports
- No engine imports

This module is allowed to read:
- files
- environment variables (later)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# ============================================================================
# Config data models (IMMUTABLE)
# ============================================================================

@dataclass(frozen=True, slots=True)
class ProjectConfig:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class UIConfig:
    default_mode: str
    theme: str
    remember_window_geometry: bool


@dataclass(frozen=True, slots=True)
class PathsConfig:
    project_root: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """
    Root immutable configuration object.
    """

    project: ProjectConfig
    ui: UIConfig
    paths: PathsConfig


# ============================================================================
# Loader
# ============================================================================

def load_config() -> AppConfig:
    """
    Load HVACgooee configuration.

    v1 behaviour:
    - hard-coded defaults
    - file/env support can be added later
    """

    project = ProjectConfig(
        name="HVACgooee",
        version="v2-dev",
    )

    ui = UIConfig(
        default_mode="comfort",
        theme="dark",
        remember_window_geometry=False,
    )

    paths = PathsConfig(
        project_root=Path.cwd(),
    )

    return AppConfig(
        project=project,
        ui=ui,
        paths=paths,
    )
