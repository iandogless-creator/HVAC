from __future__ import annotations

from types import MethodType

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


class _PanelSurface:
    pass


def main() -> None:
    app = QApplication.instance() or QApplication([])
    surface = _PanelSurface()
    surface._commit_proportioning_button = QPushButton()
    surface._return_arrangement_acceptance_status_label = QLabel()
    surface._refresh_commit_proportioning_status_label_v1 = MethodType(
        HydronicsSchematicPanel._refresh_commit_proportioning_status_label_v1,
        surface,
    )

    blocker = (
        "Blocked — H-S48-D point disposition evidence required; "
        "current H-S47-C/H-S48-C evidence must be reviewed"
    )
    HydronicsSchematicPanel.set_commit_proportioning_ready(
        surface,
        ready=False,
        reason=blocker,
    )
    HydronicsSchematicPanel.set_commit_proportioning_committed(
        surface,
        committed=True,
    )

    assert not surface._commit_proportioning_button.isEnabled()
    assert surface._commit_proportioning_button.text() == (
        "Recommit Proportioning"
    )
    assert surface._commit_proportioning_button.toolTip() == blocker
    visible = surface._return_arrangement_acceptance_status_label.text()
    assert "Recommit Proportioning is blocked." in visible
    assert blocker in visible

    HydronicsSchematicPanel.set_commit_proportioning_ready(
        surface,
        ready=True,
    )
    assert surface._commit_proportioning_button.isEnabled()
    assert "ready to recommit" in (
        surface._return_arrangement_acceptance_status_label.text().lower()
    )

    print(
        "OK — H-S70-B2C keeps the exact commit/recommit readiness blocker "
        "persistently visible for inspection and screenshots without changing "
        "the readiness gate or engineering authority."
    )


if __name__ == "__main__":
    main()
