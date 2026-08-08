# ======================================================================
# H-S66-N3D — Committed-room mean-radiant temperature authority
# ======================================================================

from __future__ import annotations

import math

from HVAC.heatloss.physics.committed_room_mean_radiant_temperature_authority_v1 import (
    build_committed_room_mean_radiant_temperature_authority_v1,
)


def _build(**changes):
    values = {
        "surface_temperature_evidence_fresh": True,
        "committed_room_ids": ("room-a", "room-b"),
        "internal_surface_rows": (
            {
                "room_id": "room-a",
                "surface_id": "room-a-wall",
                "internal_surface_temperature_C": 18.0,
                "radiant_view_factor": 0.75,
            },
            {
                "room_id": "room-a",
                "surface_id": "room-a-window",
                "internal_surface_temperature_C": 10.0,
                "radiant_view_factor": 0.25,
            },
            {
                "room_id": "room-b",
                "surface_id": "room-b-enclosure",
                "internal_surface_temperature_C": 20.0,
                "radiant_view_factor": 1.0,
            },
        ),
    }
    values.update(changes)
    return build_committed_room_mean_radiant_temperature_authority_v1(**values)


resolved = _build()
assert resolved == _build()
assert resolved.ready
assert resolved.room_count == 2
assert resolved.blockers == ()
rows = {row.room_id: row for row in resolved.rooms}

expected_room_a_C = (
    0.75 * (18.0 + 273.15) ** 4 + 0.25 * (10.0 + 273.15) ** 4
) ** 0.25 - 273.15
assert math.isclose(
    rows["room-a"].mean_radiant_temperature_C,
    expected_room_a_C,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert not math.isclose(
    rows["room-a"].mean_radiant_temperature_C,
    0.75 * 18.0 + 0.25 * 10.0,
    rel_tol=0.0,
    abs_tol=1.0e-6,
)
assert rows["room-a"].surface_count == 2
assert rows["room-a"].radiant_view_factor_sum == 1.0
assert rows["room-b"].mean_radiant_temperature_C == 20.0
assert "does not infer surface temperatures from Qf" in resolved.note
assert "Environment-temperature proxy" in resolved.note

stale = _build(surface_temperature_evidence_fresh=False)
assert not stale.ready
assert stale.rooms == ()
assert stale.blockers == (
    "Fresh internal-surface temperature evidence is required",
)

# Supply only room-a explicitly; room-b must not silently inherit or proxy.
missing_room = _build(
    internal_surface_rows=(
        {
            "room_id": "room-a",
            "surface_id": "room-a-enclosure",
            "internal_surface_temperature_C": 18.0,
            "radiant_view_factor": 1.0,
        },
    )
)
assert not missing_room.ready
assert "room-b: complete internal-surface evidence is required" in (
    missing_room.blockers
)

incomplete_weights = _build(
    internal_surface_rows=(
        {
            "room_id": "room-a",
            "surface_id": "room-a-enclosure",
            "internal_surface_temperature_C": 18.0,
            "radiant_view_factor": 0.9,
        },
        {
            "room_id": "room-b",
            "surface_id": "room-b-enclosure",
            "internal_surface_temperature_C": 20.0,
            "radiant_view_factor": 1.0,
        },
    )
)
assert not incomplete_weights.ready
assert any(
    blocker.startswith("room-a: radiant view factors must sum to one")
    for blocker in incomplete_weights.blockers
)

duplicate_surface = _build(
    internal_surface_rows=(
        {
            "room_id": "room-a",
            "surface_id": "surface-shared",
            "internal_surface_temperature_C": 18.0,
            "radiant_view_factor": 1.0,
        },
        {
            "room_id": "room-b",
            "surface_id": "surface-shared",
            "internal_surface_temperature_C": 20.0,
            "radiant_view_factor": 1.0,
        },
    )
)
assert not duplicate_surface.ready
assert "Duplicate committed internal-surface identity: surface-shared" in (
    duplicate_surface.blockers
)

absolute_zero = _build(
    internal_surface_rows=(
        {
            "room_id": "room-a",
            "surface_id": "room-a-enclosure",
            "internal_surface_temperature_C": -273.15,
            "radiant_view_factor": 1.0,
        },
        {
            "room_id": "room-b",
            "surface_id": "room-b-enclosure",
            "internal_surface_temperature_C": 20.0,
            "radiant_view_factor": 1.0,
        },
    )
)
assert not absolute_zero.ready
assert (
    "room-a/room-a-enclosure: Internal-surface temperature must be above "
    "absolute zero"
) in absolute_zero.blockers

print(
    "OK — H-S66-N3D committed-room mean-radiant temperature authority "
    "passed."
)
