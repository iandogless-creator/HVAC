"""
simple_heatloss_input_dto.py
----------------------------

HVACgooee — Simple Heat-Loss Input DTO (v1)

Purpose
-------
Provide a minimal, explicit user-input model for estimating
total heat demand (QT) without fabric geometry.

Design Rules
------------
• Dumb data only
• No calculations
• No defaults hidden in code
• Stable and explicit
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


# ------------------------------------------------------------------
# Input DTO
# ------------------------------------------------------------------

@dataclass(frozen=True)
class SimpleHeatLossInputDTO:
    """
    Simple heat-loss input model (v1).

    Exactly ONE of the following bases must be used:
    - area-based
    - volume-based
    """

    basis: Literal["area", "volume"]

    # Geometry proxy
    floor_area_m2: float | None = None
    volume_m3: float | None = None

    # Loss rates
    loss_rate_w_per_m2: float | None = None
    loss_rate_w_per_m3: float | None = None

    # Metadata (non-physical)
    source: str = "user"
    notes: str | None = None
