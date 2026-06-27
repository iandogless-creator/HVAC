# ======================================================================
# HVAC/hydronics/proportioning/proportioned_basis_snapshot_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.hydronics.proportioning.proportioning_readiness_v1 import (
    build_proportioning_readiness_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    UNDECIDED,
)


@dataclass(frozen=True, slots=True)
class ProportionedBasisSnapshotV1:
    """
    H-S26-G:
    Frozen accepted basis snapshot created by Commit Proportioning.

    This is not a final hydraulic proportioning result.

    It records the accepted design basis used at commit time:
    • accepted return arrangement basis
    • Basic/index readiness context
    • terminal alignment status

    It does not contain:
    • pump selection
    • valve selection
    • pipe resizing
    • balancing mutation
    """

    schema: str = "proportioned_basis_snapshot_v1"
    status: str = "COMMITTED_BASIS_ONLY"

    return_arrangement_basis: str = UNDECIDED
    return_arrangement_status: str = ""

    index_room_id: str | None = None
    index_room_label: str = "—"
    terminal_room_id: str | None = None
    terminal_room_label: str = "—"
    terminal_alignment_status: str = "—"

    basis_mode: str = "—"
    total_index_length_label: str = "—"
    nominal_gradient_label: str = "—"

    note: str = (
        "Frozen accepted proportioning basis only — no pump, valve, "
        "pipe resizing, balancing, or final Proportioned result."
    )


@dataclass(frozen=True, slots=True)
class ProportionedBasisSnapshotBuildResultV1:
    ready: bool = False
    snapshot: ProportionedBasisSnapshotV1 | None = None
    blockers: tuple[str, ...] = ()
    status: str = ""


def build_proportioned_basis_snapshot_v1(
        project_state: Any,
) -> ProportionedBasisSnapshotBuildResultV1:
    """
    Build a frozen accepted proportioning-basis snapshot.

    Readiness authority:
    Uses H-S26-E ProportioningReadinessV1.

    No ProjectState mutation occurs in this function.
    The adapter/button handler may assign the returned snapshot later.
    """
    readiness = build_proportioning_readiness_v1(project_state)

    blockers: list[str] = []

    if not getattr(readiness, "return_arrangement_basis_ready", False):
        blockers.append("Accepted return arrangement basis required")

    if blockers:
        return ProportionedBasisSnapshotBuildResultV1(
            ready=False,
            snapshot=None,
            blockers=tuple(blockers),
            status="Blocked — " + "; ".join(blockers),
        )

    snapshot = ProportionedBasisSnapshotV1(
        return_arrangement_basis=readiness.return_arrangement_basis_label,
        return_arrangement_status=readiness.return_arrangement_basis_status,
        index_room_id=readiness.index_room_id,
        index_room_label=readiness.index_room_label,
        terminal_room_id=readiness.terminal_room_id,
        terminal_room_label=readiness.terminal_room_label,
        terminal_alignment_status=readiness.terminal_alignment_status,
        basis_mode=readiness.basis_mode,
        total_index_length_label=readiness.total_index_length_label,
        nominal_gradient_label=readiness.nominal_gradient_label,
    )

    return ProportionedBasisSnapshotBuildResultV1(
        ready=True,
        snapshot=snapshot,
        blockers=(),
        status=(
            "Committed accepted proportioning basis snapshot — "
            "basis only; final hydraulic proportioning is deferred"
        ),
    )


def proportioned_basis_snapshot_to_dict_v1(
        snapshot: ProportionedBasisSnapshotV1 | None,
) -> dict | None:
    if snapshot is None:
        return None

    return {
        "schema": snapshot.schema,
        "status": snapshot.status,
        "return_arrangement_basis": snapshot.return_arrangement_basis,
        "return_arrangement_status": snapshot.return_arrangement_status,
        "index_room_id": snapshot.index_room_id,
        "index_room_label": snapshot.index_room_label,
        "terminal_room_id": snapshot.terminal_room_id,
        "terminal_room_label": snapshot.terminal_room_label,
        "terminal_alignment_status": snapshot.terminal_alignment_status,
        "basis_mode": snapshot.basis_mode,
        "total_index_length_label": snapshot.total_index_length_label,
        "nominal_gradient_label": snapshot.nominal_gradient_label,
        "note": snapshot.note,
    }


def proportioned_basis_snapshot_from_dict_v1(
        data: object,
) -> ProportionedBasisSnapshotV1 | None:
    if not isinstance(data, dict):
        return None

    return ProportionedBasisSnapshotV1(
        schema=str(data.get("schema", "proportioned_basis_snapshot_v1")),
        status=str(data.get("status", "COMMITTED_BASIS_ONLY")),
        return_arrangement_basis=str(
            data.get("return_arrangement_basis", UNDECIDED)
            or UNDECIDED
        ),
        return_arrangement_status=str(
            data.get("return_arrangement_status", "")
            or ""
        ),
        index_room_id=(
            str(data.get("index_room_id"))
            if data.get("index_room_id")
            else None
        ),
        index_room_label=str(data.get("index_room_label", "—") or "—"),
        terminal_room_id=(
            str(data.get("terminal_room_id"))
            if data.get("terminal_room_id")
            else None
        ),
        terminal_room_label=str(
            data.get("terminal_room_label", "—")
            or "—"
        ),
        terminal_alignment_status=str(
            data.get("terminal_alignment_status", "—")
            or "—"
        ),
        basis_mode=str(data.get("basis_mode", "—") or "—"),
        total_index_length_label=str(
            data.get("total_index_length_label", "—")
            or "—"
        ),
        nominal_gradient_label=str(
            data.get("nominal_gradient_label", "—")
            or "—"
        ),
        note=str(
            data.get(
                "note",
                (
                    "Frozen accepted proportioning basis only — no pump, "
                    "valve, pipe resizing, balancing, or final Proportioned "
                    "result."
                ),
            )
            or ""
        ),
    )
