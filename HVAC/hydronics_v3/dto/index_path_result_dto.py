# ======================================================================
# HVAC/hydronics_v3/dto/index_path_result_dto.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from HVAC_legacy.hydronics_v3.dto.pressure_drop_path_dto import PressureDropPathDTO


@dataclass(frozen=True, slots=True)
class IndexPathResultDTO:
    """
    IndexPathResultDTO (v1)

    PURPOSE
    -------
    Declares the *index path* of a hydronic system after
    pressure-drop estimation.

    The index path is:
    • The path with the greatest total pressure drop
    • The governing path for balancing and valve authority

    RULES (LOCKED)
    --------------
    • Immutable
    • Engine-produced only
    • Derived solely from PressureDropPathDTOs
    • No physics
    • No inference
    """

    # -------------------------------------------------
    # Index path identity
    # -------------------------------------------------
    index_path_id: str
    """
    Identifier of the governing (index) path.
    """

    index_leg_ids: List[str]
    """
    Ordered leg IDs from boiler → terminal for the index path.
    """

    terminal_leg_id: str
    """
    Terminal (leaf) leg at the end of the index path.
    """

    # -------------------------------------------------
    # Governing values
    # -------------------------------------------------
    total_pressure_drop_pa: float
    """
    Governing pressure drop for the system [Pa].
    """

    total_length_m: float
    """
    Total developed length of the index path [m].
    """

    design_qt_w: float
    """
    Design heat load routed through the index path [W].
    """

    # -------------------------------------------------
    # Context (read-only)
    # -------------------------------------------------
    all_paths: List[PressureDropPathDTO]
    """
    All evaluated paths (including non-index).
    Used for reporting and balancing comparison.
    """

    # -------------------------------------------------
    # Convenience helpers (NO logic)
    # -------------------------------------------------
    def non_index_paths(self) -> List[PressureDropPathDTO]:
        """
        All paths except the index path.
        """
        return [
            p for p in self.all_paths
            if p.path_id != self.index_path_id
        ]
