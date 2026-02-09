"""Superseded in V3 by unified HeatLossEngine + assumption resolvers.”
HVACgooee — Technical Heat-Loss Engine (Level 3)
GPLv3 — Core Module

Purpose
-------
This level allows custom constructions:
- multiple layers
- material database lookup
- calculated U-values
- basic psi-values
- options for improved precision

This is the bridge between simple design and full building physics.
"""

from dataclasses import dataclass


@dataclass
class MaterialLayer:
    thickness_m: float
    conductivity: float  # W/mK
    description: str = ""


@dataclass
class TechnicalConstruction:
    layers: list  # list[MaterialLayer]
    internal_resistance: float = 0.13
    external_resistance: float = 0.04


@dataclass
class TechnicalSurface:
    area: float
    construction: TechnicalConstruction
    psi_value: float = 0.0


@dataclass
class TechnicalRoom:
    name: str
    design_temp: float
    outside_temp: float
    surfaces: list  # list[TechnicalSurface]
    volume: float
    ach: float


class TechnicalHeatlossEngine:
    """
    Provides U-value calculation and moderate thermal bridge handling.
    """

    def u_value_from_construction(self, construction: TechnicalConstruction) -> float:
        layers_r = sum(layer.thickness_m / layer.conductivity for layer in construction.layers)
        total_r = construction.internal_resistance + layers_r + construction.external_resistance
        return 1.0 / total_r

    def surface_loss(self, surface: TechnicalSurface, delta_t: float) -> float:
        u = self.u_value_from_construction(surface.construction)
        return u * surface.area * delta_t + (surface.psi_value * delta_t)

    def ventilation_loss(self, volume: float, ach: float, delta_t: float) -> float:
        factor = 0.33
        return volume * ach * factor * delta_t

    def calculate_room(self, room: TechnicalRoom) -> dict:
        delta_t = room.design_temp - room.outside_temp

        envelope = sum(self.surface_loss(s, delta_t) for s in room.surfaces)
        vent = self.ventilation_loss(room.volume, room.ach, delta_t)

        total = envelope + vent

        return {
            "envelope_loss": envelope,
            "ventilation_loss": vent,
            "total_loss": total,
        }
