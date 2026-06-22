# ======================================================================
# HVAC/hydronics/sizing/basic_ps_topology_sections_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.topology.hydronic_topology_editor_v1 import (
    HydronicTopologyEditorV1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    primary_subleg_for_leg_id,
)
from HVAC.hydronics.design_conditions.hydronic_design_temperature_basis_v1 import (
    resolve_hydronic_design_temperature_basis_v1,
)
from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    build_branch_aware_carried_flow_basis_v1,
)


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPSTopologySectionV1:
    """
    Read-only Basic PS section row derived from hydronic topology.

    This is a pipe-section projection, not a pipe-size result.
    """

    section_id: str
    leg_id: str
    subleg_id: str
    order: int

    from_label: str
    to_room_id: str
    to_room_label: str

    downstream_room_ids: tuple[str, ...]
    downstream_emitter_ids: tuple[str, ...]

    carried_heat_W: float
    carried_flow_kg_s: float

    is_terminal: bool = False
    is_index_room: bool = False
    status: str = "Projection only"


@dataclass(frozen=True, slots=True)
class BasicPSTopologySectionsProjectionV1:
    """
    Read-only Basic PS topology section projection.
    """

    leg_id: str
    leg_label: str
    subleg_id: str
    subleg_label: str
    heat_source_room_id: str
    design_delta_t_K: float
    sections: tuple[BasicPSTopologySectionV1, ...]
    status: str = "Projection only"


# ======================================================================
# Public builder
# ======================================================================

def build_basic_ps_topology_sections_v1(
    project_state: Any,
    *,
    leg_id: str = "leg-001",
    subleg_id: str | None = None,
    design_delta_t_K: float | None = None,
) -> BasicPSTopologySectionsProjectionV1:
    """
    Build Basic PS section rows from hydronic topology.

    Authority
    ---------
    Reads:
    - ProjectState.hydronic_topology
    - ProjectState.emitters
    - ProjectState.basic_hydronic_sizing_intent, if present

    Does not:
    - mutate ProjectState
    - size pipes
    - calculate pressure loss
    - balance branches
    - modify topology
    """

    if project_state is None:
        raise ValueError("project_state is required")

    topology = getattr(project_state, "hydronic_topology", None)

    if topology is None:
        raise ValueError("ProjectState has no hydronic_topology")

    if not isinstance(topology, HydronicTopologyV1):
        raise TypeError("ProjectState.hydronic_topology is not HydronicTopologyV1")

    leg = HydronicTopologyEditorV1.require_leg(topology, leg_id)

    if subleg_id:
        primary_subleg = HydronicTopologyEditorV1.require_subleg(
            topology,
            str(subleg_id),
        )
    else:
        primary_subleg = primary_subleg_for_leg_id(topology, leg_id)

    resolved_delta_t_K = _resolve_design_delta_t_K(
        project_state=project_state,
        explicit_delta_t_K=design_delta_t_K,
    )

    room_lookup = getattr(project_state, "rooms", {}) or {}
    emitters = getattr(project_state, "emitters", {}) or {}

    branch_aware_by_section_id = _branch_aware_rows_by_section_id(
        project_state
    )

    sections: list[BasicPSTopologySectionV1] = []
    route_room_ids = list(primary_subleg.route_room_ids)

    for index, to_room_id in enumerate(route_room_ids):
        order = index + 1

        from_label = (
            "Common main / leg entry"
            if index == 0
            else _room_label(
                room_lookup.get(route_room_ids[index - 1]),
                route_room_ids[index - 1],
            )
        )

        section_id = f"{primary_subleg.subleg_id}-section-{order:03d}"
        branch_aware_row = branch_aware_by_section_id.get(section_id)

        if branch_aware_row is not None:
            downstream_room_ids = tuple(branch_aware_row.carried_room_ids)
            carried_heat_W = float(branch_aware_row.carried_heat_W)

            branch_aware_flow = getattr(
                branch_aware_row,
                "carried_flow_kg_s",
                None,
            )
            carried_flow_kg_s = (
                float(branch_aware_flow)
                if branch_aware_flow is not None
                else _heat_W_to_flow_kg_s(
                    heat_W=carried_heat_W,
                    delta_t_K=resolved_delta_t_K,
                )
            )

            row_status = (
                "Branch-aware carried-flow basis / "
                f"{branch_aware_row.status}"
            )
        else:
            downstream_room_ids = tuple(route_room_ids[index:])

            carried_heat_W = sum(
                _emitter_heat_W(emitters[emitter_id])
                for emitter_id in _emitter_ids_for_rooms(
                    emitters=emitters,
                    room_ids=downstream_room_ids,
                )
                if emitter_id in emitters
            )

            carried_flow_kg_s = _heat_W_to_flow_kg_s(
                heat_W=carried_heat_W,
                delta_t_K=resolved_delta_t_K,
            )

            row_status = "Projection only"

        downstream_emitter_ids = tuple(
            _emitter_ids_for_rooms(
                emitters=emitters,
                room_ids=downstream_room_ids,
            )
        )

        to_room = room_lookup.get(to_room_id)

        sections.append(
            BasicPSTopologySectionV1(
                section_id=section_id,
                leg_id=leg.leg_id,
                subleg_id=primary_subleg.subleg_id,
                order=order,
                from_label=from_label,
                to_room_id=str(to_room_id),
                to_room_label=_room_label(to_room, str(to_room_id)),
                downstream_room_ids=downstream_room_ids,
                downstream_emitter_ids=downstream_emitter_ids,
                carried_heat_W=carried_heat_W,
                carried_flow_kg_s=carried_flow_kg_s,
                is_terminal=(order == len(route_room_ids)),
                is_index_room=(str(to_room_id) == primary_subleg.index_room_id),
                status=row_status,
            )
        )

    return BasicPSTopologySectionsProjectionV1(
        leg_id=leg.leg_id,
        leg_label=leg.label,
        subleg_id=primary_subleg.subleg_id,
        subleg_label=primary_subleg.label,
        heat_source_room_id=topology.heat_source_room_id,
        design_delta_t_K=resolved_delta_t_K,
        sections=tuple(sections),
        status="Projection only",
    )


