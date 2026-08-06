# ======================================================================
# H-S66-N2D1A — Independent automatic-field resolution and blockers
# ======================================================================

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.heatloss.physics.automatic_committed_pipe_thermal_basis_resolver_v1 import (
    build_automatic_committed_pipe_thermal_basis_resolution_v1,
)


authority = SimpleNamespace(
    ready=True,
    sections=(SimpleNamespace(section_id="section-001"),),
)
valid_n2d = SimpleNamespace(
    section_id="section-001",
    ready=True,
    ambient_air_temperature_C=21.0,
    mean_surface_temperature_C=70.0,
    effective_external_convection_coefficient_W_m2K=4.75,
    source="Stacked pair — H-S66-N2D evidence",
)

# A missing unrelated emissivity must not suppress valid N2D preview evidence.
partial = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule-a",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=21.0,
    default_pipe_emissivity=None,
    external_convection_by_section_id={"section-001": valid_n2d},
)
assert partial.ready
assert partial.complete_section_count == 0
row = partial.sections[0]
assert row.external_convection_coefficient_W_m2K == 4.75
assert row.external_convection_source == valid_n2d.source
assert row.emissivity is None
assert not row.complete
assert row.blockers == (
    "Environment universal bare-pipe emissivity is required",
)
assert "N2D external convection resolved independently" in row.status
assert "Environment universal bare-pipe emissivity is required" in row.status

# A convection-specific mismatch still withholds h and reports the exact cause.
mismatched_n2d = SimpleNamespace(
    **{
        **vars(valid_n2d),
        "ambient_air_temperature_C": 20.0,
    }
)
mismatched = build_automatic_committed_pipe_thermal_basis_resolution_v1(
    committed_authority=authority,
    committed_schedule_fingerprint="schedule-a",
    design_flow_temperature_C=75.0,
    design_return_temperature_C=65.0,
    default_internal_temperature_C=21.0,
    default_pipe_emissivity=0.20,
    external_convection_by_section_id={"section-001": mismatched_n2d},
)
mismatched_row = mismatched.sections[0]
assert mismatched_row.external_convection_coefficient_W_m2K is None
assert not mismatched_row.complete
assert any(
    "local ambient-air temperature does not match" in blocker
    for blocker in mismatched_row.blockers
)
assert "external convection unresolved" in mismatched_row.status
assert "local ambient-air temperature does not match" in mismatched_row.status

# The live adapter must report actual row resolution, not mapping presence alone.
root = Path(__file__).resolve().parents[2]
adapter_source = (
    root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
).read_text(encoding="utf-8")
assert "n2d_h_count" in adapter_source
assert "automatic_blockers" in adapter_source
assert "automatic external h conv is resolved from N2D for all" in adapter_source
assert "automatic external h conv is only resolved from N2D" in adapter_source
assert "Remaining incomplete automatic input(s)" in adapter_source

print(
    "OK — H-S66-N2D1A independent automatic external-convection preview "
    "and truthful blocker reporting passed."
)
