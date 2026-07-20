from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


DIRECT_RETURN = "DIRECT_RETURN"
REVERSE_RETURN = "REVERSE_RETURN"


@dataclass(frozen=True)
class ChosenBasisRoutePressurePreviewRowV1:
    """
    H-S27-C read-only chosen-basis route Δp preview row.

    This is an evidence compositor only:
    - consumes resolved return-arrangement basis
    - consumes existing F&R / F+RR comparison evidence
    - selects the matching evidence for the accepted/effective basis
    - does not resize pipes
    - does not select valves
    - does not size pumps
    - does not commit final hydraulic results
    """

    scope: str
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: Optional[float]
    alternative_dp_pa: Optional[float]
    difference_pa: Optional[float]
    source: str
    status: str

    # H-S42-D evidence; chosen_dp_pa already includes this exactly once.
    common_main_dp_pa: Optional[float] = 0.0
    leg_entry_dp_pa: Optional[float] = 0.0
    physical_main_entry_dp_pa: Optional[float] = 0.0


@dataclass(frozen=True)
class _RoutePressureEvidence:
    route_id: str
    route_label: str
    direct_dp_pa: Optional[float]
    reverse_dp_pa: Optional[float]
    common_main_dp_pa: Optional[float]
    leg_entry_dp_pa: Optional[float]
    physical_main_entry_dp_pa: Optional[float]


def build_chosen_basis_route_pressure_preview_v1(
    resolved_basis_rows: Iterable[Any],
    return_comparison_rows: Iterable[Any],
) -> list[ChosenBasisRoutePressurePreviewRowV1]:
    """
    Build H-S27-C chosen-basis route pressure preview.

    Real return-comparison rows may be room/emitter rows. Therefore this function
    groups by route/subleg and keeps the highest direct/reverse Δp evidence for
    each route. That gives one preview row per resolved route/subleg.
    """

    evidence_by_route_id = _build_route_pressure_evidence(return_comparison_rows)

    out: list[ChosenBasisRoutePressurePreviewRowV1] = []

    for resolved_row in resolved_basis_rows:
        route_id = _route_id_from_resolved_row(resolved_row)
        if not route_id:
            continue

        evidence = None
        for lookup_key in _resolved_lookup_keys(resolved_row, route_id):
            evidence = evidence_by_route_id.get(lookup_key)
            if evidence is not None:
                break

        if evidence is None:
            out.append(
                ChosenBasisRoutePressurePreviewRowV1(
                    scope=_read_text_any(resolved_row, "scope", default="—"),
                    route_id=route_id,
                    route=_read_text_any(
                        resolved_row,
                        "target_label",
                        "target",
                        "route",
                        default=route_id,
                    ),
                    basis="—",
                    chosen_dp_pa=None,
                    alternative_dp_pa=None,
                    difference_pa=None,
                    source=_read_text_any(resolved_row, "source", default="—"),
                    status="Preview only — missing return comparison evidence",
                )
            )
            continue

        effective_basis = _normalise_basis(
            _read_any(
                resolved_row,
                "effective_basis",
                "basis",
                "return_arrangement",
                "effective_return_arrangement",
            )
        )

        if effective_basis == DIRECT_RETURN:
            basis_label = "F&R"
            chosen_dp = evidence.direct_dp_pa
            alternative_dp = evidence.reverse_dp_pa
        elif effective_basis == REVERSE_RETURN:
            basis_label = "F+RR"
            chosen_dp = evidence.reverse_dp_pa
            alternative_dp = evidence.direct_dp_pa
        else:
            basis_label = "—"
            chosen_dp = None
            alternative_dp = None

        difference = (
            chosen_dp - alternative_dp
            if chosen_dp is not None and alternative_dp is not None
            else None
        )

        out.append(
            ChosenBasisRoutePressurePreviewRowV1(
                scope=_read_text_any(resolved_row, "scope", default="—"),
                route_id=route_id,
                route=evidence.route_label or _read_text_any(
                    resolved_row,
                    "target_label",
                    "target",
                    "route",
                    default=route_id,
                ),
                basis=basis_label,
                chosen_dp_pa=chosen_dp,
                alternative_dp_pa=alternative_dp,
                difference_pa=difference,
                source=_read_text_any(resolved_row, "source", default="—"),
                status=_status_for(effective_basis, chosen_dp, alternative_dp, difference),
                common_main_dp_pa=evidence.common_main_dp_pa,
                leg_entry_dp_pa=evidence.leg_entry_dp_pa,
                physical_main_entry_dp_pa=evidence.physical_main_entry_dp_pa,
            )
        )

    return out


