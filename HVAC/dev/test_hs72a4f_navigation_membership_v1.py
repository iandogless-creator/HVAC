from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow

from HVAC.gui_v3.context.appearance_scheme_v1 import application_stylesheet_v1
from HVAC.gui_v3.context.gui_settings import GuiSettings
from HVAC.gui_v3.context.workspace_view_definition_v2 import (
    default_workspace_views_v2, normalise_workspace_views_v2,
)
from HVAC.gui_v3.panels.workspace_navigation_panel_v1 import WorkspaceNavigationPanelV1
from HVAC.gui_v3.widgets.workspace_view_manager_dialog_v2 import WorkspaceViewManagerDialogV2


def main() -> None:
    app = QApplication.instance() or QApplication([])

    def settle() -> None:
        for _ in range(8):
            app.processEvents()

    with TemporaryDirectory(prefix="hvac-navigation-membership-") as temporary:
        root = Path(temporary)
        legacy = default_workspace_views_v2()
        for view in legacy:
            view.pop("in_navigation")
        (root / "gui_v3_workspace.json").write_text(json.dumps({"workspace_views_v2": legacy}))
        settings = GuiSettings(root)
        assert {v["view_id"] for v in settings.workspace_views_v2() if v["in_navigation"]} == {
            "building_edit", "heat_loss", "basic_sizing", "proportioning", "results",
        }
        malformed = [{**legacy[0], "in_navigation": "false"}]
        assert normalise_workspace_views_v2(malformed)[0]["in_navigation"] is True
        assert not settings.set_workspace_view_in_navigation_v2("missing", True)
        assert not settings.set_workspace_view_in_navigation_v2("heat_loss", "false")
        custom = settings.create_workspace_view_v2(name="My custom view", panels={"dock_rooms": "main"})
        assert custom and not settings.workspace_view_v2(custom)["in_navigation"]
        assert settings.set_last_workspace_view_v2(view_id=custom, mode="floating")

        window = QMainWindow()
        panel = WorkspaceNavigationPanelV1()
        dock = QDockWidget("Navigation", window)
        dock.setWidget(panel)
        window.addDockWidget(Qt.TopDockWidgetArea, dock)
        window.show()
        dock.setFloating(True)
        dock.show()
        settle()
        expected = QRect(60, 80, 520, 160)
        dock.setGeometry(expected)
        dialog = WorkspaceViewManagerDialogV2(
            settings=settings, panel_rows=(("dock_rooms", "Rooms"),), parent=window,
        )
        switched, requests = [], []
        dialog.views_changed.connect(switched.append)
        panel.view_requested.connect(requests.append)
        dialog.navigation_changed.connect(lambda: panel.set_workspace_views_v1(settings.workspace_views_v2()))
        panel.set_workspace_views_v1(settings.workspace_views_v2())
        panel.set_presentation_mode_v1("floating")
        assert dialog._in_navigation_checkbox.text() == "In Navigation"
        assert not dialog._in_navigation_checkbox.isChecked()
        dialog._in_navigation_checkbox.click()
        settle()
        assert not switched and not requests
        assert settings.last_workspace_view_v2() == {"view_id": custom, "mode": "floating"}
        assert panel.presentation_mode_v1() == "floating"
        assert dock.isFloating() and dock.geometry() == expected
        button = panel.button_for_route_v1(f"view:{custom}")
        assert button and button.text() == "My custom view"
        button.click()
        assert requests == [f"view:{custom}"]
        assert panel.active_route_v1() == f"view:{custom}"
        assert settings.rename_workspace_view_v2(custom, "Renamed workspace with a very long display name")
        dialog._persist_and_refresh_v2(view_id=custom)
        button = panel.button_for_route_v1(f"view:{custom}")
        assert button.isChecked() and "Renamed workspace" in button.toolTip()
        assert settings.workspace_view_v2(custom)["in_navigation"]
        check = '''from pathlib import Path
import sys
from HVAC.gui_v3.context.gui_settings import GuiSettings
s = GuiSettings(Path(sys.argv[1]))
v = s.workspace_view_v2(sys.argv[2])
assert v["in_navigation"] is True
assert v["name"].startswith("Renamed")
assert s.last_workspace_view_v2() == {"view_id": sys.argv[2], "mode": "floating"}
'''
        subprocess.run([sys.executable, "-c", check, str(root), custom], check=True, timeout=20)

        for view in settings.workspace_views_v2():
            settings.set_workspace_view_in_navigation_v2(view["view_id"], False)
        settings.save()
        panel.set_workspace_views_v1(settings.workspace_views_v2())
        settle()
        assert not panel._view_buttons and panel.active_route_v1() == ""
        assert panel.preferences_button_v1().isVisible()
        assert panel.presentation_mode_v1() == "floating"
        assert dock.geometry() == expected
        assert not any(v["in_navigation"] for v in GuiSettings(root).workspace_views_v2())
        settings.set_workspace_view_in_navigation_v2(custom, True)
        assert settings.delete_workspace_view_v2(custom)
        panel.set_workspace_views_v1(settings.workspace_views_v2())
        assert panel.button_for_route_v1(f"view:{custom}") is None

        many = [dict(view_id=f"custom_{i:03d}", name=f"A long saved view number {i}", in_navigation=True) for i in range(64)]
        for scheme in ("light", "dark"):
            app.setStyleSheet(application_stylesheet_v1(scheme))
            panel.set_workspace_views_v1(many)
            row_counts = []
            for width in (620, 260, 100, 620):
                dock.setGeometry(QRect(60, 80, width, 160))
                settle()
                assert dock.geometry() == QRect(60, 80, width, 160)
                rects = [b.geometry() for b in panel._ordered_buttons]
                row_counts.append(len({r.y() for r in rects}))
                assert all(r.left() >= 0 and r.right() < panel._button_host.width() for r in rects)
                assert all(not a.intersects(b) for i, a in enumerate(rects) for b in rects[i + 1:])
                assert panel._scroll.verticalScrollBar().maximum() > 0
                panel._scroll.ensureWidgetVisible(panel._ordered_buttons[-1])
                settle()
                assert panel._scroll.verticalScrollBar().value() > 0
            assert row_counts[1] > row_counts[0] and row_counts[3] == row_counts[0]
        dock.hide()
        panel.set_workspace_views_v1(settings.workspace_views_v2())
        settle()
        assert dock.isHidden(), "Refreshing membership reopened Navigation"
        dialog.close()
        dock.close()
        window.close()
    print("OK — H-S72-A4F membership persists, updates without layout intent, supports custom names/deletion/empty selection, and wraps within fixed floating geometry in Light and Dark.")


if __name__ == "__main__":
    main()
