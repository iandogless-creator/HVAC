from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)
from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    CommittedPipeSectionThermalConditionBasisIntentV1,
)


def _basis(emissivity: float = 0.95):
    return build_explicit_bare_pipe_thermal_condition_basis_v1(
        surface_temperature_C=70.0,
        ambient_air_temperature_C=21.0,
        mean_radiant_temperature_C=21.0,
        emissivity=emissivity,
        external_convection_coefficient_W_m2K=5.0,
    )


def _resolve(intent, default_emissivity):
    return build_automatic_committed_pipe_thermal_basis_resolution_v1(
        committed_authority=SimpleNamespace(
            ready=True,
            sections=(SimpleNamespace(section_id="section-001"),),
        ),
        committed_schedule_fingerprint="schedule-a",
        design_flow_temperature_C=75.0,
        design_return_temperature_C=65.0,
        default_internal_temperature_C=21.0,
        default_pipe_emissivity=default_emissivity,
        thermal_basis_intent=intent,
    )


def main() -> None:
    # Environment owns one explicit project default; legacy projects remain
    # unresolved rather than acquiring a hidden surface assumption.
    assert EnvironmentStateV1().bare_pipe_emissivity is None
    legacy = EnvironmentStateV1.from_dict({})
    assert legacy.bare_pipe_emissivity is None
    stored = EnvironmentStateV1(bare_pipe_emissivity=0.93)
    assert EnvironmentStateV1.from_dict(stored.to_dict()).bare_pipe_emissivity == 0.93

    # A persisted complete section may inherit Environment emissivity.
    intent = CommittedPipeSectionThermalConditionBasisIntentV1()
    intent.set_section_basis(
        section_id="section-001",
        committed_schedule_fingerprint="schedule-a",
        thermal_basis=_basis(),
        emissivity_override=None,
    )
    assert intent.emissivity_override_by_section_id == {}
    inherited = _resolve(intent, 0.93).sections[0]
    assert inherited.complete is True
    assert inherited.emissivity == 0.93
    assert inherited.emissivity_source == (
        "Environment universal bare-pipe emissivity"
    )
    changed_default = _resolve(intent, 0.28).sections[0]
    assert changed_default.emissivity == 0.28

    # One stable section can override the project default; serialisation keeps
    # the override and clearing/reapplying inheritance removes it.
    intent.set_section_basis(
        section_id="section-001",
        committed_schedule_fingerprint="schedule-a",
        thermal_basis=_basis(0.77),
        emissivity_override=0.77,
    )
    local = _resolve(intent, 0.28).sections[0]
    assert local.emissivity == 0.77
    assert local.emissivity_source == (
        "Committed-section local emissivity override"
    )
    restored = CommittedPipeSectionThermalConditionBasisIntentV1.from_dict(
        intent.to_dict()
    )
    assert restored.emissivity_override_by_section_id == {
        "section-001": 0.77
    }

    # Pre-H-S66-K records migrate conservatively: their explicit section
    # emissivity remains a local override.
    legacy_payload = intent.to_dict()
    legacy_payload.pop("emissivity_override_by_section_id")
    legacy_intent = CommittedPipeSectionThermalConditionBasisIntentV1.from_dict(
        legacy_payload
    )
    assert legacy_intent.emissivity_override_by_section_id == {
        "section-001": 0.77
    }

    root = Path(__file__).resolve().parents[2]
    environment_panel = (
        root / "HVAC/gui_v3/panels/environment_panel.py"
    ).read_text(encoding="utf-8")
    environment_adapter = (
        root / "HVAC/gui_v3/adapters/environment_panel_adapter.py"
    ).read_text(encoding="utf-8")
    hydronics_panel = (
        root / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    hydronics_adapter = (
        root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "Pipe heat-loss defaults" in environment_panel
    assert "Universal bare-pipe emissivity (0–1)" in environment_panel
    assert "bare_pipe_emissivity_changed = Signal(float)" in environment_panel
    assert "set_bare_pipe_emissivity" in environment_panel
    assert "Painted/coated pipe — 0.95" in environment_panel
    assert "Bright/polished metal — 0.05" in environment_panel
    assert "_bare_pipe_emissivity_input = QComboBox" in environment_panel
    assert "_on_bare_pipe_emissivity_changed" in environment_adapter
    assert "env.bare_pipe_emissivity" in environment_adapter
    assert "project_changed" in environment_adapter
    assert "Override universal emissivity for this section" in hydronics_panel
    assert "_committed_pipe_emissivity_input_v1 = QComboBox" in hydronics_panel
    assert "_committed_pipe_emissivity_value_v1" in hydronics_panel
    assert hydronics_adapter.count(
        "default_pipe_emissivity="
    ) >= 2
    assert 'emissivity_override=payload.get("emissivity_override")' in (
        hydronics_adapter
    )

    print(
        "OK — H-S66-K Environment universal pipe emissivity and exact "
        "committed-section local overrides passed."
    )


if __name__ == "__main__":
    main()
