from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.context.appearance_scheme_v1 import (
    appearance_tokens_v1,
    application_stylesheet_v1,
)
from HVAC.gui_v3.context.panel_category_v1 import (
    PANEL_CATEGORY_BY_DOCK_ID_V1,
    panel_category_for_dock_id_v1,
)


EXPECTED = {
    "dock_project": "main_readonly",
    "dock_rooms": "main_readonly",
    "dock_heat_loss": "main_readonly",
    "dock_education": "main_readonly",
    "dock_basic_hydronics": "main_readonly",
    "dock_hydronics": "main_readonly",
    "dock_environment": "helper_input",
    "dock_geometry": "helper_input",
    "dock_ach": "helper_input",
    "dock_construction": "helper_input",
    "dock_uvp": "helper_input",
    "dock_hydronic_control": "helper_input",
    "dock_topology_arranger": "helper_input",
    "dock_local_k": "helper_input",
    "dock_dev": "helper_input",
}


def main() -> None:
    assert PANEL_CATEGORY_BY_DOCK_ID_V1 == EXPECTED
    for dock_id, category in EXPECTED.items():
        assert panel_category_for_dock_id_v1(dock_id) == category
    assert panel_category_for_dock_id_v1("dock_unknown") is None
    assert panel_category_for_dock_id_v1(None) is None

    colour_fields = {
        "main_readonly": (
            "category_main_border",
            "category_main_title",
        ),
        "helper_input": (
            "category_helper_border",
            "category_helper_title",
        ),
    }
    for scheme in ("light", "dark"):
        tokens = appearance_tokens_v1(scheme)
        stylesheet = application_stylesheet_v1(scheme)
        for category, fields in colour_fields.items():
            border_field, title_field = fields
            dock_selector = (
                f'QDockWidget[hvacPanelCategory="{category}"]'
            )
            title_selector = f"{dock_selector}::title"
            border_colour = getattr(tokens, border_field)
            title_colour = getattr(tokens, title_field)
            assert dock_selector in stylesheet
            assert title_selector in stylesheet
            assert f"border: 2px solid {border_colour};" in stylesheet
            assert f"background: {title_colour};" in stylesheet
            assert f"color: {tokens.text};" in stylesheet

        # Accepted action and current-focus semantics stay independent.
        assert 'QPushButton[hvacAction="calculate"]' in stylesheet
        assert 'QPushButton[hvacAction="add"]' in stylesheet
        assert 'QPushButton[hvacAction="remove"]' in stylesheet
        assert (
            f"background: {tokens.panel_focus_fill};" in stylesheet
        )

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert 'd.setProperty("hvacPanelCategory", category)' in source
    assert 'widget.setProperty("hvacPanelCategory", category)' in source
    for dock_id in EXPECTED:
        assert f'"{dock_id}"' in source
    assert "ProjectState" not in Path(
        "HVAC/gui_v3/context/panel_category_v1.py"
    ).read_text(encoding="utf-8")

    print(
        "OK — H-S69-B3J1 assigns fixed GUI-only categories to all 15 "
        "main and helper dock-panel families, renders scheme-specific "
        "idle accents and preserves action and focus semantics."
    )


if __name__ == "__main__":
    main()
