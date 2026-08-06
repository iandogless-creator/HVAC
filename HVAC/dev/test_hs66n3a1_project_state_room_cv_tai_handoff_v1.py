# ======================================================================
# H-S66-N3A1 — ProjectState handoff into committed room Cv/Tai evidence
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


# Avoid the legacy Qt-owning HVAC.core package initialiser in headless tests.
root = Path(__file__).resolve().parents[2]
if "HVAC.core" not in sys.modules:
    core_package = ModuleType("HVAC.core")
    core_package.__path__ = [str(root / "HVAC/core")]
    sys.modules["HVAC.core"] = core_package

from HVAC.heatloss.adapters.committed_room_cv_tai_project_state_adapter_v1 import (
    build_committed_room_cv_tai_from_project_state_v1,
)


def _fabric_rows():
    return [
        {
            "surface_id": "surface-a1",
            "room_id": "room-a",
            "area_m2": 20.0,
            "delta_t_K": 23.0,
            "q_fabric_W": 500.0,
        },
        {
            "surface_id": "surface-a2",
            "room_id": "room-a",
            "area_m2": 20.0,
            "delta_t_K": 23.0,
            "q_fabric_W": 460.0,
        },
        {
            "surface_id": "surface-b1",
            "room_id": "room-b",
            "area_m2": 25.0,
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
resolved = build_committed_room_cv_tai_from_project_state_v1(project)
repeated = build_committed_room_cv_tai_from_project_state_v1(project)
assert resolved == repeated
assert repr(project) == before
assert resolved.ready
assert resolved.room_count == 2
rows = {row.room_id: row for row in resolved.rooms}
assert rows["room-a"].total_fabric_heat_loss_W == 960.0
assert rows["room-a"].total_exposed_area_m2 == 40.0
assert rows["room-a"].tei_C == 20.0
assert rows["room-a"].cv_K == 5.0
assert rows["room-a"].tai_C == 25.0
assert rows["room-a"].tei_source == (
    "Room internal design temperature (Ti/Tei)"
)
assert rows["room-b"].tei_C == 21.0
assert rows["room-b"].cv_K == 4.0
assert rows["room-b"].tai_C == 25.0
assert rows["room-b"].tei_source == (
    "Environment internal design temperature (Ti/Tei)"
)

# Persisted JSON uses the same list-of-dicts fabric shape.
persisted = _project()
persisted_result = build_committed_room_cv_tai_from_project_state_v1(persisted)
assert persisted_result == resolved

stale = build_committed_room_cv_tai_from_project_state_v1(
    _project(heatloss_valid=False)
)
assert not stale.ready
assert stale.blockers == ("Fresh accepted heat-loss results are required",)

# Qv/Qtotal are ignored: changing them cannot alter derived Tai.
qv_changed = _project()
qv_changed.heatloss_results["room_totals"]["room-a"].update(
    q_ventilation_W=99999.0,
    q_total_W=100959.0,
)
assert build_committed_room_cv_tai_from_project_state_v1(qv_changed) == resolved

# Accepted room Qf must reconcile exactly with its committed fabric rows.
qf_mismatch = _project()
qf_mismatch.heatloss_results["room_totals"]["room-a"]["q_fabric_W"] = 961.0
qf_blocked = build_committed_room_cv_tai_from_project_state_v1(qf_mismatch)
assert not qf_blocked.ready
assert "room-a: accepted room Qf does not match its fabric rows" in (
    qf_blocked.blockers
)

# An old fabric delta T cannot be combined with current Ti/Tei.
temperature_stale = _project()
temperature_stale.rooms["room-a"].internal_temp_override_C = 21.0
temperature_blocked = build_committed_room_cv_tai_from_project_state_v1(
    temperature_stale
)
assert not temperature_blocked.ready
assert "room-a: accepted fabric Ti/Tei basis is stale" in (
    temperature_blocked.blockers
)

# Exact identities are enforced through the N3A authority.
extra = _project()
extra.heatloss_results["room_totals"]["room-extra"] = {
    "q_fabric_W": 0.0,
    "q_ventilation_W": 0.0,
    "q_total_W": 0.0,
}
extra_result = build_committed_room_cv_tai_from_project_state_v1(extra)
assert not extra_result.ready
assert (
    "room-extra: fabric heat-loss evidence has no committed room identity"
    in extra_result.blockers
)

print(
    "OK — H-S66-N3A1 fresh ProjectState room Qf/area/Ti-Tei evidence "
    "hands off to N3A without Qv feedback."
)
