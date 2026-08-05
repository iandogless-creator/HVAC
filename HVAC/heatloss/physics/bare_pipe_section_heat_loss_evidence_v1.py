# ======================================================================
# H-S66-D — Deterministic single-section bare-pipe heat-loss evidence
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    BarePipeThermalConditionBasisV1,
    build_catalogue_bare_pipe_input_from_thermal_basis_v1,
)
from HVAC.heatloss.physics.pipe_radiation_engine import (
    compute_bare_pipe_heat_loss_v1,
)


@dataclass(frozen=True, slots=True)
class BarePipeSectionHeatLossEvidenceV1:
    """Read-only external heat-loss evidence for one identified pipe section."""

    section_id: str
    material_key: str
    material_label: str
    catalogue_size_key: int
    actual_outside_diameter_mm: float
    length_m: float
    surface_temperature_C: float
    ambient_air_temperature_C: float
    mean_radiant_temperature_C: float
    emissivity: float
    external_convection_coefficient_W_m2K: float
    exposed_area_m2: float
    convection_heat_loss_W_per_m: float
    radiation_heat_loss_W_per_m: float
    total_heat_loss_W_per_m: float
    convection_heat_loss_W: float
    radiation_heat_loss_W: float
    total_heat_loss_W: float
    ready: bool
    status: str


def build_bare_pipe_section_heat_loss_evidence_v1(
        *,
        section_id: str,
        material_key: object,
        catalogue_size_key: int,
        length_m: float,
        thermal_basis: BarePipeThermalConditionBasisV1,
) -> BarePipeSectionHeatLossEvidenceV1:
    """Resolve, calculate and package one deterministic section result.

    The function is pure and accepts section identity as explicit evidence.
    It does not read ProjectState, infer a pipe schedule, aggregate a route,
    change fluid temperature or commit heat loss anywhere.
    """

    if not isinstance(section_id, str) or not section_id.strip():
        raise ValueError("Bare-pipe heat-loss section identity is required")
    clean_section_id = section_id.strip()

    handoff = build_catalogue_bare_pipe_input_from_thermal_basis_v1(
        material_key=material_key,
        catalogue_size_key=catalogue_size_key,
        length_m=length_m,
        thermal_basis=thermal_basis,
    )
    calculation = compute_bare_pipe_heat_loss_v1(
        handoff.bare_pipe_heat_loss_input
    )
    calculation_input = handoff.bare_pipe_heat_loss_input

    return BarePipeSectionHeatLossEvidenceV1(
        section_id=clean_section_id,
        material_key=handoff.material_key,
        material_label=handoff.material_label,
        catalogue_size_key=handoff.catalogue_size_key,
        actual_outside_diameter_mm=handoff.actual_outside_diameter_mm,
        length_m=calculation_input.length_m,
        surface_temperature_C=calculation_input.surface_temperature_C,
        ambient_air_temperature_C=(
            calculation_input.ambient_air_temperature_C
        ),
        mean_radiant_temperature_C=(
            calculation_input.mean_radiant_temperature_C
        ),
        emissivity=calculation.emissivity_used,
        external_convection_coefficient_W_m2K=(
            calculation.external_convection_coefficient_W_m2K
        ),
        exposed_area_m2=calculation.exposed_area_m2,
        convection_heat_loss_W_per_m=(
            calculation.convection_heat_loss_W_per_m
        ),
        radiation_heat_loss_W_per_m=(
            calculation.radiation_heat_loss_W_per_m
        ),
        total_heat_loss_W_per_m=calculation.total_heat_loss_W_per_m,
        convection_heat_loss_W=calculation.convection_heat_loss_W,
        radiation_heat_loss_W=calculation.radiation_heat_loss_W,
        total_heat_loss_W=calculation.total_heat_loss_W,
        ready=True,
        status="Ready — deterministic bare-pipe section heat-loss evidence",
    )
