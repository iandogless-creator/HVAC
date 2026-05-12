
# ======================================================================
# HVAC/hydronics/models/hydronic_skeleton_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from HVAC.hydronics.emitter_v1 import EmitterV1


@dataclass(slots=True)
class BoilerNodeV1:
    boiler_id: str
    name: str


@dataclass(slots=True)
class TerminalNodeV1:
    terminal_id: str
    room_id: str
    room_name: str
    design_heat_loss_w: float


@dataclass(slots=True)
class HydronicLegV1:
    leg_id: str
    from_node_id: str
    to_node_id: str
    length_m: Optional[float] = None
    notes: str = ""


@dataclass(slots=True)
class HydronicSkeletonV1:
    """
    Declarative hydronic system intent.

    Authority
    ---------
    • Intent/schematic scaffold only
    • No pipe sizing
    • No pressure loss
    • No pump selection
    • No balancing
    """

    skeleton_id: str
    boiler: BoilerNodeV1

    terminals: dict[str, TerminalNodeV1] = field(default_factory=dict)
    supply_legs: dict[str, HydronicLegV1] = field(default_factory=dict)
    return_legs: dict[str, HydronicLegV1] = field(default_factory=dict)

    # Intent only — no physics
    emitters: dict[str, EmitterV1] = field(default_factory=dict)

    def add_terminal(self, terminal: TerminalNodeV1) -> None:
        self.terminals[terminal.terminal_id] = terminal

    def add_supply_leg(self, leg: HydronicLegV1) -> None:
        self.supply_legs[leg.leg_id] = leg

    def add_return_leg(self, leg: HydronicLegV1) -> None:
        self.return_legs[leg.leg_id] = leg

    def all_legs(self) -> list[HydronicLegV1]:
        return [
            *self.supply_legs.values(),
            *self.return_legs.values(),
        ]
