from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from HVAC.education.resolver import resolve
from HVAC.education.workspace_guidance_v1 import EDUCATION_MODES_V1
from HVAC.gui_v3.adapters.education_panel_adapter import EducationPanelAdapter
from HVAC.gui_v3.panels.education_panel import EducationPanel


def main() -> None:
    view_ids = (
        "heat_loss",
        "building_edit",
        "openings",
        "hydronics_setup",
        "basic_sizing",
        "proportioning",
        "results",
        "user",
    )
    assert EDUCATION_MODES_V1 == ("beginner", "standard", "classical")
    for view_id in view_ids:
        bodies = []
        for mode in EDUCATION_MODES_V1:
            title, body = resolve(
                domain="workspace",
                topic=view_id,
                mode=mode,
            )
            assert title != "Education"
            assert "No education content" not in body
            assert body.count("Next:") == 1
            assert 120 <= len(body) <= 900
            bodies.append(body)
        assert len(set(bodies)) == 3

    # Original flat Education v1 dictionaries remain readable.
    legacy_title, legacy_body = resolve(
        domain="heatloss",
        topic="overview",
        mode="standard",
    )
    assert legacy_title == "Heat Loss — Education"
    assert "No education content" not in legacy_body

    app = QApplication.instance() or QApplication([])
    panel = EducationPanel()
    adapter = EducationPanelAdapter(
        panel=panel,
        domain="workspace",
        topic="heat_loss",
        mode="standard",
    )
    assert panel._btn_standard.isChecked()
    panel._btn_beginner.click()
    assert panel._btn_beginner.isChecked()
    assert "Beginner" in panel._title.text()
    panel._btn_classical.click()
    assert panel._btn_classical.isChecked()
    assert "ΣQf" in panel._body.toPlainText()

    adapter.set_topic(domain="workspace", topic="openings")
    assert panel._title.text().startswith("Openings")

    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    assert 'education.set_topic(domain="workspace", topic=view_id)' in main_source
    assert 'domain="workspace"' in main_source
    assert 'topic="heat_loss"' in main_source

    panel.close()
    app.processEvents()
    print(
        "OK — H-S69-B3I provides compact Beginner, Standard and Classical "
        "Education that follows all docked, exploded and user workspaces, "
        "while preserving legacy read-only topics and engineering authority."
    )


if __name__ == "__main__":
    main()
