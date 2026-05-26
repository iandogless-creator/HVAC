# ======================================================================
# HVAC/hydronics/sizing/basic_ps_pipe_sizing_v1.py
# ======================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    BasicPSTopologySectionV1,
)


# ======================================================================
# Constants
# ======================================================================

WATER_DENSITY_KG_M3 = 998.0
WATER_DYNAMIC_VISCOSITY_PA_S = 0.001
DEFAULT_PIPE_ROUGHNESS_M = 0.0000015  # drawn copper / smooth plastic order


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class BasicPSPipeCandidateV1:
    """
    Candidate pipe size for Basic PS first-pass sizing.

    internal_diameter_m is the hydraulic internal diameter.
    """

    pipe_size_label: str
    internal_diameter_m: float
    roughness_m: float = DEFAULT_PIPE_ROUGHNESS_M


@dataclass(frozen=True, slots=True)
class BasicPSPipeSizingResultV1:
    """
    Basic first-pass pipe sizing result for one topology section.

    This is not final proportioning/balancing.
    """

    section_id: str
    order: int
    from_label: str
    to_room_label: str

    carried_heat_W: float
    carried_flow_kg_s: float

    pipe_size_label: str
    internal_diameter_m: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    pressure_gradient_Pa_per_m: float

    is_index_room: bool = False
    is_terminal: bool = False
    status: str = "First-pass Haaland estimate"


@dataclass(frozen=True, slots=True)
class BasicPSPipeSizingProjectionV1:
    """
    Read-only Basic PS pipe sizing projection.

    Consumes topology section rows and estimates:
    - pipe size
    - velocity
    - Reynolds number
    - Haaland friction factor
    - Darcy pressure gradient
    """

    results: tuple[BasicPSPipeSizingResultV1, ...]
    status: str = "First-pass Haaland estimate"


# ======================================================================
# Candidate pipe table — DEV v1
# ======================================================================

DEFAULT_PIPE_CANDIDATES: tuple[BasicPSPipeCandidateV1, ...] = (
    BasicPSPipeCandidateV1("10 mm", 0.0100),
    BasicPSPipeCandidateV1("15 mm", 0.0136),
    BasicPSPipeCandidateV1("22 mm", 0.0202),
    BasicPSPipeCandidateV1("28 mm", 0.0262),
    BasicPSPipeCandidateV1("35 mm", 0.0330),
)


# ======================================================================
# Public API
# ======================================================================

def build_basic_ps_pipe_sizing_v1(
    sections: Iterable[BasicPSTopologySectionV1],
    *,
    pipe_candidates: Iterable[BasicPSPipeCandidateV1] = DEFAULT_PIPE_CANDIDATES,
    max_velocity_m_s: float = 1.0,
    min_velocity_m_s: float = 0.15,
    water_density_kg_m3: float = WATER_DENSITY_KG_M3,
    water_dynamic_viscosity_Pa_s: float = WATER_DYNAMIC_VISCOSITY_PA_S,
) -> BasicPSPipeSizingProjectionV1:
    """
    Build first-pass Basic PS pipe sizing rows from topology sections.

    Authority
    ---------
    Reads BasicPSTopologySectionV1 carried flow.

    Does not:
    - mutate ProjectState
    - perform final proportioning
    - balance branches
    - size pumps
    - account for fittings/tees/valves yet
    """

    candidate_tuple = tuple(pipe_candidates)

    if not candidate_tuple:
        raise ValueError("At least one pipe candidate is required")

    results: list[BasicPSPipeSizingResultV1] = []

    for section in sections:
        result = size_basic_ps_section_v1(
            section,
            pipe_candidates=candidate_tuple,
            max_velocity_m_s=max_velocity_m_s,
            min_velocity_m_s=min_velocity_m_s,
            water_density_kg_m3=water_density_kg_m3,
            water_dynamic_viscosity_Pa_s=water_dynamic_viscosity_Pa_s,
        )

        results.append(result)

    return BasicPSPipeSizingProjectionV1(
        results=tuple(results),
        status="First-pass Haaland estimate",
    )


