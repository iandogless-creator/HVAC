# ======================================================================
# HVACgooee — GUI v3 Runner
# ======================================================================

import sys

from PySide6.QtWidgets import QApplication

from HVAC_legacy.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC_legacy.gui_v3.context.gui_project_context import GuiProjectContext
from HVAC_legacy.gui_v3.main_window import MainWindowV3


def main() -> None:
    app = QApplication(sys.argv)

    # --------------------------------------------------------------
    # Project creation is NOT a GUI concern
    # --------------------------------------------------------------
    project = ProjectFactoryV3.create_empty()

    # --------------------------------------------------------------
    # GUI-facing context (opaque authority boundary)
    # --------------------------------------------------------------
    context = GuiProjectContext(
        project_state=project
    )

    # --------------------------------------------------------------
    # Main window (observer only)
    # --------------------------------------------------------------
    win = MainWindowV3(context)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
