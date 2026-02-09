# ======================================================================
# HVAC/hydronics_v3/dto/pressure_drop_path_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class PressureDropPathDTO:
    """
    PressureDropPathDTO (v1)

    PURPOSE
    -------
    Represents a single *fully-resolved hydronic flow path*
    from a boiler entry point to a terminal leg.

    This DTO is the atomic unit used to:
    • compare pressure drops
    • identify the index path
    • derive balancing targets
    • report critical path data

    RULES (LOCKED)
    --------------
    • Immutable
    • Engine-produced only
    • NO sizing
    • NO balancing
    • NO valve logic
    • NO inference

    Physics values MUST be explicit.
    """

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    path_id: str
    """
    Stable identifier for this path (engine-defined).
    """

    # -------------------------------------------------
    # Structural definition
    # -------------------------------------------------
    leg_ids: List[str]
    """
    Ordered list of leg_ids from boiler → terminal.
    """

    terminal_leg_id: str
    """
    Final leg owning rooms (leaf leg).
    """

    # -------------------------------------------------
    # Geometry aggregation
    # -------------------------------------------------
    total_length_m: float
    """
    Total developed pipe length for this path.
    """

    # -------------------------------------------------
    # Pressure drop (explicit physics result)
    # -------------------------------------------------
    total_pressure_drop_pa: float
    """
    Total pressure drop for this path [Pa].
    """

    # -------------------------------------------------
    # Design load context (read-only)
    # -------------------------------------------------
    design_qt_w: float
    """
    Design heat load routed through this path [W].
    """

    # -------------------------------------------------
    # Convenience helpers (NO logic)
    # -------------------------------------------------
    def is_index_candidate(self) -> bool:
        """
        True if this path has a non-zero pressure drop.
        (Zero-drop paths are ignored for indexing.)
        """
        return self.total_pressure_drop_pa > 0.0
