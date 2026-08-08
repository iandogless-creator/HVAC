# ======================================================================
# H-S66-N3D2 — ProjectState handoff into standard-Rsi Tsi evidence
# ======================================================================

from __future__ import annotations

import math
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


# Avoid the legacy Qt-owning HVAC.core package initialiser in headless tests.
root = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(root / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.adapters.committed_internal_surface_temperature_project_state_adapter_v1 import (
    build_committed_internal_surface_temperatures_from_project_state_v1,
)


def _fabric_rows():
    return [
        {
            "surface_id": "surface-a-wall",
            "room_id": "room-a",
            "surface_class": "external_wall",
            "area_m2": 20.0,
            "u_value_W_m2K": 500.0 / (20.0 * 23.0),
            "delta_t_K": 23.0,
            "q_fabric_W": 500.0,
        },
        {
            "surface_id": "surface-a-roof",
            "room_id": "room-a",
            "surface_class": "roof",
            "area_m2": 20.0,
            "u_value_W_m2K": 1.0,
            "delta_t_K": 23.0,
            "q_fabric_W": 460.0,
        },
        {
            "surface_id": "surface-b-floor",
            "room_id": "room-b",
            "surface_class": "floor",
            "area_m2": 25.0,
            "u_value_W_m2K": 0.8,
            "delta_t_K": 24.0,
            "q_fabric_W": 480.0,
        },
    ]


def _project(**changes):
    values = {
        "heatloss_valid": True,
        "environment": SimpleNamespace(
            default_internal_temp_C=21.0,
            external_design_temp_C=-3.0,
        ),
        "rooms": {
            "room-a": SimpleNamespace(internal_temp_override_C=20.0),
            "room-b": SimpleNamespace(internal_temp_override_C=None),
        },
        "heatloss_results": {
            "room_totals": {
                "room-a": {
                    "q_fabric_W": 960.0,
                    "q_ventilation_W": 100.0,
                    "q_total_W": 1060.0,
                },
                "room-b": {
                    "q_fabric_W": 480.0,
                    "q_ventilation_W": 80.0,
                    "q_total_W": 560.0,
                },
            },
            "fabric": _fabric_rows(),
            "ventilation": {"deliberately": "ignored"},
        },
    }
    values.update(changes)
    return SimpleNamespace(**values)


project = _project()
before = repr(project)
resolved = build_committed_internal_surface_temperatures_from_project_state_v1(
    project
)
repeated = build_committed_internal_surface_temperatures_from_project_state_v1(
    project
)
assert resolved == repeated
assert repr(project) == before
assert resolved.ready
assert resolved.surface_count == 3
assert resolved.room_count == 2
assert resolved.blockers == ()
rows = {row.surface_id: row for row in resolved.surfaces}
assert math.isclose(
    rows["surface-a-wall"].internal_surface_temperature_C,
    16.75,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert rows["surface-a-wall"].internal_air_temperature_C == 20.0
assert rows["surface-a-wall"].internal_surface_resistance_m2K_W == 0.13
assert math.isclose(
    rows["surface-a-roof"].internal_surface_temperature_C,
    17.7,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert rows["surface-a-roof"].internal_surface_resistance_m2K_W == 0.10
assert math.isclose(
    rows["surface-b-floor"].internal_surface_temperature_C,
    17.736,
    rel_tol=0.0,
    abs_tol=1.0e-12,
)
assert rows["surface-b-floor"].internal_air_temperature_C == 21.0
assert rows["surface-b-floor"].internal_surface_resistance_m2K_W == 0.17

# Qv/Qtotal are outside both N3A1 freshness and N3D1 surface physics.
qv_changed = _project()
qv_changed.heatloss_results["room_totals"]["room-a"].update(
    q_ventilation_W=99999.0,
    q_total_W=100959.0,
)
assert (
    build_committed_internal_surface_temperatures_from_project_state_v1(
        qv_changed
    )
    == resolved
)

stale = build_committed_internal_surface_temperatures_from_project_state_v1(
    _project(heatloss_valid=False)
)
assert not stale.ready
assert stale.surfaces == ()
assert stale.blockers == ("Fresh accepted heat-loss results are required",)

# Changing room Ti without a new accepted heat-loss run remains blocked by N3A1.
temperature_stale_project = _project()
temperature_stale_project.rooms["room-a"].internal_temp_override_C = 21.0
temperature_stale = (
    build_committed_internal_surface_temperatures_from_project_state_v1(
        temperature_stale_project
    )
)
assert not temperature_stale.ready
assert "room-a: accepted fabric Ti/Tei basis is stale" in (
    temperature_stale.blockers
)

# N3D1 owns surface-direction classification and blocks unknown rows.
unknown_class_project = _project()
unknown_class_project.heatloss_results["fabric"][0]["surface_class"] = "mystery"
unknown_class = build_committed_internal_surface_temperatures_from_project_state_v1(
    unknown_class_project
)
assert not unknown_class.ready
assert (
    "room-a/surface-a-wall: Unsupported surface class for standard Rsi: "
    "'mystery'"
) in unknown_class.blockers

# Persisted fabric containers are accepted without changing the result.
persisted = _project()
persisted.heatloss_results["fabric"] = {"rows": _fabric_rows()}
assert (
    build_committed_internal_surface_temperatures_from_project_state_v1(
        persisted
    )
    == resolved
)

print(
    "OK — H-S66-N3D2 fresh ProjectState accepted-fabric and room-temperature "
    "handoff into N3D1 passed."
)
