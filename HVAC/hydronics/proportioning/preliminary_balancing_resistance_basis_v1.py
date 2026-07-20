# ======================================================================
# HVAC/hydronics/proportioning/preliminary_balancing_resistance_basis_v1.py
# ======================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field

from HVAC.hydronics.proportioning.preliminary_route_balancing_requirement_v1 import (
    PreliminaryRouteBalancingPreviewV1,
)
from HVAC.hydronics.proportioning.proportioning_input_snapshot_v1 import (
    ProportioningInputSnapshotV1,
)


@dataclass(slots=True)
class PreliminaryBalancingResistanceRowV1:
    """
    Preliminary theoretical resistance basis for route/subleg balancing.

    This is not valve selection.
    """

    route_id: str = ""
    route_label: str = ""
    sections: str = ""

    flow_kg_s: str = ""
    required_added_dp: str = ""
    resistance_pa_per_kg_s2: str = ""

    controlling: str = "No"
    status: str = ""


@dataclass(slots=True)
class PreliminaryBalancingResistanceBasisV1:
    """
    Preliminary route/subleg balancing resistance basis.

    Authority boundary:
    • no ProjectState mutation
    • no valve selection
    • no Kv/Kvs selection
    • no lockshield setting
    • no pump selection
    • no pipe resizing
    • no committed return arrangement
    """

    ready: bool = False
    status: str = "Balancing resistance basis not ready"
    rows: list[PreliminaryBalancingResistanceRowV1] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def _parse_number(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text == "—":
        return None

    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    return float(match.group(0))


def _format_flow(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.5f} kg/s"


def _format_pa(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f} Pa"


def _format_resistance(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f} Pa/(kg/s)²"


def _route_label_matches(wanted: str, candidate: str) -> bool:
    wanted_text = str(wanted or "").strip().lower()
    candidate_text = str(candidate or "").strip().lower()

    if not wanted_text or not candidate_text:
        return False

    return (
        wanted_text == candidate_text
        or wanted_text in candidate_text
        or candidate_text in wanted_text
    )


def _ids_match(left: str, right: str) -> bool:
    left = str(left or "").strip()
    right = str(right or "").strip()

    if not left or not right:
        return False

    if left == right:
        return True

    if left.endswith(":" + right):
        return True

    if right.endswith(":" + left):
        return True

    return False


def _section_matches_route(
    *,
    section_route_id: str,
    section_subleg_id: str,
    section_route_label: str,
    route_id: str,
    route_label: str,
) -> bool:
    if _ids_match(section_route_id, route_id):
        return True

    if _ids_match(section_subleg_id, route_id):
        return True

    if _ids_match(section_route_id, section_subleg_id):
        return True

    if route_label and section_route_label:
        return _route_label_matches(route_label, section_route_label)

    return False


def _route_flow_kg_s_from_snapshot(
    *,
    snapshot: ProportioningInputSnapshotV1,
    route_id: str,
    route_label: str,
) -> float | None:
    """
    Derive a route/subleg balancing-point flow from section rows.

    v1 rule:
    use the largest available section flow for the route/subleg as the
    balancing-point flow basis.

    This is conservative for a route-level balancing preview and avoids
    room-level balancing authority.
    """
    matched_flows: list[float] = []

    for section in snapshot.sections:
        section_route_id = str(getattr(section, "route_id", "") or "")
        section_subleg_id = str(getattr(section, "subleg_id", "") or "")

        section_route_label = (
                str(getattr(section, "route_label", "") or "")
                or str(getattr(section, "route", "") or "")
                or str(getattr(section, "to_label", "") or "")
        )

        if not _section_matches_route(
            section_route_id=section_route_id,
            section_subleg_id=section_subleg_id,
            section_route_label=section_route_label,
            route_id=route_id,
            route_label=route_label,
        ):
            continue

        flow = _parse_number(section.flow_kg_s)
        if flow is not None and flow > 0:
            matched_flows.append(flow)

    if not matched_flows:
        return None

    return max(matched_flows)


def build_preliminary_balancing_resistance_basis_v1(
    *,
    snapshot: ProportioningInputSnapshotV1 | None,
    balancing_preview: PreliminaryRouteBalancingPreviewV1 | None,
) -> PreliminaryBalancingResistanceBasisV1:
    """
    Calculate preliminary resistance basis:

        R = Δp_added / ṁ²

    This does not select a valve. It only states the theoretical route/subleg
    resistance basis required by the preliminary balancing preview.
    """
    if snapshot is None:
        return PreliminaryBalancingResistanceBasisV1(
            ready=False,
            status="Balancing resistance basis not ready",
            blockers=["No proportioning input snapshot is available"],
        )

    if balancing_preview is None:
        return PreliminaryBalancingResistanceBasisV1(
            ready=False,
            status="Balancing resistance basis not ready",
            blockers=["No preliminary route balancing preview is available"],
        )

    if not balancing_preview.ready:
        return PreliminaryBalancingResistanceBasisV1(
            ready=False,
            status="Balancing resistance basis not ready",
            blockers=list(balancing_preview.blockers or []),
        )

    rows: list[PreliminaryBalancingResistanceRowV1] = []
    blockers: list[str] = []

    for route_row in balancing_preview.rows:
        added_dp = _parse_number(route_row.required_added_resistance_dp)

        flow_kg_s = _route_flow_kg_s_from_snapshot(
            snapshot=snapshot,
            route_id=str(route_row.route_id or ""),
            route_label=str(route_row.route_label or ""),
        )

        resistance: float | None = None

        if added_dp is None:
            status = "Required added Δp unavailable"
            blockers.append(f"{route_row.route_label}: required added Δp unavailable")
        elif added_dp <= 0:
            resistance = 0.0
            status = "No added resistance required"
        elif flow_kg_s is None or flow_kg_s <= 0:
            status = "Flow basis unavailable — resistance not calculated"
            blockers.append(f"{route_row.route_label}: flow basis unavailable")
        else:
            resistance = added_dp / (flow_kg_s ** 2)
            status = "Preliminary resistance basis calculated"

        rows.append(
            PreliminaryBalancingResistanceRowV1(
                route_id=route_row.route_id,
                route_label=route_row.route_label,
                sections=route_row.sections,
                flow_kg_s=_format_flow(flow_kg_s),
                required_added_dp=_format_pa(added_dp),
                resistance_pa_per_kg_s2=_format_resistance(resistance),
                controlling=route_row.controlling,
                status=status,
            )
        )

    ready = not blockers

    return PreliminaryBalancingResistanceBasisV1(
        ready=ready,
        status=(
            "Preliminary balancing resistance basis ready"
            if ready
            else "Balancing resistance basis incomplete"
        ),
        rows=rows,
        blockers=blockers,
    )


# ======================================================================
# H-S43-B — chosen-basis mains-aware resistance consumption
# ======================================================================

def _read_row_value_v1(row: object, name: str, default=None):
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


def _chosen_row_is_controlling_v1(row: object) -> bool:
    raw = _read_row_value_v1(row, "is_controlling", None)
    if raw is None:
        raw = _read_row_value_v1(row, "controlling", False)
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() in {
        "1", "true", "yes", "y", "controlling"
    }


def _flow_basis_row_for_chosen_route_v1(
    chosen_row: object,
    flow_rows: list[object],
) -> object | None:
    route_id = str(_read_row_value_v1(chosen_row, "route_id", "") or "")
    route_label = str(_read_row_value_v1(chosen_row, "route", "") or "")

    for flow_row in flow_rows:
        candidate_id = str(
            _read_row_value_v1(flow_row, "route_id", "") or ""
        )
        candidate_label = str(
            _read_row_value_v1(flow_row, "route_label", "")
            or _read_row_value_v1(flow_row, "route", "")
            or ""
        )
        if _ids_match(route_id, candidate_id):
            return flow_row
        if _route_label_matches(route_label, candidate_label):
            return flow_row

    return None


def build_chosen_basis_balancing_resistance_basis_v1(
    *,
    chosen_controlling_rows: object,
    flow_basis: PreliminaryBalancingResistanceBasisV1 | None,
) -> PreliminaryBalancingResistanceBasisV1:
    """
    H-S43-B mains-aware provisional resistance consumption.

    The canonical required added pressure is the H-S43-A chosen-basis
    shortfall. Existing preliminary resistance rows supply route flow only;
    their older Δp and resistance values are deliberately not consumed.

        R = chosen-basis shortfall / route flow²

    This is theoretical preview evidence only. It does not select a valve,
    calculate Kv/Kvs, select a pump, resize pipework, or commit balance.
    """
    chosen_rows = list(chosen_controlling_rows or ())
    flow_rows = list(getattr(flow_basis, "rows", ()) or ())

    if not chosen_rows:
        return PreliminaryBalancingResistanceBasisV1(
            ready=False,
            status="Chosen-basis balancing resistance not ready",
            blockers=["No chosen-basis controlling/shortfall rows available"],
        )

    rows: list[PreliminaryBalancingResistanceRowV1] = []
    blockers: list[str] = []

    for chosen_row in chosen_rows:
        route_id = str(
            _read_row_value_v1(chosen_row, "route_id", "") or ""
        )
        route_label = str(
            _read_row_value_v1(chosen_row, "route", "")
            or _read_row_value_v1(chosen_row, "route_label", "")
            or route_id
            or "—"
        )
        is_controlling = _chosen_row_is_controlling_v1(chosen_row)
        added_dp = _parse_number(
            _read_row_value_v1(
                chosen_row,
                "dp_below_controlling_pa",
                _read_row_value_v1(chosen_row, "required_added_dp", None),
            )
        )

        flow_row = _flow_basis_row_for_chosen_route_v1(
            chosen_row,
            flow_rows,
        )
        flow_kg_s = (
            _parse_number(_read_row_value_v1(flow_row, "flow_kg_s", None))
            if flow_row is not None
            else None
        )
        sections = (
            str(_read_row_value_v1(flow_row, "sections", "") or "")
            if flow_row is not None
            else ""
        )

        resistance: float | None = None

        if added_dp is None:
            status = "Chosen-basis required added Δp unavailable"
            blockers.append(
                f"{route_label}: chosen-basis required added Δp unavailable"
            )
        elif is_controlling and abs(added_dp) > 0.05:
            status = "Inconsistent controlling-route shortfall"
            blockers.append(
                f"{route_label}: controlling route has non-zero shortfall"
            )
        elif added_dp <= 0.05:
            resistance = 0.0
            status = (
                "Mains-aware chosen-basis resistance — none required"
            )
        elif flow_kg_s is None or flow_kg_s <= 0.0:
            status = "Flow basis unavailable — resistance not calculated"
            blockers.append(f"{route_label}: positive route flow unavailable")
        else:
            resistance = added_dp / (flow_kg_s ** 2)
            status = (
                "Mains-aware chosen-basis provisional resistance calculated"
            )

        rows.append(
            PreliminaryBalancingResistanceRowV1(
                route_id=route_id,
                route_label=route_label,
                sections=sections,
                flow_kg_s=_format_flow(flow_kg_s),
                required_added_dp=_format_pa(added_dp),
                resistance_pa_per_kg_s2=_format_resistance(resistance),
                controlling="Yes" if is_controlling else "No",
                status=status,
            )
        )

    ready = not blockers
    return PreliminaryBalancingResistanceBasisV1(
        ready=ready,
        status=(
            "Mains-aware chosen-basis balancing resistance ready"
            if ready
            else "Chosen-basis balancing resistance incomplete"
        ),
        rows=rows,
        blockers=blockers,
    )
