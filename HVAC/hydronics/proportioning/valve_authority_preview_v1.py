# ======================================================================
# HVAC/hydronics/proportioning/valve_authority_preview_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any

from HVAC.hydronics.proportioning.controlled_circuit_dp_basis_v1 import (
    ROUTE_CHOSEN_DP,
    controlled_circuit_dp_basis_model_to_dict_v1,
    build_controlled_circuit_dp_basis_model_v1,
    resolve_controlled_circuit_dp_v1,
)
from HVAC.hydronics.proportioning.valve_authority_design_v1 import (
    ACCEPTABLE_AUTHORITY_PREVIEW,
    HIGH_THROTTLING_BURDEN,
    MANUAL_REVIEW_REQUIRED,
    TOO_LOW_AUTHORITY_PREVIEW,
    VALVE_AUTHORITY_INPUT_AVAILABLE,
    VALVE_AUTHORITY_NONE_REQUIRED,
    classify_valve_authority_band_v1,
)


_NUMBER_RE_V1 = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")

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


_BAND_LABELS_V1: dict[str, str] = {
    VALVE_AUTHORITY_NONE_REQUIRED: "No valve authority required",
    VALVE_AUTHORITY_INPUT_AVAILABLE: "Valve authority input available",
    TOO_LOW_AUTHORITY_PREVIEW: "Too low authority preview",
    ACCEPTABLE_AUTHORITY_PREVIEW: "Acceptable authority preview",
    HIGH_THROTTLING_BURDEN: "High throttling burden",
    MANUAL_REVIEW_REQUIRED: "Manual review required",
}


@dataclass(frozen=True, slots=True)
class ValveAuthorityPreviewRowV1:
    """
    H-S32-F:
    Route-level valve authority preview row.

    Preview only:
        • calculates authority ratio where inputs are available
        • classifies authority band
        • does not select valve product
        • does not calculate Kv / Kvs
        • does not calculate lockshield turns
        • does not use manufacturer valve data
        • does not select pump
        • does not perform final balancing
        • does not resize pipes
        • does not mutate ProjectState
    """

    route: str = "—"
    balancing_method_label: str = "—"

    ready: bool = False
    design_valve_dp_pa: float | None = None
    controlled_circuit_dp_pa: float | None = None
    authority: float | None = None

    authority_band_id: str = MANUAL_REVIEW_REQUIRED
    authority_label: str = "Manual review required"

    route_flow_kg_s: float | None = None
    candidate_resistance_pa_per_kg_s2: float | None = None

    controlled_circuit_basis_id: str = ROUTE_CHOSEN_DP
    status: str = ""
    blockers: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class ValveAuthorityPreviewV1:
    """
    H-S32-F:
    Valve authority preview.

    This is a preview calculation only.
    """

    schema: str = "valve_authority_preview_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[ValveAuthorityPreviewRowV1, ...] = ()
    controlled_circuit_basis_model: dict[str, Any] | None = None
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Valve authority preview only — no valve sizing, no Kv/Kvs, "
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
            "route_id",
            "balancing_method_label",
            "authority_band_id",
            "authority_label",
            "ready",
            "design_valve_dp_pa",
            "route_flow_kg_s",
            "candidate_resistance_pa_per_kg_s2",
            "controlled_circuit_dp_pa",
            "authority",
            "status",
            "blockers",
            "note",
            "chosen_dp_pa",
            "chosen_dp",
            "route_chosen_dp_pa",
    ):
        if hasattr(row, name):
            data[name] = getattr(row, name)

    return data


def _normalise_key_v1(value: object) -> str:
    return str(value or "").strip().lower()


def _parse_float_v1(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return float(value)

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "").strip()

    if not text or text in {"—", "-", "None", "none", "null"}:
        return None

    match = _NUMBER_RE_V1.search(text)

    if match is None:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def _input_rows_v1(input_mapping: object) -> tuple[object, ...]:
    if input_mapping is None:
        return ()

    if isinstance(input_mapping, (list, tuple)):
        return tuple(input_mapping)

    return tuple(getattr(input_mapping, "rows", ()) or ())


def _blockers_v1(value: object) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()

    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())

    return (str(value),)


def _route_pressure_lookup_v1(
        route_pressure_rows: object,
) -> dict[str, float]:
    lookup: dict[str, float] = {}

    for row in list(route_pressure_rows or ()):
        data = _row_to_dict_v1(row)

        route = _normalise_key_v1(
            data.get("route")
            or data.get("route_id")
            or ""
        )

        chosen_dp = (
            _parse_float_v1(data.get("route_chosen_dp_pa"))
            or _parse_float_v1(data.get("chosen_dp_pa"))
            or _parse_float_v1(data.get("chosen_dp"))
        )

        if route and chosen_dp is not None:
            lookup[route] = chosen_dp

    return lookup


