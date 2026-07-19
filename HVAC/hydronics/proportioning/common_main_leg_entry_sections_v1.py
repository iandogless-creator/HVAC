# ======================================================================
# HVAC/hydronics/proportioning/common_main_leg_entry_sections_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from HVAC.hydronics.proportioning.branch_aware_carried_flow_basis_v1 import (
    BranchAwareCarriedFlowSectionRowV1,
    build_branch_aware_carried_flow_basis_v1,
)
from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1


COMMON_MAIN_SECTION_KIND = "common_main"
LEG_ENTRY_SECTION_KIND = "leg_entry"


@dataclass(frozen=True, slots=True)
class CommonMainLegEntrySectionV1:
    """One stable read-only common-main or leg-entry topology section."""

    section_id: str
    section_kind: str
    order: int
    takeoff_leg_id: str
    takeoff_leg_label: str
    from_label: str
    to_label: str

    carried_leg_ids: tuple[str, ...]
    carried_subleg_ids: tuple[str, ...]
    carried_room_ids: tuple[str, ...]
    carried_heat_W: float
    carried_flow_kg_s: float | None

    status: str


@dataclass(frozen=True, slots=True)
class CommonMainLegEntrySectionsProjectionV1:
    """
    H-S40-A read-only topology and carried-flow projection.

    Authority:
    - persisted HydronicTopologyV1.legs order is physical take-off order
    - H-S24 branch-aware carried-flow rows provide leg roll-up evidence

    It does not size pipe, resolve length or Local K, calculate pressure loss,
    proportion mains, select pumps/valves, or mutate ProjectState.
    """

    ready: bool
    common_main_sections: tuple[CommonMainLegEntrySectionV1, ...]
    leg_entry_sections: tuple[CommonMainLegEntrySectionV1, ...]
    sections: tuple[CommonMainLegEntrySectionV1, ...]
    blockers: tuple[str, ...] = ()
    status: str = "H-S40-A common-main topology not ready"


@dataclass(frozen=True, slots=True)
class _LegBasisV1:
    leg_id: str
    leg_label: str
    subleg_ids: tuple[str, ...]
    room_ids: tuple[str, ...]
    carried_heat_W: float
    carried_flow_kg_s: float | None


