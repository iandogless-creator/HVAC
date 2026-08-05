# ======================================================================
# H-S66-E — Committed pipe-section bare heat-loss evidence
# ======================================================================

from __future__ import annotations

import math
from pathlib import Path

from HVAC.heatloss.physics.bare_pipe_section_heat_loss_evidence_v1 import (
    build_bare_pipe_section_heat_loss_evidence_v1,
)
from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.heatloss.physics.committed_pipe_section_bare_heat_loss_evidence_v1 import (
    build_committed_pipe_section_bare_heat_loss_evidence_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicSectionV1,
)


def _basis(*, surface_temperature_C: float = 60.0):
    return build_explicit_bare_pipe_thermal_condition_basis_v1(
        surface_temperature_C=surface_temperature_C,
        ambient_air_temperature_C=20.0,
        mean_radiant_temperature_C=18.0,
        emissivity=0.95,
        external_convection_coefficient_W_m2K=5.0,
    )


def _section(
        *,
        section_id: str,
        order: int,
        material_key: str,
        material_label: str,
        pipe_size_label: str,
        dn: int,
        length_m: float,
        route_ids: tuple[str, ...],
) -> CommittedProportioningHydraulicSectionV1:
    return CommittedProportioningHydraulicSectionV1(
        section_id=section_id,
        section_scope="common" if len(route_ids) > 1 else "route-exclusive",
        route_ids=route_ids,
        order=order,
        from_label=f"{section_id}-from",
        to_label=f"{section_id}-to",
        carried_flow_kg_s=0.1,
        pipe_size_label=pipe_size_label,
        dn=dn,
        length_m=length_m,
        k_total=0.0,
        velocity_m_s=0.4,
        reynolds_number=5000.0,
        friction_factor=0.03,
        friction_method="colebrook",
        colebrook_iteration_count=4,
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=100.0,
        straight_pressure_drop_Pa=100.0 * length_m,
        local_pressure_drop_Pa=0.0,
        section_total_pressure_drop_Pa=100.0 * length_m,
        material_key=material_key,
        material_label=material_label,
        internal_diameter_m=0.020,
        material_roughness_m=0.0000015,
    )


def _authority(*, ready: bool = True):
    copper = _section(
        section_id="section-copper-022",
        order=2,
        material_key="copper",
        material_label="Copper EN1057",
        pipe_size_label="22 mm",
        dn=22,
        length_m=5.0,
        route_ids=("route-a", "route-b"),
    )
    steel = _section(
        section_id="section-steel-dn32",
        order=1,
        material_key="steel",
        material_label="Steel Medium",
        pipe_size_label="DN32",
        dn=32,
        length_m=3.0,
        route_ids=("route-b",),
    )
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=ready,
        sections=(copper, steel),
        routes=(),
        status="Ready — committed fixture" if ready else "Blocked — fixture",
        blockers=() if ready else ("fixture blocked",),
    )


def _bases():
    return {
        "section-copper-022": _basis(),
        "section-steel-dn32": _basis(surface_temperature_C=55.0),
    }


def main() -> None:
    authority = _authority()
    bases = _bases()
    before_authority = repr(authority)
    before_bases = repr(bases)

    result = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id=bases,
    )
    repeated = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id=bases,
    )

    assert result == repeated
    assert repr(authority) == before_authority
    assert repr(bases) == before_bases
    assert result.ready is True
    assert result.section_count == 2
    assert result.blockers == ()
    assert [row.section_id for row in result.sections] == [
        "section-steel-dn32",
        "section-copper-022",
    ]

    by_id = {row.section_id: row for row in result.sections}
    copper = by_id["section-copper-022"]
    steel = by_id["section-steel-dn32"]
    assert copper.route_ids == ("route-a", "route-b")
    assert copper.section_scope == "common"
    assert copper.pipe_size_label == "22 mm"
    assert copper.catalogue_size_key == 22
    assert math.isclose(copper.actual_outside_diameter_mm, 22.0)
    assert math.isclose(copper.length_m, 5.0)
    assert copper.total_heat_loss_W > 0.0
    assert steel.route_ids == ("route-b",)
    assert steel.pipe_size_label == "DN32"
    assert steel.catalogue_size_key == 32
    assert math.isclose(steel.actual_outside_diameter_mm, 42.4)
    assert steel.surface_temperature_C == 55.0

    direct_copper = build_bare_pipe_section_heat_loss_evidence_v1(
        section_id="section-copper-022",
        material_key="copper",
        catalogue_size_key=22,
        length_m=5.0,
        thermal_basis=bases["section-copper-022"],
    )
    assert math.isclose(
        copper.total_heat_loss_W,
        direct_copper.total_heat_loss_W,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        copper.total_heat_loss_W_per_m,
        direct_copper.total_heat_loss_W_per_m,
        abs_tol=1.0e-12,
    )

    missing = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id={
            "section-copper-022": bases["section-copper-022"],
        },
    )
    assert missing.ready is False
    assert missing.sections == ()
    assert missing.section_count == 0
    assert missing.blockers == (
        "section-steel-dn32: explicit bare-pipe thermal-condition basis missing",
    )

    stale = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id={**bases, "stale-section": _basis()},
    )
    assert stale.ready is False
    assert stale.sections == ()
    assert stale.blockers == (
        "stale-section: thermal-condition basis has no committed section",
    )

    wrong_basis = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=authority,
        thermal_basis_by_section_id={
            "section-copper-022": object(),
            "section-steel-dn32": bases["section-steel-dn32"],
        },
    )
    assert wrong_basis.ready is False
    assert wrong_basis.sections == ()
    assert (
        "section-copper-022: explicit bare-pipe thermal-condition basis "
        "is required"
    ) in wrong_basis.blockers

    unavailable = build_committed_pipe_section_bare_heat_loss_evidence_v1(
        committed_authority=_authority(ready=False),
        thermal_basis_by_section_id=bases,
    )
    assert unavailable.ready is False
    assert unavailable.sections == ()
    assert unavailable.blockers[0] == (
        "Committed proportioning hydraulic-input authority is not ready"
    )

    source = Path(
        "HVAC/heatloss/physics/"
        "committed_pipe_section_bare_heat_loss_evidence_v1.py"
    ).read_text(encoding="utf-8")
    assert "HVAC.gui_v3" not in source
    assert "from HVAC.project" not in source
    assert "import HVAC.project" not in source
    assert "proposed_material" not in source
    assert "route_heat_loss" not in source
    assert "system_heat_loss" not in source

    print(
        "OK — H-S66-E committed pipe-section bare heat-loss evidence "
        "passed."
    )


if __name__ == "__main__":
    main()
