# ======================================================================
# HVAC/hydronics/worksheets/basic_hydronics_worksheet_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from HVAC.project.project_state import ProjectState
from HVAC.core.room_identity import room_short_label
from HVAC.hydronics.adapters.room_emitter_demand_adapter_v1 import (
    RoomEmitterDemandAdapterV1,
)


# ======================================================================
# Constants
# ======================================================================

CP_WATER_J_KG_K = 4180.0


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicHydronicsWorksheetRoomRowV1:
    """
    Read-only basic hydronics worksheet row.

    Authority
    ---------
    • Derived from ProjectState
    • Does not mutate ProjectState
    • Does not size pipes
    • Does not calculate pressure loss
    • Does not call Colebrook
    """

    room_id: str
    room_label: str

    heat_load_W: Optional[float]

    emitter_count: int
    emitter_summary: str
    emitter_output_W: Optional[float]
    emitter_status: str

    flow_temp_C: Optional[float]
    return_temp_C: Optional[float]
    water_delta_t_K: Optional[float]

    mass_flow_kg_s: Optional[float]


@dataclass(frozen=True, slots=True)
class BasicHydronicsWorksheetIndexSummaryV1:
    """
    Read-only projection of BasicHydronicSizingIntentV1.
    """

    basis_mode: str

    index_room_id: Optional[str]
    index_room_label: Optional[str]

    index_emitter_id: Optional[str]
    index_emitter_label: Optional[str]

    total_index_length_m: Optional[float]
    nominal_pressure_gradient_Pa_per_m: Optional[float]
    nominal_index_pipework_dp_Pa: Optional[float]

    length_source: str
    pressure_gradient_source: str


@dataclass(frozen=True, slots=True)
class BasicHydronicsWorksheetV1:
    """
    H-N5 read-only basic hydronics worksheet.

    This object is display/projection only.
    """

    rows: list[BasicHydronicsWorksheetRoomRowV1]
    index_summary: BasicHydronicsWorksheetIndexSummaryV1


# ======================================================================
# Builder
# ======================================================================

def build_basic_hydronics_worksheet_v1(
    project: ProjectState,
) -> BasicHydronicsWorksheetV1:
    """
    Build the H-N5 basic hydronics worksheet.

    Rules
    -----
    • Reads ProjectState only
    • Does not mutate ProjectState
    • Does not size pipes
    • Does not calculate pressure loss
    • Does not call Colebrook
    """

    demand_rows = RoomEmitterDemandAdapterV1().build_rows(project)

    rows: list[BasicHydronicsWorksheetRoomRowV1] = []

    for demand in demand_rows:
        emitters = _emitters_for_room(project, demand.room_id)

        flow_temp_C = _common_optional_float(emitters, "flow_temp_C")
        return_temp_C = _common_optional_float(emitters, "return_temp_C")

        water_delta_t_K = _water_delta_t_K(
            flow_temp_C=flow_temp_C,
            return_temp_C=return_temp_C,
        )

        mass_flow_kg_s = _mass_flow_kg_s(
            heat_load_W=demand.design_heat_load_W,
            water_delta_t_K=water_delta_t_K,
        )

        rows.append(
            BasicHydronicsWorksheetRoomRowV1(
                room_id=demand.room_id,
                room_label=demand.room_name,
                heat_load_W=demand.design_heat_load_W,
                emitter_count=demand.emitter_count,
                emitter_summary=demand.emitter_summary,
                emitter_output_W=demand.emitter_output_W,
                emitter_status=demand.status,
                flow_temp_C=flow_temp_C,
                return_temp_C=return_temp_C,
                water_delta_t_K=water_delta_t_K,
                mass_flow_kg_s=mass_flow_kg_s,
            )
        )

    return BasicHydronicsWorksheetV1(
        rows=rows,
        index_summary=_build_index_summary(project),
    )


# ======================================================================
# Index summary
# ======================================================================

