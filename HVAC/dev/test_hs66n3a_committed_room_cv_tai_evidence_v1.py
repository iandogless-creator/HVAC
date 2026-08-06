# ======================================================================
# H-S66-N3A — Committed room Cv/Tai evidence authority
# ======================================================================

from __future__ import annotations

from HVAC.heatloss.physics.committed_room_cv_tai_evidence_v1 import (
    build_committed_room_cv_tai_evidence_v1,
)


def _build(**changes):
    values = {
        "heatloss_results_valid": True,
        "committed_room_ids": ("room-a", "room-b"),
        "total_fabric_heat_loss_W_by_room_id": {
            "room-a": 960.0,
            "room-b": 480.0,
        },
        "total_exposed_area_m2_by_room_id": {
            "room-a": 40.0,
            "room-b": 25.0,
        },
        "effective_tei_C_by_room_id": {
            "room-a": 20.0,
            "room-b": 18.0,
        },
        "tei_source_by_room_id": {
            "room-a": "Room explicit Tei",
            "room-b": "Environment default Tei",
        },
    }
    values.update(changes)
    return build_committed_room_cv_tai_evidence_v1(**values)


resolved = _build()
repeated = _build()
assert resolved == repeated
assert resolved.ready
assert resolved.room_count == 2
assert resolved.blockers == ()
rows = {row.room_id: row for row in resolved.rooms}
assert rows["room-a"].cv_K == 5.0
assert rows["room-a"].tai_C == 25.0
assert rows["room-a"].tei_C == 20.0
assert rows["room-a"].tei_source == "Room explicit Tei"
assert rows["room-b"].cv_K == 4.0
assert rows["room-b"].tai_C == 22.0

# Qv is intentionally absent from the contract and cannot affect Tai.
assert not hasattr(rows["room-a"], "q_ventilation_W")
assert "Qv is neither an input nor an output" in resolved.note

stale = _build(heatloss_results_valid=False)
assert not stale.ready
assert stale.rooms == ()
assert stale.blockers == ("Fresh accepted heat-loss results are required",)

missing_area = _build(
    total_exposed_area_m2_by_room_id={"room-a": 40.0}
)
assert not missing_area.ready
assert "room-b: committed room exposed-area is required" in (
    missing_area.blockers
)

zero_area = _build(
    total_exposed_area_m2_by_room_id={"room-a": 0.0, "room-b": 25.0}
)
assert not zero_area.ready
assert "room-a: Total exposed area must be greater than zero" in (
    zero_area.blockers
)

extra_identity = _build(
    effective_tei_C_by_room_id={
        "room-a": 20.0,
        "room-b": 18.0,
        "room-c": 19.0,
    }
)
assert not extra_identity.ready
assert "room-c: Tei evidence has no committed room identity" in (
    extra_identity.blockers
)

noncanonical = _build(committed_room_ids=(" room-a ", "room-b"))
assert not noncanonical.ready
assert "Every committed room requires canonical room_id" in (
    noncanonical.blockers
)

negative_qf = _build(
    total_fabric_heat_loss_W_by_room_id={"room-a": -1.0, "room-b": 480.0}
)
assert not negative_qf.ready
assert "room-a: Total fabric heat loss must not be negative" in (
    negative_qf.blockers
)

print(
    "OK — H-S66-N3A fresh committed room fabric evidence resolves "
    "Cv/Tai without ventilation feedback."
)
