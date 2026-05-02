from __future__ import annotations

from HVAC.project.project_state import ProjectState

from HVAC.dev.bootstrap_project_state import make_dev_bootstrap_project_state
from HVAC.dev.bootstrap_vertical_3room import build_vertical_stack_project_state

# ======================================================================
# DEV constructions
# ======================================================================

from HVAC.core.construction_v1 import ConstructionV1


def ensure_dev_constructions(ps) -> None:
    ps.constructions.setdefault(
        "DEV-EXT-WALL",
        ConstructionV1(
            construction_id="DEV-EXT-WALL",
            name="External Wall",
            u_value_W_m2K=0.28,
        ),
    )

    ps.constructions.setdefault(
        "DEV-INT-WALL",
        ConstructionV1(
            construction_id="DEV-INT-WALL",
            name="Internal Wall",
            u_value_W_m2K=1.50,
        ),
    )

    ps.constructions.setdefault(
        "DEV-FLOOR",
        ConstructionV1(
            construction_id="DEV-FLOOR",
            name="Floor",
            u_value_W_m2K=0.22,
        ),
    )

    ps.constructions.setdefault(
        "DEV-ROOF",
        ConstructionV1(
            construction_id="DEV-ROOF",
            name="Roof",
            u_value_W_m2K=0.18,
        ),
    )

    ps.constructions.setdefault(
        "DEV-WINDOW",
        ConstructionV1(
            construction_id="DEV-WINDOW",
            name="Window / Door",
            u_value_W_m2K=1.40,
        ),
    )

# ============================================================
# DEV Scenario Registry (authoritative)
# ============================================================

def build_dev_project(mode: str) -> ProjectState:
    """
    Central DEV entry point.

    Guarantees:
    • returns valid ProjectState
    • enforces schema invariants
    • isolates DEV from UI layer
    """

    if mode == "simple":
        ps = make_dev_bootstrap_project_state()

    elif mode == "vertical_stack":
        ps = build_vertical_stack_project_state()

    else:
        raise ValueError(f"[DEV] Unknown mode: {mode}")

    # --------------------------------------------------
    # 🔒 Enforce invariants (single place)
    # --------------------------------------------------
    if not hasattr(ps, "project_dir"):
        ps.project_dir = None

    return ps