# ======================================================================
# H-S47-A — Point-scoped required Kv preview
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from HVAC.core.flow_units import flow_from_kg_s
from HVAC.hydronics.proportioning.balancing_point_valve_duty_design_basis_v1 import (
    NO_VALVE_DUTY_REQUIRED,
    POINT_VALVE_DUTY_BASIS_AVAILABLE,
    BalancingPointValveDutyDesignBasisRowV1,
    BalancingPointValveDutyDesignBasisV1,
)


DEFAULT_KV_WATER_DENSITY_KG_M3 = 998.0
KV_WATER_DENSITY_BASIS_V1 = "hydronic_water_density_998_kg_m3"
NO_REQUIRED_KV = "no_required_kv"
REQUIRED_KV_PREVIEW_AVAILABLE = "required_kv_preview_available"
REQUIRED_KV_EVIDENCE_UNAVAILABLE = "required_kv_evidence_unavailable"
KV_FORMULA_V1 = "Kv = flow_m3_h / sqrt(design_valve_dp_bar)"


@dataclass(frozen=True, slots=True)
class BalancingPointRequiredKvPreviewRowV1(
    BalancingPointValveDutyDesignBasisRowV1
):
    """H-S46-A point duty plus transparent required-Kv evidence."""

    required_kv_state_id: str = ""
    required_kv_available: bool = False
    flow_m3_h: float | None = None
    design_valve_dp_bar: float | None = None
    required_kv: float | None = None
    fluid_density_kg_m3: float | None = None
    fluid_density_basis_id: str = ""
    kv_formula: str = KV_FORMULA_V1


@dataclass(frozen=True, slots=True)
class BalancingPointRequiredKvPreviewV1:
    """
    H-S47-A required-Kv preview evidence.

    Required Kv is calculated only where H-S46-A exposes a point valve-duty
    basis. It does not choose Kvs, a valve size, a product, a setting, a pump,
    or a final balancing result, and it grants no engineering approval.
    """

    schema: str = "balancing_point_required_kv_preview_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointRequiredKvPreviewRowV1, ...] = ()
    fluid_density_kg_m3: float = DEFAULT_KV_WATER_DENSITY_KG_M3
    fluid_density_basis_id: str = KV_WATER_DENSITY_BASIS_V1
    exclusions: tuple[str, ...] = (
        "No engineering approval granted",
        "No Kvs candidate selected",
        "No valve selected",
        "No valve size selected",
        "No valve product selected",
        "No lockshield setting selected",
        "No design valve pressure changed",
        "No pipe restriction added",
        "No pipe resizing",
        "No pump selected",
        "No hydraulic recalculation outside required Kv",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Required Kv is preview evidence only; manual engineering approval "
        "remains pending."
    )


def calculate_required_kv_v1(
    *,
    mass_flow_kg_s: float,
    design_valve_dp_pa: float,
    fluid_density_kg_m3: float = DEFAULT_KV_WATER_DENSITY_KG_M3,
) -> tuple[float, float, float]:
    """Return (flow m³/h, valve Δp bar, required Kv)."""

    flow_value = _positive_finite_v1(mass_flow_kg_s)
    dp_value = _positive_finite_v1(design_valve_dp_pa)
    density_value = _positive_finite_v1(fluid_density_kg_m3)
    if flow_value is None:
        raise ValueError("mass_flow_kg_s must be positive and finite")
    if dp_value is None:
        raise ValueError("design_valve_dp_pa must be positive and finite")
    if density_value is None:
        raise ValueError("fluid_density_kg_m3 must be positive and finite")

    flow_m3_h = flow_from_kg_s(
        flow_value,
        density_kg_m3=density_value,
    ).m3_h
    design_valve_dp_bar = dp_value / 100_000.0
    required_kv = flow_m3_h / math.sqrt(design_valve_dp_bar)
    return flow_m3_h, design_valve_dp_bar, required_kv


