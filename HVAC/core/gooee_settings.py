"""
Module 66 — Global Settings Manager
==================================

Provides a single access point for all Gooee settings.

Backed by:
    config/hvacgooee_config.toml

Integrates with:
    - GUI (Preferences window)
    - Theme manager
    - Solvers and exports
"""

from __future__ import annotations
import os
from typing import Any, Dict
import tomllib

def _load(self):
    cfg = os.path.join(self.config_dir, "hvacgooee_config.toml")
    with open(cfg, "rb") as f:
        self._settings = tomllib.load(f)

# NOTE:
# This module assumes TOML loading has already populated
# self._settings as a nested dict.


class GooeeSettings:
    """
    Singleton-style global settings manager.
    """

    def __init__(self, base_path: str):
        self.base_path = base_path
        self.config_dir = os.path.join(base_path, "config")

        # Loaded settings dict (from TOML)
        self._settings: Dict[str, Any] = {}

        self._load()

    # ------------------------------------------------------------
    # Internal loader
    # ------------------------------------------------------------

    def _load(self):
        """
        Load settings from hvacgooee_config.toml.
        """
        import tomllib
        cfg_path = os.path.join(self.config_dir, "hvacgooee_config.toml")

        if not os.path.exists(cfg_path):
            raise FileNotFoundError(
                f"Missing config file: {cfg_path}"
            )

        with open(cfg_path, "rb") as f:
            self._settings = tomllib.load(f)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value

    # ------------------------------------------------------------
    # Theme access (THE ONLY THEME API)
    # ------------------------------------------------------------

    def theme(self, name: str | None = None) -> dict:
        ui = self._settings.get("ui", {})
        theme_name = name or ui.get("theme", "gooee_dark_brown")

        themes = self._settings.get("themes")
        if not isinstance(themes, dict):
            raise RuntimeError(
                f"No [themes] table found in hvacgooee_config.toml. "
                f"Loaded keys: {list(self._settings.keys())}"
            )

        theme = themes.get(theme_name)
        if not isinstance(theme, dict):
            raise RuntimeError(
                f"Theme '{theme_name}' not found. Available themes: {list(themes.keys())}"
            )

        return theme


# ------------------------------------------------------------
# Global Singleton Accessor
# ------------------------------------------------------------

_settings_instance: GooeeSettings | None = None


def settings() -> GooeeSettings:
    """
    Access the global GooeeSettings singleton.
    """
    global _settings_instance
    if _settings_instance is None:
        from pathlib import Path

        base = Path(__file__).resolve().parents[1]
        _settings_instance = GooeeSettings(str(base))

    return _settings_instance
