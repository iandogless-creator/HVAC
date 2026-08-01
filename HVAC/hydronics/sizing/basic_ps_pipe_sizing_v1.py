# ======================================================================
# HVAC/hydronics/sizing/basic_ps_pipe_sizing_v1.py
# ======================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    BasicPSTopologySectionV1,
)
from HVAC.core.fluid_friction.friction_factor_v1 import (
    darcy_weisbach_pressure_gradient as _shared_darcy_pressure_gradient,
    haaland_friction_factor as _shared_haaland_friction_factor,
    reynolds_number as _shared_reynolds_number,
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

    # H-S37-B3 — Applied first-pass selection criterion evidence.
    applied_max_velocity_m_s: float = 1.0
    max_velocity_source: str = "Function argument"

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
# H-S63-B1 — material-library-derived Basic PS copper candidates
# ======================================================================

# This tuple is the Basic PS v1 candidate-range criterion, not dimensional
# authority. Bore and roughness are read from pipe_materials_library.
# 6/8 mm microbore and the 42/54 mm Proportioned extension remain excluded.
DEFAULT_BASIC_PS_COPPER_SIZE_KEYS_V1: tuple[int, ...] = (
    10,
    15,
    22,
    28,
    35,
)


def build_default_basic_ps_copper_candidates_v1(
) -> tuple[BasicPSPipeCandidateV1, ...]:
    """Return the Basic PS v1 copper ladder from shared material authority."""

    material = get_material("copper")
    if material is None:
        raise ValueError("Basic PS copper material authority is unavailable")

    roughness_m = float(material.roughness_mm) / 1000.0
    if roughness_m < 0.0:
        raise ValueError("Basic PS copper roughness must not be negative")

    candidates: list[BasicPSPipeCandidateV1] = []
    for size_key in DEFAULT_BASIC_PS_COPPER_SIZE_KEYS_V1:
        size = material.sizes.get(size_key)
        if size is None:
            raise ValueError(
                "Basic PS copper size is missing from material authority: "
                f"{size_key} mm"
            )

        internal_diameter_m = float(size.id_mm) / 1000.0
        if internal_diameter_m <= 0.0:
            raise ValueError(
                "Basic PS copper bore must be positive: "
                f"{size_key} mm"
            )

        candidates.append(
            BasicPSPipeCandidateV1(
                pipe_size_label=f"{size_key} mm",
                internal_diameter_m=internal_diameter_m,
                roughness_m=roughness_m,
            )
        )

    return tuple(candidates)


DEFAULT_PIPE_CANDIDATES: tuple[BasicPSPipeCandidateV1, ...] = (
    build_default_basic_ps_copper_candidates_v1()
)


# ======================================================================
# Public API
# ======================================================================

def build_basic_ps_pipe_sizing_v1(
    sections: Iterable[BasicPSTopologySectionV1],
    *,
    pipe_candidates: Iterable[BasicPSPipeCandidateV1] = DEFAULT_PIPE_CANDIDATES,
    max_velocity_m_s: float = 1.0,
    max_velocity_source: str = "Function argument",
    max_velocity_m_s_by_section_id: Mapping[str, float] | None = None,
    max_velocity_source_by_section_id: Mapping[str, str] | None = None,
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

    velocity_by_section = dict(max_velocity_m_s_by_section_id or {})
    source_by_section = dict(max_velocity_source_by_section_id or {})

    results: list[BasicPSPipeSizingResultV1] = []

    for section in sections:
        section_max_velocity = velocity_by_section.get(
            section.section_id,
            max_velocity_m_s,
        )
        section_max_velocity_source = source_by_section.get(
            section.section_id,
            max_velocity_source,
        )

        result = size_basic_ps_section_v1(
            section,
            pipe_candidates=candidate_tuple,
            max_velocity_m_s=section_max_velocity,
            max_velocity_source=section_max_velocity_source,
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
    max_velocity_source: str = "Function argument",
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

    max_velocity_m_s = float(max_velocity_m_s)
    if not math.isfinite(max_velocity_m_s) or max_velocity_m_s <= 0.0:
        raise ValueError("max_velocity_m_s must be finite and greater than zero")

    max_velocity_source = str(max_velocity_source or "").strip()
    if not max_velocity_source:
        raise ValueError("max_velocity_source is required")

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
            applied_max_velocity_m_s=max_velocity_m_s,
            max_velocity_source=max_velocity_source,
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
        applied_max_velocity_m_s=max_velocity_m_s,
        max_velocity_source=max_velocity_source,
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
    """
    Basic PS compatibility wrapper around shared Reynolds helper.
    """
    return _shared_reynolds_number(
        velocity_m_s=velocity_m_s,
        internal_diameter_m=internal_diameter_m,
        density_kg_m3=water_density_kg_m3,
        dynamic_viscosity_pa_s=dynamic_viscosity_Pa_s,
    )

def haaland_friction_factor(
    *,
    reynolds_number: float,
    internal_diameter_m: float,
    roughness_m: float,
) -> float:
    """
    Basic PS compatibility wrapper around shared Haaland helper.

    Basic PS remains first-pass Haaland only.
    """
    if internal_diameter_m <= 0.0:
        raise ValueError("internal_diameter_m must be > 0")

    return _shared_haaland_friction_factor(
        reynolds_number=reynolds_number,
        relative_roughness=roughness_m / internal_diameter_m,
    )


def darcy_pressure_gradient_Pa_per_m(
    *,
    friction_factor: float,
    water_density_kg_m3: float,
    velocity_m_s: float,
    internal_diameter_m: float,
) -> float:
    """
    Basic PS compatibility wrapper around shared Darcy-Weisbach
    pressure-gradient helper.
    """
    return _shared_darcy_pressure_gradient(
        friction_factor=friction_factor,
        density_kg_m3=water_density_kg_m3,
        velocity_m_s=velocity_m_s,
        internal_diameter_m=internal_diameter_m,
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
    applied_max_velocity_m_s: float,
    max_velocity_source: str,
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
        applied_max_velocity_m_s=applied_max_velocity_m_s,
        max_velocity_source=max_velocity_source,
        is_index_room=section.is_index_room,
        is_terminal=section.is_terminal,
        status=(
            f"{status} / Maximum velocity "
            f"{applied_max_velocity_m_s:.2f} m/s — {max_velocity_source}"
        ),
    )