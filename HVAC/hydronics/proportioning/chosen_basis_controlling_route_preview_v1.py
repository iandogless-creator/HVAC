from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True)
class ChosenBasisControllingRoutePreviewRowV1:
    """
    H-S27-D read-only controlling-route preview from chosen-basis route Δp.

    Consumes H-S27-C chosen-basis route pressure preview rows.
    Does not perform balancing, pump sizing, valve selection, pipe resizing,
    or final hydraulic commitment.
    """

    scope: str
    route_id: str
    route: str
    basis: str
    chosen_dp_pa: Optional[float]
    is_controlling: bool
    dp_below_controlling_pa: Optional[float]
    source: str
    status: str


def build_chosen_basis_controlling_route_preview_v1(
    chosen_basis_route_pressure_rows: Iterable[Any],
) -> list[ChosenBasisControllingRoutePreviewRowV1]:
    """
    Identify the controlling route from H-S27-C chosen-basis route Δp rows.

    Controlling route = highest chosen Δp.
    Ties are all marked controlling.
    """

    input_rows = list(chosen_basis_route_pressure_rows or ())

    valid_rows = [
        row
        for row in input_rows
        if _read_float_any(row, "chosen_dp_pa", "chosen_dp") is not None
    ]

    if not valid_rows:
        return [
            ChosenBasisControllingRoutePreviewRowV1(
                scope="—",
                route_id="",
                route="—",
                basis="—",
                chosen_dp_pa=None,
                is_controlling=False,
                dp_below_controlling_pa=None,
                source="—",
                status="Preview only — no chosen-basis route pressure evidence",
            )
        ]

    controlling_dp = max(
        _read_float_any(row, "chosen_dp_pa", "chosen_dp") or 0.0
        for row in valid_rows
    )

    out: list[ChosenBasisControllingRoutePreviewRowV1] = []

    for row in valid_rows:
        chosen_dp = _read_float_any(row, "chosen_dp_pa", "chosen_dp")
        route_id = _read_text_any(row, "route_id", default="")
        is_controlling = (
            chosen_dp is not None
            and abs(chosen_dp - controlling_dp) <= 0.05
        )

        dp_below = (
            controlling_dp - chosen_dp
            if chosen_dp is not None
            else None
        )

        out.append(
            ChosenBasisControllingRoutePreviewRowV1(
                scope=_read_text_any(row, "scope", default="—"),
                route_id=route_id,
                route=_read_text_any(
                    row,
                    "route",
                    "route_label",
                    default=route_id or "—",
                ),
                basis=_read_text_any(row, "basis", default="—"),
                chosen_dp_pa=chosen_dp,
                is_controlling=is_controlling,
                dp_below_controlling_pa=dp_below,
                source=_read_text_any(row, "source", default="—"),
                status=(
                    "Preview only — chosen-basis controlling route"
                    if is_controlling
                    else "Preview only — below chosen-basis controlling route"
                ),
            )
        )

    return out


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


def _read_float_any(row: Any, *names: str) -> Optional[float]:
    value = _read_any(row, *names, default=None)
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

    try:
        return float(lowered.strip()) * factor
    except (TypeError, ValueError):
        return None
