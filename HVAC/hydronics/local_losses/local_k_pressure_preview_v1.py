# ======================================================================
# HVAC/hydronics/local_losses/local_k_pressure_preview_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# H-S42-B1: pressure evidence must not depend on the GUI selector
# projection; keeping this primitive here breaks that import cycle.
WATER_DENSITY_KG_M3 = 998.0


def _local_pressure_drop_from_k_v1(
    *,
    k_total: float,
    velocity_m_s: float,
    density_kg_m3: float = WATER_DENSITY_KG_M3,
) -> float:
    return (
        float(k_total)
        * float(density_kg_m3)
        * float(velocity_m_s) ** 2
        / 2.0
    )


@dataclass(frozen=True, slots=True)
class LocalKPressurePreviewV1:
    """
    Live Local K pressure preview for one Basic PS section.

    Authority
    ---------
    Reads persisted visible Local K intent.
    Does not persist calculated pressure drops.
    Does not perform final proportioning or balancing.
    """

    section_id: str
    length_m: float | None
    k_total: float
    local_pressure_drop_Pa: float
    straight_pressure_drop_Pa: float | None
    section_total_pressure_drop_Pa: float | None
    status: str


def build_local_k_pressure_preview_v1(
    project_state: Any,
    *,
    section_id: str,
    velocity_m_s: float,
    pressure_gradient_Pa_per_m: float,
) -> LocalKPressurePreviewV1:
    section_id = str(section_id or "")

    intent = getattr(project_state, "hydronic_local_k_intent", None)
    section = None

    if intent is not None:
        section = getattr(intent, "sections", {}).get(section_id)

    if section is None:
        return LocalKPressurePreviewV1(
            section_id=section_id,
            length_m=None,
            k_total=0.0,
            local_pressure_drop_Pa=0.0,
            straight_pressure_drop_Pa=None,
            section_total_pressure_drop_Pa=None,
            status="No Local K intent",
        )

    k_total = (
        int(getattr(section, "bend_90_count", 0) or 0) * 0.7
        + int(getattr(section, "bend_45_count", 0) or 0) * 0.4
        + int(getattr(section, "tee_through_count", 0) or 0) * 0.6
        + int(getattr(section, "tee_branch_count", 0) or 0) * 1.8
        + int(getattr(section, "isolation_valve_count", 0) or 0) * 0.2
        + int(getattr(section, "trv_count", 0) or 0) * 0.0
        + int(getattr(section, "lockshield_count", 0) or 0) * 0.0
        + float(getattr(section, "misc_k", 0.0) or 0.0)
    )

    local_dp = _local_pressure_drop_from_k_v1(
        k_total=k_total,
        velocity_m_s=float(velocity_m_s or 0.0),
        density_kg_m3=WATER_DENSITY_KG_M3,
    )

    raw_length = getattr(section, "length_m", None)

    if raw_length is None:
        return LocalKPressurePreviewV1(
            section_id=section_id,
            length_m=None,
            k_total=k_total,
            local_pressure_drop_Pa=local_dp,
            straight_pressure_drop_Pa=None,
            section_total_pressure_drop_Pa=None,
            status="Local K preview — length not set",
        )

    length_m = float(raw_length)
    straight_dp = float(pressure_gradient_Pa_per_m or 0.0) * length_m

    return LocalKPressurePreviewV1(
        section_id=section_id,
        length_m=length_m,
        k_total=k_total,
        local_pressure_drop_Pa=local_dp,
        straight_pressure_drop_Pa=straight_dp,
        section_total_pressure_drop_Pa=straight_dp + local_dp,
        status="Basic PS + Local K preview only",
    )