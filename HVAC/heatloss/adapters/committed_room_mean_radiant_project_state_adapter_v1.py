# ======================================================================
# H-S66-N3D4 — Live ProjectState room Tri orchestration
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping

from HVAC.heatloss.adapters.committed_internal_surface_temperature_project_state_adapter_v1 import (
    build_committed_internal_surface_temperatures_from_project_state_v1,
)
from HVAC.heatloss.physics.committed_room_enclosure_mean_radiant_handoff_v1 import (
    build_committed_room_enclosure_mean_radiant_handoff_v1,
)
from HVAC.heatloss.physics.committed_room_mean_radiant_temperature_authority_v1 import (
    CommittedRoomMeanRadiantTemperatureAuthorityV1,
)


def build_committed_room_mean_radiant_from_project_state_v1(
        project_state: object,
) -> CommittedRoomMeanRadiantTemperatureAuthorityV1:
    """Orchestrate N3D2 into N3D3 without duplicating either authority."""

    surface_evidence = (
        build_committed_internal_surface_temperatures_from_project_state_v1(
            project_state
        )
    )
    if not surface_evidence.ready:
        return _blocked_v1(*surface_evidence.blockers)

    rooms = getattr(project_state, "rooms", None)
    if not isinstance(rooms, Mapping) or not rooms:
        return _blocked_v1("Committed ProjectState room identities are required")
    room_ids = tuple(rooms)

    return build_committed_room_enclosure_mean_radiant_handoff_v1(
        committed_room_ids=room_ids,
        internal_surface_temperature_evidence=surface_evidence,
    )


def _blocked_v1(
        *blockers: str,
) -> CommittedRoomMeanRadiantTemperatureAuthorityV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedRoomMeanRadiantTemperatureAuthorityV1(
        ready=False,
        rooms=(),
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
