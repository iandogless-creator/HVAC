# ======================================================================
# HVAC/hydronics/sizing/basic_ps_velocity_limit_resolver_v1.py
# H-S37-B2 — Resolve Environment/default and local section velocity intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Optional


DEFAULT_BASIC_PS_MAX_VELOCITY_M_S = 1.0
ENVIRONMENT_DEFAULT_SOURCE = "Environment default"
LOCAL_SECTION_OVERRIDE_SOURCE = "Local section override"


@dataclass(frozen=True, slots=True)
class BasicPSMaximumVelocityResolutionV1:
    section_id: str
    effective_max_velocity_m_s: float
    source: str
    environment_default_m_s: float
    local_override_m_s: Optional[float]
    status: str


def resolve_basic_ps_max_velocity_v1(
    project_state: Any = None,
    *,
    section_id: str,
    environment: Any = None,
    sizing_intent: Any = None,
) -> BasicPSMaximumVelocityResolutionV1:
    """Resolve one section's Basic PS maximum-velocity criterion.

    Resolution is intent-only at H-S37-B2. No pipe sizing or pressure
    calculation is performed here.
    """
    key = str(section_id or "").strip()
    if not key:
        raise ValueError("section_id is required")

    if environment is None and project_state is not None:
        environment = getattr(project_state, "environment", None)
    if sizing_intent is None and project_state is not None:
        sizing_intent = getattr(
            project_state,
            "basic_hydronic_sizing_intent",
            None,
        )

    raw_environment_default = (
        getattr(
            environment,
            "basic_ps_max_velocity_m_s",
            DEFAULT_BASIC_PS_MAX_VELOCITY_M_S,
        )
        if environment is not None
        else DEFAULT_BASIC_PS_MAX_VELOCITY_M_S
    )
    if raw_environment_default is None:
        raw_environment_default = DEFAULT_BASIC_PS_MAX_VELOCITY_M_S

    environment_default = _positive_velocity_v1(
        raw_environment_default,
        label="Environment Basic PS maximum velocity",
    )

    overrides = (
        getattr(
            sizing_intent,
            "section_max_velocity_overrides_m_s",
            {},
        )
        if sizing_intent is not None
        else {}
    )
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ValueError(
            "section_max_velocity_overrides_m_s must be a dictionary"
        )

    raw_local_override = overrides.get(key)
    if raw_local_override is None:
        return BasicPSMaximumVelocityResolutionV1(
            section_id=key,
            effective_max_velocity_m_s=environment_default,
            source=ENVIRONMENT_DEFAULT_SOURCE,
            environment_default_m_s=environment_default,
            local_override_m_s=None,
            status="Inherited Environment Basic PS maximum velocity.",
        )

    local_override = _positive_velocity_v1(
        raw_local_override,
        label="Local section Basic PS maximum velocity override",
    )
    return BasicPSMaximumVelocityResolutionV1(
        section_id=key,
        effective_max_velocity_m_s=local_override,
        source=LOCAL_SECTION_OVERRIDE_SOURCE,
        environment_default_m_s=environment_default,
        local_override_m_s=local_override,
        status="Local section override applied.",
    )


def _positive_velocity_v1(value: Any, *, label: str) -> float:
    try:
        resolved = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc

    if not isfinite(resolved) or resolved <= 0.0:
        raise ValueError(f"{label} must be finite and greater than zero")

    return resolved
