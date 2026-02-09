# ======================================================================
# HVAC/hydronics/emitters/committed_terminal_emitter_v1.py
# ======================================================================

"""
HVACgooee — Committed Terminal Emitter v1
----------------------------------------

Represents an authoritative terminal heat emitter.

RULES
-----
• One per terminal leg
• No sizing
• No balancing
• No pipe geometry
• Immutable
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


EmitterType = Literal[
    "radiator",
    "ufh_loop",
    "fan_coil",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class CommittedTerminalEmitterV1:
    leg_id: str

    emitter_type: EmitterType
    design_heat_w: float
    design_flow_lps: float

    label: Optional[str] = None
