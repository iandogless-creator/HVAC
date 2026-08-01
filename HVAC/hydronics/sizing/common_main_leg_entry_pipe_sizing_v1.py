# ======================================================================
# HVAC/hydronics/sizing/common_main_leg_entry_pipe_sizing_v1.py
# H-S40-B — Preliminary Basic PS sizing for common-main / leg-entry rows
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.proportioning.proportioned_pipe_material_family_intent_v1 import (
    DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1,
)
from HVAC.hydronics.proportioning.common_main_leg_entry_sections_v1 import (
    COMMON_MAIN_SECTION_KIND,
    LEG_ENTRY_SECTION_KIND,
    CommonMainLegEntrySectionV1,
    build_common_main_leg_entry_sections_v1,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    build_basic_ps_pipe_candidates_for_material_v1,
    build_basic_ps_pipe_sizing_v1,
    current_basic_ps_pipe_material_key_v1,
)
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    BasicPSTopologySectionV1,
)
from HVAC.hydronics.sizing.basic_ps_velocity_limit_resolver_v1 import (
    resolve_basic_ps_max_velocity_v1,
)


@dataclass(frozen=True, slots=True)
class CommonMainLegEntryPipeSizingRowV1:
    """
    Preliminary Basic PS selection evidence for one H-S40-A section.

    Every hydraulic evidence field is explicitly Basic/Haaland evidence. It is
    not a final Proportioning Colebrook result.
    """

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
    carried_flow_kg_s: float

    basic_pipe_size_label: str
    basic_internal_diameter_m: float
    basic_velocity_m_s: float
    applied_max_velocity_m_s: float
    max_velocity_source: str

    basic_reynolds_number: float
    basic_friction_factor: float
    basic_friction_method: str
    basic_pressure_gradient_Pa_per_m: float

    section_basis_status: str
    sizing_status: str
    status: str

    # H-S63-B2A — exact selected family/catalogue identity.
    basic_material_key: str = DEFAULT_PROPORTIONED_PIPE_MATERIAL_FAMILY_V1
    basic_material_label: str = "Copper EN1057"
    basic_pipe_size_key: int | None = None


@dataclass(frozen=True, slots=True)
class CommonMainLegEntryPipeSizingProjectionV1:
    """
    H-S40-B read-only preliminary sizing projection.

    Does not resolve section length or Local K, run Colebrook Proportioning,
    accumulate route/main pressure, balance, select pumps/valves, resize a
    committed design, or mutate ProjectState.
    """

    ready: bool
    common_main_rows: tuple[CommonMainLegEntryPipeSizingRowV1, ...]
    leg_entry_rows: tuple[CommonMainLegEntryPipeSizingRowV1, ...]
    rows: tuple[CommonMainLegEntryPipeSizingRowV1, ...]
    blockers: tuple[str, ...] = ()
    status: str = "H-S40-B common-main Basic PS sizing not ready"


def build_common_main_leg_entry_pipe_sizing_v1(
    project_state: Any,
) -> CommonMainLegEntryPipeSizingProjectionV1:
    """Size H-S40-A sections through the existing Basic PS/Haaland engine."""

    sections_projection = build_common_main_leg_entry_sections_v1(project_state)
    if not sections_projection.ready:
        return _blocked_projection(
            *tuple(sections_projection.blockers or (sections_projection.status,))
        )

    source_sections = tuple(sections_projection.sections)
    unresolved = tuple(
        section.section_id
        for section in source_sections
        if section.carried_flow_kg_s is None
    )
    if unresolved:
        return _blocked_projection(
            "Carried flow unresolved for H-S40-A sections: "
            + ", ".join(unresolved)
        )

    basic_sections = tuple(_to_basic_section_v1(section) for section in source_sections)
    resolutions = tuple(
        resolve_basic_ps_max_velocity_v1(
            project_state,
            section_id=section.section_id,
        )
        for section in source_sections
    )
    # H-S63-B2A — use the exact persisted current family only.
    current_material_key = current_basic_ps_pipe_material_key_v1(project_state)
    basic_projection = build_basic_ps_pipe_sizing_v1(
        basic_sections,
        pipe_candidates=build_basic_ps_pipe_candidates_for_material_v1(
            current_material_key
        ),
        max_velocity_m_s_by_section_id={
            resolution.section_id: resolution.effective_max_velocity_m_s
            for resolution in resolutions
        },
        max_velocity_source_by_section_id={
            resolution.section_id: resolution.source
            for resolution in resolutions
        },
    )

    source_by_id = {section.section_id: section for section in source_sections}
    rows = tuple(
        _combine_result_v1(
            section=source_by_id[result.section_id],
            result=result,
        )
        for result in basic_projection.results
    )
    common_rows = tuple(
        row for row in rows if row.section_kind == COMMON_MAIN_SECTION_KIND
    )
    entry_rows = tuple(
        row for row in rows if row.section_kind == LEG_ENTRY_SECTION_KIND
    )

    return CommonMainLegEntryPipeSizingProjectionV1(
        ready=True,
        common_main_rows=common_rows,
        leg_entry_rows=entry_rows,
        rows=rows,
        blockers=(),
        status=(
            "H-S40-B preliminary common-main / leg-entry Basic PS sizing ready"
        ),
    )


