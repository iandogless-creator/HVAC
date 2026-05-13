# ======================================================================
# HVAC/hydronics/models/basic_hydronic_sizing_intent_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class BasicHydronicSizingIntentV1:
    """
    Basic first-pass hydronic sizing intent.

    Authority
    ---------
    • Stores user/default sizing assumptions
    • Does not perform pipe sizing
    • Does not perform pressure-loss calculation
    • Does not call Colebrook or Darcy-Weisbach

    Basic method
    ------------
    Uses an index-circuit basis:

        nominal pipework dp ≈ index length × nominal pressure gradient

    Advanced/proportioning calculation later uses:
        HVAC.hydronics.physics.colebrook
    """

    basis_mode: str = "INDEX_LENGTH"
    # INDEX_LENGTH | BASIC_SECTIONS | ADVANCED_PROPORTIONING

    index_room_id: Optional[str] = None
    index_emitter_id: Optional[str] = None

    total_index_length_m: Optional[float] = None

    flow_length_m: Optional[float] = None
    return_length_m: Optional[float] = None
    allowance_percent: Optional[float] = None

    nominal_pressure_gradient_Pa_per_m: Optional[float] = None

    length_source: str = "unset"
    pressure_gradient_source: str = "unset"

    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "basis_mode": self.basis_mode,
            "index_room_id": self.index_room_id,
            "index_emitter_id": self.index_emitter_id,
            "total_index_length_m": self.total_index_length_m,
            "flow_length_m": self.flow_length_m,
            "return_length_m": self.return_length_m,
            "allowance_percent": self.allowance_percent,
            "nominal_pressure_gradient_Pa_per_m": self.nominal_pressure_gradient_Pa_per_m,
            "length_source": self.length_source,
            "pressure_gradient_source": self.pressure_gradient_source,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BasicHydronicSizingIntentV1":
        return cls(
            basis_mode=data.get("basis_mode", "INDEX_LENGTH"),
            index_room_id=data.get("index_room_id"),
            index_emitter_id=data.get("index_emitter_id"),
            total_index_length_m=data.get("total_index_length_m"),
            flow_length_m=data.get("flow_length_m"),
            return_length_m=data.get("return_length_m"),
            allowance_percent=data.get("allowance_percent"),
            nominal_pressure_gradient_Pa_per_m=data.get(
                "nominal_pressure_gradient_Pa_per_m"
            ),
            length_source=data.get("length_source", "unset"),
            pressure_gradient_source=data.get("pressure_gradient_source", "unset"),
            notes=data.get("notes", ""),
        )