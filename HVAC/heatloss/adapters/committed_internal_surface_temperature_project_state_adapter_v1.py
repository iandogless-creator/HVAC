# ======================================================================
# H-S66-N3D2 — ProjectState handoff into standard-Rsi Tsi evidence
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping

from HVAC.heatloss.adapters.committed_room_cv_tai_project_state_adapter_v1 import (
    build_committed_room_cv_tai_from_project_state_v1,
)
from HVAC.heatloss.physics.committed_internal_surface_temperature_evidence_v1 import (
    CommittedInternalSurfaceTemperatureEvidenceV1,
    build_committed_internal_surface_temperature_evidence_v1,
)


def build_committed_internal_surface_temperatures_from_project_state_v1(
        project_state: object,
) -> CommittedInternalSurfaceTemperatureEvidenceV1:
    """Hand fresh accepted fabric rows and exact effective Ti into N3D1."""

    room_evidence = build_committed_room_cv_tai_from_project_state_v1(
        project_state
    )
    if not room_evidence.ready:
        return _blocked_v1(*room_evidence.blockers)

    results = getattr(project_state, "heatloss_results", None)
    if not isinstance(results, Mapping):
        return _blocked_v1("Accepted heat-loss result container is required")
    fabric_rows = _fabric_rows_v1(results.get("fabric"))
    if not fabric_rows:
        return _blocked_v1("Accepted fabric result rows are required")

    room_ids = tuple(row.room_id for row in room_evidence.rooms)
    effective_ti_by_room = {
        row.room_id: row.tei_C for row in room_evidence.rooms
    }
    return build_committed_internal_surface_temperature_evidence_v1(
        heatloss_results_valid=(
            getattr(project_state, "heatloss_valid", False) is True
        ),
        committed_room_ids=room_ids,
        effective_internal_temperature_C_by_room_id=effective_ti_by_room,
        accepted_fabric_rows=fabric_rows,
    )


def _fabric_rows_v1(raw_fabric: object) -> tuple[object, ...]:
    if isinstance(raw_fabric, (list, tuple)):
        return tuple(raw_fabric)
    if isinstance(raw_fabric, Mapping):
        raw_rows = raw_fabric.get("rows", raw_fabric.get("surfaces"))
        return tuple(raw_rows) if isinstance(raw_rows, (list, tuple)) else ()
    raw_rows = getattr(raw_fabric, "surfaces", None)
    return tuple(raw_rows) if isinstance(raw_rows, (list, tuple)) else ()


def _blocked_v1(
        *blockers: str,
) -> CommittedInternalSurfaceTemperatureEvidenceV1:
    unique = tuple(dict.fromkeys(str(value) for value in blockers if value))
    return CommittedInternalSurfaceTemperatureEvidenceV1(
        ready=False,
        surfaces=(),
        surface_count=0,
        room_count=0,
        status="Blocked — " + "; ".join(unique),
        blockers=unique,
    )
