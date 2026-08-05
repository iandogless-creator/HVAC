# ======================================================================
# H-S66-L — Committed pipe external-arrangement authority
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


DIRECT_RETURN_BASIS_V1 = "F&R"
REVERSE_RETURN_BASIS_V1 = "F+RR"

STACKED_FLOW_RETURN_PAIR_V1 = "stacked_flow_return_pair"
SEPARATE_PIPE_V1 = "separate_pipe"

PHYSICAL_LOOP_ZERO_EXTRA_V1 = "physical_loop_zero_extra"
DOWNSTREAM_PROXY_V1 = "downstream_proxy"
MANUAL_ALLOWANCE_V1 = "manual_allowance"


@dataclass(frozen=True, slots=True)
class CommittedPipeExternalArrangementRowV1:
    """External-arrangement evidence for one exact committed section."""

    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    route_bases: tuple[str, ...]
    rr_added_length_basis_modes: tuple[str, ...]
    order: int
    external_arrangement: str
    external_arrangement_label: str
    source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedPipeExternalArrangementAuthorityV1:
    """Deterministic physical-exposure basis; it performs no heat transfer."""

    schema: str = "committed_pipe_external_arrangement_authority_v1"
    ready: bool = False
    sections: tuple[CommittedPipeExternalArrangementRowV1, ...] = ()
    section_count: int = 0
    status: str = "Committed pipe external-arrangement authority not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Exact committed section and chosen route-basis evidence only. "
        "F&R is a stacked flow/return pair; a perfect physical-loop F+RR "
        "is stacked again, while proxy/manual RR allowance is separate. "
        "No spacing, vertical order, "
        "convection coefficient, shielding or heat loss is calculated."
    )


