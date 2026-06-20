# ======================================================================
# HVAC/hydronics/design_conditions/hydronic_design_temperature_basis_v1.py
# H-S23-A — Shared hydronic design-temperature basis helper
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class HydronicDesignTemperatureBasisV1:
    """
    Read-only hydronic design-temperature basis.

    Authority
    ---------
    Environment is the v1 project-level source for hydronic design
    flow/return temperatures.

    Notes
    -----
    • Derived ΔT is not stored on ProjectState.
    • This helper does not use emitter-level fallback.
    • Legacy emitter flow/return fallback remains local to old/compat paths.
    """

    flow_temp_c: Optional[float]
    return_temp_c: Optional[float]
    delta_t_k: Optional[float]
    source: str
    status: str

    @property
    def is_resolved(self) -> bool:
        return (
            self.flow_temp_c is not None
            and self.return_temp_c is not None
            and self.delta_t_k is not None
            and self.delta_t_k > 0.0
        )

    def display_label(self) -> str:
        if not self.is_resolved:
            return "Hydronic design temperature basis: unresolved"

        return (
            "Hydronic design temperature basis: "
            f"{self.source} flow/return "
            f"{self.flow_temp_c:.1f} / {self.return_temp_c:.1f} °C "
            f"→ ΔT {self.delta_t_k:.1f} K"
        )


def resolve_hydronic_design_temperature_basis_v1(
    project_state: Any,
) -> HydronicDesignTemperatureBasisV1:
    """
    Resolve the v1 hydronic design-temperature basis from ProjectState.

    Source:
        project_state.environment.design_flow_temp_c
        project_state.environment.design_return_temp_c

    This function is display/calculation support only.
    It does not mutate ProjectState.
    """

    environment = getattr(project_state, "environment", None)

    if environment is None:
        return HydronicDesignTemperatureBasisV1(
            flow_temp_c=None,
            return_temp_c=None,
            delta_t_k=None,
            source="unresolved",
            status="Environment not available",
        )

    flow_temp_c = getattr(environment, "design_flow_temp_c", None)
    return_temp_c = getattr(environment, "design_return_temp_c", None)

    if flow_temp_c is None or return_temp_c is None:
        return HydronicDesignTemperatureBasisV1(
            flow_temp_c=None,
            return_temp_c=None,
            delta_t_k=None,
            source="unresolved",
            status="Environment hydronic temperatures not set",
        )

    try:
        flow = float(flow_temp_c)
        ret = float(return_temp_c)
    except (TypeError, ValueError):
        return HydronicDesignTemperatureBasisV1(
            flow_temp_c=None,
            return_temp_c=None,
            delta_t_k=None,
            source="unresolved",
            status="Environment hydronic temperatures invalid",
        )

    delta_t = flow - ret

    if delta_t <= 0.0:
        return HydronicDesignTemperatureBasisV1(
            flow_temp_c=flow,
            return_temp_c=ret,
            delta_t_k=None,
            source="unresolved",
            status="Environment hydronic ΔT invalid",
        )

    return HydronicDesignTemperatureBasisV1(
        flow_temp_c=flow,
        return_temp_c=ret,
        delta_t_k=delta_t,
        source="Environment",
        status="Environment hydronic design temperatures resolved",
    )
