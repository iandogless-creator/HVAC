# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_controlled_circuit_dp_authority_v1.py
# H-S45-A — Point-scoped controlled-circuit pressure authority
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any, Iterable, Mapping

from HVAC.hydronics.proportioning.balancing_point_valve_authority_input_mapping_v1 import (
    BalancingPointValveAuthorityInputMappingV1,
    BalancingPointValveAuthorityInputRowV1,
)
from HVAC.hydronics.proportioning.controlled_circuit_dp_basis_v1 import (
    resolve_controlled_circuit_dp_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    VALVE_AUTHORITY_NONE_REQUIRED,
)


POINT_GOVERNED_ROUTE_CHOSEN_DP_V1 = "point_governed_route_chosen_dp"
POINT_CONTROLLED_CIRCUIT_NOT_REQUIRED_V1 = "not_required"
_NUMBER_RE_V1 = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


@dataclass(frozen=True, slots=True)
class BalancingPointControlledCircuitDpRowV1(
    BalancingPointValveAuthorityInputRowV1
):
    """H-S44-D row plus selected, provenance-preserving circuit pressure."""

    controlled_circuit_basis_id: str = ""
    governed_route_dp_evidence: tuple[tuple[str, float], ...] = ()
    controlling_route_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BalancingPointControlledCircuitDpAuthorityV1:
    """
    H-S45-A point-scoped controlled-circuit pressure authority.

    Existing mains-inclusive chosen-route pressure evidence is selected, never
    summed or recalculated. This projection does not calculate an authority
    ratio, choose a valve product, calculate/select Kv or Kvs, infer physical
    valve position, choose a pump, resize pipe, persist intent, or perform
    final balancing.
    """

    schema: str = "balancing_point_controlled_circuit_dp_authority_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[BalancingPointControlledCircuitDpRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No valve-authority ratio calculated",
        "No final authority classification",
        "No valve product selected",
        "No Kv or Kvs calculated or selected",
        "No physical valve position inferred",
        "No pump selected",
        "No pipe resizing",
        "No persistence mutation",
        "No final balancing",
        "No ProjectState mutation",
    )
    note: str = (
        "Shared points select the highest existing chosen Δp among governed "
        "routes; route-exclusive points select their sole governed route."
    )