def build_committed_pipe_external_arrangement_authority_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        rr_added_length_basis_mode_by_route_id: Mapping[str, str],
) -> CommittedPipeExternalArrangementAuthorityV1:
    """Resolve arrangement from exact H-S54-A section/route identities."""

    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked_v1(
            "Committed proportioning hydraulic-input authority is required"
        )

    blockers: list[str] = []
    if not committed_authority.ready:
        blockers.append(
            "Committed proportioning hydraulic-input authority is not ready"
        )

    routes = tuple(committed_authority.routes or ())
    sections = tuple(committed_authority.sections or ())
    if not routes:
        blockers.append("Committed chosen-basis routes are required")
    if not sections:
        blockers.append("Committed pipe sections are required")

    route_basis_by_id: dict[str, str] = {}
    for route in routes:
        route_id = _text_v1(getattr(route, "route_id", ""))
        if not route_id:
            blockers.append("Every committed route requires route_id")
            continue
        if route_id in route_basis_by_id:
            blockers.append(f"Duplicate committed route identity: {route_id}")
            continue
        try:
            route_basis_by_id[route_id] = _normalise_route_basis_v1(
                getattr(route, "basis", "")
            )
        except ValueError as exc:
            blockers.append(f"{route_id}: {exc}")

    rr_modes_by_route_id: dict[str, str] = {}
    if not isinstance(rr_added_length_basis_mode_by_route_id, Mapping):
        blockers.append("RR physical-loop basis mapping is required")
    else:
        for raw_route_id, raw_mode in (
            rr_added_length_basis_mode_by_route_id.items()
        ):
            route_id = _text_v1(raw_route_id)
            if not route_id:
                blockers.append("Every RR physical-loop basis requires route_id")
                continue
            try:
                rr_modes_by_route_id[route_id] = _normalise_rr_mode_v1(
                    raw_mode
                )
            except ValueError as exc:
                blockers.append(f"{route_id}: {exc}")

    reverse_route_ids = {
        route_id
        for route_id, basis in route_basis_by_id.items()
        if basis == REVERSE_RETURN_BASIS_V1
    }
    supplied_rr_route_ids = set(rr_modes_by_route_id)
    for route_id in sorted(reverse_route_ids - supplied_rr_route_ids):
        blockers.append(f"{route_id}: RR physical-loop basis is required")
    for route_id in sorted(supplied_rr_route_ids - reverse_route_ids):
        blockers.append(
            f"{route_id}: RR physical-loop basis has no committed F+RR route"
        )

    rows: list[CommittedPipeExternalArrangementRowV1] = []
    seen_section_ids: set[str] = set()
    for section in sections:
        section_id = _text_v1(getattr(section, "section_id", ""))
        if not section_id:
            blockers.append("Every committed pipe section requires section_id")
            continue
        if section_id in seen_section_ids:
            blockers.append(f"Duplicate committed section identity: {section_id}")
            continue
        seen_section_ids.add(section_id)

        route_ids = tuple(
            _text_v1(route_id)
            for route_id in tuple(getattr(section, "route_ids", ()) or ())
            if _text_v1(route_id)
        )
        if not route_ids:
            blockers.append(f"{section_id}: committed route membership required")
            continue
        if len(set(route_ids)) != len(route_ids):
            blockers.append(
                f"{section_id}: duplicate committed route membership"
            )
            continue

        missing_routes = tuple(
            route_id
            for route_id in route_ids
            if route_id not in route_basis_by_id
        )
        if missing_routes:
            blockers.append(
                f"{section_id}: chosen route basis missing for "
                + ", ".join(missing_routes)
            )
            continue

        route_bases = tuple(
            route_basis_by_id[route_id] for route_id in route_ids
        )
        rr_modes = tuple(
            rr_modes_by_route_id[route_id]
            for route_id in route_ids
            if route_basis_by_id[route_id] == REVERSE_RETURN_BASIS_V1
            and route_id in rr_modes_by_route_id
        )
        if any(
            mode in {DOWNSTREAM_PROXY_V1, MANUAL_ALLOWANCE_V1}
            for mode in rr_modes
        ):
            arrangement = SEPARATE_PIPE_V1
            label = "Separate pipe — RR proxy/manual allowance"
            source = (
                "Committed chosen route and effective RR length basis; "
                "separate arrangement takes precedence"
            )
        else:
            arrangement = STACKED_FLOW_RETURN_PAIR_V1
            label = "Stacked flow/return pair — F&R or perfect RR loop"
            source = "Committed chosen route and effective RR length basis"

        rows.append(
            CommittedPipeExternalArrangementRowV1(
                section_id=section_id,
                section_scope=_text_v1(
                    getattr(section, "section_scope", "")
                ),
                route_ids=route_ids,
                route_bases=route_bases,
                rr_added_length_basis_modes=rr_modes,
                order=int(getattr(section, "order", 0)),
                external_arrangement=arrangement,
                external_arrangement_label=label,
                source=source,
                ready=True,
                status="Ready — committed external arrangement resolved",
            )
        )

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(*clean)

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (row.order, row.section_id),
        )
    )
    return CommittedPipeExternalArrangementAuthorityV1(
        ready=True,
        sections=ordered_rows,
        section_count=len(ordered_rows),
        status=(
            "Ready — committed pipe external-arrangement authority resolved"
        ),
        blockers=(),
    )


def _normalise_route_basis_v1(value: object) -> str:
    text = _text_v1(value).upper().replace(" ", "")
    if text in {"F&R", "DIRECT_RETURN", "DIRECTRETURN"}:
        return DIRECT_RETURN_BASIS_V1
    if text in {"F+RR", "REVERSE_RETURN", "REVERSERETURN"}:
        return REVERSE_RETURN_BASIS_V1
    raise ValueError("committed chosen route basis must be F&R or F+RR")


def _normalise_rr_mode_v1(value: object) -> str:
    text = _text_v1(value).lower().replace(" ", "_")
    if text in {
        PHYSICAL_LOOP_ZERO_EXTRA_V1,
        DOWNSTREAM_PROXY_V1,
        MANUAL_ALLOWANCE_V1,
    }:
        return text
    raise ValueError(
        "RR physical-loop basis must be physical_loop_zero_extra, "
        "downstream_proxy or manual_allowance"
    )


def _blocked_v1(
        *blockers: str,
) -> CommittedPipeExternalArrangementAuthorityV1:
    clean = _unique_v1(blockers)
    return CommittedPipeExternalArrangementAuthorityV1(
        ready=False,
        sections=(),
        section_count=0,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: object) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)