def build_common_main_leg_entry_sections_v1(
    project_state: Any,
) -> CommonMainLegEntrySectionsProjectionV1:
    """Build stable main and leg-entry identities in persisted leg order."""

    if project_state is None:
        return _blocked_projection("No project_state is available")

    topology = getattr(project_state, "hydronic_topology", None)
    if not isinstance(topology, HydronicTopologyV1):
        return _blocked_projection(
            "project_state.hydronic_topology is not HydronicTopologyV1"
        )

    legs = tuple(topology.legs or ())
    if not legs:
        return _blocked_projection("Hydronic topology has no persisted legs")

    leg_ids = tuple(str(getattr(leg, "leg_id", "") or "").strip() for leg in legs)
    invalid_ids = [leg_id for leg_id in leg_ids if not leg_id]
    duplicate_ids = sorted(
        {leg_id for leg_id in leg_ids if leg_ids.count(leg_id) > 1}
    )
    if invalid_ids or duplicate_ids:
        blockers: list[str] = []
        if invalid_ids:
            blockers.append("Every persisted leg requires a stable leg_id")
        if duplicate_ids:
            blockers.append(
                "Persisted leg_id values must be unique: "
                + ", ".join(duplicate_ids)
            )
        return _blocked_projection(*blockers)

    flow_basis = build_branch_aware_carried_flow_basis_v1(project_state)
    rows_by_leg: dict[str, list[BranchAwareCarriedFlowSectionRowV1]] = {
        leg_id: [] for leg_id in leg_ids
    }
    for row in tuple(getattr(flow_basis, "rows", ()) or ()):
        row_leg_id = str(getattr(row, "leg_id", "") or "")
        if row_leg_id in rows_by_leg:
            rows_by_leg[row_leg_id].append(row)

    leg_bases: list[_LegBasisV1] = []
    unresolved_leg_ids: list[str] = []
    for leg, leg_id in zip(legs, leg_ids):
        basis = _leg_basis_v1(
            leg_id=leg_id,
            leg_label=str(getattr(leg, "label", "") or leg_id),
            rows=rows_by_leg[leg_id],
        )
        leg_bases.append(basis)
        if basis.carried_flow_kg_s is None:
            unresolved_leg_ids.append(leg_id)

    heat_source_label = _room_label_v1(
        project_state,
        str(topology.heat_source_room_id or ""),
        fallback="Heat source",
    )

    common_main_sections: list[CommonMainLegEntrySectionV1] = []
    leg_entry_sections: list[CommonMainLegEntrySectionV1] = []

    for index, basis in enumerate(leg_bases):
        order = index + 1
        downstream = leg_bases[index:]
        common_main_sections.append(
            CommonMainLegEntrySectionV1(
                section_id=f"common-main-to-{basis.leg_id}-section-001",
                section_kind=COMMON_MAIN_SECTION_KIND,
                order=order,
                takeoff_leg_id=basis.leg_id,
                takeoff_leg_label=basis.leg_label,
                from_label=(
                    heat_source_label
                    if index == 0
                    else f"{leg_bases[index - 1].leg_label} take-off"
                ),
                to_label=f"{basis.leg_label} take-off",
                carried_leg_ids=tuple(item.leg_id for item in downstream),
                carried_subleg_ids=_ordered_union(
                    item.subleg_ids for item in downstream
                ),
                carried_room_ids=_ordered_union(
                    item.room_ids for item in downstream
                ),
                carried_heat_W=sum(item.carried_heat_W for item in downstream),
                carried_flow_kg_s=_optional_sum(
                    item.carried_flow_kg_s for item in downstream
                ),
                status=(
                    "Persisted leg-order common-main section / "
                    "branch-aware downstream roll-up"
                ),
            )
        )

        leg_entry_sections.append(
            CommonMainLegEntrySectionV1(
                section_id=f"{basis.leg_id}-entry-section-001",
                section_kind=LEG_ENTRY_SECTION_KIND,
                order=order,
                takeoff_leg_id=basis.leg_id,
                takeoff_leg_label=basis.leg_label,
                from_label=f"{basis.leg_label} take-off",
                to_label=f"{basis.leg_label} entry",
                carried_leg_ids=(basis.leg_id,),
                carried_subleg_ids=basis.subleg_ids,
                carried_room_ids=basis.room_ids,
                carried_heat_W=basis.carried_heat_W,
                carried_flow_kg_s=basis.carried_flow_kg_s,
                status=(
                    "Stable leg-entry section / branch-aware whole-leg roll-up"
                ),
            )
        )

    blockers = list(tuple(getattr(flow_basis, "blockers", ()) or ()))
    if unresolved_leg_ids:
        blockers.append(
            "Whole-leg carried flow unresolved for: "
            + ", ".join(unresolved_leg_ids)
        )

    ready = bool(getattr(flow_basis, "ready", False)) and not blockers
    sections = tuple(common_main_sections + leg_entry_sections)
    return CommonMainLegEntrySectionsProjectionV1(
        ready=ready,
        common_main_sections=tuple(common_main_sections),
        leg_entry_sections=tuple(leg_entry_sections),
        sections=sections,
        blockers=tuple(blockers),
        status=(
            "H-S40-A common-main and leg-entry section basis ready"
            if ready
            else "H-S40-A identities ready; carried-flow basis incomplete"
        ),
    )


def _leg_basis_v1(
    *,
    leg_id: str,
    leg_label: str,
    rows: list[BranchAwareCarriedFlowSectionRowV1],
) -> _LegBasisV1:
    subleg_ids = _ordered_union(
        (str(getattr(row, "subleg_id", "") or ""),) for row in rows
    )
    room_ids = _ordered_union(
        tuple(getattr(row, "carried_room_ids", ()) or ()) for row in rows
    )
    heat_values = [float(getattr(row, "carried_heat_W", 0.0) or 0.0) for row in rows]
    flow_values = [
        float(value)
        for row in rows
        for value in (getattr(row, "carried_flow_kg_s", None),)
        if value is not None
    ]
    return _LegBasisV1(
        leg_id=leg_id,
        leg_label=leg_label,
        subleg_ids=subleg_ids,
        room_ids=room_ids,
        carried_heat_W=max(heat_values, default=0.0),
        carried_flow_kg_s=max(flow_values) if flow_values else None,
    )


def _ordered_union(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    values: list[str] = []
    for group in groups:
        for raw_value in group:
            value = str(raw_value or "").strip()
            if value and value not in values:
                values.append(value)
    return tuple(values)


def _optional_sum(values: Iterable[float | None]) -> float | None:
    resolved = tuple(values)
    if any(value is None for value in resolved):
        return None
    return sum(float(value) for value in resolved if value is not None)


def _room_label_v1(
    project_state: Any,
    room_id: str,
    *,
    fallback: str,
) -> str:
    room = (getattr(project_state, "rooms", {}) or {}).get(room_id)
    if room is None:
        return fallback
    return str(
        getattr(room, "name", None)
        or getattr(room, "room_name", None)
        or getattr(room, "label", None)
        or fallback
    )


def _blocked_projection(
    *blockers: str,
) -> CommonMainLegEntrySectionsProjectionV1:
    return CommonMainLegEntrySectionsProjectionV1(
        ready=False,
        common_main_sections=(),
        leg_entry_sections=(),
        sections=(),
        blockers=tuple(blockers),
        status="H-S40-A common-main topology not ready",
    )
