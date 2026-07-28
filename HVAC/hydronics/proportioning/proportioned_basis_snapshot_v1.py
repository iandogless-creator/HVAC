# ======================================================================
# HVAC/hydronics/proportioning/proportioned_basis_snapshot_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    committed_proportioning_hydraulic_input_authority_from_dict_v1,
    committed_proportioning_hydraulic_input_authority_to_dict_v1,
)
from HVAC.hydronics.proportioning.balancing_point_proportioning_commit_readiness_v1 import (
    GENERIC_KVS_BASIS_APPROVED,
    PointProportioningCommitReadinessV1,
)
from HVAC.hydronics.proportioning.proportioning_readiness_v1 import (
    build_proportioning_readiness_v1,
)
from HVAC.hydronics.proportioning.return_arrangement_acceptance_intent_v1 import (
    UNDECIDED,
)


_BASIS_ONLY_OUTPUT_STATUS_V1 = (
    "Ready for basis-only Proportioned output export — "
    "final hydraulics not included"
)


@dataclass(frozen=True, slots=True)
class CommittedPointValveBasisV1:
    """Frozen manual generic-Kvs basis; never a selected valve product."""

    balancing_point_id: str
    accepted_kvs_basis: float
    disposition: str = APPROVED_FOR_PRODUCT_SEARCH


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
    • manually approved generic-Kvs point bases

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

    committed_point_valve_bases: tuple[CommittedPointValveBasisV1, ...] = ()
    point_valve_basis_status: str = (
        "No committed point-valve basis evidence"
    )

    # H-S54-A — optional typed numeric authority; H-S54-B wires Commit.
    hydraulic_input_authority: (
        CommittedProportioningHydraulicInputAuthorityV1 | None
    ) = None
    hydraulic_input_authority_status: str = (
        "No committed hydraulic-input authority"
    )

    basis_only_output_ready: bool = True
    basis_only_output_status: str = _BASIS_ONLY_OUTPUT_STATUS_V1

    note: str = (
        "Frozen accepted proportioning basis only — no pump, valve product, "
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
        *,
        point_commit_readiness: PointProportioningCommitReadinessV1 | None = None,
        hydraulic_input_authority: (
            CommittedProportioningHydraulicInputAuthorityV1 | None
        ) = None,
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

    point_valve_bases: tuple[CommittedPointValveBasisV1, ...] = ()
    point_valve_basis_status = "No committed point-valve basis evidence"
    if point_commit_readiness is not None:
        if not isinstance(
                point_commit_readiness,
                PointProportioningCommitReadinessV1,
        ):
            blockers.append("H-S51-A point commit readiness type required")
        elif not point_commit_readiness.ready:
            blockers.extend(tuple(point_commit_readiness.blockers or ()))
            if not point_commit_readiness.blockers:
                blockers.append("H-S51-A point commit readiness required")
        else:
            try:
                point_valve_bases = _freeze_point_valve_bases_v1(
                    point_commit_readiness
                )
            except ValueError as exc:
                blockers.append(str(exc))
            point_valve_basis_status = (
                f"{len(point_valve_bases)} manually approved generic-Kvs "
                "point basis row(s) frozen — no valve product selected"
            )

    hydraulic_input_authority_status = (
        "No committed hydraulic-input authority"
    )
    if hydraulic_input_authority is not None:
        if not isinstance(
            hydraulic_input_authority,
            CommittedProportioningHydraulicInputAuthorityV1,
        ):
            blockers.append(
                "H-S54-A hydraulic-input authority type required"
            )
        elif not hydraulic_input_authority.ready:
            blockers.extend(tuple(hydraulic_input_authority.blockers or ()))
            if not hydraulic_input_authority.blockers:
                blockers.append(
                    "H-S54-A hydraulic-input authority must be ready"
                )
        else:
            hydraulic_input_authority_status = (
                hydraulic_input_authority.status
            )

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
        committed_point_valve_bases=point_valve_bases,
        point_valve_basis_status=point_valve_basis_status,
        hydraulic_input_authority=hydraulic_input_authority,
        hydraulic_input_authority_status=(
            hydraulic_input_authority_status
        ),
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


def _freeze_point_valve_bases_v1(
        readiness: PointProportioningCommitReadinessV1,
) -> tuple[CommittedPointValveBasisV1, ...]:
    result: list[CommittedPointValveBasisV1] = []
    seen: set[str] = set()
    for row in tuple(readiness.rows or ()):
        if not bool(getattr(row, "valve_duty_required", False)):
            continue
        point_id = str(getattr(row, "balancing_point_id", "") or "").strip()
        kvs = _positive_finite_v1(getattr(row, "accepted_kvs_basis", None))
        disposition = str(getattr(row, "disposition", "") or "").strip()
        if not point_id:
            raise ValueError("Committed point-valve basis requires stable point ID")
        if point_id in seen:
            raise ValueError(f"Duplicate committed point-valve basis: {point_id}")
        if (
                getattr(row, "readiness_state_id", "")
                != GENERIC_KVS_BASIS_APPROVED
                or not bool(getattr(row, "ready", False))
                or kvs is None
                or disposition != APPROVED_FOR_PRODUCT_SEARCH
        ):
            raise ValueError(
                f"{point_id}: manually approved generic Kvs basis required"
            )
        seen.add(point_id)
        result.append(CommittedPointValveBasisV1(
            balancing_point_id=point_id,
            accepted_kvs_basis=kvs,
            disposition=disposition,
        ))
    return tuple(result)


def _positive_finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0.0 else None


def _point_valve_bases_from_dict_v1(
        value: object,
) -> tuple[CommittedPointValveBasisV1, ...]:
    if not isinstance(value, list):
        return ()
    result: list[CommittedPointValveBasisV1] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, dict):
            continue
        point_id = str(raw.get("balancing_point_id") or "").strip()
        kvs = _positive_finite_v1(raw.get("accepted_kvs_basis"))
        disposition = str(raw.get("disposition") or "").strip()
        if (
                not point_id
                or point_id in seen
                or kvs is None
                or disposition != APPROVED_FOR_PRODUCT_SEARCH
        ):
            continue
        seen.add(point_id)
        result.append(CommittedPointValveBasisV1(
            balancing_point_id=point_id,
            accepted_kvs_basis=kvs,
            disposition=disposition,
        ))
    return tuple(result)


