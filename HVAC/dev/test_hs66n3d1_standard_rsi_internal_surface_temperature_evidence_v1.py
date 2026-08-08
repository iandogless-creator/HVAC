# ======================================================================
# H-S66-N3D1 — Standard-Rsi internal-surface temperature evidence
# ======================================================================

from __future__ import annotations

from HVAC.heatloss.physics.committed_internal_surface_temperature_evidence_v1 import (
    build_committed_internal_surface_temperature_evidence_v1,
    standard_rsi_for_surface_class_v1,
)


def _rows():
    return (
        {
            "room_id": "room-a",
            "surface_id": "wall-a",
            "surface_class": "external_wall",
            "area_m2": 20.0,
            "q_fabric_W": 200.0,
        },
        {
            "room_id": "room-a",
            "surface_id": "roof-a",
            "surface_class": "roof",
            "area_m2": 10.0,
            "q_fabric_W": 50.0,
        },
        {
            "room_id": "room-b",
            "surface_id": "floor-b",
            "surface_class": "floor",
            "area_m2": 15.0,
            "q_fabric_W": 90.0,
        },
    )


def _build(**changes):
    values = {
        "heatloss_results_valid": True,
        "committed_room_ids": ("room-a", "room-b"),
        "effective_internal_temperature_C_by_room_id": {
            "room-a": 21.0,
            "room-b": 20.0,
        },
        "accepted_fabric_rows": _rows(),
    }
    values.update(changes)
    return build_committed_internal_surface_temperature_evidence_v1(**values)


resolved = _build()
assert resolved == _build()
assert resolved.ready
assert resolved.surface_count == 3
assert resolved.room_count == 2
assert resolved.blockers == ()
rows = {row.surface_id: row for row in resolved.surfaces}

assert rows["wall-a"].heat_flow_direction == "horizontal"
assert rows["wall-a"].internal_surface_resistance_m2K_W == 0.13
assert rows["wall-a"].internal_surface_temperature_C == 19.7
assert rows["roof-a"].heat_flow_direction == "upward"
assert rows["roof-a"].internal_surface_resistance_m2K_W == 0.10
assert rows["roof-a"].internal_surface_temperature_C == 20.5
assert rows["floor-b"].heat_flow_direction == "downward"
assert rows["floor-b"].internal_surface_resistance_m2K_W == 0.17
assert rows["floor-b"].internal_surface_temperature_C == 18.98
assert "do not come from, alter or complete the U-value" in resolved.note
assert "No view factors, Tri" in resolved.note

assert standard_rsi_for_surface_class_v1("window") == ("horizontal", 0.13)
assert standard_rsi_for_surface_class_v1("ceiling") == ("upward", 0.10)
assert standard_rsi_for_surface_class_v1("ground floor") == ("downward", 0.17)

# Signed inward heat flow raises the internal face temperature above room air.
inward = _build(
    accepted_fabric_rows=(
        {
            "room_id": "room-a",
            "surface_id": "wall-a",
            "surface_class": "wall",
            "area_m2": 10.0,
            "q_fabric_W": -100.0,
        },
        {
            "room_id": "room-b",
            "surface_id": "wall-b",
            "surface_class": "wall",
            "area_m2": 10.0,
            "q_fabric_W": 0.0,
        },
    )
)
assert inward.ready
assert inward.surfaces[0].internal_surface_temperature_C == 22.3

stale = _build(heatloss_results_valid=False)
assert not stale.ready
assert stale.surfaces == ()
assert "Fresh accepted heat-loss results are required" in stale.blockers

unsupported = _build(
    accepted_fabric_rows=(
        *_rows(),
        {
            "room_id": "room-a",
            "surface_id": "mystery-a",
            "surface_class": "mystery",
            "area_m2": 1.0,
            "q_fabric_W": 1.0,
        },
    )
)
assert not unsupported.ready
assert (
    "room-a/mystery-a: Unsupported surface class for standard Rsi: 'mystery'"
) in unsupported.blockers

missing_room_rows = _build(
    accepted_fabric_rows=tuple(
        row for row in _rows() if row["room_id"] == "room-a"
    )
)
assert not missing_room_rows.ready
assert "room-b: accepted fabric rows are required" in missing_room_rows.blockers

duplicate = _build(
    accepted_fabric_rows=(*_rows(), dict(_rows()[0]))
)
assert not duplicate.ready
assert "Duplicate accepted fabric surface: wall-a" in duplicate.blockers

extra_temperature = _build(
    effective_internal_temperature_C_by_room_id={
        "room-a": 21.0,
        "room-b": 20.0,
        "room-extra": 19.0,
    }
)
assert not extra_temperature.ready
assert (
    "room-extra: internal-temperature evidence has no committed room identity"
) in extra_temperature.blockers

print(
    "OK — H-S66-N3D1 standard-Rsi internal-surface temperature evidence "
    "from accepted fabric rows passed."
)
