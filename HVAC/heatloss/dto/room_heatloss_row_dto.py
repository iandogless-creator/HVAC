"""
room_heatloss_row_dto.py
-----------------------

HVACgooee — Heat-Loss GUI Row DTO (v1)

Represents one row in the Heat-Loss table.

RULES
-----
• One row == one room
• Calculated fields are read-only
• Overrides are explicit and optional
• Notes are free text only
• No calculations are performed here
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class RoomHeatLossRowDTO:
    # ------------------------------------------------------------------
    # Identity / Context
    # ------------------------------------------------------------------
    room_id: str
    room_name: str
    hl_method: str
    """
    Heat-loss method used.
    Expected values (v1):
        - "simple"
        - "fabric"
    """

    # ------------------------------------------------------------------
    # Calculated values (ENGINE-OWNED)
    # ------------------------------------------------------------------
    qt_calc_w: float
    """
    Calculated total heat loss for the room (W).
    Authoritative engine output.
    """

    qf_w: float
    """
    Fabric heat loss contribution (W).
    """

    qv_w: float
    """
    Ventilation heat loss contribution (W).
    """

    # ------------------------------------------------------------------
    # User intent (GUI-OWNED)
    # ------------------------------------------------------------------
    qt_override_w: Optional[float] = None
    """
    Optional user override for QT (W).
    If set, this replaces qt_calc_w for downstream use.
    """

    notes: str = ""
    """
    Free-form user notes.
    Never parsed.
    Never used in calculations.
    """

    # ------------------------------------------------------------------
    # State flags (GUI-OWNED, derived)
    # ------------------------------------------------------------------
    is_stale: bool = False
    """
    True if inputs have changed since last calculation.
    Used for UI status only.
    """

    # ------------------------------------------------------------------
    # Derived helpers (NO SIDE EFFECTS)
    # ------------------------------------------------------------------
    @property
    def qt_effective_w(self) -> float:
        """
        Effective QT used for summation and hand-off.
        Override takes precedence if present.
        """
        return self.qt_override_w if self.qt_override_w is not None else self.qt_calc_w

    @property
    def has_override(self) -> bool:
        return self.qt_override_w is not None
