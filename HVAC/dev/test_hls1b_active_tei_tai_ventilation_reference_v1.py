from __future__ import annotations

import math
from types import SimpleNamespace

import HVAC.heatloss.controller_v4_orchestrator as controller_module
from HVAC.heatloss.controller_v4_orchestrator import HeatLossControllerV4
from HVAC.heatloss.dto.effective_project_snapshot import (
    EffectiveProjectSnapshotDTO,
)
from HVAC.heatloss.dto.effective_room_snapshot import EffectiveRoomSnapshotDTO
from HVAC.heatloss.dto.fabric_inputs import FabricSurfaceInputDTO
from HVAC.core.value_resolution import resolve_effective_internal_temp_C


class _Project:
    def __init__(self) -> None:
        self.heatloss_results = None
        self.heatloss_valid = False

    def evaluate_heatloss_readiness(self):
        return SimpleNamespace(is_ready=True, blocking_reasons=())

    def mark_heatloss_dirty(self) -> None:
        self.heatloss_valid = False

    def mark_heatloss_valid(self) -> None:
        self.heatloss_valid = True


def _snapshot(environmental_mode: bool) -> EffectiveProjectSnapshotDTO:
    # tei/Ti 20 C, Te -3 C, Qf 960 W over 40 m2.
    # Cv = 960 / (40 * 4.8) = 5 K; tai = 25 C.
    surface = FabricSurfaceInputDTO(
        surface_id="surface-a",
        room_id="room-a",
        surface_class="External Wall",
        area_m2=40.0,
        u_value_W_m2K=960.0 / (40.0 * 23.0),
        delta_t_K=23.0,
    )
    room = EffectiveRoomSnapshotDTO(
        room_id="room-a",
        floor_area_m2=40.0,
        height_m=2.5,
        volume_m3=100.0,
        ach=0.5,
        internal_design_temp_C=20.0,
    )
    return EffectiveProjectSnapshotDTO(
        project_id="project-a",
        external_design_temp_C=-3.0,
        internal_design_temp_C=20.0,
        fabric_surfaces=[surface],
        rooms=[room],
        use_internal_environmental_temperature=environmental_mode,
    )


def _run(snapshot: EffectiveProjectSnapshotDTO):
    project = _Project()
    original_builder = controller_module.build_effective_project_snapshot
    controller_module.build_effective_project_snapshot = (
        lambda **_kwargs: snapshot
    )
    try:
        HeatLossControllerV4(project_state=project).run(
            internal_design_temp_C=20.0
        )
    finally:
        controller_module.build_effective_project_snapshot = original_builder
    assert project.heatloss_valid
    return project.heatloss_results


def main() -> None:
    room_with_override = SimpleNamespace(internal_temp_override_C=19.0)
    ordinary_project = SimpleNamespace(
        environment=SimpleNamespace(
            default_internal_temp_C=21.0,
            use_internal_environmental_temperature=False,
        )
    )
    assert resolve_effective_internal_temp_C(
        ordinary_project, room_with_override
    ) == (19.0, "room")

    environmental_project = SimpleNamespace(
        environment=SimpleNamespace(
            default_internal_temp_C=20.0,
            use_internal_environmental_temperature=True,
        )
    )
    assert resolve_effective_internal_temp_C(
        environmental_project, room_with_override
    ) == (20.0, "environment")

    ordinary = _run(_snapshot(False))
    ordinary_room = ordinary["room_totals"]["room-a"]
    assert math.isclose(ordinary_room["q_fabric_W"], 960.0)
    assert math.isclose(
        ordinary_room["q_ventilation_W"],
        0.33 * 0.5 * 100.0 * (20.0 - (-3.0)),
    )
    assert "tai_C" not in ordinary_room
    assert "tai_C_by_room_id" not in ordinary
    assert "internal_environmental_temperature_mode" not in ordinary

    environmental = _run(_snapshot(True))
    environmental_room = environmental["room_totals"]["room-a"]
    assert math.isclose(environmental_room["q_fabric_W"], 960.0)
    assert math.isclose(environmental_room["tai_C"], 25.0)
    assert math.isclose(
        environmental_room["q_ventilation_W"],
        0.33 * 0.5 * 100.0 * (25.0 - (-3.0)),
    )
    assert math.isclose(
        environmental_room["q_total_W"],
        960.0 + environmental_room["q_ventilation_W"],
    )
    assert environmental["internal_environmental_temperature_mode"] is True
    assert environmental["tai_C_by_room_id"] == {"room-a": 25.0}

    print(
        "OK — HL-S1B selected environmental mode derives tai from fresh Qf/area "
        "and uses tai as the Qv reference; ordinary Ti results remain unchanged."
    )


if __name__ == "__main__":
    main()
