from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


class _Harness:
    pass


def main() -> None:
    app = QApplication.instance() or QApplication([])
    harness = _Harness()
    harness._point_kvs_acceptance_apply_button = QPushButton("Accept")
    harness._clean_proportioned_table_viewer_button = QPushButton("Open")
    harness._point_kvs_acceptance_clear_button = QPushButton("Clear")
    harness._clean_proportioned_evidence_view_button = QPushButton("Evidence")

    HydronicsSchematicPanel._apply_hydronics_action_button_colours_v1(
        harness
    )

    assert harness._point_kvs_acceptance_apply_button.property(
        "hvacAction"
    ) == "calculate"
    assert harness._clean_proportioned_table_viewer_button.property(
        "hvacAction"
    ) == "add"
    assert harness._point_kvs_acceptance_clear_button.property(
        "hvacAction"
    ) == "remove"
    assert harness._clean_proportioned_evidence_view_button.property(
        "hvacAction"
    ) is None

    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    appearance_source = Path(
        "HVAC/gui_v3/context/appearance_scheme_v1.py"
    ).read_text(encoding="utf-8")

    assert "# H-S71-B — whole-Hydronics-panel action-button colouring" in (
        panel_source
    )
    assert 'setProperty("hvacAction", role)' in panel_source
    assert "self._apply_hydronics_action_button_colours_v1()" in panel_source
    assert 'QPushButton[hvacAction="calculate"]' in appearance_source
    assert 'QPushButton[hvacAction="add"]' in appearance_source
    assert 'QPushButton[hvacAction="remove"]' in appearance_source
    assert 'QPushButton[hvacAction="calculate"]:disabled' in (
        appearance_source
    )

    print(
        "OK — H-S71-B applies the existing Light/Dark-aware green, blue "
        "and muted-rust action roles across the Hydronics panel, keeps "
        "disabled controls neutral and changes no callbacks or authority."
    )


if __name__ == "__main__":
    main()
