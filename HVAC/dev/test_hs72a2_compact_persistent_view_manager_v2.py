from __future__ import annotations

from pathlib import Path


def main() -> None:
    dialog_source = Path(
        "HVAC/gui_v3/widgets/workspace_view_manager_dialog_v2.py"
    ).read_text(encoding="utf-8")
    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )

    assert "class WorkspaceViewManagerDialogV2(QDialog)" in dialog_source
    assert 'self.setWindowTitle("Views")' in dialog_source
    assert '"Include"' in dialog_source
    assert '"Main"' in dialog_source
    assert '"Side"' in dialog_source
    assert '"Bottom"' in dialog_source
    assert "QToolButton" in dialog_source
    assert "SP_TitleBarMaxButton" in dialog_source
    assert "SP_ArrowRight" in dialog_source
    assert "SP_ArrowDown" in dialog_source
    assert '"Include in view"' in dialog_source
    assert '"Changes save immediately."' in dialog_source
    assert "create_workspace_view_v2" in dialog_source
    assert "rename_workspace_view_v2" in dialog_source
    assert "delete_workspace_view_v2" in dialog_source
    assert "set_workspace_view_panel_v2" in dialog_source
    assert "self._settings.save()" in dialog_source
    assert "ProjectState" not in dialog_source
    assert "saveState(" not in dialog_source
    assert "restoreState(" not in dialog_source

    assert "WorkspaceViewManagerDialogV2" in main_source
    assert 'QAction("Manage Views…", self)' in main_source
    assert "def _show_workspace_view_manager_v2" in main_source
    assert 'not in {"", "dock_dev"}' in main_source
    assert "dialog.exec()" in main_source

    print(
        "OK — H-S72-A2 adds one compact persistent View Manager with "
        "New/Rename/Delete controls, Include checkboxes and icon-based "
        "Main/Side/Bottom placement without touching live dock authority."
    )


if __name__ == "__main__":
    main()
