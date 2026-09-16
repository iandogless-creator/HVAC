from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.gui_v3.context.gui_settings import GuiSettings


def _floating_geometry() -> dict:
    return {
        "x": 40,
        "y": 60,
        "width": 520,
        "height": 760,
        "screen_name": "Display-1",
    }


def main() -> None:
    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        settings = GuiSettings(settings_dir)

        views = settings.workspace_views_v2()
        assert len(views) == 7
        assert views[0]["view_id"] == "heat_loss"
        assert views[0]["panels"]["dock_heat_loss"] == "main"
        assert settings.last_workspace_view_v2() == {
            "view_id": "heat_loss",
            "mode": "main",
        }

        assert settings.rename_workspace_view_v2(
            "heat_loss", "My Heat-Loss"
        )
        assert not settings.rename_workspace_view_v2(
            "heat_loss", "Building Edit"
        )
        assert settings.set_workspace_view_panel_v2(
            view_id="heat_loss",
            panel_id="dock_ach",
            included=False,
        )
        assert settings.set_workspace_view_panel_v2(
            view_id="heat_loss",
            panel_id="dock_dev",
            included=True,
            placement="main",
        )
        edited = settings.workspace_view_v2("heat_loss")
        assert edited is not None
        assert edited["panels"]["dock_dev"] == "main"
        assert edited["panels"]["dock_heat_loss"] == "side"
        assert list(edited["panels"].values()).count("main") == 1
        assert not settings.set_workspace_view_panel_v2(
            view_id="heat_loss",
            panel_id="",
            included=True,
        )

        custom_id = settings.create_workspace_view_v2(
            name="My Single Panel",
            panels={"dock_rooms": "bottom"},
        )
        assert custom_id == "custom_001"
        custom = settings.workspace_view_v2(custom_id)
        assert custom is not None
        assert custom["panels"] == {"dock_rooms": "main"}
        assert not settings.set_workspace_view_panel_v2(
            view_id=custom_id,
            panel_id="dock_rooms",
            included=False,
        )
        assert settings.set_last_workspace_view_v2(
            view_id=custom_id,
            mode="floating",
        )

        settings.save()
        restored = GuiSettings(settings_dir)
        assert restored.workspace_view_v2("heat_loss")["name"] == (
            "My Heat-Loss"
        )
        assert restored.workspace_view_v2(custom_id)["panels"] == {
            "dock_rooms": "main"
        }
        assert restored.last_workspace_view_v2() == {
            "view_id": custom_id,
            "mode": "floating",
        }
        assert restored.delete_workspace_view_v2(custom_id)
        assert restored.last_workspace_view_v2() == {
            "view_id": "heat_loss",
            "mode": "main",
        }

        for view in restored.workspace_views_v2()[1:]:
            assert restored.delete_workspace_view_v2(view["view_id"])
        assert len(restored.workspace_views_v2()) == 1
        assert not restored.delete_workspace_view_v2("heat_loss")

    with TemporaryDirectory() as directory:
        settings_dir = Path(directory)
        path = settings_dir / "gui_v3_workspace.json"
        path.write_text(
            json.dumps({
                "workspace_panel_sets_v1": {
                    "heat_loss:docked": ["dock_rooms"],
                },
                "named_workspace_layouts_v1": {
                    "user:exploded": {
                        "docks": {
                            "dock_uvp": _floating_geometry(),
                        },
                    },
                },
                "last_workspace_presentation_v1": {
                    "view_id": "user",
                    "mode": "exploded",
                },
            }),
            encoding="utf-8",
        )
        migrated = GuiSettings(settings_dir)
        assert migrated.workspace_view_v2("heat_loss")["panels"] == {
            "dock_rooms": "main"
        }
        assert migrated.workspace_view_v2("user")["name"] == (
            "User Workspace"
        )
        assert migrated.last_workspace_view_v2() == {
            "view_id": "user",
            "mode": "floating",
        }

    print(
        "OK — H-S72-A1 provides one persistent editable named-view model "
        "with checkbox membership, Main/Side/Bottom placement, one-panel "
        "views, rename/delete safeguards and safe H-S69 migration."
    )


if __name__ == "__main__":
    main()
