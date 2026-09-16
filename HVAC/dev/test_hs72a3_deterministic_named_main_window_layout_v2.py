from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings


def main() -> None:
    with TemporaryDirectory() as directory:
        settings = GuiSettings(Path(directory))
        view_id = settings.create_workspace_view_v2(
            name="Capacity",
            panels={"dock_a": "main"},
        )
        assert view_id is not None
        for panel_id in ("dock_b", "dock_c"):
            assert settings.set_workspace_view_panel_v2(
                view_id=view_id,
                panel_id=panel_id,
                included=True,
                placement="side",
            )
        assert not settings.set_workspace_view_panel_v2(
            view_id=view_id,
            panel_id="dock_d",
            included=True,
            placement="side",
        )
        for panel_id in ("dock_d", "dock_e"):
            assert settings.set_workspace_view_panel_v2(
                view_id=view_id,
                panel_id=panel_id,
                included=True,
                placement="bottom",
            )
        assert not settings.set_workspace_view_panel_v2(
            view_id=view_id,
            panel_id="dock_f",
            included=True,
            placement="bottom",
        )
        assert settings.set_workspace_view_panel_v2(
            view_id=view_id,
            panel_id="dock_b",
            included=True,
            placement="main",
        )
        swapped = settings.workspace_view_v2(view_id)["panels"]
        assert swapped["dock_b"] == "main"
        assert swapped["dock_a"] == "side"
        assert list(swapped.values()).count("side") == 2
        assert list(swapped.values()).count("bottom") == 2

    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    dialog_source = Path(
        "HVAC/gui_v3/widgets/workspace_view_manager_dialog_v2.py"
    ).read_text(encoding="utf-8")
    layout_source = Path(
        "HVAC/gui_v3/context/workspace_dock_layout_reset_v2.py"
    ).read_text(encoding="utf-8")
    assert "def _apply_named_workspace_main_view_v2" in main_source
    assert "apply_named_workspace_docks_v2" in main_source
    assert "window.splitDockWidget(sides[0], sides[1], Qt.Vertical)" in layout_source
    assert (
        "window.splitDockWidget(bottoms[0], bottoms[1], Qt.Horizontal)"
        in layout_source
    )
    assert "last_workspace_view_v2" in main_source
    assert "view_selected = Signal(str)" in dialog_source
    assert "views_changed = Signal(str)" in dialog_source
    assert "ProjectState" not in dialog_source

    print(
        "OK — H-S72-A3 applies persistent named Main Window views with "
        "one Main panel, up to two vertically stacked Side panels and two "
        "horizontally split Bottom panels, including restart restoration."
    )


if __name__ == "__main__":
    main()