def _lookup_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _add_lookup_key(keys: list[str], value: Any) -> None:
    key = _lookup_key(value)
    if key and key not in keys:
        keys.append(key)


def _resolved_lookup_keys(row: Any, route_id: str) -> list[str]:
    keys: list[str] = []

    _add_lookup_key(keys, route_id)
    _add_lookup_key(keys, _read_any(row, "target_id"))
    _add_lookup_key(keys, _read_any(row, "route_id"))
    _add_lookup_key(keys, _read_any(row, "subleg_id"))
    _add_lookup_key(keys, _read_any(row, "label"))
    _add_lookup_key(keys, _read_any(row, "target"))
    _add_lookup_key(keys, _read_any(row, "target_label"))
    _add_lookup_key(keys, _read_any(row, "route"))

    return keys



def _build_route_pressure_evidence(
    return_comparison_rows: Iterable[Any],
) -> dict[str, _RoutePressureEvidence]:
    grouped: dict[str, _RoutePressureEvidence] = {}

    for row in return_comparison_rows:
        route_id = _route_id_from_comparison_row(row)
        subleg_id = _read_text_any(row, "subleg_id", default="")

        route_label = _read_text_any(
            row,
            "route_label",
            "route",
            "target_label",
            default=route_id or subleg_id,
        )

        keys: list[str] = []
        _add_lookup_key(keys, route_id)
        _add_lookup_key(keys, subleg_id)
        _add_lookup_key(keys, route_label)
        _add_lookup_key(keys, _read_any(row, "target"))
        _add_lookup_key(keys, _read_any(row, "target_label"))

        if route_id and ":" in route_id:
            _add_lookup_key(keys, route_id.split(":", 1)[1])

        if not keys:
            continue

        direct_dp = _read_float_any(
            row,
            # Canonical CircuitReturnPathComparisonRowV1 field first.
            "direct_total_dp_Pa",
            "direct_dp_pa",
            "direct_route_dp_pa",
            "direct_total_dp_pa",
            "direct_sum_dp_pa",
            "direct_sigma_dp_pa",
            "direct_pressure_pa",
            "direct_return_dp_pa",
            "direct_route_pressure_pa",
            "direct_total_dp",
            "direct_route_dp",
            "direct_dp",
            "direct_ΣΔp",
            "direct_Σdp",
        )

        if direct_dp is None:
            direct_dp = _read_float_by_key_terms(
                row,
                required_any=("direct", "f&r", "fr"),
            )

        reverse_dp = _read_float_any(
            row,
            # Canonical CircuitReturnPathComparisonRowV1 field first.
            "reverse_return_total_dp_Pa",
            "reverse_dp_pa",
            "reverse_route_dp_pa",
            "reverse_total_dp_pa",
            "reverse_sum_dp_pa",
            "reverse_sigma_dp_pa",
            "reverse_pressure_pa",
            "reverse_return_dp_pa",
            "reverse_route_pressure_pa",
            "f_plus_rr_dp_pa",
            "reverse_total_dp",
            "reverse_route_dp",
            "reverse_dp",
            "reverse_ΣΔp",
            "reverse_Σdp",
        )

        if reverse_dp is None:
            reverse_dp = _read_float_by_key_terms(
                row,
                required_any=("reverse", "f+rr", "rr"),
            )

        common_main_dp = _read_float_any(
            row, "common_main_dp_Pa", "common_main_dp_pa"
        )
        leg_entry_dp = _read_float_any(
            row, "leg_entry_dp_Pa", "leg_entry_dp_pa"
        )
        physical_main_entry_dp = _read_float_any(
            row, "physical_main_entry_dp_Pa", "physical_main_entry_dp_pa"
        )

        previous = None
        for key in keys:
            previous = grouped.get(key)
            if previous is not None:
                break

        if previous is None:
            updated = _RoutePressureEvidence(
                route_id=route_id or subleg_id,
                route_label=route_label,
                direct_dp_pa=direct_dp,
                reverse_dp_pa=reverse_dp,
                common_main_dp_pa=common_main_dp,
                leg_entry_dp_pa=leg_entry_dp,
                physical_main_entry_dp_pa=physical_main_entry_dp,
            )
        else:
            updated = _RoutePressureEvidence(
                route_id=previous.route_id,
                route_label=previous.route_label or route_label,
                direct_dp_pa=_max_optional(previous.direct_dp_pa, direct_dp),
                reverse_dp_pa=_max_optional(previous.reverse_dp_pa, reverse_dp),
                common_main_dp_pa=_same_optional_v1(
                    previous.common_main_dp_pa, common_main_dp
                ),
                leg_entry_dp_pa=_same_optional_v1(
                    previous.leg_entry_dp_pa, leg_entry_dp
                ),
                physical_main_entry_dp_pa=_same_optional_v1(
                    previous.physical_main_entry_dp_pa, physical_main_entry_dp
                ),
            )

        for key in keys:
            grouped[key] = updated

    return grouped

