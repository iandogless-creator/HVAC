# ======================================================================
# HVAC/hydronics/proportioning/valve_authority_input_mapping_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED as BALANCING_MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
    build_valve_authority_design_model_v1,
    valve_authority_design_model_to_dict_v1,
)


_EXCLUSIONS_V1: tuple[str, ...] = (
    "No valve product selected",
    "No Kv or Kvs selected",
    "No lockshield turn count",
    "No manufacturer valve data",
    "No pump selected",
    "No final balancing",
    "No pipe resizing",
    "No ProjectState mutation",
)


@dataclass(frozen=True, slots=True)
class ValveAuthorityInputRowV1:
    """
    H-S32-B:
    Route-level valve authority input preview.

    This maps balancing method candidates to valve-authority input states.

    It does not:
        • calculate final authority unless controlled circuit Δp is available
        • select a valve product
        • select Kv / Kvs
        • calculate lockshield turns
        • use manufacturer valve data
        • select a pump
        • perform final balancing
        • resize pipes
        • mutate ProjectState
    """

    route: str = "—"
    balancing_method_id: str = BALANCING_MANUAL_REVIEW_REQUIRED
    balancing_method_label: str = "Manual review required"

    authority_band_id: str = MANUAL_REVIEW_REQUIRED
    authority_label: str = "Manual review required"

    ready: bool = False
    design_valve_dp_pa: float | None = None
    route_flow_kg_s: float | None = None
    candidate_resistance_pa_per_kg_s2: float | None = None
    controlled_circuit_dp_pa: float | None = None
    authority: float | None = None

    status: str = ""
    blockers: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class ValveAuthorityInputMappingV1:
    """
    H-S32-B:
    Map balancing method candidates to valve-authority input rows.

    Mapping authority only:
        no valve product selected
        no Kv / Kvs selected
        no lockshield turn count
        no manufacturer valve data
        no pump selected
        no final balancing
        no pipe resizing
        no ProjectState mutation
    """

    schema: str = "valve_authority_input_mapping_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ValveAuthorityInputRowV1, ...] = ()
    design_model: dict[str, Any] | None = None
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Valve authority input mapping only — no valve sizing, no Kv/Kvs, "
        "no valve product selection, no pump selection, and no final balancing."
    )


def _row_to_dict_v1(row: object) -> dict[str, object]:
    if row is None:
        return {}

    if isinstance(row, dict):
        return dict(row)

    if is_dataclass(row):
        return asdict(row)

    data: dict[str, object] = {}

    for name in (
            "route",
            "method_id",
            "method_label",
            "ready",
            "required_added_dp_pa",
            "flow_kg_s",
            "resistance_pa_per_kg_s2",
            "status",
            "blockers",
            "note",
    ):
        if hasattr(row, name):
            data[name] = getattr(row, name)

    return data


def _candidate_rows_v1(candidate_mapping: object) -> tuple[object, ...]:
    if candidate_mapping is None:
        return ()

    if isinstance(candidate_mapping, (list, tuple)):
        return tuple(candidate_mapping)

    return tuple(getattr(candidate_mapping, "candidates", ()) or ())


def _float_or_none_v1(value: object) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _blockers_v1(value: object) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()

    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())

    return (str(value),)