def size_basic_ps_section_v1(
    section: BasicPSTopologySectionV1,
    *,
    pipe_candidates: Iterable[BasicPSPipeCandidateV1] = DEFAULT_PIPE_CANDIDATES,
    max_velocity_m_s: float = 1.0,
    min_velocity_m_s: float = 0.15,
    water_density_kg_m3: float = WATER_DENSITY_KG_M3,
    water_dynamic_viscosity_Pa_s: float = WATER_DYNAMIC_VISCOSITY_PA_S,
) -> BasicPSPipeSizingResultV1:
    """
    Size one Basic PS section by selecting the smallest candidate whose
    velocity is not above max_velocity_m_s.

    Pressure gradient is estimated using Darcy-Weisbach with Haaland friction.
    """

    candidate_tuple = tuple(pipe_candidates)

    if section.carried_flow_kg_s <= 0.0:
        candidate = candidate_tuple[0]
        velocity = 0.0
        reynolds = 0.0
        friction_factor = 0.0
        pressure_gradient = 0.0
        status = "No carried flow"

        return _result_from_values(
            section=section,
            candidate=candidate,
            velocity_m_s=velocity,
            reynolds_number=reynolds,
            friction_factor=friction_factor,
            pressure_gradient_Pa_per_m=pressure_gradient,
            status=status,
        )

    selected_candidate = candidate_tuple[-1]
    selected_velocity = 0.0
    selected_reynolds = 0.0
    selected_friction_factor = 0.0
    selected_pressure_gradient = 0.0
    selected_status = "Exceeds max velocity on largest candidate"

    for candidate in candidate_tuple:
        velocity = velocity_m_s_from_mass_flow(
            mass_flow_kg_s=section.carried_flow_kg_s,
            internal_diameter_m=candidate.internal_diameter_m,
            water_density_kg_m3=water_density_kg_m3,
        )

        reynolds = reynolds_number(
            velocity_m_s=velocity,
            internal_diameter_m=candidate.internal_diameter_m,
            water_density_kg_m3=water_density_kg_m3,
            dynamic_viscosity_Pa_s=water_dynamic_viscosity_Pa_s,
        )

        friction_factor = haaland_friction_factor(
            reynolds_number=reynolds,
            internal_diameter_m=candidate.internal_diameter_m,
            roughness_m=candidate.roughness_m,
        )

        pressure_gradient = darcy_pressure_gradient_Pa_per_m(
            friction_factor=friction_factor,
            water_density_kg_m3=water_density_kg_m3,
            velocity_m_s=velocity,
            internal_diameter_m=candidate.internal_diameter_m,
        )

        selected_candidate = candidate
        selected_velocity = velocity
        selected_reynolds = reynolds
        selected_friction_factor = friction_factor
        selected_pressure_gradient = pressure_gradient

        if velocity <= max_velocity_m_s:
            if velocity < min_velocity_m_s:
                selected_status = "Low velocity — first-pass selected"
            else:
                selected_status = "First-pass Haaland estimate"
            break

    return _result_from_values(
        section=section,
        candidate=selected_candidate,
        velocity_m_s=selected_velocity,
        reynolds_number=selected_reynolds,
        friction_factor=selected_friction_factor,
        pressure_gradient_Pa_per_m=selected_pressure_gradient,
        status=selected_status,
    )


# ======================================================================
# Hydraulic helpers
# ======================================================================

def velocity_m_s_from_mass_flow(
    *,
    mass_flow_kg_s: float,
    internal_diameter_m: float,
    water_density_kg_m3: float = WATER_DENSITY_KG_M3,
) -> float:
    if mass_flow_kg_s <= 0.0:
        return 0.0

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    volume_flow_m3_s = mass_flow_kg_s / water_density_kg_m3
    area_m2 = math.pi * internal_diameter_m**2 / 4.0

    return volume_flow_m3_s / area_m2


def reynolds_number(
    *,
    velocity_m_s: float,
    internal_diameter_m: float,
    water_density_kg_m3: float = WATER_DENSITY_KG_M3,
    dynamic_viscosity_Pa_s: float = WATER_DYNAMIC_VISCOSITY_PA_S,
) -> float:
    if velocity_m_s <= 0.0:
        return 0.0

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    if dynamic_viscosity_Pa_s <= 0.0:
        raise ValueError("dynamic_viscosity_Pa_s must be > 0")

    return (
        water_density_kg_m3
        * velocity_m_s
        * internal_diameter_m
        / dynamic_viscosity_Pa_s
    )


def haaland_friction_factor(
    *,
    reynolds_number: float,
    internal_diameter_m: float,
    roughness_m: float,
) -> float:
    """
    Return Darcy friction factor.

    Laminar:
        f = 64 / Re

    Turbulent/transitional first pass:
        Haaland explicit approximation.
    """

    if reynolds_number <= 0.0:
        return 0.0

    if reynolds_number < 2300.0:
        return 64.0 / reynolds_number

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    relative_roughness = roughness_m / internal_diameter_m

    term = ((relative_roughness / 3.7) ** 1.11) + (6.9 / reynolds_number)

    if term <= 0.0:
        return 0.0

    inverse_sqrt_f = -1.8 * math.log10(term)

    if inverse_sqrt_f <= 0.0:
        return 0.0

    return 1.0 / (inverse_sqrt_f**2)


def darcy_pressure_gradient_Pa_per_m(
    *,
    friction_factor: float,
    water_density_kg_m3: float,
    velocity_m_s: float,
    internal_diameter_m: float,
) -> float:
    """
    Darcy-Weisbach pressure gradient:

        Δp/L = f × ρ × v² / (2D)
    """

    if friction_factor <= 0.0 or velocity_m_s <= 0.0:
        return 0.0

    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    return (
        friction_factor
        * water_density_kg_m3
        * velocity_m_s**2
        / (2.0 * internal_diameter_m)
    )


# ======================================================================
# Internals
# ======================================================================

def _result_from_values(
    *,
    section: BasicPSTopologySectionV1,
    candidate: BasicPSPipeCandidateV1,
    velocity_m_s: float,
    reynolds_number: float,
    friction_factor: float,
    pressure_gradient_Pa_per_m: float,
    status: str,
) -> BasicPSPipeSizingResultV1:
    return BasicPSPipeSizingResultV1(
        section_id=section.section_id,
        order=section.order,
        from_label=section.from_label,
        to_room_label=section.to_room_label,
        carried_heat_W=section.carried_heat_W,
        carried_flow_kg_s=section.carried_flow_kg_s,
        pipe_size_label=candidate.pipe_size_label,
        internal_diameter_m=candidate.internal_diameter_m,
        velocity_m_s=velocity_m_s,
        reynolds_number=reynolds_number,
        friction_factor=friction_factor,
        pressure_gradient_Pa_per_m=pressure_gradient_Pa_per_m,
        is_index_room=section.is_index_room,
        is_terminal=section.is_terminal,
        status=status,
    )