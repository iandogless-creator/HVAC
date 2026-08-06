# ======================================================================
# H-S66-N2D1B — Atomic missing automatic thermal-basis acceptance
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_automatic_thermal_basis_bulk_acceptance_v1 import (
    build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisIntentV1,
)


def _row(section_id: str, h_conv: float, *, complete: bool = True):
    return SimpleNamespace(
        section_id=section_id,
        surface_temperature_C=70.0,
        ambient_air_temperature_C=21.0,
        mean_radiant_temperature_C=21.0,
        emissivity=0.20,
        external_convection_coefficient_W_m2K=h_conv,
        complete=complete,
        blockers=() if complete else ("test unresolved input",),
    )


existing = CommittedPipeSectionThermalConditionBasisIntentV1()
existing.set_section_basis(
    section_id="section-a",
    committed_schedule_fingerprint="schedule-a",
    thermal_basis=build_explicit_bare_pipe_thermal_condition_basis_v1(
        surface_temperature_C=58.0,
        ambient_air_temperature_C=19.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.85,
        external_convection_coefficient_W_m2K=5.2,
    ),
    emissivity_override=0.85,
)
automatic = SimpleNamespace(
    ready=True,
    sections=(
        _row("section-a", 7.1),
        _row("section-b", 7.6),
        _row("section-c", 8.4),
    ),
)

accepted = build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1(
    committed_schedule_fingerprint="schedule-a",
    committed_section_ids=("section-a", "section-b", "section-c"),
    automatic_resolution=automatic,
    existing_intent=existing,
)
assert accepted.section_count == 3
assert accepted.preserved_section_count == 1
assert accepted.added_section_count == 2
assert set(accepted.intent.basis_by_section_id) == {
    "section-a", "section-b", "section-c"
}
assert set(existing.basis_by_section_id) == {"section-a"}
assert accepted.intent.basis_by_section_id["section-a"] == (
    existing.basis_by_section_id["section-a"]
)
assert accepted.intent.emissivity_override_by_section_id == {
    "section-a": 0.85
}
assert accepted.intent.basis_by_section_id[
    "section-b"
].external_convection_coefficient_W_m2K == 7.6

# One incomplete missing preview blocks before the source intent is touched.
incomplete = SimpleNamespace(
    ready=True,
    sections=(
        _row("section-a", 7.1),
        _row("section-b", 7.6),
        _row("section-c", 8.4, complete=False),
    ),
)
try:
    build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1(
        committed_schedule_fingerprint="schedule-a",
        committed_section_ids=("section-a", "section-b", "section-c"),
        automatic_resolution=incomplete,
        existing_intent=existing,
    )
except ValueError as exc:
    assert "section-c" in str(exc)
    assert "test unresolved input" in str(exc)
else:
    raise AssertionError("Incomplete automatic preview should block")
assert set(existing.basis_by_section_id) == {"section-a"}

# Stale and non-exact identity sets remain fail closed.
for fingerprint, ids in (
    ("schedule-b", ("section-a", "section-b", "section-c")),
    ("schedule-a", ("section-a", "section-b")),
):
    try:
        build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1(
            committed_schedule_fingerprint=fingerprint,
            committed_section_ids=ids,
            automatic_resolution=automatic,
            existing_intent=existing,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Stale or non-exact bulk acceptance should block")

root = Path(__file__).resolve().parents[2]
adapter_source = (
    root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
).read_text(encoding="utf-8")
panel_source = (
    root / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
).read_text(encoding="utf-8")
assert 'action == "set_all_missing_automatic"' in adapter_source
assert "build_committed_pipe_automatic_thermal_basis_bulk_acceptance_v1(" in (
    adapter_source
)
assert '"automatic_complete"' in adapter_source
assert "missing automatic preview remains" in adapter_source
assert "Apply complete automatic bases to all missing sections" in panel_source
assert "Existing explicit section bases and local emissivity" in panel_source
assert 'callback({"action": "set_all_missing_automatic"})' in panel_source

print(
    "OK — H-S66-N2D1B atomic acceptance of complete automatic bases for "
    "all missing committed sections passed."
)