def _to_basic_section_v1(
    section: CommonMainLegEntrySectionV1,
) -> BasicPSTopologySectionV1:
    carried_flow = section.carried_flow_kg_s
    if carried_flow is None:
        raise ValueError(f"Carried flow unresolved for {section.section_id}")

    return BasicPSTopologySectionV1(
        section_id=section.section_id,
        leg_id=section.takeoff_leg_id,
        subleg_id=(
            "common-main"
            if section.section_kind == COMMON_MAIN_SECTION_KIND
            else f"{section.takeoff_leg_id}-entry"
        ),
        order=section.order,
        from_label=section.from_label,
        to_room_id="",
        to_room_label=section.to_label,
        downstream_room_ids=section.carried_room_ids,
        downstream_emitter_ids=(),
        carried_heat_W=float(section.carried_heat_W),
        carried_flow_kg_s=float(carried_flow),
        is_terminal=False,
        is_index_room=False,
        status=section.status,
    )


def _combine_result_v1(*, section: Any, result: Any) -> CommonMainLegEntryPipeSizingRowV1:
    section_basis_status = str(section.status or "")
    sizing_status = str(result.status or "")
    return CommonMainLegEntryPipeSizingRowV1(
        section_id=section.section_id,
        section_kind=section.section_kind,
        order=section.order,
        takeoff_leg_id=section.takeoff_leg_id,
        takeoff_leg_label=section.takeoff_leg_label,
        from_label=section.from_label,
        to_label=section.to_label,
        carried_leg_ids=section.carried_leg_ids,
        carried_subleg_ids=section.carried_subleg_ids,
        carried_room_ids=section.carried_room_ids,
        carried_heat_W=float(section.carried_heat_W),
        carried_flow_kg_s=float(section.carried_flow_kg_s),
        basic_pipe_size_label=result.pipe_size_label,
        basic_internal_diameter_m=float(result.internal_diameter_m),
        basic_velocity_m_s=float(result.velocity_m_s),
        applied_max_velocity_m_s=float(result.applied_max_velocity_m_s),
        max_velocity_source=str(result.max_velocity_source),
        basic_reynolds_number=float(result.reynolds_number),
        basic_friction_factor=float(result.friction_factor),
        basic_friction_method="Haaland",
        basic_pressure_gradient_Pa_per_m=float(
            result.pressure_gradient_Pa_per_m
        ),
        section_basis_status=section_basis_status,
        sizing_status=sizing_status,
        status=" / ".join(
            part for part in (section_basis_status, sizing_status) if part
        ),
        basic_material_key=str(result.material_key),
        basic_material_label=str(result.material_label),
        basic_pipe_size_key=result.pipe_size_key,
    )


def _blocked_projection(
    *blockers: str,
) -> CommonMainLegEntryPipeSizingProjectionV1:
    return CommonMainLegEntryPipeSizingProjectionV1(
        ready=False,
        common_main_rows=(),
        leg_entry_rows=(),
        rows=(),
        blockers=tuple(str(blocker) for blocker in blockers if str(blocker)),
        status="H-S40-B common-main Basic PS sizing not ready",
    )
