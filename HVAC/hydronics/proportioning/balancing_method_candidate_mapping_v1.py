# ======================================================================
# HVAC/hydronics/proportioning/balancing_method_candidate_mapping_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any

from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    MANUAL_REVIEW_REQUIRED,
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
    balancing_method_design_model_to_dict_v1,
    build_balancing_method_design_model_v1,
)


_NUMBER_RE_V1 = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


@dataclass(frozen=True, slots=True)
class BalancingMethodCandidateV1:
    """
    H-S31-B:
    Route-level balancing method candidate.

    This maps provisional route burden evidence to a balancing method intent.

    It does not:
        • select a valve product
        • select Kv / Kvs
        • calculate lockshield turns
        • select a pump
        • perform final balancing
        • resize pipes
        • mutate ProjectState
    """

    route: str = "—"
    method_id: str = MANUAL_REVIEW_REQUIRED
    method_label: str = "Manual review required"
    ready: bool = False
    controlling: bool = False

    required_added_dp_pa: float | None = None
    flow_kg_s: float | None = None
    resistance_pa_per_kg_s2: float | None = None

    status: str = ""
    blockers: tuple[str, ...] = ()
    source_status: str = ""
    note: str = ""


@dataclass(frozen=True, slots=True)
class BalancingMethodCandidateMappingV1:
    """
    H-S31-B:
    Map provisional route burden rows to route-level balancing method candidates.

    Mapping authority only:
        no valve product selected
        no Kv / Kvs selected
        no lockshield turn count
        no pump selected
        no final balancing
        no pipe resizing
        no ProjectState mutation
    """

    schema: str = "balancing_method_candidate_mapping_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    candidates: tuple[BalancingMethodCandidateV1, ...] = ()
    design_model: dict[str, Any] | None = None
    exclusions: tuple[str, ...] = (
        "No valve product selected",
        "No Kv or Kvs selected",
        "No lockshield turn count",
        "No pump selected",
        "No final balancing",
        "No pipe resizing",
        "No ProjectState mutation",
    )
    note: str = (
        "Balancing method candidate mapping only — no valve sizing, "
        "pump selection, pipe resizing, or final balancing."
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
            "basis",
            "flow_kg_s",
            "chosen_dp",
            "chosen_dp_pa",
            "controlling",
            "is_controlling",
            "required_added_dp",
            "required_added_dp_pa",
            "dp_below_controlling_pa",
            "resistance_pa_per_kg_s2",
            "resistance_basis",
            "action",
            "status",
    ):
        if hasattr(row, name):
            data[name] = getattr(row, name)

    return data


