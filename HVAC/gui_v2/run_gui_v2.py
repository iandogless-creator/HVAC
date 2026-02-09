"""
GUI ENTRY POINT (LOCKED)

Rules:
- MUST NOT create ProjectState
- MUST NOT import engines
- MUST NOT own domain state
- GUI wiring only
"""

from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Config loading (GUI-only, ONCE)
# ---------------------------------------------------------------------------

from HVAC_legacy.config.load_config import load_config

# ---------------------------------------------------------------------------
# GUI core
# ---------------------------------------------------------------------------

from HVAC_legacy.gui_v2.main_window_v2 import MainWindowV2
from HVAC_legacy.gui_v2.common.gui_view_state import GuiViewState
from HVAC_legacy.gui_v2.common.theme_manager import ThemeManagerV2


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def run_gui() -> None:
    """
    Canonical GUI v2 startup sequence.
    """

    # ------------------------------------------------------------
    # 1. Load config ONCE
    # ------------------------------------------------------------
    try:
        config = load_config()
    except Exception as exc:
        raise RuntimeError("Failed to load HVACgooee configuration") from exc

    # ------------------------------------------------------------
    # 2. Create QApplication
    # ------------------------------------------------------------
    app = QApplication(sys.argv)
    app.setApplicationName(config.project.name)
    app.setApplicationVersion(config.project.version)

    # ------------------------------------------------------------
    # 3. Apply GLOBAL GUI theme (ONCE)
    # ------------------------------------------------------------
    ThemeManagerV2.apply(app)

    # ------------------------------------------------------------
    # 4. Initialise GUI view state (presentation only)
    # ------------------------------------------------------------
    view_state = GuiViewState()

    # ------------------------------------------------------------
    # 5. Create main window (PROJECT STATE IS OWNED THERE)
    # ------------------------------------------------------------
    main_window = MainWindowV2(
        view_state=view_state,
        theme_manager=None,
        paths=config.paths,
        project_meta=config.project,
    )

    # ------------------------------------------------------------
    # 6. Restore window geometry
    # ------------------------------------------------------------
    if config.ui.remember_window_geometry:
        main_window.restore_geometry()

    main_window.show()

    # ------------------------------------------------------------
    # 7. Enter event loop
    # ------------------------------------------------------------
    exit_code = app.exec()

    # ------------------------------------------------------------
    # 8. Persist geometry on exit
    # ------------------------------------------------------------
    if config.ui.remember_window_geometry:
        main_window.save_geometry()

    sys.exit(exit_code)


if __name__ == "__main__":
    run_gui()