def _bool_from_dict_v1(
        value: object,
        *,
        default: bool,
) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    text = str(value).strip().lower()

    if text in {"1", "true", "yes", "y", "ready"}:
        return True

    if text in {"0", "false", "no", "n", "blocked"}:
        return False

    return default


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
        "committed_point_valve_bases": [
            {
                "balancing_point_id": row.balancing_point_id,
                "accepted_kvs_basis": float(row.accepted_kvs_basis),
                "disposition": row.disposition,
            }
            for row in tuple(
                getattr(snapshot, "committed_point_valve_bases", ()) or ()
            )
        ],
        "point_valve_basis_status": str(
            getattr(
                snapshot,
                "point_valve_basis_status",
                "No committed point-valve basis evidence",
            )
            or "No committed point-valve basis evidence"
        ),
        "hydraulic_input_authority": (
            committed_proportioning_hydraulic_input_authority_to_dict_v1(
                getattr(snapshot, "hydraulic_input_authority", None)
            )
        ),
        "hydraulic_input_authority_status": str(
            getattr(
                snapshot,
                "hydraulic_input_authority_status",
                "No committed hydraulic-input authority",
            )
            or "No committed hydraulic-input authority"
        ),
        "basis_only_output_ready": bool(
            getattr(snapshot, "basis_only_output_ready", True)
        ),
        "basis_only_output_status": str(
            getattr(
                snapshot,
                "basis_only_output_status",
                _BASIS_ONLY_OUTPUT_STATUS_V1,
            )
            or _BASIS_ONLY_OUTPUT_STATUS_V1
        ),
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
        committed_point_valve_bases=_point_valve_bases_from_dict_v1(
            data.get("committed_point_valve_bases")
        ),
        point_valve_basis_status=str(
            data.get(
                "point_valve_basis_status",
                "No committed point-valve basis evidence",
            )
            or "No committed point-valve basis evidence"
        ),
        hydraulic_input_authority=(
            committed_proportioning_hydraulic_input_authority_from_dict_v1(
                data.get("hydraulic_input_authority")
            )
        ),
        hydraulic_input_authority_status=str(
            data.get(
                "hydraulic_input_authority_status",
                "No committed hydraulic-input authority",
            )
            or "No committed hydraulic-input authority"
        ),
        basis_only_output_ready=_bool_from_dict_v1(
            data.get("basis_only_output_ready"),
            default=True,
        ),
        basis_only_output_status=str(
            data.get(
                "basis_only_output_status",
                _BASIS_ONLY_OUTPUT_STATUS_V1,
            )
            or _BASIS_ONLY_OUTPUT_STATUS_V1
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
