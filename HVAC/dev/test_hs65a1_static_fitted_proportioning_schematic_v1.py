# ======================================================================
# H-S65-A1 — Static fitted Proportioning schematic
# ======================================================================

from __future__ import annotations

import ast
from pathlib import Path


PANEL_PATH = Path("HVAC/gui_v3/panels/hydronics_schematic_panel.py")
WIDGET_PATH = Path(
    "HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py"
)


def _method_source(source: str, method_name: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return "".join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError(f"Method not found: {method_name}")


def main() -> None:
    panel = PANEL_PATH.read_text(encoding="utf-8")
    widget = WIDGET_PATH.read_text(encoding="utf-8")

    # Only the original Proportioning instance is explicitly hover-disabled.
    assert panel.count("set_hover_enabled_v1(") == 1
    assert (
        "_common_main_leg_subleg_schematic_widget.set_hover_enabled_v1("
        in panel
    )
    clean_window = panel[
        panel.index("_clean_proportioned_common_main_leg_subleg_schematic_widget"):
        panel.index("_clean_proportioned_section_view_controls")
    ]
    assert "set_hover_enabled_v1(False)" not in clean_window

    # Proportioning fits its calculated canvas; Proportioned scrolling remains.
    proportioning_window = panel[
        panel.index("# H-S19-K — DEV common-main / leg / subleg drawn schematic"):
        panel.index("# H-S19-N-A — Current proportioning focus summary")
    ]
    assert "Qt.ScrollBarAlwaysOff" in proportioning_window
    assert "Qt.ScrollBarAsNeeded" not in proportioning_window.split(
        "setVerticalScrollBarPolicy", 1
    )[1]
    clean_window = panel[
        panel.index("# H-S34-B — separate clean Proportioned schematic"):
        panel.index("_clean_proportioned_section_view_controls")
    ]
    assert "Qt.ScrollBarAsNeeded" in clean_window

    fit_source = _method_source(
        panel,
        "_fit_proportioning_schematic_viewport_v1",
    )
    assert "widget.minimumHeight()" in fit_source
    assert "horizontalScrollBar().sizeHint().height()" in fit_source
    assert "setFixedHeight(" in fit_source
    setter = _method_source(panel, "set_common_main_leg_subleg_schematic")
    assert setter.index("set_schematic(") < setter.index(
        "_fit_proportioning_schematic_viewport_v1()"
    )

    hover_control = _method_source(widget, "set_hover_enabled_v1")
    assert "self.setMouseTracking(self._hover_enabled_v1)" in hover_control
    assert "QToolTip.hideText()" in hover_control
    mouse_move = _method_source(widget, "mouseMoveEvent")
    assert "if not self._hover_enabled_v1:" in mouse_move
    assert mouse_move.index("if not self._hover_enabled_v1:") < (
        mouse_move.index("event.position()")
    )
    assert "ProjectState" not in hover_control
    assert "ProjectState" not in fit_source

    print(
        "OK — H-S65-A1 static fitted Proportioning schematic and "
        "Proportioned-only hover passed."
    )


if __name__ == "__main__":
    main()