def _lookup_route_chosen_dp_v1(
        *,
        route: str,
        lookup: dict[str, float],
) -> float | None:
    key = _normalise_key_v1(route)

    if key in lookup:
        return lookup[key]

    for candidate_key, value in lookup.items():
        if key and (key in candidate_key or candidate_key in key):
            return value

    return None


def _authority_v1(
        *,
        design_valve_dp_pa: float,
        controlled_circuit_dp_pa: float,
) -> float | None:
    denominator = design_valve_dp_pa + controlled_circuit_dp_pa

    if denominator <= 0.0:
        return None

    return design_valve_dp_pa / denominator


def _preview_row_from_input_v1(
        input_row: object,
        *,
        route_chosen_dp_lookup: dict[str, float],
        controlled_circuit_basis_id: str,
) -> ValveAuthorityPreviewRowV1:
    data = _row_to_dict_v1(input_row)

    route = str(data.get("route") or "—")
    balancing_method_label = str(
        data.get("balancing_method_label") or "—"
    )

    input_band_id = str(
        data.get("authority_band_id") or MANUAL_REVIEW_REQUIRED
    )
    input_label = str(
        data.get("authority_label")
        or _BAND_LABELS_V1.get(input_band_id, "Manual review required")
    )

    design_valve_dp_pa = _parse_float_v1(data.get("design_valve_dp_pa"))
    route_flow_kg_s = _parse_float_v1(data.get("route_flow_kg_s"))
    resistance = _parse_float_v1(
        data.get("candidate_resistance_pa_per_kg_s2")
    )

    source_blockers = _blockers_v1(data.get("blockers"))

    if input_band_id == VALVE_AUTHORITY_NONE_REQUIRED:
        return ValveAuthorityPreviewRowV1(
            route=route,
            balancing_method_label=balancing_method_label,
            ready=True,
            design_valve_dp_pa=design_valve_dp_pa,
            controlled_circuit_dp_pa=None,
            authority=None,
            authority_band_id=VALVE_AUTHORITY_NONE_REQUIRED,
            authority_label="No valve authority required",
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
            status="No valve authority preview required",
            blockers=(),
            note=(
                "No added balancing resistance burden; this does not prove "
                "final hydraulic balance."
            ),
        )

    if input_band_id != VALVE_AUTHORITY_INPUT_AVAILABLE:
        blockers = source_blockers or (
            "Valve authority input is not available",
        )

        return ValveAuthorityPreviewRowV1(
            route=route,
            balancing_method_label=balancing_method_label,
            ready=False,
            design_valve_dp_pa=design_valve_dp_pa,
            controlled_circuit_dp_pa=None,
            authority=None,
            authority_band_id=MANUAL_REVIEW_REQUIRED,
            authority_label="Manual review required",
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
            status="Manual review required — " + "; ".join(blockers),
            blockers=tuple(blockers),
            note="No authority preview calculated for this row.",
        )

    blockers: list[str] = []

    if design_valve_dp_pa is None or design_valve_dp_pa <= 0.0:
        blockers.append("Positive design valve Δp required")

    route_chosen_dp_pa = _lookup_route_chosen_dp_v1(
        route=route,
        lookup=route_chosen_dp_lookup,
    )

    resolution = resolve_controlled_circuit_dp_v1(
        basis_id=controlled_circuit_basis_id,
        route_chosen_dp_pa=route_chosen_dp_pa,
        required_added_dp_pa=design_valve_dp_pa,
    )

    if not resolution.ready:
        blockers.extend(resolution.blockers)

    if blockers:
        return ValveAuthorityPreviewRowV1(
            route=route,
            balancing_method_label=balancing_method_label,
            ready=False,
            design_valve_dp_pa=design_valve_dp_pa,
            controlled_circuit_dp_pa=None,
            authority=None,
            authority_band_id=MANUAL_REVIEW_REQUIRED,
            authority_label="Manual review required",
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
            status="Blocked — " + "; ".join(blockers),
            blockers=tuple(blockers),
            note=(
                "Authority preview requires design valve Δp and resolved "
                "controlled-circuit Δp."
            ),
        )

    controlled_dp = resolution.controlled_circuit_dp_pa

    if controlled_dp is None:
        return ValveAuthorityPreviewRowV1(
            route=route,
            balancing_method_label=balancing_method_label,
            ready=False,
            design_valve_dp_pa=design_valve_dp_pa,
            controlled_circuit_dp_pa=None,
            authority=None,
            authority_band_id=MANUAL_REVIEW_REQUIRED,
            authority_label="Manual review required",
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
            status="Blocked — controlled-circuit Δp not resolved",
            blockers=("Controlled-circuit Δp not resolved",),
            note="No authority preview calculated.",
        )

    authority = _authority_v1(
        design_valve_dp_pa=design_valve_dp_pa,
        controlled_circuit_dp_pa=controlled_dp,
    )

    band_id = classify_valve_authority_band_v1(authority)
    label = _BAND_LABELS_V1.get(band_id, "Manual review required")

    if band_id == MANUAL_REVIEW_REQUIRED:
        return ValveAuthorityPreviewRowV1(
            route=route,
            balancing_method_label=balancing_method_label,
            ready=False,
            design_valve_dp_pa=design_valve_dp_pa,
            controlled_circuit_dp_pa=controlled_dp,
            authority=authority,
            authority_band_id=band_id,
            authority_label=label,
            route_flow_kg_s=route_flow_kg_s,
            candidate_resistance_pa_per_kg_s2=resistance,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
            status="Blocked — authority ratio could not be classified",
            blockers=("Authority ratio could not be classified",),
            note="No valve selection.",
        )

    if band_id == ACCEPTABLE_AUTHORITY_PREVIEW:
        status = "Ready — acceptable authority preview"
    elif band_id == TOO_LOW_AUTHORITY_PREVIEW:
        status = "Warning — valve authority below preview minimum"
    elif band_id == HIGH_THROTTLING_BURDEN:
        status = "Warning — high throttling burden preview"
    else:
        status = f"Ready — {label}"

    return ValveAuthorityPreviewRowV1(
        route=route,
        balancing_method_label=balancing_method_label,
        ready=True,
        design_valve_dp_pa=design_valve_dp_pa,
        controlled_circuit_dp_pa=controlled_dp,
        authority=authority,
        authority_band_id=band_id,
        authority_label=label,
        route_flow_kg_s=route_flow_kg_s,
        candidate_resistance_pa_per_kg_s2=resistance,
        controlled_circuit_basis_id=controlled_circuit_basis_id,
        status=status,
        blockers=(),
        note=(
            "Authority preview only. No Kv/Kvs, valve product, lockshield "
            "setting, pump selection, or final balancing."
        ),
    )


