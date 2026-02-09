"""Superseded in V3 by unified HeatLossEngine + assumption resolvers.”
HVACgooee — Novice Heat-Loss Engine (Level 1)
GPLv3 — Core Module

Purpose
-------
Provides a very simple, beginner-friendly heat-loss estimator
using preset U-values, preset ventilation rates, and basic room
geometry.

This is used by the Novice Wizard GUI and produces approximate
results suitable for homeowners, trainees, and quick checks.

No advanced physics. No custom constructions.
"""

from dataclasses import dataclass


@dataclass
class NoviceRoomInput:
    width: float
    length: float
    height: float
    construction_type: str
    glazing_type: str
    design_temp: float
    outside_temp: float


class NoviceHeatlossEngine:
    """
    Main calculator for Level 1 novice mode.
    """

    def __init__(self, presets):
        """
        presets: dict containing preset U-values and ACH values.
        Expected keys:
            - 'u_values'
            - 'ach'
        """
        self.presets = presets

    def estimate_envelope_loss(self, area: float, u_value: float, delta_t: float) -> float:
        """Basic Q = U × A × ΔT."""
        return u_value * area * delta_t

    def estimate_ventilation_loss(self, volume: float, ach: float, delta_t: float) -> float:
        """Simplified ventilation formula for novice mode."""
        air_density = 0.33  # kW·h/(m³·ΔT) approx factor
        return volume * ach * air_density * delta_t

    def calculate_room(self, room: NoviceRoomInput) -> dict:
        """
        Perform a very simplified heat-loss calculation.
        """
        delta_t = room.design_temp - room.outside_temp
        volume = room.width * room.length * room.height

        u = self.presets["u_values"].get(room.construction_type, 1.5)
        u_glazing = self.presets["u_values"].get(room.glazing_type, 2.8)
        ach = self.presets["ach"]

        wall_area = 2 * room.height * (room.width + room.length)
        window_area = (room.width * room.height) * 0.15  # simple guess

        envelope_loss = (
            self.estimate_envelope_loss(wall_area, u, delta_t)
            + self.estimate_envelope_loss(window_area, u_glazing, delta_t)
        )

        ventilation_loss = self.estimate_ventilation_loss(volume, ach, delta_t)

        total = envelope_loss + ventilation_loss

        return {
            "envelope_loss_watts": envelope_loss,
            "ventilation_loss_watts": ventilation_loss,
            "total_heat_loss_watts": total,
        }
