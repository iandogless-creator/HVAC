from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication
except ImportError:
    QApplication = None

from HVAC.constructions.physics.declared_whole_product_construction_candidate_v1 import (
    build_declared_whole_product_construction_candidate_v1,
)
from HVAC.project.project_state import ProjectState


def main() -> None:
    candidate = build_declared_whole_product_construction_candidate_v1(
        opening_type="WINDOW",
        name="Modern uPVC window",
        declared_u_value_W_m2K=1.4,
        source_kind="manufacturer_declaration",
        source_ref="Example manufacturer declaration",
        source_version="2026",
    )
    assert candidate.ready
    assert candidate.u_value_W_m2K == 1.4
    assert candidate.evidence is not None
    assert candidate.evidence.opening_type == "WINDOW"
    assert candidate.acceptance is not None
    assert candidate.acceptance.accepted

    duplicate = build_declared_whole_product_construction_candidate_v1(
        opening_type="DOOR",
        name="Modern uPVC window",
        declared_u_value_W_m2K=1.6,
        source_kind="product_schedule",
        source_ref="Example schedule",
        existing_constructions={candidate.construction_id: type(
            "Existing", (), {"name": candidate.name}
        )()},
    )
    assert not duplicate.ready
    assert any("already exists" in item for item in duplicate.blockers)

    if QApplication is None:
        panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        adapter_source = Path(
            "HVAC/gui_v3/adapters/uvp_panel_adapter.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "declared_opening_construction_save_requested = Signal(object)",
            '"Declared Window / Door Construction"',
            '"Save declared construction"',
            "def set_declared_opening_save_result",
        ):
            assert marker in panel_source
        assert (
            "build_declared_whole_product_construction_candidate_v1("
            in adapter_source
        )
        print(
            "OK — U-S5E1A declared window/door entry controls and "
            "save handoff passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.adapters.uvp_panel_adapter import UVPPanelAdapter
    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5e1a", name="U-S5E1A")
    project.heatloss_valid = True
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)
    adapter = UVPPanelAdapter(panel=panel, context=context)

    # Reproduce the live MainWindow ordering: a broad project refresh may
    # temporarily project the previously focused construction value.
    context.project_changed.connect(lambda: panel.set_u_value(0.26))

    panel._declared_opening_name.setText("Modern uPVC window")
    panel._declared_opening_u_value.setValue(1.4)
    panel._declared_opening_source_ref.setText(
        "Example manufacturer declaration"
    )
    panel._declared_opening_source_version.setText("2026")
    panel._declared_opening_save_button.click()

    windows = [
        item for item in project.constructions.values()
        if item.name == "Modern uPVC window"
    ]
    assert len(windows) == 1
    window = windows[0]
    assert window.u_value_W_m2K == 1.4
    assert window.declared_whole_product_u_value_evidence["opening_type"] == "WINDOW"
    assert window.declared_whole_product_u_value_acceptance["accepted"] is True
    assert not project.heatloss_valid
    assert "Created" in panel._declared_opening_status.text()
    assert panel._selected_cid == window.construction_id
    assert abs(panel._u_spin.value() - 1.4) < 1.0e-12
    assert "1.400" in panel._u_label.text()

    # Repeated focus must still restore the full UVP projection even when
    # GuiProjectContext correctly suppresses a duplicate focus signal.
    panel._selected_cid = "DEV-EXT-WALL"
    panel.set_u_value(0.26)
    adapter._on_construction_focus(window.construction_id)
    assert panel._selected_cid == window.construction_id
    assert abs(panel._u_spin.value() - 1.4) < 1.0e-12
    assert "1.400" in panel._u_label.text()

    type_index = panel._declared_opening_type.findData("DOOR")
    panel._declared_opening_type.setCurrentIndex(type_index)
    panel._declared_opening_name.setText("Insulated external door")
    panel._declared_opening_u_value.setValue(1.6)
    panel._declared_opening_source_ref.setText("Example door schedule")
    panel._declared_opening_save_button.click()
    doors = [
        item for item in project.constructions.values()
        if item.name == "Insulated external door"
    ]
    assert len(doors) == 1
    assert doors[0].declared_whole_product_u_value_evidence["opening_type"] == "DOOR"

    count = len(project.constructions)
    panel._declared_opening_name.setText("Insulated external door")
    panel._declared_opening_save_button.click()
    assert len(project.constructions) == count
    assert "already exists" in panel._declared_opening_status.text()
    assert adapter is not None

    print(
        "OK — U-S5E1A simple declared window/door entry creates accepted "
        "construction models and refreshes the project atomically."
    )


if __name__ == "__main__":
    main()
