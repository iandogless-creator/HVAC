from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Room:
    id: str
    name: str
    design_temp: float
    outside_temp: float = -3.0


@dataclass
class HeatLossResult:
    fabric_loss_W: float
    ventilation_loss_W: float
    total_loss_W: float
