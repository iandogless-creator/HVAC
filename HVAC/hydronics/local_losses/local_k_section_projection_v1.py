# ======================================================================
# HVAC/hydronics/local_losses/local_k_section_projection_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)


WATER_DENSITY_KG_M3 = 998.0


@dataclass(frozen=True, slots=True)
class LocalKSectionProjectionRowV1:
    """
    Read-only Local K section basis row.

    H-S12-A shell:
    - reads Basic PS first-pass section basis
    - supplies section choices for the Local K panel
    - does not persist fitting counts
    - does not perform final proportioning or balancing
    """

    section_id: str
    order: int
    from_label: str
    to_room_label: str

    pipe_size_label: str
    carried_flow_kg_s: float
    velocity_m_s: float
    pressure_gradient_Pa_per_m: float

    k_total: float = 0.0
    local_pressure_drop_Pa: float = 0.0
    status: str = "Local K shell — no fittings persisted"


@dataclass(frozen=True, slots=True)
class LocalKSectionProjectionV1:
    rows: tuple[LocalKSectionProjectionRowV1, ...]
    status: str = "Local K section projection"


def build_local_k_section_projection_v1(
    project_state: Any,
    *,
    leg_id: str = "leg-001",
) -> LocalKSectionProjectionV1:
    """
    Build Local K section choices from the Basic PS read-only projection.

    Display/editor basis only:
    - no ProjectState mutation
    - no Local K persistence yet
    - no final balancing
    """
    basic_ps = build_basic_ps_readonly_projection_v1(
        project_state,
        leg_id=leg_id,
    )

    rows: list[LocalKSectionProjectionRowV1] = []

    for result in basic_ps.pipe_sizing_projection.results:
        rows.append(
            LocalKSectionProjectionRowV1(
                section_id=str(result.section_id),
                order=int(result.order),
                from_label=str(result.from_label),
                to_room_label=str(result.to_room_label),
                pipe_size_label=str(result.pipe_size_label),
                carried_flow_kg_s=float(result.carried_flow_kg_s),
                velocity_m_s=float(result.velocity_m_s),
                pressure_gradient_Pa_per_m=float(
                    result.pressure_gradient_Pa_per_m
                ),
                k_total=0.0,
                local_pressure_drop_Pa=0.0,
                status="Local K shell — no fittings persisted",
            )
        )

    return LocalKSectionProjectionV1(
        rows=tuple(rows),
        status="Local K section projection",
    )


def local_pressure_drop_from_k_v1(
    *,
    k_total: float,
    velocity_m_s: float,
    density_kg_m3: float = WATER_DENSITY_KG_M3,
) -> float:
    """
    Local pressure drop preview:

        Δp_local = K × ρ × v² / 2

    Preview only. Not final proportioning.
    """
    return float(k_total) * float(density_kg_m3) * float(velocity_m_s) ** 2 / 2.0