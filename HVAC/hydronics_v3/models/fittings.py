"""
fittings.py
-----------

HVACgooee — Hydronics Fittings Registry v3 (Engine-side, GUI-safe)

RULES (V3)
---------
• No GUI imports
• Registry defines canonical fitting IDs and K-values
• GUI may use this registry for labels + K-values
• Engine should consume ΣK per PipeSection (counts optional)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class FittingType:
    """
    Canonical fitting type.

    K-value is dimensionless (local loss coefficient).
    """
    id: str
    name: str
    k_value: float
    category: str = "general"
    notes: str = ""


class FittingRegistry:
    """
    Lookup and helper tools for fittings.

    Primary use:
        registry.get("elbow_90_standard").k_value

    Optional helper:
        registry.sum_k({"elbow_90_standard": 2, "iso_valve": 1})
    """

    def __init__(self, fittings: Iterable[FittingType]):
        self._by_id: Dict[str, FittingType] = {f.id: f for f in fittings}

    def get(self, fitting_id: str) -> FittingType:
        return self._by_id[fitting_id]

    def list_all(self) -> list[FittingType]:
        return list(self._by_id.values())

    def sum_k(self, counts_by_id: Dict[str, int]) -> float:
        total = 0.0
        for fid, count in counts_by_id.items():
            if count <= 0:
                continue
            total += self.get(fid).k_value * float(count)
        return total


def build_default_fitting_registry_v3() -> FittingRegistry:
    """
    Conservative starter set (generic).
    Extend later; do not overfit in v3.
    """
    fittings = [
        FittingType("elbow_90_standard", "90° elbow (standard)", 0.9, "bend"),
        FittingType("elbow_45_standard", "45° elbow (standard)", 0.4, "bend"),
        FittingType("tee_through", "Tee (through)", 0.6, "tee"),
        FittingType("tee_branch", "Tee (branch)", 1.8, "tee"),
        FittingType("iso_valve", "Isolation valve (generic)", 0.2, "valve"),
        FittingType("lockshield_valve", "Lockshield valve (generic)", 1.5, "valve"),
        FittingType("trv_valve", "TRV (generic)", 2.5, "valve"),
        FittingType("strainer", "Strainer (generic)", 1.0, "valve"),
        FittingType("check_valve", "Check valve (generic)", 2.0, "valve"),
        FittingType("reducer", "Reducer (generic)", 0.2, "transition"),
        FittingType("radiator_connection", "Emitter connection (generic)", 1.0, "emitter"),
    ]
    return FittingRegistry(fittings)
