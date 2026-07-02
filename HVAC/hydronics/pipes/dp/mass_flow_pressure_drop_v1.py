from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.core.fluid_friction.friction_factor_v1 import (
    colebrook_friction_factor,
    darcy_weisbach_pressure_drop,
    darcy_weisbach_pressure_gradient,
    haaland_friction_factor,
    reynolds_number,
)
from HVAC.core.materials.pipe_materials_library import (
    get_internal_diameter,
    get_roughness,
)


WATER_DENSITY_KG_M3 = 998.0
WATER_DYNAMIC_VISCOSITY_PA_S = 0.001


@dataclass(frozen=True)
class HydronicMassFlowPressureDropResultV1:
    material: str
    dn: int
    length_m: float

    mass_flow_kg_s: float
    volume_flow_m3_s: float

    internal_diameter_m: float
    roughness_m: float
    relative_roughness: float

    velocity_m_s: float
    reynolds_number: float

    haaland_friction_factor: float
    selected_friction_factor: float
    friction_method: str

    colebrook_iteration_count: int
    colebrook_converged: bool
    colebrook_residual: float | None

    pressure_gradient_pa_per_m: float
    pressure_drop_pa: float

    status: str


def calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
    *,
    mass_flow_kg_s: float,
    material: str,
    dn: int,
    length_m: float,
    density_kg_m3: float = WATER_DENSITY_KG_M3,
    dynamic_viscosity_pa_s: float = WATER_DYNAMIC_VISCOSITY_PA_S,
    friction_method: str = "colebrook",
    colebrook_tolerance: float = 1.0e-6,
    colebrook_max_iterations: int = 100,
) -> HydronicMassFlowPressureDropResultV1:
    """
    H-S29-C hydronics mass-flow pressure wrapper.

    Hydronics-facing API:
        mass_flow_kg_s + material + DN + length

    Shared physics API:
        velocity + internal diameter + roughness + fluid properties

    Display/catalogue:
        material + DN come from the pipe material library.

    Calculation:
        material + DN -> internal diameter and roughness
        kg/s -> m³/s -> velocity
        velocity -> Reynolds
        roughness / diameter -> relative roughness
        Haaland or Colebrook -> Darcy friction factor
        Darcy-Weisbach -> Δp/m and Δp

    No GUI access.
    No ProjectState mutation.
    No pump sizing.
    No valve selection.
    No pipe resizing.
    """
    if mass_flow_kg_s < 0.0:
        raise ValueError("mass_flow_kg_s must be >= 0")

    if length_m < 0.0:
        raise ValueError("length_m must be >= 0")

    if density_kg_m3 <= 0.0:
        raise ValueError("density_kg_m3 must be > 0")

    if dynamic_viscosity_pa_s <= 0.0:
        raise ValueError("dynamic_viscosity_pa_s must be > 0")

    material_key = str(material or "").strip().lower()
    dn_int = int(dn)

    internal_diameter_mm = get_internal_diameter(material_key, dn_int)
    if internal_diameter_mm is None:
        raise ValueError(
            f"No internal diameter for material={material_key!r}, dn={dn_int!r}"
        )

    roughness_mm = get_roughness(material_key)
    if roughness_mm is None:
        raise ValueError(f"No roughness for material={material_key!r}")

    internal_diameter_m = float(internal_diameter_mm) / 1000.0
    roughness_m = float(roughness_mm) / 1000.0

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    if roughness_m < 0.0:
        raise ValueError("roughness_m must be >= 0")

    relative_roughness = roughness_m / internal_diameter_m

    if mass_flow_kg_s == 0.0:
        return HydronicMassFlowPressureDropResultV1(
            material=material_key,
            dn=dn_int,
            length_m=float(length_m),
            mass_flow_kg_s=0.0,
            volume_flow_m3_s=0.0,
            internal_diameter_m=internal_diameter_m,
            roughness_m=roughness_m,
            relative_roughness=relative_roughness,
            velocity_m_s=0.0,
            reynolds_number=0.0,
            haaland_friction_factor=0.0,
            selected_friction_factor=0.0,
            friction_method="none",
            colebrook_iteration_count=0,
            colebrook_converged=True,
            colebrook_residual=0.0,
            pressure_gradient_pa_per_m=0.0,
            pressure_drop_pa=0.0,
            status="No flow",
        )

    area_m2 = math.pi * internal_diameter_m**2 / 4.0
    volume_flow_m3_s = float(mass_flow_kg_s) / float(density_kg_m3)
    velocity_m_s = volume_flow_m3_s / area_m2

    re = reynolds_number(
        velocity_m_s=velocity_m_s,
        internal_diameter_m=internal_diameter_m,
        density_kg_m3=density_kg_m3,
        dynamic_viscosity_pa_s=dynamic_viscosity_pa_s,
    )

    haaland_f = haaland_friction_factor(
        reynolds_number=re,
        relative_roughness=relative_roughness,
    )

    method = str(friction_method or "").strip().lower()

    if method == "haaland":
        selected_f = haaland_f
        iteration_count = 0
        converged = True
        residual = None
        status = "First-pass Haaland estimate"

    elif method == "colebrook":
        colebrook_result = colebrook_friction_factor(
            reynolds_number=re,
            relative_roughness=relative_roughness,
            tolerance=colebrook_tolerance,
            max_iterations=colebrook_max_iterations,
            initial_guess_method="haaland",
        )
        selected_f = colebrook_result.friction_factor
        iteration_count = colebrook_result.iteration_count
        converged = colebrook_result.converged
        residual = colebrook_result.residual
        status = f"Colebrook — {colebrook_result.status}"

    else:
        raise ValueError("friction_method must be 'colebrook' or 'haaland'")

    pressure_gradient = darcy_weisbach_pressure_gradient(
        friction_factor=selected_f,
        density_kg_m3=density_kg_m3,
        velocity_m_s=velocity_m_s,
        internal_diameter_m=internal_diameter_m,
    )

    pressure_drop = darcy_weisbach_pressure_drop(
        friction_factor=selected_f,
        length_m=length_m,
        internal_diameter_m=internal_diameter_m,
        density_kg_m3=density_kg_m3,
        velocity_m_s=velocity_m_s,
    )

    return HydronicMassFlowPressureDropResultV1(
        material=material_key,
        dn=dn_int,
        length_m=float(length_m),
        mass_flow_kg_s=float(mass_flow_kg_s),
        volume_flow_m3_s=volume_flow_m3_s,
        internal_diameter_m=internal_diameter_m,
        roughness_m=roughness_m,
        relative_roughness=relative_roughness,
        velocity_m_s=velocity_m_s,
        reynolds_number=re,
        haaland_friction_factor=haaland_f,
        selected_friction_factor=selected_f,
        friction_method=method,
        colebrook_iteration_count=iteration_count,
        colebrook_converged=converged,
        colebrook_residual=residual,
        pressure_gradient_pa_per_m=pressure_gradient,
        pressure_drop_pa=pressure_drop,
        status=status,
    )