def _text_v1(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


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


def _bool_v1(value: object) -> bool:
    if isinstance(value, bool):
        return value

    text = str(value or "").strip().lower()

    return text in {"1", "true", "yes", "y", "controlling"}


def _first_number_v1(
        row: dict[str, object],
        *keys: str,
) -> float | None:
    for key in keys:
        value = _parse_float_v1(row.get(key))

        if value is not None:
            return value

    return None


def _candidate_from_row_v1(
        row: object,
        *,
        dp_tolerance_pa: float,
) -> BalancingMethodCandidateV1:
    data = _row_to_dict_v1(row)

    route = _text_v1(
        data.get("route")
        or data.get("route_id")
        or "—",
        default="—",
    )

    controlling = (
        _bool_v1(data.get("controlling"))
        or _bool_v1(data.get("is_controlling"))
    )

    required_added_dp_pa = _first_number_v1(
        data,
        "required_added_dp_pa",
        "required_added_dp",
        "dp_below_controlling_pa",
    )
    flow_kg_s = _first_number_v1(data, "flow_kg_s")
    resistance_pa_per_kg_s2 = _first_number_v1(
        data,
        "resistance_pa_per_kg_s2",
        "resistance_basis",
    )
    source_status = _text_v1(data.get("status"), default="—")

    blockers: list[str] = []

    if route == "—":
        blockers.append("Route label required")

    if controlling:
        # H-S43-C: a controlling route is "None required" only when its
        # canonical chosen-basis shortfall is present and zero/within
        # tolerance. A positive resistance value is also inconsistent.
        if required_added_dp_pa is None:
            blockers.append("Controlling-route shortfall evidence required")
        elif abs(required_added_dp_pa) > dp_tolerance_pa:
            blockers.append("Controlling route must have zero added Δp")

        if (
                resistance_pa_per_kg_s2 is not None
                and abs(resistance_pa_per_kg_s2) > dp_tolerance_pa
        ):
            blockers.append("Controlling route must have zero resistance")

        if blockers:
            return BalancingMethodCandidateV1(
                route=route,
                method_id=MANUAL_REVIEW_REQUIRED,
                method_label="Manual review required",
                ready=False,
                controlling=True,
                required_added_dp_pa=required_added_dp_pa,
                flow_kg_s=flow_kg_s,
                resistance_pa_per_kg_s2=resistance_pa_per_kg_s2,
                status="Blocked — " + "; ".join(blockers),
                blockers=tuple(blockers),
                source_status=source_status,
                note=(
                    "Inconsistent controlling-route burden fails closed; "
                    "no balancing method is selected."
                ),
            )

        return BalancingMethodCandidateV1(
            route=route,
            method_id=NONE_REQUIRED,
            method_label="None required",
            ready=True,
            controlling=True,
            required_added_dp_pa=required_added_dp_pa,
            flow_kg_s=flow_kg_s,
            resistance_pa_per_kg_s2=resistance_pa_per_kg_s2,
            status=(
                "None required — controlling route has no added "
                "resistance burden"
            ),
            blockers=(),
            source_status=source_status,
            note=(
                "This does not prove final balance; it only records no "
                "preview added-resistance burden for the controlling route."
            ),
        )

    if required_added_dp_pa is None:
        blockers.append("Required added Δp evidence required")
    elif required_added_dp_pa <= dp_tolerance_pa:
        return BalancingMethodCandidateV1(
            route=route,
            method_id=NONE_REQUIRED,
            method_label="None required",
            ready=not blockers,
            controlling=False,
            required_added_dp_pa=required_added_dp_pa,
            flow_kg_s=flow_kg_s,
            resistance_pa_per_kg_s2=resistance_pa_per_kg_s2,
            status=(
                "None required — zero/near-zero added resistance burden"
                if not blockers
                else "Blocked — " + "; ".join(blockers)
            ),
            blockers=tuple(blockers),
            source_status=source_status,
            note="Preview burden is zero or within tolerance.",
        )

    if flow_kg_s is None or flow_kg_s <= 0.0:
        blockers.append("Positive route flow kg/s required")

    if (
            resistance_pa_per_kg_s2 is None
            or resistance_pa_per_kg_s2 <= 0.0
    ):
        blockers.append("Positive resistance Pa/(kg/s)² required")

    if blockers:
        return BalancingMethodCandidateV1(
            route=route,
            method_id=MANUAL_REVIEW_REQUIRED,
            method_label="Manual review required",
            ready=False,
            controlling=False,
            required_added_dp_pa=required_added_dp_pa,
            flow_kg_s=flow_kg_s,
            resistance_pa_per_kg_s2=resistance_pa_per_kg_s2,
            status="Blocked — " + "; ".join(blockers),
            blockers=tuple(blockers),
            source_status=source_status,
            note=(
                "Automatic proportional added-resistance mapping needs "
                "positive added Δp, positive flow, and positive resistance."
            ),
        )

    return BalancingMethodCandidateV1(
        route=route,
        method_id=PROPORTIONAL_ADDED_RESISTANCE,
        method_label="Proportional added resistance",
        ready=True,
        controlling=False,
        required_added_dp_pa=required_added_dp_pa,
        flow_kg_s=flow_kg_s,
        resistance_pa_per_kg_s2=resistance_pa_per_kg_s2,
        status=(
            "Candidate — proportional added resistance from preview burden"
        ),
        blockers=(),
        source_status=source_status,
        note=(
            "Identifies required added resistance only; no valve selected "
            "and no Kv/Kvs calculated."
        ),
    )


def build_balancing_method_candidate_mapping_v1(
        provisional_burden_rows: object,
        *,
        dp_tolerance_pa: float = 0.5,
) -> BalancingMethodCandidateMappingV1:
    """
    Build H-S31-B route-level balancing method candidates.

    Pure mapping:
        no ProjectState mutation
        no GUI dependency
        no file export
        no valve sizing
        no pump sizing
        no final balancing
    """
    rows = list(provisional_burden_rows or ())

    if not rows:
        design_model = build_balancing_method_design_model_v1()

        return BalancingMethodCandidateMappingV1(
            ready=False,
            status="Blocked — provisional route burden rows required",
            blockers=("Provisional route burden rows required",),
            candidates=(),
            design_model=balancing_method_design_model_to_dict_v1(
                design_model
            ),
        )

    candidates = tuple(
        _candidate_from_row_v1(
            row,
            dp_tolerance_pa=dp_tolerance_pa,
        )
        for row in rows
    )

    blockers = tuple(
        f"{candidate.route}: {blocker}"
        for candidate in candidates
        for blocker in candidate.blockers
    )

    ready = not blockers

    status = (
        "Ready — balancing method candidates mapped from provisional burden"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    design_model = build_balancing_method_design_model_v1()

    return BalancingMethodCandidateMappingV1(
        ready=ready,
        status=status,
        blockers=blockers,
        candidates=candidates,
        design_model=balancing_method_design_model_to_dict_v1(design_model),
    )


def balancing_method_candidate_mapping_to_dict_v1(
        mapping: BalancingMethodCandidateMappingV1 | None,
) -> dict[str, Any] | None:
    if mapping is None:
        return None

    return {
        "schema": mapping.schema,
        "ready": mapping.ready,
        "status": mapping.status,
        "blockers": tuple(mapping.blockers),
        "candidates": tuple(
            asdict(candidate)
            for candidate in mapping.candidates
        ),
        "design_model": mapping.design_model,
        "exclusions": tuple(mapping.exclusions),
        "note": mapping.note,
    }
