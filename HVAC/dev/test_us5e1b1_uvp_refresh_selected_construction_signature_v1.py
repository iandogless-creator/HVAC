from __future__ import annotations

from types import SimpleNamespace

from HVAC.gui_v3.adapters.uvp_panel_adapter import UVPPanelAdapter


class PanelSpy:
    def __init__(self) -> None:
        self.selected_surface = None
        self.selected_construction_args = None

    def set_constructions(self, _constructions) -> None:
        pass

    def set_heat_flow_temperature_contexts(self, _contexts, _room_id=None) -> None:
        pass

    def set_selected_surface(self, surface_id) -> None:
        self.selected_surface = surface_id

    def set_selected_construction(self, construction_id, u_value_W_m2K) -> None:
        self.selected_construction_args = (
            construction_id,
            u_value_W_m2K,
        )


class ContextStub:
    def __init__(self, project_state) -> None:
        self.project_state = project_state
        self.current_surface_id = "SEG-1"
        self.current_room_id = "ROOM-1"

    def get_uvp_focus(self):
        return "SEG-1"


def main() -> None:
    construction = SimpleNamespace(u_value_W_m2K=1.4)
    project = SimpleNamespace(
        constructions={"WINDOW-1": construction},
        rooms={},
        environment=None,
        boundary_segments={},
        surface_construction_map={"SEG-1": "WINDOW-1"},
    )
    panel = PanelSpy()
    adapter = UVPPanelAdapter.__new__(UVPPanelAdapter)
    adapter._context = ContextStub(project)
    adapter._panel = panel

    adapter.refresh()

    assert panel.selected_surface == "SEG-1"
    assert panel.selected_construction_args == ("WINDOW-1", 1.4)

    source = (
        __import__("pathlib").Path(
            "HVAC/gui_v3/adapters/uvp_panel_adapter.py"
        ).read_text(encoding="utf-8")
    )
    assert "set_selected_construction(assigned_cid)" not in source

    print(
        "OK — U-S5E1B1 UVP refresh supplies construction identity and "
        "U-value to the panel without a signature error."
    )


if __name__ == "__main__":
    main()
