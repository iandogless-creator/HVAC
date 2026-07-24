# ======================================================================
# H-S51-A — Point-aware proportioning commit readiness
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.hydronics.proportioning.balancing_point_accepted_kvs_consequence_disposition_intent_v1 import (
    APPROVED_FOR_PRODUCT_SEARCH,
    KVS_REVISION_REQUIRED,
    ResolvedPointAcceptedKvsConsequenceDispositionV1,
)


NO_VALVE_POINT_READY = "no_valve_point_ready"
GENERIC_KVS_BASIS_APPROVED = "generic_kvs_basis_approved"
MANUAL_DISPOSITION_PENDING = "manual_disposition_pending"
KVS_REVISION_BLOCKS_COMMIT = "kvs_revision_blocks_commit"
POINT_EVIDENCE_UNAVAILABLE = "point_evidence_unavailable"


@dataclass(frozen=True, slots=True)
class PointProportioningCommitReadinessRowV1:
    balancing_point_id: str = ""
    readiness_state_id: str = ""
    ready: bool = False
    valve_duty_required: bool = False
    accepted_kvs_basis: float | None = None
    disposition: str = ""
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PointProportioningCommitReadinessV1:
    schema: str = "point_proportioning_commit_readiness_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    rows: tuple[PointProportioningCommitReadinessRowV1, ...] = ()
    exclusions: tuple[str, ...] = (
        "No valve catalogue required",
        "No valve product match required",
        "No valve product selected",
        "No automatic Kvs approval or revision",
        "No hydraulic mutation",
        "No pipe resizing",
        "No pump selection",
        "No final balancing",
        "No final hydraulic result",
        "No ProjectState mutation",
    )
    note: str = (
        "This gate permits a basis-only proportioning commit when every "
        "valve-duty point has explicit manual generic-Kvs approval."
    )


def build_point_proportioning_commit_readiness_v1(
    disposition_resolution: (
        ResolvedPointAcceptedKvsConsequenceDispositionV1 | None
    ),
) -> PointProportioningCommitReadinessV1:
    """Evaluate H-S48-D point dispositions for basis-only commit readiness."""

    if disposition_resolution is None:
        return _blocked_projection("H-S48-D point disposition evidence required")
    if not isinstance(
        disposition_resolution,
        ResolvedPointAcceptedKvsConsequenceDispositionV1,
    ):
        return _blocked_projection(
            "disposition_resolution is not "
            "ResolvedPointAcceptedKvsConsequenceDispositionV1"
        )

    input_rows = tuple(disposition_resolution.rows or ())
    if not input_rows:
        return _blocked_projection(
            "H-S48-D point disposition rows required",
            *tuple(disposition_resolution.blockers or ()),
        )

    rows = tuple(_resolve_row_v1(row) for row in input_rows)
    blockers = _unique_v1(
        tuple(disposition_resolution.blockers or ())
        + tuple(
            f"{row.balancing_point_id}: {blocker}"
            for row in rows
            for blocker in row.blockers
        )
    )
    ready = not blockers and all(row.ready for row in rows)
    approved_count = sum(
        row.readiness_state_id == GENERIC_KVS_BASIS_APPROVED for row in rows
    )
    return PointProportioningCommitReadinessV1(
        ready=ready,
        status=(
            f"Ready — {approved_count} valve-duty point(s) manually approved "
            "for basis-only proportioning commit; catalogue/product deferred"
            if ready
            else "Blocked — " + "; ".join(blockers)
        ),
        blockers=blockers,
        rows=rows,
    )


def _resolve_row_v1(row) -> PointProportioningCommitReadinessRowV1:
    point_id = str(getattr(row, "balancing_point_id", "") or "").strip()
    row_blockers = _unique_v1(tuple(getattr(row, "blockers", ()) or ()))
    status = str(getattr(row, "status", "") or "").strip()
    disposition = str(getattr(row, "disposition", "") or "").strip()

    if not point_id:
        return PointProportioningCommitReadinessRowV1(
            readiness_state_id=POINT_EVIDENCE_UNAVAILABLE,
            status="Blocked — stable balancing-point identity required",
            blockers=("Stable balancing-point identity required",),
        )
    if row_blockers or not bool(getattr(row, "ready", False)):
        blockers = row_blockers or ("Current H-S48-D point evidence required",)
        return PointProportioningCommitReadinessRowV1(
            balancing_point_id=point_id,
            readiness_state_id=POINT_EVIDENCE_UNAVAILABLE,
            status="Blocked — current point disposition evidence unavailable",
            blockers=blockers,
        )

    if status.startswith("No consequence disposition required"):
        return PointProportioningCommitReadinessRowV1(
            balancing_point_id=point_id,
            readiness_state_id=NO_VALVE_POINT_READY,
            ready=True,
            valve_duty_required=False,
            status="Ready — no valve duty at this point",
        )

    if (
        disposition == APPROVED_FOR_PRODUCT_SEARCH
        and bool(getattr(row, "approved_for_product_search", False))
    ):
        return PointProportioningCommitReadinessRowV1(
            balancing_point_id=point_id,
            readiness_state_id=GENERIC_KVS_BASIS_APPROVED,
            ready=True,
            valve_duty_required=True,
            accepted_kvs_basis=getattr(row, "accepted_kvs_basis", None),
            disposition=disposition,
            status=(
                "Ready — generic Kvs consequence manually approved; "
                "catalogue/product deferred"
            ),
        )

    if (
        disposition == KVS_REVISION_REQUIRED
        or bool(getattr(row, "kvs_revision_required", False))
    ):
        blocker = "Kvs revision required before proportioning commit"
        return PointProportioningCommitReadinessRowV1(
            balancing_point_id=point_id,
            readiness_state_id=KVS_REVISION_BLOCKS_COMMIT,
            valve_duty_required=True,
            status="Blocked — " + blocker,
            blockers=(blocker,),
        )

    blocker = "Manual accepted-Kvs consequence disposition required"
    return PointProportioningCommitReadinessRowV1(
        balancing_point_id=point_id,
        readiness_state_id=MANUAL_DISPOSITION_PENDING,
        valve_duty_required=True,
        status="Blocked — " + blocker,
        blockers=(blocker,),
    )


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_projection(*blockers: str) -> PointProportioningCommitReadinessV1:
    clean = _unique_v1(tuple(blockers))
    return PointProportioningCommitReadinessV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
