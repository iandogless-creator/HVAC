from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.context.appearance_scheme_v1 import (
    appearance_tokens_v1,
    application_stylesheet_v1,
)


def main() -> None:
    for scheme in ("light", "dark"):
        tokens = appearance_tokens_v1(scheme)
        stylesheet = application_stylesheet_v1(scheme)
        focus_selector = 'QDockWidget[hvacPanelFocus="active"]'
        title_selector = f"{focus_selector}::title"
        assert focus_selector in stylesheet
        assert title_selector in stylesheet
        assert f"border: 3px solid {tokens.panel_focus_border};" in stylesheet
        assert f"background: {tokens.panel_focus_fill};" in stylesheet
        assert f"color: {tokens.panel_focus_text};" in stylesheet
        assert stylesheet.index(focus_selector) > stylesheet.index(
            'QDockWidget[hvacPanelCategory="helper_input"]'
        )

    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert "def _update_active_dock_focus_v1" in source
    assert 'dock.setProperty("hvacPanelFocus", "active")' in source
    assert 'previous.setProperty("hvacPanelFocus", "")' in source
    assert 'd.setProperty("hvacPanelFocus", "")' in source
    assert "style.unpolish(dock)" in source
    assert "style.polish(dock)" in source
    assert "QEvent.FocusIn" in source
    assert "QEvent.MouseButtonPress" in source
    assert "QEvent.WindowActivate" in source
    assert "ProjectState" not in source[
        source.index("    def _refresh_dock_focus_style_v1"):
        source.index("    # ESC handling")
    ]

    print(
        "OK — H-S69-B3J1B keeps two scheme-aware idle panel families "
        "and transfers one pale-orange focus frame between dock panels "
        "without persistence or engineering mutation."
    )


if __name__ == "__main__":
    main()
