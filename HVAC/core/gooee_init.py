"""
Module 64 — Directory Structure Initialiser
===========================================

Provides:
    • create_standard_structure(base_path)
    • ensure_gooee_environment()
    • create_default_config()

This ensures all required folders exist for HVACgooee to run,
including data/, config/, assets/, logs/, projects/.

"""

from __future__ import annotations

import os
import json
from typing import Dict


# ---------------------------------------------------------------
# Standard Folder Layout
# ---------------------------------------------------------------

STANDARD_DIRS = {
    "data": [
        "materials",
        "pump_curves",
        "images",
        "examples",
    ],
    "config": [],
    "assets": [
        "icons",
        "templates",
    ],
    "logs": [],
    "projects": [],
}


DEFAULT_SETTINGS = {
    "version": "0.1",
    "units": "metric",
    "default_velocity_limit": 1.0,
    "default_dp_per_m": 200,
}

DEFAULT_THEME = {
    "name": "gooee_default",
    "background": "#2c2c2c",
    "panel_bg": "#333333",
    "text": "#ffffff",
    "accent": "#4aa3ff",
}


# ---------------------------------------------------------------
# Core Initialiser
# ---------------------------------------------------------------

def create_standard_structure(base_path: str) -> None:
    """
    Create the full directory tree under base_path.

    Example:
        create_standard_structure("/home/user/HVACgooee")
    """

    for main_dir, sub_dirs in STANDARD_DIRS.items():
        main_path = os.path.join(base_path, main_dir)
        os.makedirs(main_path, exist_ok=True)

        for sub in sub_dirs:
            os.makedirs(os.path.join(main_path, sub), exist_ok=True)


def create_default_config(config_path: str) -> None:
    """
    Create default settings.json and themes.json if missing.
    """

    settings_file = os.path.join(config_path, "settings.json")
    theme_file = os.path.join(config_path, "themes.json")

    if not os.path.exists(settings_file):
        with open(settings_file, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)

    if not os.path.exists(theme_file):
        with open(theme_file, "w") as f:
            json.dump(DEFAULT_THEME, f, indent=2)


# ---------------------------------------------------------------
# Environment bootstrap
# ---------------------------------------------------------------

def ensure_gooee_environment(base_path: str) -> None:
    """
    Ensure the entire HVACgooee environment exists.
    Creates folders + default config + empty log file.
    """

    create_standard_structure(base_path)

    config_path = os.path.join(base_path, "config")
    create_default_config(config_path)

    # create empty log file
    log_file = os.path.join(base_path, "logs", "gooee.log")
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("HVACgooee Log Start\n")

    # create projects directory
    projects_path = os.path.join(base_path, "projects")
    os.makedirs(projects_path, exist_ok=True)


# ---------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------

def init_new_workspace(path: str) -> None:
    """
    Create a new Gooee workspace at the specified path.

    Example:
        gooee init /home/user/HVACgooee
    """
    ensure_gooee_environment(path)
    print(f"New HVACgooee workspace created at: {path}")
