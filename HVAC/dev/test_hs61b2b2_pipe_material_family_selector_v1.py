# ======================================================================
# H-S61-B2B2 — Pipe Resizing material-family selector and handoff
# ======================================================================

from __future__ import annotations

import inspect
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.dev.test_hs61f_proportioned_pipe_resizing_schedule_acceptance_v1 import (
    _projection,
)
from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.project.project_state import ProjectState


class _Signal:
    def __init__(self) -> None:
        self.emissions = 0

    def emit(self, *_args) -> None:
        self.emissions += 1


def main() -> None:
    app = QApplication.instance() or QApplication([])
    assert app is not None

    panel = HydronicsSchematicPanel()
    payloads: list[dict] = []
    panel.set_proportioned_pipe_material_family_callback_v1(
        payloads.append
    )
    panel.set_proportioned_pipe_material_family_state_v1(
        current_material_key="copper",
        current_material_label="Copper EN1057",
        proposed_material_key="mlcp",
        proposed_material_label="MLCP",
    )
    combo = panel._proportioned_pipe_material_family_combo_v1
    assert combo.currentData() == "mlcp"
    assert "Copper EN1057" in (
        panel._proportioned_pipe_current_material_label_v1.text()
    )
    assert "MLCP" in (
        panel._proportioned_pipe_material_family_status_label_v1.text()
    )
    assert combo.findData("copper") >= 0
    assert combo.findData("mlcp") >= 0
    assert combo.findData("pex") >= 0
    assert combo.findData("steel") >= 0
    assert combo.findData("pvc") < 0

    combo.setCurrentIndex(combo.findData("pex"))
    assert payloads == [
        {
            "action": "set_proposed",
            "material_key": "pex",
        }
    ]

    project = ProjectState(project_id="hs61b2b2", name="H-S61-B2B2")
    signal = _Signal()
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._context = SimpleNamespace(project_state_changed=signal)
    refreshes: list[bool] = []
    adapter.refresh = lambda: refreshes.append(True)

    adapter.set_proportioned_pipe_material_family_v1(
        {
            "action": "set_proposed",
            "material_key": "mlcp",
        }
    )
    intent = project.hydronic_proportioned_pipe_material_family_intent
    assert intent.current_material_key == "copper"
    assert intent.proposed_material_key == "mlcp"
    assert refreshes == [True]
    assert signal.emissions == 1

    rows = adapter._build_resized_pipe_section_review_rows_v1(
        _projection()
    )
    assert rows
    assert all("Copper EN1057" in row["current_pipe"] for row in rows)
    assert all("Copper EN1057" in row["projected_pipe"] for row in rows)
    assert all("ID " in row["current_pipe"] for row in rows)
    assert all("ID " in row["projected_pipe"] for row in rows)

    panel_handler_source = inspect.getsource(
        HydronicsSchematicPanel
        ._on_proportioned_pipe_material_family_changed_v1
    )
    adapter_handler_source = inspect.getsource(
        HydronicsSchematicPanelAdapter
        .set_proportioned_pipe_material_family_v1
    )
    assert "ProjectState" not in panel_handler_source
    assert "set_proposed_material_family" in adapter_handler_source
    assert "current_material_key" not in panel_handler_source
    assert "current_material_key =" not in adapter_handler_source

    panel.close()
    print(
        "OK — H-S61-B2B2 Pipe Resizing material-family selector, "
        "persistence handoff and material/bore review passed."
    )


if __name__ == "__main__":
    main()
