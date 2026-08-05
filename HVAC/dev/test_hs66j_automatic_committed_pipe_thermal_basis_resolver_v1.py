# ======================================================================
# H-S66-J — Automatic committed-section bare-pipe thermal-basis resolver
# ======================================================================

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)


def _authority(*section_ids: str):
    return SimpleNamespace(
        ready=True,
        sections=tuple(
            SimpleNamespace(section_id=section_id)
            for section_id in section_ids
        ),
    )


def main() -> None:
    authority = _authority("section-001", "section-002")
    result = build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=authority,
        committed_schedule_fingerprint="schedule-a",
        design_flow_temperature_C=75.0,
        design_return_temperature_C=65.0,
        default_internal_temperature_C=21.0,
    )
    repeated = build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=authority,
        committed_schedule_fingerprint="schedule-a",
        design_flow_temperature_C=75.0,
        design_return_temperature_C=65.0,
        default_internal_temperature_C=21.0,
    )
    assert result == repeated
    assert result.ready is True
    assert result.section_count == 2
    assert result.complete_section_count == 0
    for row in result.sections:
        assert math.isclose(row.surface_temperature_C or 0.0, 70.0)
        assert row.ambient_air_temperature_C == 21.0
        assert row.mean_radiant_temperature_C == 21.0
        assert row.emissivity is None
        assert row.external_convection_coefficient_W_m2K is None
        assert row.complete is False
        assert "no temperature decay" in row.surface_temperature_source
        assert "MRT equals air" in row.mean_radiant_temperature_source
        assert row.emissivity_source == "Unresolved"
        assert "orientation/correlation" in row.external_convection_source

    manual_entry = SimpleNamespace(
        surface_temperature_C=58.0,
        ambient_air_temperature_C=19.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.94,
        external_convection_coefficient_W_m2K=5.2,
    )
    manual_intent = SimpleNamespace(
        committed_schedule_fingerprint="schedule-a",
        basis_by_section_id={"section-001": manual_entry},
    )
    mixed = build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=authority,
        committed_schedule_fingerprint="schedule-a",
        design_flow_temperature_C=75.0,
        design_return_temperature_C=65.0,
        default_internal_temperature_C=21.0,
        thermal_basis_intent=manual_intent,
    )
    assert mixed.complete_section_count == 1
    first, second = mixed.sections
    assert first.complete is True
    assert first.surface_temperature_C == 58.0
    assert first.emissivity == 0.94
    assert first.surface_temperature_source == "Manual H-S66-F override"
    assert second.complete is False
    assert second.surface_temperature_C == 70.0

    inherited_emissivity = (
        build_automatic_committed_pipe_thermal_basis_resolution_v1(
            committed_authority=authority,
            committed_schedule_fingerprint="schedule-a",
            design_flow_temperature_C=75.0,
            design_return_temperature_C=65.0,
            default_internal_temperature_C=21.0,
            default_pipe_emissivity=0.93,
        )
    )
    assert inherited_emissivity.sections[0].emissivity == 0.93
    assert inherited_emissivity.sections[0].emissivity_source == (
        "Environment universal bare-pipe emissivity"
    )

    # A stale manual intent never crosses into the current schedule.
    stale = build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=authority,
        committed_schedule_fingerprint="schedule-b",
        design_flow_temperature_C=75.0,
        design_return_temperature_C=65.0,
        default_internal_temperature_C=21.0,
        thermal_basis_intent=manual_intent,
    )
    assert stale.ready is False
    assert stale.complete_section_count == 0
    assert stale.sections[0].surface_temperature_C == 70.0
    assert any("stale" in blocker for blocker in stale.blockers)

    unresolved = build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=authority,
        committed_schedule_fingerprint="schedule-a",
        design_flow_temperature_C=None,
        design_return_temperature_C=None,
        default_internal_temperature_C=None,
    )
    assert unresolved.ready is True
    assert unresolved.sections[0].surface_temperature_C is None
    assert unresolved.sections[0].ambient_air_temperature_C is None
    assert unresolved.sections[0].mean_radiant_temperature_C is None
    assert any("flow temperature" in blocker for blocker in unresolved.sections[0].blockers)
    assert any("internal temperature" in blocker for blocker in unresolved.sections[0].blockers)

    root = Path(__file__).resolve().parents[2]
    adapter_source = (
        root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    panel_source = (
        root / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    assert "resolve_hydronic_design_temperature_basis_v1(" in adapter_source
    assert (
        "build_automatic_committed_pipe_thermal_basis_resolution_v1("
        in adapter_source
    )
    assert '"resolution_note"' in adapter_source
    assert 'row.get("resolution_note")' in panel_source
    assert "thermal_basis_intent=intent" in adapter_source

    print(
        "OK — H-S66-J automatic committed-section bare-pipe thermal-basis "
        "resolver passed."
    )


if __name__ == "__main__":
    main()
