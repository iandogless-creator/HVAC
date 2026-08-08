# ======================================================================
# H-S66-N3D3 — Complete-room enclosure weighting into N3D
# ======================================================================

from __future__ import annotations

from dataclasses import replace
import math

from HVAC.heatloss.physics.committed_internal_surface_temperature_evidence_v1 import (
    build_committed_internal_surface_temperature_evidence_v1,
)
from HVAC.heatloss.physics.committed_room_enclosure_mean_radiant_handoff_v1 import (
    build_committed_room_enclosure_mean_radiant_handoff_v1,
)


def _surface_evidence(*, area_scale=1.0):
    return build_committed_internal_surface_temperature_evidence_v1(
        heatloss_results_valid=True,
        committed_room_ids=("room-a", "room-b"),
        effective_internal_temperature_C_by_room_id={
            "room-a": 20.0,
            "room-b": 21.0,
        },
        accepted_fabric_rows=(
            {
                "room_id": "room-a",
                "surface_id": "room-a-wall",
                "surface_class": "wall",
                "area_m2": 20.0 * area_scale,
                "q_fabric_W": 200.0 * area_scale,
            },
            {
                "room_id": "room-a",
                "surface_id": "room-a-window",
                "surface_class": "window",
                "area_m2": 10.0 * area_scale,
                "q_fabric_W": 200.0 * area_scale,
            },
            {
                "room_id": "room-b",
                "surface_id": "room-b-enclosure",
                "surface_class": "wall",
                "area_m2": 30.0 * area_scale,
                "q_fabric_W": 0.0,
            },
        ),
    )


def _build(evidence=None, room_ids=("room-a", "room-b")):
    return build_committed_room_enclosure_mean_radiant_handoff_v1(
        committed_room_ids=room_ids,
        internal_surface_temperature_evidence=(
            _surface_evidence() if evidence is None else evidence
        ),
    )


resolved = _build()
assert resolved == _build()
assert resolved.ready
assert resolved.room_count == 2
assert resolved.blockers == ()
rooms = {row.room_id: row for row in resolved.rooms}

# N3D1 resolves 18.7 C wall and 17.4 C window for room-a. N3D3 uses
# their 2/3 and 1/3 enclosure area fractions in N3D's fourth-power mean.
expected_room_a_C = (
    (2.0 / 3.0) * (18.7 + 273.15) ** 4
    + (1.0 / 3.0) * (17.4 + 273.15) ** 4
) ** 0.25 - 273.15
assert math.isclose(
    rooms["room-a"].mean_radiant_temperature_C,
    expected_room_a_C,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert rooms["room-a"].surface_count == 2
assert math.isclose(
    rooms["room-a"].radiant_view_factor_sum,
    1.0,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert rooms["room-b"].mean_radiant_temperature_C == 21.0
assert "area-fraction weighting" in rooms["room-a"].source
assert "not position-specific geometric view factors" in (
    rooms["room-a"].source
)
assert "area-fraction approximation" in resolved.note
assert "not a geometric view-factor solution" in resolved.note

# Only relative areas matter; uniform area scaling cannot change Tri.
scaled = _build(evidence=_surface_evidence(area_scale=10.0))
assert scaled.ready
for original, enlarged in zip(resolved.rooms, scaled.rooms, strict=True):
    assert original.room_id == enlarged.room_id
    assert math.isclose(
        original.mean_radiant_temperature_C,
        enlarged.mean_radiant_temperature_C,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )

stale_evidence = replace(
    _surface_evidence(),
    ready=False,
    surfaces=(),
    surface_count=0,
    room_count=0,
    blockers=("Fresh accepted heat-loss results are required",),
)
stale = _build(evidence=stale_evidence)
assert not stale.ready
assert "Ready N3D1 internal-surface temperature evidence is required" in (
    stale.blockers
)
assert "Fresh accepted heat-loss results are required" in stale.blockers

missing_room = _build(room_ids=("room-a", "room-b", "room-c"))
assert not missing_room.ready
assert "room-c: complete resolved enclosure surfaces are required" in (
    missing_room.blockers
)

extra_room = _build(room_ids=("room-a",))
assert not extra_room.ready
assert "room-b: resolved surface has no committed room identity" in (
    extra_room.blockers
)

evidence = _surface_evidence()
duplicate = replace(
    evidence,
    surfaces=(*evidence.surfaces, evidence.surfaces[0]),
    surface_count=evidence.surface_count + 1,
)
duplicate_result = _build(evidence=duplicate)
assert not duplicate_result.ready
assert "Duplicate resolved internal surface: room-a-wall" in (
    duplicate_result.blockers
)

zero_area_surface = replace(evidence.surfaces[0], area_m2=0.0)
zero_area = replace(
    evidence,
    surfaces=(zero_area_surface, *evidence.surfaces[1:]),
)
zero_area_result = _build(evidence=zero_area)
assert not zero_area_result.ready
assert "room-a/room-a-wall: Resolved surface area must be greater than zero" in (
    zero_area_result.blockers
)

print(
    "OK — H-S66-N3D3 complete-room enclosure area weighting into N3D "
    "passed."
)
