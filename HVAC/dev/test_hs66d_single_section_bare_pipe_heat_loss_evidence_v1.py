# ======================================================================
# H-S66-D — Deterministic single-section bare-pipe heat-loss evidence
# ======================================================================

from __future__ import annotations

import math
from pathlib import Path

from HVAC.heatloss.physics.bare_pipe_section_heat_loss_evidence_v1 import (
    build_bare_pipe_section_heat_loss_evidence_v1,
)
from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_catalogue_bare_pipe_input_from_thermal_basis_v1,
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.pipe_radiation_engine import (
    compute_bare_pipe_heat_loss_v1,
)


def _basis():
    return build_explicit_bare_pipe_thermal_condition_basis_v1(
        surface_temperature_C=60.0,
        ambient_air_temperature_C=20.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.95,
        external_convection_coefficient_W_m2K=5.0,
    )


def _section(
        *,
        section_id: str = "section-001",
        material_key: str = "copper",
        catalogue_size_key: int = 22,
        length_m: float = 5.0,
):
    return build_bare_pipe_section_heat_loss_evidence_v1(
        section_id=section_id,
        material_key=material_key,
        catalogue_size_key=catalogue_size_key,
        length_m=length_m,
        thermal_basis=_basis(),
    )


def main() -> None:
    evidence = _section()
    repeated = _section()
    assert evidence == repeated
    assert evidence.section_id == "section-001"
    assert evidence.material_key == "copper"
    assert evidence.material_label == "Copper EN1057"
    assert evidence.catalogue_size_key == 22
    assert math.isclose(evidence.actual_outside_diameter_mm, 22.0)
    assert math.isclose(evidence.length_m, 5.0)
    assert evidence.surface_temperature_C == 60.0
    assert evidence.ambient_air_temperature_C == 20.0
    assert evidence.mean_radiant_temperature_C == 18.0
    assert evidence.emissivity == 0.95
    assert evidence.external_convection_coefficient_W_m2K == 5.0
    assert math.isclose(
        evidence.exposed_area_m2,
        math.pi * 0.022 * 5.0,
        abs_tol=1.0e-12,
    )
    assert evidence.convection_heat_loss_W > 0.0
    assert evidence.radiation_heat_loss_W > 0.0
    assert math.isclose(
        evidence.total_heat_loss_W,
        evidence.convection_heat_loss_W + evidence.radiation_heat_loss_W,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        evidence.total_heat_loss_W_per_m,
        evidence.convection_heat_loss_W_per_m
        + evidence.radiation_heat_loss_W_per_m,
        abs_tol=1.0e-12,
    )
    assert evidence.ready is True
    assert evidence.status == (
        "Ready — deterministic bare-pipe section heat-loss evidence"
    )

    direct_handoff = build_catalogue_bare_pipe_input_from_thermal_basis_v1(
        material_key="copper",
        catalogue_size_key=22,
        length_m=5.0,
        thermal_basis=_basis(),
    )
    direct = compute_bare_pipe_heat_loss_v1(
        direct_handoff.bare_pipe_heat_loss_input
    )
    assert math.isclose(
        evidence.total_heat_loss_W,
        direct.total_heat_loss_W,
        abs_tol=1.0e-12,
    )

    doubled = _section(length_m=10.0)
    assert math.isclose(
        doubled.total_heat_loss_W,
        2.0 * evidence.total_heat_loss_W,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        doubled.total_heat_loss_W_per_m,
        evidence.total_heat_loss_W_per_m,
        abs_tol=1.0e-12,
    )

    steel = _section(
        section_id="steel-section-dn32",
        material_key="steel",
        catalogue_size_key=32,
    )
    assert steel.material_label == "Steel Medium"
    assert math.isclose(steel.actual_outside_diameter_mm, 42.4)
    assert math.isclose(
        steel.total_heat_loss_W / evidence.total_heat_loss_W,
        42.4 / 22.0,
        abs_tol=1.0e-12,
    )

    for invalid_id in ("", "   ", None):
        try:
            build_bare_pipe_section_heat_loss_evidence_v1(
                section_id=invalid_id,
                material_key="copper",
                catalogue_size_key=22,
                length_m=5.0,
                thermal_basis=_basis(),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Expected explicit section identity")

    try:
        _section(length_m=0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected positive exposed section length")

    source = Path(
        "HVAC/heatloss/physics/bare_pipe_section_heat_loss_evidence_v1.py"
    ).read_text(encoding="utf-8")
    assert "from HVAC.project" not in source
    assert "import HVAC.project" not in source
    assert "HVAC.gui_v3" not in source

    print(
        "OK — H-S66-D deterministic single-section bare-pipe heat-loss "
        "evidence passed."
    )


if __name__ == "__main__":
    main()