def _input_row_from_candidate_v1(candidate: object) -> ValveAuthorityInputRowV1:
    data = _row_to_dict_v1(candidate)

    route = str(data.get("route") or "—")
    method_id = str(
        data.get("method_id")
        or BALANCING_MANUAL_REVIEW_REQUIRED
    )
    method_label = str(data.get("method_label") or "Manual review required")

    candidate_blockers = _blockers_v1(data.get("blockers"))
    required_added_dp_pa = _float_or_none_v1(data.get("required_added_dp_pa"))
    route_flow_kg_s = _float_or_none_v1(data.get("flow_kg_s"))
    resistance = _float_or_none_v1(data.get("resistance_pa_per_kg_s2"))

    if method_id == NONE_REQUIRED:
        return ValveAuthorityInputRowV1(
            route=route,
            balancing_method_id=method_id,
            balancing_method_label=method_label,
            authority_band_id=VALVE_AUTHORITY_NONE_REQUIRED,
            authority_label="No valve authority required",
            ready=True,
            design_valve_dp_pa=required_added_dp_pa,
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            status=(
                "No valve authority required — no added balancing "
                "resistance burden"
            ),
            blockers=(),
            note=(
                "Used for controlling or zero-burden routes; does not prove "
                "final hydraulic balance."
            ),
        )

    if method_id == PROPORTIONAL_ADDED_RESISTANCE:
        blockers: list[str] = []

        if required_added_dp_pa is None or required_added_dp_pa <= 0.0:
            blockers.append("Positive design valve/throttling Δp required")

        if route_flow_kg_s is None or route_flow_kg_s <= 0.0:
            blockers.append("Positive route flow kg/s required")

        if resistance is None or resistance <= 0.0:
            blockers.append("Positive candidate resistance required")

        if blockers:
            return ValveAuthorityInputRowV1(
                route=route,
                balancing_method_id=method_id,
                balancing_method_label=method_label,
                authority_band_id=MANUAL_REVIEW_REQUIRED,
                authority_label="Manual review required",
                ready=False,
                design_valve_dp_pa=required_added_dp_pa,
                route_flow_kg_s=route_flow_kg_s,
                candidate_resistance_pa_per_kg_s2=resistance,
                status="Blocked — " + "; ".join(blockers),
                blockers=tuple(blockers),
                note=(
                    "Valve authority input requires positive Δp, flow, and "
                    "candidate resistance before controlled circuit Δp is "
                    "considered."
                ),
            )

        return ValveAuthorityInputRowV1(
            route=route,
            balancing_method_id=method_id,
            balancing_method_label=method_label,
            authority_band_id=VALVE_AUTHORITY_INPUT_AVAILABLE,
            authority_label="Valve authority input available",
            ready=True,
            design_valve_dp_pa=required_added_dp_pa,
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_dp_pa=None,
            authority=None,
            status=(
                "Input available — pending controlled circuit Δp before "
                "authority classification"
            ),
            blockers=(),
            note=(
                "Required added Δp is treated as theoretical valve/throttling "
                "Δp. No Kv/Kvs or valve product is selected."
            ),
        )

    blockers = candidate_blockers or (
        "Balancing method requires manual review",
    )

    return ValveAuthorityInputRowV1(
        route=route,
        balancing_method_id=method_id,
        balancing_method_label=method_label,
        authority_band_id=MANUAL_REVIEW_REQUIRED,
        authority_label="Manual review required",
        ready=False,
        design_valve_dp_pa=required_added_dp_pa,
        route_flow_kg_s=route_flow_kg_s,
        candidate_resistance_pa_per_kg_s2=resistance,
        status="Manual review required — " + "; ".join(blockers),
        blockers=tuple(blockers),
        note="No valve-authority input is produced for this row.",
    )


def build_valve_authority_input_mapping_v1(
        balancing_candidate_mapping: object,
) -> ValveAuthorityInputMappingV1:
    """
    Build H-S32-B valve-authority input rows from H-S31 balancing candidates.

    Pure mapping:
        no ProjectState mutation
        no GUI dependency
        no file export
        no valve product selection
        no Kv / Kvs selection
        no lockshield turns
        no manufacturer valve data
        no pump sizing
        no final balancing
    """
    candidates = _candidate_rows_v1(balancing_candidate_mapping)
    design_model = build_valve_authority_design_model_v1()

    if not candidates:
        return ValveAuthorityInputMappingV1(
            ready=False,
            status="Blocked — balancing method candidates required",
            blockers=("Balancing method candidates required",),
            rows=(),
            design_model=valve_authority_design_model_to_dict_v1(
                design_model
            ),
        )

    rows = tuple(
        _input_row_from_candidate_v1(candidate)
        for candidate in candidates
    )

    blockers = tuple(
        f"{row.route}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )

    ready = not blockers

    status = (
        "Ready — valve authority input mapping available"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return ValveAuthorityInputMappingV1(
        ready=ready,
        status=status,
        blockers=blockers,
        rows=rows,
        design_model=valve_authority_design_model_to_dict_v1(design_model),
    )


def valve_authority_input_mapping_to_dict_v1(
        mapping: ValveAuthorityInputMappingV1 | None,
) -> dict[str, Any] | None:
    if mapping is None:
        return None

    return {
        "schema": mapping.schema,
        "ready": mapping.ready,
        "status": mapping.status,
        "blockers": tuple(mapping.blockers),
        "rows": tuple(asdict(row) for row in mapping.rows),
        "design_model": mapping.design_model,
        "exclusions": tuple(mapping.exclusions),
        "note": mapping.note,
    }
