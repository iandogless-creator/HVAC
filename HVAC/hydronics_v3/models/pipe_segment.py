from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class PipeSegment:
    """
    Minimal hydronic pipe segment (v1).

    PURPOSE
    -------
    Describes pipe geometry only.

    RULES (LOCKED)
    --------------
    • No flow calculations
    • No pressure calculations
    • No sizing logic
    • No engine imports
    • Pure data container

    All physics is handled by separate engines.
    """

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    segment_id: str

    # -------------------------------------------------
    # Geometry
    # -------------------------------------------------
    length_m: float

    # -------------------------------------------------
    # Declared pipe properties (optional at v1)
    # -------------------------------------------------
    nominal_diameter: Optional[str] = None      # e.g. "DN15", "DN20"
    internal_diameter_mm: Optional[float] = None

    material: Optional[str] = None               # copper | steel | pex
    roughness_mm: Optional[float] = None

    # -------------------------------------------------
    # Metadata only
    # -------------------------------------------------
    notes: Optional[str] = None
