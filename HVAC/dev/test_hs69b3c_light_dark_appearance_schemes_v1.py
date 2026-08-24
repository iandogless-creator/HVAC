from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.context.appearance_scheme_v1 import (
    appearance_tokens_v1,
    application_palette_v1,
    application_stylesheet_v1,
)
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.panels.heat_loss_panel import HeatLossPanelV3
from HVAC.gui_v3.panels.room_tree_panel import RoomTreePanel


def _method_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Method not found: {name}")


def main() -> None:
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        settings = GuiSettings(settings_dir)
        assert settings.appearance_scheme_v1() == "light"
        assert not settings.set_appearance_scheme_v1("unknown")
        assert settings.set_appearance_scheme_v1("dark")
        settings.save()

        path = settings_dir / "gui_v3_workspace.json"
        stored = json.loads(path.read_text(encoding="utf-8"))
        assert stored["appearance_scheme_v1"] == "dark"
        restored = GuiSettings(settings_dir)
        assert restored.appearance_scheme_v1() == "dark"

        stored["appearance_scheme_v1"] = "invalid"
        path.write_text(json.dumps(stored), encoding="utf-8")
        assert GuiSettings(settings_dir).appearance_scheme_v1() == "light"

    light = application_palette_v1("light")
    dark = application_palette_v1("dark")
    assert light.color(QPalette.ColorRole.Window) != dark.color(
        QPalette.ColorRole.Window
    )
    for scheme in ("light", "dark"):
        tokens = appearance_tokens_v1(scheme)
        stylesheet = application_stylesheet_v1(scheme)
        assert "QDockWidget" in stylesheet
        assert 'QPushButton[hvacAction="calculate"]' in stylesheet
        assert 'QPushButton[hvacAction="add"]' in stylesheet
        assert 'QPushButton[hvacAction="remove"]' in stylesheet
        assert f"background: {tokens.panel_focus_fill}" in stylesheet
        assert f"color: {tokens.panel_focus_text}" in stylesheet

    app = QApplication.instance() or QApplication([])
    heat_loss = HeatLossPanelV3()
    rooms = RoomTreePanel()
    assert heat_loss._run_button.property("hvacAction") == "calculate"
    assert heat_loss._add_room_btn.property("hvacAction") == "add"
    assert heat_loss._remove_room_btn.property("hvacAction") == "remove"
    assert heat_loss._run_button.minimumWidth() == 96
    assert heat_loss._run_button.text() == "Calculate"
    assert heat_loss._run_button.toolTip() == "Calculate Heat-Loss"
    assert heat_loss._add_room_btn.minimumWidth() == 96
    assert heat_loss._remove_room_btn.minimumWidth() == 96
    heat_loss.close()
    rooms.close()
    app.processEvents()

    main_source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    assert 'view_menu.addMenu("Appearance")' in main_source
    assert "QActionGroup" in main_source
    apply_scheme = _method_source(main_source, "_apply_appearance_scheme_v1")
    assert "setPalette" in apply_scheme
    assert "setStyleSheet" in apply_scheme
    assert "set_appearance_scheme_v1" in apply_scheme
    assert "project_state" not in apply_scheme

    heat_source = Path(
        "HVAC/gui_v3/panels/heat_loss_panel.py"
    ).read_text(encoding="utf-8")
    heat_build = _method_source(heat_source, "_build_ui")
    assert "QHBoxLayout" in heat_source
    assert "action_row.addStretch" in heat_build
    assert "run_requested" not in heat_build

    room_source = Path(
        "HVAC/gui_v3/panels/room_tree_panel.py"
    ).read_text(encoding="utf-8")
    room_build = _method_source(room_source, "_build_ui")
    assert "_remove_room_btn" not in room_build
    assert "room_remove_requested" not in room_build

    print(
        "OK — H-S69-B3C persists restrained Light/Dark GUI appearance, "
        "keeps orange focus semantics, adds subtle dock borders and tidies "
        "the Heat-Loss and Rooms action buttons without engineering mutation."
    )


if __name__ == "__main__":
    main()
