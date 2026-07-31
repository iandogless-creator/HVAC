# ======================================================================
# H-S61-H2B2 — Committed resized-output semantics
# ======================================================================

from __future__ import annotations

from HVAC.dev.test_hs58a_committed_proportioned_system_completion_status_v1 import (
    _build as _build_completion,
)
from HVAC.dev.test_hs59a_committed_proportioned_system_result_package_v1 import (
    _build as _build_package,
)
from HVAC.dev.test_hs61h1b_transactional_pipe_schedule_rebuild_v1 import (
    _fixtures,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_completion_status_v1 import (
    build_committed_proportioned_system_completion_status_v1,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_export_payload_v1 import (
    build_committed_proportioned_system_export_payload_v1,
)
from HVAC.hydronics.proportioning.committed_proportioned_system_result_package_v1 import (
    build_committed_proportioned_system_result_package_v1,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)
from HVAC.hydronics.proportioning.proportioned_pipe_schedule_commit_rebuild_v1 import (
    build_proportioned_pipe_schedule_commit_rebuild_v1,
)


def _assert_no_false_pipe_exclusion(result) -> None:
    exclusions = tuple(getattr(result, "exclusions", ()) or ())
    assert "No pipe resizing" not in exclusions
    assert any(
        "No pipe resizing performed" in value for value in exclusions
    )


def main() -> None:
    snapshot, material, acceptance, projection, reconciliation = _fixtures()
    rebuild = build_proportioned_pipe_schedule_commit_rebuild_v1(
        committed_snapshot=snapshot,
        material_intent=material,
        acceptance_resolution=acceptance,
        resized_hydraulics=projection,
        resized_point_reconciliation=reconciliation,
    )
    assert rebuild.ready is True, rebuild.status
    replacement = rebuild.replacement_snapshot
    assert replacement is not None

    completion = (
        build_committed_proportioned_system_completion_status_v1(replacement)
    )
    package = build_committed_proportioned_system_result_package_v1(
        replacement
    )
    payload = build_committed_proportioned_system_export_payload_v1(package)

    assert completion.ready is False
    assert completion.committed_resized_hydraulics is True
    assert completion.fresh_generic_kvs_review_required is True
    assert "committed resized hydraulics available" in completion.status
    assert "fresh manual generic-Kvs review required" in completion.status
    assert "overall completion awaits" in completion.note
    _assert_no_false_pipe_exclusion(completion)

    assert package.ready is False
    assert package.committed_resized_hydraulics is True
    assert package.fresh_generic_kvs_review_required is True
    assert "committed resized hydraulics available" in package.status
    assert "fresh manual generic-Kvs review required" in package.status
    _assert_no_false_pipe_exclusion(package)

    assert payload.ready is False
    assert "Committed resized hydraulics available" in payload.status
    assert "generic-Kvs review required before export" in payload.status
    _assert_no_false_pipe_exclusion(payload)

    # Existing basis-only snapshots retain their established readiness and do
    # not acquire resized-hydraulics or fresh-Kvs-review semantics.
    basis_only = ProportionedBasisSnapshotV1(
        return_arrangement_basis="DIRECT_RETURN",
    )
    basis_completion = _build_completion(basis_only)
    basis_package = _build_package(basis_only)
    assert basis_completion.ready is True
    assert basis_completion.committed_resized_hydraulics is False
    assert basis_completion.fresh_generic_kvs_review_required is False
    assert "committed resized hydraulics" not in basis_completion.status
    assert basis_package.ready is True
    assert basis_package.committed_resized_hydraulics is False
    assert basis_package.fresh_generic_kvs_review_required is False

    print(
        "OK — H-S61-H2B2 committed resized hydraulic/output semantics "
        "passed."
    )


if __name__ == "__main__":
    main()