def _same_optional_v1(
    previous: Optional[float],
    current: Optional[float],
) -> Optional[float]:
    if previous is None:
        return current
    if current is None:
        return previous
    return previous if abs(previous - current) <= 1.0e-9 else None


def _max_optional(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _route_id_from_resolved_row(row: Any) -> str:
    return _read_text_any(
        row,
        "target_id",
        "route_id",
        "subleg_id",
        "target",
        default="",
    )


def _route_id_from_comparison_row(row: Any) -> str:
    return _read_text_any(
        row,
        "route_id",
        "target_id",
        "subleg_id",
        "route_key",
        default="",
    )


def _normalise_basis(raw: Any) -> str:
    text = str(raw or "").strip().upper()

    if "REVERSE" in text or "F+RR" in text or "F_PLUS_RR" in text:
        return REVERSE_RETURN

    if "DIRECT" in text or "F&R" in text or "FLOW_AND_RETURN" in text:
        return DIRECT_RETURN

    return ""


def _status_for(
    effective_basis: str,
    chosen_dp: Optional[float],
    alternative_dp: Optional[float],
    difference: Optional[float],
) -> str:
    if effective_basis not in {DIRECT_RETURN, REVERSE_RETURN}:
        return "Preview only — unknown effective basis"

    if chosen_dp is None or alternative_dp is None or difference is None:
        return "Preview only — missing pressure evidence"

    if difference < -0.05:
        return "Preview only — chosen basis lower than alternative"

    if difference > 0.05:
        return "Preview only — chosen basis higher than alternative"

    return "Preview only — chosen basis equal to alternative"


def _read_any(row: Any, *names: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        for name in names:
            if name in row:
                return row[name]
        return default

    for name in names:
        if hasattr(row, name):
            return getattr(row, name)

    return default


def _read_text_any(row: Any, *names: str, default: str = "—") -> str:
    value = _read_any(row, *names, default=default)
    if value is None:
        return default
    return str(value)



def _iter_public_items(row: Any):
    if isinstance(row, Mapping):
        for key, value in row.items():
            yield str(key), value
        return

    for name in dir(row):
        if name.startswith("_"):
            continue
        try:
            value = getattr(row, name)
        except Exception:
            continue
        if callable(value):
            continue
        yield str(name), value


def _read_float_by_key_terms(
    row: Any,
    *,
    required_any: tuple[str, ...],
    pressure_terms: tuple[str, ...] = ("dp", "pressure", "pa"),
    exclude_terms: tuple[str, ...] = (
        "rank",
        "controlling",
        "suitability",
        "status",
        "source",
        "basis",
        "room",
        "route",
        "label",
        "id",
    ),
) -> Optional[float]:
    for key, value in _iter_public_items(row):
        key_l = key.lower()

        if not any(term in key_l for term in required_any):
            continue

        if not any(term in key_l for term in pressure_terms):
            continue

        if any(term in key_l for term in exclude_terms):
            continue

        parsed = _parse_pressure_float(value)
        if parsed is not None:
            return parsed

    return None


def _parse_pressure_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text == "—":
        return None

    lowered = text.lower().replace(",", "").strip()

    factor = 1.0
    if "kpa" in lowered:
        factor = 1000.0
        lowered = lowered.replace("kpa", "")
    else:
        lowered = lowered.replace("pa", "")

    lowered = lowered.strip()

    try:
        return float(lowered) * factor
    except (TypeError, ValueError):
        return None


def _read_float_any(row: Any, *names: str) -> Optional[float]:
    value = _read_any(row, *names, default=None)
    return _parse_pressure_float(value)

