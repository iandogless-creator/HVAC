"""Superseded in V3 by unified HeatLossEngine + assumption resolvers.”
HVACgooee — Simple Heat-Loss Engine (Level 2)
GPLv3 — Core Module

Purpose
-------
Provides a practical, room-by-room heat-loss calculator suitable for
heating engineers, apprentices, and day-to-day design work.

Allows:
- Real surface breakdowns (walls, windows, roof, floor)
- Editable U-values
- Simple Y-value or thermal bridge allowances
- Simple ventilation/infiltration options
- Partial data allowed (Draft/Preliminary/Final workflow)
"""

from dataclasses import dataclass


@dataclass
class SimpleSurface:
    area: float
    u_value: float
    description: str = ""


@dataclass
class SimpleRoom:
    name: str
    design_temp: float
    outside_temp: float
    surfaces: list  # list[SimpleSurface]
    volume: float
    ach: float
    y_value: float = 0.0


class SimpleHeatlossEngine:
    """
    Level 2 heat-loss engine.
    """

    def calculate_surface_loss(self, surface: SimpleSurface, delta_t: float) -> float:
        return surface.u_value * surface.area * delta_t

    def calculate_ventilation(self, volume: float, ach: float, delta_t: float) -> float:
        factor = 0.33
        return volume * ach * factor * delta_t

    def calculate_room(self, room: SimpleRoom) -> dict:
        delta_t = room.design_temp - room.outside_temp

        envelope_loss = sum(
            self.calculate_surface_loss(s, delta_t) for s in room.surfaces
        )

        thermal_bridge_loss = envelope_loss * room.y_value

        ventilation_loss = self.calculate_ventilation(
            room.volume, room.ach, delta_t
        )

        total = envelope_loss + thermal_bridge_loss + ventilation_loss

        return {
            "envelope_loss": envelope_loss,
            "thermal_bridge_loss": thermal_bridge_loss,
            "ventilation_loss": ventilation_loss,
            "total_loss": total,
        }
