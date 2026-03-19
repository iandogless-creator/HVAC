# ======================================================================
# HVACgooee — Room Geometry V1 (Rectangular, Phase IV-A stable)
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class RoomGeometryV1:
    """
    Authoritative room geometry (Phase IV-A)

    Model
    -----
    Rectangular geometry only.

    Notes
    -----
    • USER INPUT geometry only
    • No derived values stored
    • Topology comes later (Phase IV-B)
    """

    length_m: Optional[float] = None
    width_m: Optional[float] = None
    height_m: Optional[float] = None

    # Optional explicit override (engineer intent)
    external_wall_length_m: Optional[float] = None

    # ------------------------------------------------------------------
    # Helpers (non-authoritative, safe)
    # ------------------------------------------------------------------

    def floor_area_m2(self) -> Optional[float]:
        if self.length_m is not None and self.width_m is not None:
            return self.length_m * self.width_m
        return None

    def volume_m3(self) -> Optional[float]:
        if (
            self.length_m is not None
            and self.width_m is not None
            and self.height_m is not None
        ):
            return self.length_m * self.width_m * self.height_m
        return None

    def perimeter_m(self) -> Optional[float]:
        if self.length_m is not None and self.width_m is not None:
            return 2.0 * (self.length_m + self.width_m)
        return None

    def effective_external_wall_length_m(self) -> Optional[float]:
        """
        Non-authoritative fallback:
        If user hasn't specified external wall length,
        assume full perimeter (temporary Phase IV-A behaviour).
        """
        if self.external_wall_length_m is not None:
            return self.external_wall_length_m

        return self.perimeter_m()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "length_m": self.length_m,
            "width_m": self.width_m,
            "height_m": self.height_m,
            "external_wall_length_m": self.external_wall_length_m,
        }

    # ------------------------------------------------------------------
    # Deserialization
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict | None) -> "RoomGeometryV1":

        if not data:
            return cls()

        def _to_float(v):
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        return cls(
            length_m=_to_float(data.get("length_m")),
            width_m=_to_float(data.get("width_m")),
            height_m=_to_float(data.get("height_m")),
            external_wall_length_m=_to_float(
                data.get("external_wall_length_m")
            ),
        )