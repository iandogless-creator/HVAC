# ======================================================================
# HVAC/hydronics/sizing/basic_ps_readonly_projection_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    BasicPSTopologySectionsProjectionV1,
    build_basic_ps_topology_sections_v1,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    BasicPSPipeSizingProjectionV1,
    build_basic_ps_pipe_candidates_for_material_v1,
    build_basic_ps_pipe_sizing_v1,
    current_basic_ps_pipe_material_key_v1,
)
from HVAC.hydronics.sizing.basic_ps_velocity_limit_resolver_v1 import (
    resolve_basic_ps_max_velocity_v1,
)
from HVAC.hydronics.sizing.basic_ps_pressure_preview_v1 import (
    BasicPSPressurePreviewProjectionV1,
    build_basic_ps_pressure_preview_v1,
)
from HVAC.hydronics.sizing.basic_ps_route_dp_ranking_v1 import (
    BasicPSRoutePressureCandidateV1,
    BasicPSRoutePressureRankingProjectionV1,
    build_basic_ps_route_dp_ranking_v1,
)


# ======================================================================
# DTO
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPSReadonlyProjectionV1:
    """
    Read-only composed Basic PS projection.

    H-S8-J:
    Connects the existing read-only Basic PS stages:

        topology sections
        -> pipe sizing
        -> section Δp preview
        -> route Δp ranking

    This projection does not mutate ProjectState and does not perform
    final proportioning or balancing.
    """

    sections_projection: BasicPSTopologySectionsProjectionV1
    pipe_sizing_projection: BasicPSPipeSizingProjectionV1
    pressure_preview_projection: BasicPSPressurePreviewProjectionV1
    route_ranking_projection: BasicPSRoutePressureRankingProjectionV1

    status: str = "Read-only Basic PS projection"


# ======================================================================
# Public builder
# ======================================================================

def build_basic_ps_readonly_projection_v1(
    project_state: Any,
    *,
    leg_id: str = "leg-001",
    subleg_id: str | None = None,
    section_lengths_m: dict[str, float] | None = None,
) -> BasicPSReadonlyProjectionV1:
    """
    Build the composed Basic PS read-only projection.

    section_lengths_m:
        Optional section length map:
            section_id -> length in metres

    If lengths are missing:
        - section Δp remains incomplete
        - route ranking remains incomplete
        - no automatic index selection is made
    """

    sections_projection = build_basic_ps_topology_sections_v1(
        project_state,
        leg_id=leg_id,
        subleg_id=subleg_id,
    )

    velocity_resolutions = tuple(
        resolve_basic_ps_max_velocity_v1(
            project_state,
            section_id=section.section_id,
        )
        for section in sections_projection.sections
    )

    # H-S63-B2A — the persisted current family, never the proposed
    # preview family, supplies one unmixed Basic PS candidate ladder.
    current_material_key = current_basic_ps_pipe_material_key_v1(project_state)
    pipe_sizing_projection = build_basic_ps_pipe_sizing_v1(
        sections_projection.sections,
        pipe_candidates=build_basic_ps_pipe_candidates_for_material_v1(
            current_material_key
        ),
        max_velocity_m_s_by_section_id={
            resolution.section_id: resolution.effective_max_velocity_m_s
            for resolution in velocity_resolutions
        },
        max_velocity_source_by_section_id={
            resolution.section_id: resolution.source
            for resolution in velocity_resolutions
        },
    )

    pressure_preview_projection = build_basic_ps_pressure_preview_v1(
        pipe_sizing_projection.results,
        section_lengths_m=section_lengths_m,
    )

    route_label = (
        f"{sections_projection.leg_label} / {sections_projection.subleg_label}"
    )

    route_candidate = BasicPSRoutePressureCandidateV1(
        route_id=f"{sections_projection.leg_id}:{sections_projection.subleg_id}",
        route_label=route_label,
        leg_id=sections_projection.leg_id,
        subleg_id=sections_projection.subleg_id,
        pressure_preview=pressure_preview_projection,
    )

    route_ranking_projection = build_basic_ps_route_dp_ranking_v1(
        [route_candidate]
    )

    return BasicPSReadonlyProjectionV1(
        sections_projection=sections_projection,
        pipe_sizing_projection=pipe_sizing_projection,
        pressure_preview_projection=pressure_preview_projection,
        route_ranking_projection=route_ranking_projection,
        status="Read-only Basic PS projection",
    )