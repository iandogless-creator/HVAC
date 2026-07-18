# ======================================================================
# HVAC/dev/test_hs37b4_local_section_velocity_override_editor_v1.py
# H-S37-B4 — Explicit local Basic PS section velocity authority editor
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QPushButton

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.project.project_state import ProjectState


SECTION_1 = "leg-001-primary-subleg-section-001"
SECTION_2 = "leg-001-primary-subleg-section-002"
OTHER_SECTION = "leg-002-primary-subleg-section-001"


class _Signal:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def emit(self, *args) -> None:
        self.calls.append(args)


class _Context:
    def __init__(self) -> None:
        self.project_state_changed = _Signal()
        self.project_changed = _Signal()


def _row(
        section_id: str,
        order: int,
        *,
        local_override: float | None,
        effective: float,
        source: str,
) -> dict:
    return {
        "leg_id": "leg-001",
        "subleg_id": "leg-001-primary-subleg",
        "route_id": "leg-001-primary-subleg",
        "route": "Heating Leg 1 / Leg 1A Common subleg",
        "section_id": section_id,
        "order": order,
        "from": "Common main / leg entry" if order == 1 else "L1A-R01",
        "to": "L1A-R01" if order == 1 else "L1A-R02",
        "q_carried": "6200.0 W",
        "flow_kg_s": "0.1483 kg/s",
        "pipe": "15 mm",
        "velocity_m_s": "1.02 m/s",
        "dp_per_m": "1359.4 Pa/m",
        "reynolds_number": "13870",
        "friction_factor": "0.0280",
        "friction_method": "Haaland",
        "colebrook_iterations": "—",
        "length_m": "4.00 m",
        "k_total": "3.50",
        "local_dp": "0.0 Pa",
        "straight_dp": "5437.6 Pa",
        "section_dp": "5437.6 Pa",
        "status": "First-pass evidence",
        "environment_max_velocity_m_s": 1.0,
        "local_max_velocity_override_m_s": local_override,
        "applied_max_velocity_m_s": effective,
        "max_velocity_source": source,
    }


def _test_panel_editor() -> None:
    app = QApplication.instance() or QApplication([])
    panel = HydronicsSchematicPanel()
    payloads: list[dict] = []
    panel.set_basic_ps_section_velocity_override_callback(payloads.append)
    panel.set_proportioning_basic_ps_sections(
        [
            _row(
                SECTION_1,
                1,
                local_override=None,
                effective=1.0,
                source="Environment default",
            ),
            _row(
                SECTION_2,
                2,
                local_override=1.05,
                effective=1.05,
                source="Local section override",
            ),
        ]
    )

    combo = panel._basic_ps_velocity_section_combo
    spin = panel._basic_ps_velocity_override_spin
    assert combo.currentData() == SECTION_1
    assert panel._basic_ps_velocity_section_id_label.text() == SECTION_1
    assert panel._basic_ps_velocity_environment_label.text() == "1.00 m/s"
    assert "inherits Environment" in panel._basic_ps_velocity_effective_label.text()
    assert panel._basic_ps_velocity_clear_button.isEnabled() is False

    spin.setValue(1.05)
    assert payloads == []
    panel._basic_ps_velocity_apply_button.click()
    assert payloads == [
        {
            "action": "set",
            "section_id": SECTION_1,
            "max_velocity_m_s": 1.05,
        }
    ]

    panel._proportioning_basic_ps_sections_table.cellClicked.emit(1, 0)
    assert combo.currentData() == SECTION_2
    assert panel._basic_ps_velocity_clear_button.isEnabled() is True
    assert "Local section override" in panel._basic_ps_velocity_effective_label.text()
    panel._basic_ps_velocity_clear_button.click()
    assert payloads[-1] == {
        "action": "clear",
        "section_id": SECTION_2,
    }

    panel._build_clean_proportioned_table_viewer_v1()
    dialog = panel._clean_proportioned_table_viewer_dialog
    assert dialog.windowTitle() == "Proportioned data viewer — read-only"
    viewer_button_texts = {
        button.text()
        for button in dialog.findChildren(QPushButton)
    }
    assert "Apply to this section" not in viewer_button_texts
    assert "Clear local override — inherit Environment" not in viewer_button_texts
    panel.close()
    app.processEvents()


def _test_adapter_authority_boundary() -> None:
    project = ProjectState(
        project_id="dev-hs37b4-local-velocity-editor",
        name="DEV H-S37-B4 Local Velocity Editor",
    )
    project.hydronics_valid = True
    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1()
    intent = project.basic_hydronic_sizing_intent
    assert intent is not None
    intent.set_section_max_velocity_override(OTHER_SECTION, 0.90)

    context = _Context()
    refresh_calls: list[bool] = []
    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    adapter._project_state = project
    adapter._context = context
    adapter.refresh = lambda *args, **kwargs: refresh_calls.append(True)

    adapter.set_basic_ps_section_velocity_override(
        {
            "action": "set",
            "section_id": SECTION_1,
            "max_velocity_m_s": 1.05,
        }
    )
    assert intent.get_section_max_velocity_override(SECTION_1) == 1.05
    assert intent.get_section_max_velocity_override(OTHER_SECTION) == 0.90
    assert project.hydronics_valid is False

    adapter.set_basic_ps_section_velocity_override(
        {
            "action": "clear",
            "section_id": SECTION_1,
        }
    )
    assert intent.get_section_max_velocity_override(SECTION_1) is None
    assert intent.get_section_max_velocity_override(OTHER_SECTION) == 0.90
    assert len(refresh_calls) == 2
    assert len(context.project_state_changed.calls) == 2
    assert len(context.project_changed.calls) == 2


def main() -> None:
    _test_panel_editor()
    _test_adapter_authority_boundary()
    print(
        "OK — H-S37-B4 local section velocity override editor passed."
    )


if __name__ == "__main__":
    main()
