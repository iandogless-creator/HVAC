from __future__ import annotations

from pathlib import Path

from HVAC.education.resolver import resolve
from HVAC.education.workspace_guidance_v1 import (
    EDUCATION_MODES_V1,
    PANEL_TOPIC_BY_DOCK_ID_V1,
    education_topic_for_dock_id_v1,
)


def main() -> None:
    assert education_topic_for_dock_id_v1("dock_education") == "education"
    assert education_topic_for_dock_id_v1("unknown") is None
    assert education_topic_for_dock_id_v1("dock_heat_loss") == "heat_loss"
    assert education_topic_for_dock_id_v1("dock_environment") == "environment"

    for dock_id, topic in PANEL_TOPIC_BY_DOCK_ID_V1.items():
        assert education_topic_for_dock_id_v1(dock_id) == topic
        for mode in EDUCATION_MODES_V1:
            title, body = resolve(
                domain="workspace",
                topic=topic,
                mode=mode,
            )
            assert title != "Education"
            assert "No education content" not in body
            assert body.count("Next:") == 1
            assert 100 <= len(body) <= 900

    for mode in EDUCATION_MODES_V1:
        title, body = resolve(
            domain="workspace",
            topic="education",
            mode=mode,
        )
        assert title == f"Programme Help — {mode.title()}"
        assert "Next: Select the panel you want explained." in body

    adapter_source = Path(
        "HVAC/gui_v3/adapters/education_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "if domain == self._domain and topic == self._topic" in adapter_source

    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    assert "def _update_education_from_event_object_v1" in main_source
    assert "QEvent.FocusIn" in main_source
    assert "QEvent.MouseButtonPress" in main_source
    assert "QEvent.WindowActivate" in main_source
    assert "education_topic_for_dock_id_v1" in main_source
    assert "redirect_unsafe_input_wheel_event_v1(obj, event)" in main_source
    assert "event.key() == Qt.Key_Escape" in main_source

    print(
        "OK — H-S69-B3I1 Education follows the focused recognised panel "
        "in docked, exploded and user workspaces, includes concise "
        "programme self-help and preserves ESC and wheel-input handling."
    )


if __name__ == "__main__":
    main()