def build_balancing_point_controlled_circuit_dp_authority_v1(
    valve_inputs: BalancingPointValveAuthorityInputMappingV1 | None,
    chosen_basis_route_pressure_rows: Iterable[Any],
    *,
    dp_tolerance_pa: float = 0.05,
) -> BalancingPointControlledCircuitDpAuthorityV1:
    """Select canonical chosen-route pressure for each H-S44 point duty."""

    if valve_inputs is None:
        return _blocked_projection("H-S44-D point valve-authority inputs required")
    if not isinstance(valve_inputs, BalancingPointValveAuthorityInputMappingV1):
        return _blocked_projection(
            "valve_inputs is not BalancingPointValveAuthorityInputMappingV1"
        )
    if dp_tolerance_pa < 0.0:
        return _blocked_projection("dp_tolerance_pa must be zero or greater")

    input_rows = tuple(valve_inputs.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S44-D point valve-authority input rows required",
            *tuple(valve_inputs.blockers or ()),
        )

    point_ids = tuple(str(row.balancing_point_id or "") for row in input_rows)
    if any(not point_id for point_id in point_ids):
        return _blocked_projection("Every H-S44-D row requires balancing_point_id")
    duplicates = sorted(
        {point_id for point_id in point_ids if point_ids.count(point_id) > 1}
    )
    if duplicates:
        return _blocked_projection(
            "Duplicate H-S44-D balancing_point_id values: " + ", ".join(duplicates)
        )

    chosen_rows = tuple(chosen_basis_route_pressure_rows or ())
    rows = tuple(
        _resolve_point_row_v1(
            input_row,
            chosen_rows=chosen_rows,
            dp_tolerance_pa=dp_tolerance_pa,
        )
        for input_row in input_rows
    )
    upstream_blockers = tuple(
        f"H-S44-D: {value}" for value in tuple(valve_inputs.blockers or ())
    )
    row_blockers = tuple(
        f"{row.balancing_point_id}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    blockers = _unique_v1((*upstream_blockers, *row_blockers))
    ready = bool(valve_inputs.ready) and not blockers and all(row.ready for row in rows)
    if not valve_inputs.ready and not blockers:
        blockers = ("H-S44-D point valve-authority input mapping is not ready",)
        ready = False

    return BalancingPointControlledCircuitDpAuthorityV1(
        ready=ready,
        status=(
            "Ready — point-scoped controlled-circuit Δp authority available"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_point_row_v1(
    input_row: BalancingPointValveAuthorityInputRowV1,
    *,
    chosen_rows: tuple[Any, ...],
    dp_tolerance_pa: float,
) -> BalancingPointControlledCircuitDpRowV1:
    common = asdict(input_row)
    common["authority"] = None
    existing_blockers = list(input_row.blockers or ())

    if input_row.authority_band_id == VALVE_AUTHORITY_NONE_REQUIRED:
        common.update(
            ready=bool(input_row.ready) and not existing_blockers,
            controlled_circuit_dp_pa=None,
            status="No controlled-circuit Δp required — no point valve duty",
            blockers=_unique_v1(tuple(str(value) for value in existing_blockers)),
            note=(
                str(input_row.note or "")
                + " H-S45-A pressure selection is dormant for this point."
            ).strip(),
        )
        return BalancingPointControlledCircuitDpRowV1(
            **common,
            controlled_circuit_basis_id=POINT_CONTROLLED_CIRCUIT_NOT_REQUIRED_V1,
            governed_route_dp_evidence=(),
            controlling_route_ids=(),
        )

    if not input_row.ready and not existing_blockers:
        existing_blockers.append("H-S44-D point input is not ready")

    governed_ids = tuple(str(value or "").strip() for value in input_row.downstream_route_ids)
    if not governed_ids or any(not route_id for route_id in governed_ids):
        existing_blockers.append("Governed route ids required")

    evidence: list[tuple[str, float]] = []
    for route_id in governed_ids:
        value, blockers = _chosen_dp_for_route_v1(route_id, chosen_rows)
        existing_blockers.extend(blockers)
        if value is not None:
            evidence.append((route_id, value))

    if existing_blockers:
        clean = _unique_v1(tuple(str(value) for value in existing_blockers))
        common.update(
            ready=False,
            controlled_circuit_dp_pa=None,
            status="Blocked — " + "; ".join(clean),
            blockers=clean,
            note="No point-scoped controlled-circuit Δp released.",
        )
        return BalancingPointControlledCircuitDpRowV1(
            **common,
            controlled_circuit_basis_id=POINT_GOVERNED_ROUTE_CHOSEN_DP_V1,
            governed_route_dp_evidence=tuple(evidence),
            controlling_route_ids=(),
        )

    selected_dp = max(value for _, value in evidence)
    controlling_ids = tuple(
        route_id
        for route_id, value in evidence
        if math.isclose(value, selected_dp, rel_tol=1e-9, abs_tol=dp_tolerance_pa)
    )
    resolution = resolve_controlled_circuit_dp_v1(
        route_chosen_dp_pa=selected_dp,
        required_added_dp_pa=input_row.design_valve_dp_pa,
    )
    if not resolution.ready or resolution.controlled_circuit_dp_pa is None:
        clean = _unique_v1(tuple(resolution.blockers or ())) or (
            "Controlled-circuit Δp resolver did not release a value",
        )
        common.update(
            ready=False,
            controlled_circuit_dp_pa=None,
            status="Blocked — " + "; ".join(clean),
            blockers=clean,
            note="No point-scoped controlled-circuit Δp released.",
        )
        return BalancingPointControlledCircuitDpRowV1(
            **common,
            controlled_circuit_basis_id=POINT_GOVERNED_ROUTE_CHOSEN_DP_V1,
            governed_route_dp_evidence=tuple(evidence),
            controlling_route_ids=controlling_ids,
        )

    common.update(
        ready=True,
        controlled_circuit_dp_pa=float(resolution.controlled_circuit_dp_pa),
        authority=None,
        status=(
            "Ready — highest governed chosen-route Δp selected once"
            if input_row.is_shared
            else "Ready — route-exclusive chosen-route Δp selected once"
        ),
        blockers=(),
        note=(
            str(input_row.note or "")
            + " H-S45-A uses existing mains-inclusive chosen-route Δp; route "
            "pressures are not summed and provisional valve Δp is not added. "
            "No physical valve position is inferred."
        ).strip(),
    )
    return BalancingPointControlledCircuitDpRowV1(
        **common,
        controlled_circuit_basis_id=POINT_GOVERNED_ROUTE_CHOSEN_DP_V1,
        governed_route_dp_evidence=tuple(evidence),
        controlling_route_ids=controlling_ids,
    )


def _chosen_dp_for_route_v1(
    stable_route_id: str,
    chosen_rows: tuple[Any, ...],
) -> tuple[float | None, tuple[str, ...]]:
    matches = tuple(
        row for row in chosen_rows
        if _route_row_matches_v1(row, stable_route_id)
    )
    if not matches:
        return None, (f"{stable_route_id}: chosen-route Δp evidence missing",)
    if len(matches) > 1:
        return None, (f"{stable_route_id}: duplicate chosen-route Δp evidence",)
    value = _number_v1(_read_any_v1(matches[0], "chosen_dp_pa", "chosen_dp"))
    if value is None or value <= 0.0:
        return None, (f"{stable_route_id}: positive chosen-route Δp required",)
    return value, ()


def _route_row_matches_v1(row: Any, stable_route_id: str) -> bool:
    wanted = str(stable_route_id or "").strip()
    for name in ("route_id", "subleg_id", "stable_route_id"):
        candidate = str(_read_any_v1(row, name, default="") or "").strip()
        if candidate == wanted or candidate.endswith(":" + wanted):
            return True
    return False


def _read_any_v1(row: Any, *names: str, default=None):
    if isinstance(row, Mapping):
        for name in names:
            if name in row:
                return row[name]
        return default
    for name in names:
        if hasattr(row, name):
            return getattr(row, name)
    return default


def _number_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    match = _NUMBER_RE_V1.search(str(value).replace(",", ""))
    if match is None:
        return None
    try:
        number = float(match.group(0))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(*blockers: str) -> BalancingPointControlledCircuitDpAuthorityV1:
    clean = _unique_v1(tuple(blockers))
    return BalancingPointControlledCircuitDpAuthorityV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        rows=(),
    )