def build_balancing_point_required_kv_preview_v1(
    duty_basis: BalancingPointValveDutyDesignBasisV1 | None,
    *,
    fluid_density_kg_m3: float = DEFAULT_KV_WATER_DENSITY_KG_M3,
) -> BalancingPointRequiredKvPreviewV1:
    """Calculate required Kv only for H-S46-A valve-duty points."""

    density = _positive_finite_v1(fluid_density_kg_m3)
    if density is None:
        return _blocked_projection(
            "Positive finite fluid density required",
            fluid_density_kg_m3=DEFAULT_KV_WATER_DENSITY_KG_M3,
        )
    if duty_basis is None:
        return _blocked_projection(
            "H-S46-A point valve-duty design basis required",
            fluid_density_kg_m3=density,
        )
    if not isinstance(duty_basis, BalancingPointValveDutyDesignBasisV1):
        return _blocked_projection(
            "duty_basis is not BalancingPointValveDutyDesignBasisV1",
            fluid_density_kg_m3=density,
        )

    input_rows = tuple(duty_basis.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S46-A point valve-duty rows required",
            *tuple(duty_basis.blockers or ()),
            fluid_density_kg_m3=density,
        )

    rows = tuple(
        _resolve_row_v1(row, fluid_density_kg_m3=density)
        for row in input_rows
    )
    upstream_blockers = tuple(
        f"H-S46-A: {value}" for value in tuple(duty_basis.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = (
        bool(duty_basis.ready)
        and not blockers
        and all(row.ready for row in rows)
    )
    if not duty_basis.ready and not blockers:
        blockers = ("H-S46-A point valve-duty design basis is not ready",)
        ready = False

    calculated_count = sum(1 for row in rows if row.required_kv_available)
    return BalancingPointRequiredKvPreviewV1(
        ready=ready,
        status=(
            f"Ready — required Kv preview available at {calculated_count} "
            "point(s); manual engineering approval pending"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
        fluid_density_kg_m3=density,
    )


def _resolve_row_v1(
    input_row: BalancingPointValveDutyDesignBasisRowV1,
    *,
    fluid_density_kg_m3: float,
) -> BalancingPointRequiredKvPreviewRowV1:
    common = asdict(input_row)
    existing_blockers = _unique_v1(tuple(input_row.blockers or ()))

    if input_row.valve_duty_state_id == NO_VALVE_DUTY_REQUIRED:
        common.update(
            ready=bool(input_row.ready) and not existing_blockers,
            status="No required Kv — no valve duty",
            blockers=existing_blockers,
            note=(
                str(input_row.note or "")
                + " H-S47-A calculation is dormant for this point."
            ).strip(),
        )
        return BalancingPointRequiredKvPreviewRowV1(
            **common,
            required_kv_state_id=NO_REQUIRED_KV,
            required_kv_available=False,
            fluid_density_kg_m3=fluid_density_kg_m3,
            fluid_density_basis_id=KV_WATER_DENSITY_BASIS_V1,
        )

    blockers = list(existing_blockers)
    if (
        not input_row.ready
        or not input_row.valve_duty_required
        or not input_row.valve_duty_basis_available
        or input_row.valve_duty_state_id != POINT_VALVE_DUTY_BASIS_AVAILABLE
    ):
        blockers.append("H-S46-A point valve-duty basis unavailable")

    if blockers:
        clean = _unique_v1(tuple(blockers))
        common.update(
            ready=False,
            status="Blocked — required Kv evidence unavailable",
            blockers=clean,
            note="No required Kv released.",
        )
        return BalancingPointRequiredKvPreviewRowV1(
            **common,
            required_kv_state_id=REQUIRED_KV_EVIDENCE_UNAVAILABLE,
            required_kv_available=False,
            fluid_density_kg_m3=fluid_density_kg_m3,
            fluid_density_basis_id=KV_WATER_DENSITY_BASIS_V1,
        )

    try:
        flow_m3_h, design_dp_bar, required_kv = calculate_required_kv_v1(
            mass_flow_kg_s=input_row.point_flow_kg_s,
            design_valve_dp_pa=input_row.design_valve_dp_pa,
            fluid_density_kg_m3=fluid_density_kg_m3,
        )
    except ValueError as exc:
        blocker = str(exc)
        common.update(
            ready=False,
            status="Blocked — " + blocker,
            blockers=(blocker,),
            note="No required Kv released.",
        )
        return BalancingPointRequiredKvPreviewRowV1(
            **common,
            required_kv_state_id=REQUIRED_KV_EVIDENCE_UNAVAILABLE,
            required_kv_available=False,
            fluid_density_kg_m3=fluid_density_kg_m3,
            fluid_density_basis_id=KV_WATER_DENSITY_BASIS_V1,
        )

    common.update(
        ready=True,
        status="Required Kv preview available — manual approval pending",
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S47-A uses canonical flow conversion and the stated water "
            "density; no Kvs candidate or valve is selected."
        ).strip(),
    )
    return BalancingPointRequiredKvPreviewRowV1(
        **common,
        required_kv_state_id=REQUIRED_KV_PREVIEW_AVAILABLE,
        required_kv_available=True,
        flow_m3_h=flow_m3_h,
        design_valve_dp_bar=design_dp_bar,
        required_kv=required_kv,
        fluid_density_kg_m3=fluid_density_kg_m3,
        fluid_density_basis_id=KV_WATER_DENSITY_BASIS_V1,
    )


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(
    *blockers: str,
    fluid_density_kg_m3: float,
) -> BalancingPointRequiredKvPreviewV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointRequiredKvPreviewV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
        fluid_density_kg_m3=fluid_density_kg_m3,
    )
