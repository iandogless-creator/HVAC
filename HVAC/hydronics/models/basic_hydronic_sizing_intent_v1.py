# ======================================================================
# HVAC/hydronics/models/basic_hydronic_sizing_intent_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
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

    # H-S37-B2 — Optional Basic PS maximum-velocity overrides keyed by
    # stable topology section_id. Missing key means inherit Environment.
    section_max_velocity_overrides_m_s: dict[str, float] = field(
        default_factory=dict
    )

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
            "section_max_velocity_overrides_m_s": dict(
                self.section_max_velocity_overrides_m_s
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BasicHydronicSizingIntentV1":
        raw_overrides = data.get(
            "section_max_velocity_overrides_m_s",
            {},
        )
        if raw_overrides is None:
            raw_overrides = {}
        if not isinstance(raw_overrides, dict):
            raise ValueError(
                "section_max_velocity_overrides_m_s must be a dictionary"
            )

        overrides: dict[str, float] = {}
        for raw_section_id, raw_value in raw_overrides.items():
            section_id = str(raw_section_id or "").strip()
            if not section_id:
                raise ValueError("section velocity override requires section_id")
            if raw_value is None:
                continue

            value = float(raw_value)
            if not isfinite(value) or value <= 0.0:
                raise ValueError(
                    "section velocity override must be finite and greater than zero"
                )
            overrides[section_id] = value

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
            section_max_velocity_overrides_m_s=overrides,
        )

    def set_section_max_velocity_override(
        self,
        section_id: str,
        max_velocity_m_s: Optional[float],
    ) -> None:
        key = str(section_id or "").strip()
        if not key:
            raise ValueError("section_id is required")

        if max_velocity_m_s is None:
            self.section_max_velocity_overrides_m_s.pop(key, None)
            return

        value = float(max_velocity_m_s)
        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                "section velocity override must be finite and greater than zero"
            )

        self.section_max_velocity_overrides_m_s[key] = value

    def clear_section_max_velocity_override(self, section_id: str) -> None:
        self.set_section_max_velocity_override(section_id, None)

    def get_section_max_velocity_override(
        self,
        section_id: str,
    ) -> Optional[float]:
        key = str(section_id or "").strip()
        if not key:
            raise ValueError("section_id is required")
        return self.section_max_velocity_overrides_m_s.get(key)