def build_valve_authority_preview_v1(
        *,
        valve_authority_input_mapping: object,
        route_pressure_rows: object,
        controlled_circuit_basis_id: str = ROUTE_CHOSEN_DP,
) -> ValveAuthorityPreviewV1:
    """
    Build H-S32-F valve authority preview.

    Pure preview:
        no ProjectState mutation
        no GUI dependency
        no file export
        no valve product selection
        no Kv / Kvs selection
        no manufacturer data
        no pump sizing
        no final balancing
    """
    input_rows = _input_rows_v1(valve_authority_input_mapping)
    basis_model = build_controlled_circuit_dp_basis_model_v1(
        selected_basis_id=controlled_circuit_basis_id
    )

    if not input_rows:
        return ValveAuthorityPreviewV1(
            ready=False,
            status="Blocked — valve authority input rows required",
            blockers=("Valve authority input rows required",),
            rows=(),
            controlled_circuit_basis_model=(
                controlled_circuit_dp_basis_model_to_dict_v1(basis_model)
            ),
        )

    route_lookup = _route_pressure_lookup_v1(route_pressure_rows)

    rows = tuple(
        _preview_row_from_input_v1(
            input_row,
            route_chosen_dp_lookup=route_lookup,
            controlled_circuit_basis_id=controlled_circuit_basis_id,
        )
        for input_row in input_rows
    )

    blockers = tuple(
        f"{row.route}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )

    ready = not blockers

    status = (
        "Ready — valve authority preview calculated"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return ValveAuthorityPreviewV1(
        ready=ready,
        status=status,
        blockers=blockers,
        rows=rows,
        controlled_circuit_basis_model=(
            controlled_circuit_dp_basis_model_to_dict_v1(basis_model)
        ),
    )


def valve_authority_preview_to_dict_v1(
        preview: ValveAuthorityPreviewV1 | None,
) -> dict[str, Any] | None:
    if preview is None:
        return None

    return {
        "schema": preview.schema,
        "ready": preview.ready,
        "status": preview.status,
        "blockers": tuple(preview.blockers),
        "rows": tuple(asdict(row) for row in preview.rows),
        "controlled_circuit_basis_model": (
            preview.controlled_circuit_basis_model
        ),
        "exclusions": tuple(preview.exclusions),
        "note": preview.note,
    }
