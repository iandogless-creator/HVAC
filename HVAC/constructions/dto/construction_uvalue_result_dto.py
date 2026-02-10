from __future__ import annotations
from dataclasses import dataclass
from HVAC.constructions.construction_preset import SurfaceClass


@dataclass(frozen=True, slots=True)
class ConstructionUValueResultDTO:
    """
    Canonical construction U-value result.

    RULES (LOCKED):
    • Result ONLY (no preset metadata, no UI labels)
    • One surface, one resolved U-value
    • Serializable
    • Immutable
    """

    surface_class: SurfaceClass
    construction_ref: str   # stable ID (preset.ref or engine ref)
    u_value: float           # W/m²·K