# ======================================================================
# Branch-aware integration helpers
# ======================================================================

def _branch_aware_rows_by_section_id(project_state: Any) -> dict[str, Any]:
    """
    Return H-S24-C branch-aware carried-flow rows by section_id.

    H-S24-F integration rule:
    - if branch-aware basis is available, Basic PS uses it for carried Q/flow;
    - if unavailable, Basic PS keeps its legacy route-local basis.
    """

    try:
        basis = build_branch_aware_carried_flow_basis_v1(project_state)
    except Exception:
        return {}

    if not getattr(basis, "ready", False):
        return {}

    return {
        str(getattr(row, "section_id", "") or ""): row
        for row in getattr(basis, "rows", ()) or ()
        if str(getattr(row, "section_id", "") or "")
    }


# ======================================================================
# Internals
# ======================================================================

def _resolve_design_delta_t_K(
    *,
    project_state: Any,
    explicit_delta_t_K: float | None,
) -> float:
    """
    Resolve heating water design ΔT.

    H-S23-B rule:
    - explicit argument wins for tests/dev probes;
    - otherwise use the shared Environment hydronic design-temperature basis;
    - otherwise fall back to legacy basic hydronic intent fields;
    - otherwise use 20 K as the legacy placeholder.

    Derived ΔT is not stored on ProjectState.
    """

    if explicit_delta_t_K is not None:
        return float(explicit_delta_t_K)

    environment_basis = resolve_hydronic_design_temperature_basis_v1(
        project_state
    )
    if environment_basis.delta_t_k is not None:
        return float(environment_basis.delta_t_k)

    intent = getattr(project_state, "basic_hydronic_sizing_intent", None)

    for attr_name in (
        "design_delta_t_K",
        "water_delta_t_K",
        "flow_return_delta_t_K",
    ):
        value = getattr(intent, attr_name, None) if intent is not None else None

        if value is not None:
            return float(value)

    return 20.0


def _room_label(room: Any, room_id: str) -> str:
    label = getattr(room, "name", None) if room is not None else None
    return str(label or room_id).strip()


def _emitter_ids_for_rooms(
    *,
    emitters: dict[str, Any],
    room_ids: tuple[str, ...],
) -> list[str]:
    room_id_set = set(room_ids)
    emitter_ids: list[str] = []

    for emitter_id, emitter in emitters.items():
        emitter_room_id = getattr(emitter, "room_id", None)

        if emitter_room_id in room_id_set:
            emitter_ids.append(str(emitter_id))

    return emitter_ids


def _emitter_heat_W(emitter: Any) -> float:
    """
    Resolve emitter heat output in W.

    Supports likely current/future field names.
    """

    for attr_name in (
        "design_heat_output_W",
        "design_output_W",
        "nominal_output_W",
        "heat_output_W",
        "output_W",
        "design_heat_W",
        "load_W",
        "design_load_W",
        "q_W",
        "heat_W",
        "watts",
    ):
        value = getattr(emitter, attr_name, None)

        if value is not None:
            return float(value)

    return 0.0


def _heat_W_to_flow_kg_s(
    *,
    heat_W: float,
    delta_t_K: float,
) -> float:
    """
    Convert heat load to water mass flow.

    Q = m_dot * cp * ΔT

    cp ≈ 4180 J/kgK for water.
    """

    if heat_W <= 0.0:
        return 0.0

    if delta_t_K <= 0.0:
        return 0.0

    return float(heat_W) / (4180.0 * float(delta_t_K))
