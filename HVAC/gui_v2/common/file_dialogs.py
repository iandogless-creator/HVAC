"""
file_dialogs.py
---------------

HVACgooee — GUI File Dialog Utilities (v3)

Purpose
-------
Provide GUI-only file dialogs for selecting project files.

Design Rules (LOCKED)
---------------------
✔ GUI concerns only
✔ Returns file paths, never data
✔ No JSON parsing
✔ No project loading
✔ No validation
✔ No physics
✔ No side effects

This module is intentionally simple and stable.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QFileDialog, QWidget


# ---------------------------------------------------------------------
# Project File Dialogs
# ---------------------------------------------------------------------

def open_project_file(parent: QWidget | None = None) -> Optional[str]:
    """
    Show an 'Open Project' file dialog.

    Returns
    -------
    str | None
        Absolute path to selected .hvac.json file,
        or None if the user cancels.
    """

    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Open HVACgooee Project",
        "",
        "HVACgooee Project (*.hvac.json);;All Files (*)",
    )

    if not file_path:
        return None

    return file_path


def save_project_file(parent: QWidget | None = None) -> Optional[str]:
    """
    Show a 'Save Project' file dialog.

    NOTE:
    -----
    This returns a path only.
    Actual saving is handled elsewhere (v3 assembly / IO layer).

    Returns
    -------
    str | None
        Absolute path to target .hvac.json file,
        or None if the user cancels.
    """

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save HVACgooee Project",
        "",
        "HVACgooee Project (*.hvac.json);;All Files (*)",
    )

    if not file_path:
        return None

    # Enforce extension gently (GUI responsibility only)
    if not file_path.endswith(".hvac.json"):
        file_path += ".hvac.json"

    return file_path

# ---------------------------------------------------------------------
# Project Directory Dialogs
# ---------------------------------------------------------------------

# ======================================================================
# HVAC/gui_v2/common/file_dialogs.py
# ======================================================================

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QWidget


def open_project_directory(parent: QWidget | None = None) -> Optional[str]:
    """
    Select an HVACgooee project directory.

    Canonical location:
        HVAC/HVACprojects/
    """

    # 🔒 CANONICAL ROOT (explicit, not inferred)
    base_dir = Path(
        "//HVACprojects"
    )

    # Defensive: ensure it exists
    if not base_dir.is_dir():
        base_dir = Path.home()

    path = QFileDialog.getExistingDirectory(
        parent,
        "Open HVACgooee Project",
        str(base_dir),
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
    )

    return path or None
