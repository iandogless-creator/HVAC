# ======================================================================
# HVAC/dev/dev_constructions.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.core.construction_v1 import ConstructionV1


def ensure_dev_constructions(ps: ProjectState) -> None:
    """
    Install canonical DEV construction definitions.

    Rule
    ----
    All fabric rows must resolve U-values through construction_id.
    No surface-level U-value fallback.
    """

    ps.constructions.setdefault(
        "DEV-EXT-WALL",
        ConstructionV1("DEV-EXT-WALL", "External Wall", 0.28),
    )

    ps.constructions.setdefault(
        "DEV-INT-WALL",
        ConstructionV1("DEV-INT-WALL", "Internal Wall", 1.50),
    )

    ps.constructions.setdefault(
        "DEV-FLOOR",
        ConstructionV1("DEV-FLOOR", "Floor", 0.22),
    )

    ps.constructions.setdefault(
        "DEV-ROOF",
        ConstructionV1("DEV-ROOF", "Roof / Ceiling", 0.18),
    )

    ps.constructions.setdefault(
        "DEV-WINDOW",
        ConstructionV1("DEV-WINDOW", "Window / Door", 1.40),
    )