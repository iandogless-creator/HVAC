from __future__ import annotations

from HVAC.gui_v3.context.appearance_scheme_v1 import (
    appearance_tokens_v1,
    application_palette_v1,
    application_stylesheet_v1,
)
from PySide6.QtGui import QPalette


def _rule_body(stylesheet: str, selector: str) -> str:
    marker = selector + " {"
    assert stylesheet.count(marker) == 1
    return stylesheet.split(marker, 1)[1].split("}", 1)[0]


def main() -> None:
    for scheme in ("light", "dark"):
        tokens = appearance_tokens_v1(scheme)
        stylesheet = application_stylesheet_v1(scheme)
        palette = application_palette_v1(scheme)

        assert tokens.panel_focus_text == "#202326"
        assert (
            palette.color(QPalette.ColorRole.HighlightedText).name()
            == tokens.panel_focus_text
        )

        active_dock = _rule_body(
            stylesheet,
            'QDockWidget[hvacPanelFocus="active"]',
        )
        active_title = _rule_body(
            stylesheet,
            'QDockWidget[hvacPanelFocus="active"]::title',
        )
        selection_anchor = "QTableWidget::item:selected:!active,"
        assert stylesheet.count(selection_anchor) == 1
        selected_items = stylesheet.split(
            selection_anchor, 1
        )[1].split("}", 1)[0]

        dark_foreground = f"color: {tokens.panel_focus_text};"
        assert dark_foreground in active_dock
        assert dark_foreground in active_title
        assert dark_foreground in selected_items

    print(
        "OK — H-S72-A3D applies dark text to active dock titles and all "
        "orange selection highlights in Light and Dark schemes."
    )


if __name__ == "__main__":
    main()
