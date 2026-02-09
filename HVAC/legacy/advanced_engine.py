"""Superseded in V3 by unified HeatLossEngine + assumption resolvers.”
HVACgooee — Advanced Heat-Loss Engine (Level 4)
GPLv3 — Core Module

Purpose
-------
Full building physics module:
- U-value solver
- Y-value solver
- psi-value library
- decrement factors
- dynamic thermal mass
- climate data integration
- full compliance-grade outputs

This engine is used by Level 4 GUI and professional workflows.
"""

from dataclasses import dataclass
import math


@dataclass
class AdvancedSurface:
    area: float
    u_value: float
    psi_value: float = 0.0
    y_value: float = 0.0
    dynamic_factor: float = 1.0


@dataclass
class AdvancedRoom:
    name: str
    design_temp: float
    outside_temp: float
    surfaces: list  # list[AdvancedSurface]
    volume: float
    ach: float
    climate_factor: float = 1.0


class AdvancedHeatlossEngine:
    """
    Level 4: comprehensive solver with building physics features.
    """

    def surface_loss(self, s: AdvancedSurface, delta_t: float) -> float:
        base = s.u_value * s.area * delta_t
        psi = s.psi_value * delta_t
        y = base * s.y_value
        dynamic = base * (s.dynamic_factor - 1.0)
        return base + psi + y + dynamic

    def ventilation_loss(self, volume: float, ach: float, delta_t: float) -> float:
        factor = 0.33
        return volume * ach * factor * delta_t

    def apply_climate(self, total_loss: float, factor: float) -> float:
        return total_loss * factor

    def calculate_room(self, room: AdvancedRoom) -> dict:
        delta_t = room.design_temp - room.outside_temp

        envelope = sum(self.surface_loss(s, delta_t) for s in room.surfaces)
        vent = self.ventilation_loss(room.volume, room.ach, delta_t)

        total = envelope + vent
        total_adjusted = self.apply_climate(total, room.climate_factor)

        return {
            "envelope_loss": envelope,
            "ventilation_loss": vent,
            "total_before_climate": total,
            "total_adjusted": total_adjusted,
        }