def _build_index_summary(
    project: ProjectState,
) -> BasicHydronicsWorksheetIndexSummaryV1:
    intent = getattr(project, "basic_hydronic_sizing_intent", None)

    if intent is None:
        return BasicHydronicsWorksheetIndexSummaryV1(
            basis_mode="INDEX_LENGTH",
            index_room_id=None,
            index_room_label=None,
            index_emitter_id=None,
            index_emitter_label=None,
            total_index_length_m=None,
            nominal_pressure_gradient_Pa_per_m=None,
            nominal_index_pipework_dp_Pa=None,
            length_source="unset",
            pressure_gradient_source="unset",
        )

    index_room_label = None
    if intent.index_room_id:
        room = project.rooms.get(intent.index_room_id)
        if room is not None:
            index_room_label = room_short_label(intent.index_room_id, room)

    index_emitter_label = None
    if intent.index_emitter_id:
        emitter = (getattr(project, "emitters", {}) or {}).get(
            intent.index_emitter_id
        )
        if emitter is not None:
            index_emitter_label = _emitter_label(
                emitter_id=intent.index_emitter_id,
                emitter=emitter,
                project=project,
            )

    nominal_index_pipework_dp_Pa = _nominal_index_pipework_dp_Pa(
        total_index_length_m=intent.total_index_length_m,
        nominal_pressure_gradient_Pa_per_m=(
            intent.nominal_pressure_gradient_Pa_per_m
        ),
    )

    return BasicHydronicsWorksheetIndexSummaryV1(
        basis_mode=str(intent.basis_mode or "INDEX_LENGTH"),
        index_room_id=intent.index_room_id,
        index_room_label=index_room_label,
        index_emitter_id=intent.index_emitter_id,
        index_emitter_label=index_emitter_label,
        total_index_length_m=intent.total_index_length_m,
        nominal_pressure_gradient_Pa_per_m=(
            intent.nominal_pressure_gradient_Pa_per_m
        ),
        nominal_index_pipework_dp_Pa=nominal_index_pipework_dp_Pa,
        length_source=str(intent.length_source or "unset"),
        pressure_gradient_source=str(intent.pressure_gradient_source or "unset"),
    )


# ======================================================================
# Helpers
# ======================================================================

def _emitters_for_room(
    project: ProjectState,
    room_id: str,
) -> list[Any]:
    emitters = getattr(project, "emitters", {}) or {}

    return [
        emitter
        for emitter in emitters.values()
        if getattr(emitter, "room_id", None) == room_id
    ]


def _common_optional_float(
    emitters: list[Any],
    attr_name: str,
) -> Optional[float]:
    """
    Return a common numeric value if all populated emitters agree.

    If no value exists, or values are mixed, return None.

    This avoids inventing hidden defaults in H-N5.
    """
    values: list[float] = []

    for emitter in emitters:
        raw = getattr(emitter, attr_name, None)
        if raw is None:
            continue

        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue

    if not values:
        return None

    first = values[0]

    for value in values[1:]:
        if abs(value - first) > 1e-9:
            return None

    return first


def _water_delta_t_K(
    *,
    flow_temp_C: Optional[float],
    return_temp_C: Optional[float],
) -> Optional[float]:
    if flow_temp_C is None or return_temp_C is None:
        return None

    delta = float(flow_temp_C) - float(return_temp_C)

    if delta <= 0.0:
        return None

    return delta


def _mass_flow_kg_s(
    *,
    heat_load_W: Optional[float],
    water_delta_t_K: Optional[float],
) -> Optional[float]:
    if heat_load_W is None or water_delta_t_K is None:
        return None

    try:
        heat_load = float(heat_load_W)
        delta_t = float(water_delta_t_K)
    except (TypeError, ValueError):
        return None

    if heat_load <= 0.0 or delta_t <= 0.0:
        return None

    return heat_load / (CP_WATER_J_KG_K * delta_t)


def _nominal_index_pipework_dp_Pa(
    *,
    total_index_length_m: Optional[float],
    nominal_pressure_gradient_Pa_per_m: Optional[float],
) -> Optional[float]:
    if total_index_length_m is None or nominal_pressure_gradient_Pa_per_m is None:
        return None

    try:
        length = float(total_index_length_m)
        gradient = float(nominal_pressure_gradient_Pa_per_m)
    except (TypeError, ValueError):
        return None

    if length <= 0.0 or gradient <= 0.0:
        return None

    return length * gradient


def _emitter_label(
    *,
    emitter_id: str,
    emitter: Any,
    project: ProjectState,
) -> str:
    name = getattr(emitter, "name", None) or emitter_id
    emitter_type = getattr(emitter, "emitter_type", None) or "emitter"
    room_id = getattr(emitter, "room_id", None)

    if room_id:
        room = project.rooms.get(room_id)
        if room is not None:
            return f"{name} ({emitter_type}, {room_short_label(room_id, room)})"

    return f"{name} ({emitter_type})"