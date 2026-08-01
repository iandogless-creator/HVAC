# ======================================================================
# HVAC/hydronics/proportioning/common_main_leg_entry_pressure_authority_v1.py
# H-S42-A — Common-main / leg-entry length and Local-K pressure authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.local_losses.local_k_pressure_preview_v1 import (
    build_local_k_pressure_preview_v1,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.sizing.common_main_leg_entry_pipe_sizing_v1 import (
    build_common_main_leg_entry_pipe_sizing_v1,
)


@dataclass(frozen=True, slots=True)
class CommonMainLegEntryPressureRowV1:
    """Colebrook + persisted physical-length/Local-K evidence for one section."""

    section_id: str
    section_kind: str
    order: int
    takeoff_leg_id: str
    takeoff_leg_label: str
    from_label: str
    to_label: str

    carried_leg_ids: tuple[str, ...]
    carried_flow_kg_s: float
    pipe_size_label: str
    material: str
    dn: int

    length_m: float | None
    k_total: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool
    pressure_gradient_Pa_per_m: float

    straight_pressure_drop_Pa: float | None
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float | None
    complete: bool
    status: str
    # H-S63-B2B — exact material/bore evidence for later freezing.
    material_label: str = "Copper EN1057"
    internal_diameter_m: float | None = None
    material_roughness_m: float | None = None


@dataclass(frozen=True, slots=True)
class CommonMainLegEntryPressureProjectionV1:
    """
    H-S42-A read-only pressure-authority projection.

    Reads H-S40-B sizing and the existing LocalKIntentV1 entries keyed by the
    stable H-S40-A section IDs.  It does not persist calculated values, add RR
    allowance, accumulate routes, balance, select pumps/valves or resize pipe.
    """

    ready: bool
    complete: bool
    rows: tuple[CommonMainLegEntryPressureRowV1, ...]
    missing_section_ids: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    status: str = "H-S42-A common-main pressure authority not ready"


def build_common_main_leg_entry_pressure_authority_v1(
    project_state: Any,
) -> CommonMainLegEntryPressureProjectionV1:
    """Resolve each stable main section exactly once."""

    sizing = build_common_main_leg_entry_pipe_sizing_v1(project_state)
    if not sizing.ready:
        return CommonMainLegEntryPressureProjectionV1(
            ready=False,
            complete=False,
            rows=(),
            blockers=tuple(sizing.blockers or (sizing.status,)),
            status="H-S42-A blocked by H-S40-B sizing",
        )

    source_rows = tuple(sizing.rows)
    section_ids = tuple(row.section_id for row in source_rows)
    if len(set(section_ids)) != len(section_ids):
        return CommonMainLegEntryPressureProjectionV1(
            ready=False,
            complete=False,
            rows=(),
            blockers=("H-S40-B returned duplicate stable section IDs",),
            status="H-S42-A duplicate section identity blocker",
        )

    rows = tuple(
        _build_row_v1(project_state, source=row)
        for row in source_rows
    )
    missing = tuple(row.section_id for row in rows if not row.complete)
    complete = not missing
    return CommonMainLegEntryPressureProjectionV1(
        ready=True,
        complete=complete,
        rows=rows,
        missing_section_ids=missing,
        blockers=(),
        status=(
            "H-S42-A common-main / leg-entry Colebrook + Local K evidence ready"
            if complete
            else "H-S42-A incomplete — physical length/Local K evidence missing"
        ),
    )


def _build_row_v1(
    project_state: Any,
    *,
    source: Any,
) -> CommonMainLegEntryPressureRowV1:
    section_id = str(source.section_id)
    # H-S63-B2B — use exact sizing evidence, never parse display wording.
    material, dn = _basic_ps_main_pipe_identity_v1(source)
    section_intent = _section_intent_v1(project_state, section_id)
    raw_length = (
        getattr(section_intent, "length_m", None)
        if section_intent is not None
        else None
    )
    length_m = _positive_length_or_none_v1(raw_length)

    pressure = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=float(source.carried_flow_kg_s),
        material=material,
        dn=dn,
        length_m=float(length_m or 0.0),
        friction_method="colebrook",
    )
    local_k = build_local_k_pressure_preview_v1(
        project_state,
        section_id=section_id,
        velocity_m_s=float(pressure.velocity_m_s),
        pressure_gradient_Pa_per_m=float(pressure.pressure_gradient_pa_per_m),
    )

    converged = bool(pressure.colebrook_converged)
    complete = length_m is not None and converged
    straight_dp = (
        float(pressure.pressure_gradient_pa_per_m) * length_m
        if length_m is not None
        else None
    )
    local_dp = float(local_k.local_pressure_drop_Pa or 0.0)
    total_dp = straight_dp + local_dp if straight_dp is not None else None

    if section_intent is None:
        status = "Incomplete — no physical length / Local K intent"
    elif raw_length is None:
        status = "Incomplete — physical length not set"
    elif length_m is None:
        status = "Incomplete — physical length must be greater than zero"
    elif not converged:
        status = "Incomplete — Colebrook did not converge"
    else:
        status = "Colebrook + physical length + Local K evidence"

    return CommonMainLegEntryPressureRowV1(
        section_id=section_id,
        section_kind=str(source.section_kind),
        order=int(source.order),
        takeoff_leg_id=str(source.takeoff_leg_id),
        takeoff_leg_label=str(source.takeoff_leg_label),
        from_label=str(source.from_label),
        to_label=str(source.to_label),
        carried_leg_ids=tuple(source.carried_leg_ids),
        carried_flow_kg_s=float(source.carried_flow_kg_s),
        pipe_size_label=str(source.basic_pipe_size_label),
        material=material,
        dn=dn,
        length_m=length_m,
        k_total=float(local_k.k_total),
        velocity_m_s=float(pressure.velocity_m_s),
        reynolds_number=float(pressure.reynolds_number),
        friction_factor=float(pressure.selected_friction_factor),
        friction_method=str(pressure.friction_method),
        colebrook_iteration_count=int(pressure.colebrook_iteration_count),
        colebrook_converged=converged,
        pressure_gradient_Pa_per_m=float(pressure.pressure_gradient_pa_per_m),
        straight_pressure_drop_Pa=straight_dp,
        local_pressure_drop_Pa=local_dp,
        section_total_pressure_drop_Pa=total_dp,
        complete=complete,
        status=status,
        material_label=str(source.basic_material_label),
        internal_diameter_m=float(pressure.internal_diameter_m),
        material_roughness_m=float(pressure.roughness_m),
    )


def _section_intent_v1(project_state: Any, section_id: str) -> Any:
    intent = getattr(project_state, "hydronic_local_k_intent", None)
    return getattr(intent, "sections", {}).get(section_id) if intent else None


def _positive_length_or_none_v1(value: Any) -> float | None:
    if value is None:
        return None
    try:
        resolved = float(value)
    except (TypeError, ValueError):
        return None
    return resolved if resolved > 0.0 else None


def _basic_ps_main_pipe_identity_v1(source: Any) -> tuple[str, int]:
    """H-S63-B2B — require exact main/entry family and size evidence."""

    material_key = str(
        getattr(source, "basic_material_key", "") or ""
    ).strip().lower()
    raw_size_key = getattr(source, "basic_pipe_size_key", None)
    try:
        pipe_size_key = int(raw_size_key)
    except (TypeError, ValueError):
        pipe_size_key = 0
    if not material_key:
        raise ValueError("Basic PS main pressure evidence requires material_key")
    if pipe_size_key <= 0:
        raise ValueError("Basic PS main pressure evidence requires pipe_size_key")
    return material_key, pipe_size_key
