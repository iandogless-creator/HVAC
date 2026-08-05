# ======================================================================
# H-S66-M — Scoped RR physical-loop runtime handoff into H-S66-L
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    CommittedPipeExternalArrangementAuthorityV1,
    REVERSE_RETURN_BASIS_V1,
    build_committed_pipe_external_arrangement_authority_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeExternalArrangementRuntimeHandoffV1:
    """Runtime-only bridge from resolved RR evidence to H-S66-L."""

    schema: str = (
        "committed_pipe_external_arrangement_runtime_handoff_v1"
    )
    ready: bool = False
    authority: CommittedPipeExternalArrangementAuthorityV1 | None = None
    committed_reverse_return_route_count: int = 0
    matched_rr_evidence_route_count: int = 0
    status: str = "Committed pipe external-arrangement handoff not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Consumes exact route_id and already-resolved scoped RR added-length "
        "basis evidence, then delegates physical arrangement to H-S66-L. "
        "No ProjectState mutation, scope parsing, spacing, convection or "
        "heat-loss calculation is performed."
    )


def build_committed_pipe_external_arrangement_runtime_handoff_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        return_path_comparison_rows: Iterable[object],
) -> CommittedPipeExternalArrangementRuntimeHandoffV1:
    """Hand current exact scoped-RR evidence to H-S66-L by route identity."""

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

    committed_route_basis_by_id: dict[str, str] = {}
    for route in tuple(committed_authority.routes or ()):
        route_id = _text_v1(getattr(route, "route_id", ""))
        if not route_id:
            blockers.append("Every committed route requires route_id")
            continue
        if route_id in committed_route_basis_by_id:
            blockers.append(f"Duplicate committed route identity: {route_id}")
            continue
        basis = _normalise_route_basis_v1(getattr(route, "basis", ""))
        if basis is None:
            blockers.append(
                f"{route_id}: committed chosen route basis must be F&R or F+RR"
            )
            continue
        committed_route_basis_by_id[route_id] = basis

    reverse_route_ids = {
        route_id
        for route_id, basis in committed_route_basis_by_id.items()
        if basis == REVERSE_RETURN_BASIS_V1
    }

    rr_mode_by_route_id: dict[str, str] = {}
    try:
        evidence_rows = tuple(return_path_comparison_rows or ())
    except TypeError:
        blockers.append("Scoped RR comparison evidence rows are required")
        evidence_rows = ()

    for row in evidence_rows:
        route_id = _text_v1(getattr(row, "route_id", ""))
        if not route_id:
            blockers.append("Every scoped RR comparison row requires route_id")
            continue
        if route_id not in reverse_route_ids:
            continue
        mode = _text_v1(
            getattr(row, "rr_added_length_basis_mode", "")
        )
        if not mode:
            blockers.append(
                f"{route_id}: resolved scoped RR physical-loop basis is required"
            )
            continue
        existing = rr_mode_by_route_id.get(route_id)
        if existing is not None and existing != mode:
            blockers.append(
                f"{route_id}: conflicting scoped RR physical-loop evidence"
            )
            continue
        rr_mode_by_route_id[route_id] = mode

    for route_id in sorted(reverse_route_ids - set(rr_mode_by_route_id)):
        blockers.append(
            f"{route_id}: current scoped RR physical-loop evidence is required"
        )

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(
            *clean,
            reverse_route_count=len(reverse_route_ids),
            matched_route_count=len(rr_mode_by_route_id),
        )

    authority = build_committed_pipe_external_arrangement_authority_v1(
        committed_authority=committed_authority,
        rr_added_length_basis_mode_by_route_id=rr_mode_by_route_id,
    )
    if not authority.ready:
        return _blocked_v1(
            *authority.blockers,
            reverse_route_count=len(reverse_route_ids),
            matched_route_count=len(rr_mode_by_route_id),
            authority=authority,
        )

    return CommittedPipeExternalArrangementRuntimeHandoffV1(
        ready=True,
        authority=authority,
        committed_reverse_return_route_count=len(reverse_route_ids),
        matched_rr_evidence_route_count=len(rr_mode_by_route_id),
        status=(
            "Ready — scoped RR physical-loop evidence handed to H-S66-L"
        ),
        blockers=(),
    )


def _normalise_route_basis_v1(value: object) -> str | None:
    text = _text_v1(value).upper().replace(" ", "")
    if text in {"F&R", "DIRECT_RETURN", "DIRECTRETURN"}:
        return "F&R"
    if text in {"F+RR", "REVERSE_RETURN", "REVERSERETURN"}:
        return REVERSE_RETURN_BASIS_V1
    return None


def _blocked_v1(
        *blockers: str,
        reverse_route_count: int = 0,
        matched_route_count: int = 0,
        authority: CommittedPipeExternalArrangementAuthorityV1 | None = None,
) -> CommittedPipeExternalArrangementRuntimeHandoffV1:
    clean = _unique_v1(blockers)
    return CommittedPipeExternalArrangementRuntimeHandoffV1(
        ready=False,
        authority=authority,
        committed_reverse_return_route_count=reverse_route_count,
        matched_rr_evidence_route_count=matched_route_count,
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
