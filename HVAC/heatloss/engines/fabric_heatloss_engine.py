"""
fabric_heatloss_engine.py
-------------------------

Fabric heat-loss engine for HVACgooee.

Implements steady-state heat-loss through building elements using:

    Q = U * A * ΔT      [W]

Optionally, a dynamic multiplier based on Y-values (from y_value_engine)
can be applied, but this module is primarily about the *fabric* term.

Ventilation / infiltration is handled separately in
ventilation_heatloss_engine.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class FabricSurface:
    """
    Single building element contributing to fabric heat loss.

    Examples:
        - external wall
        - window
        - door
        - roof
        - floor
    """
    id: str
    name: str
    U_W_m2K: float
    area_m2: float
    # Optional enhancement: effective U including dynamic effects (Y)
    Y_W_m2K: Optional[float] = None
    # Optional: orientation, type, etc.
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class FabricLossBreakdown:
    """
    Result container for fabric heat-loss.

    Per-surface and total heat losses (in Watts).
    """
    surfaces: List[Dict[str, float]]  # [{id, U, A, dT, Q_W}, ...]
    total_W: float


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def compute_surface_loss(
        surface: FabricSurface,
        temp_inside_C: float,
        temp_outside_C: float,
        use_y_value: bool = False,
) -> float:
    """
    Compute heat-loss through a single surface.

    By default uses steady-state U-value:

        Q = U * A * (Ti - Te)

    If use_y_value=True and Y is provided, we treat Y as an
    *effective* transmittance for dynamic conditions:

        Q_dyn = Y * A * (Ti - Te)

    Parameters
    ----------
    surface : FabricSurface
    temp_inside_C : float
    temp_outside_C : float
    use_y_value : bool
        If True and surface.Y_W_m2K is not None, use Y instead of U.

    Returns
    -------
    float : heat-loss in Watts
    """

    dT = temp_inside_C - temp_outside_C

    if dT <= 0:
        # No heat loss if outside is warmer or equal (in this simple model)
        return 0.0

    if use_y_value and surface.Y_W_m2K is not None:
        trans = surface.Y_W_m2K
    else:
        trans = surface.U_W_m2K

    return trans * surface.area_m2 * dT


def compute_fabric_loss(
        surfaces: List[FabricSurface],
        temp_inside_C: float,
        temp_outside_C: float,
        use_y_value: bool = False,
) -> FabricLossBreakdown:
    """
    Compute fabric heat-loss for a collection of surfaces (e.g. a room).

    Parameters
    ----------
    surfaces : list[FabricSurface]
    temp_inside_C : float
    temp_outside_C : float
    use_y_value : bool
        If True, use Y-values where available.

    Returns
    -------
    FabricLossBreakdown
        Contains per-surface and total Watts.
    """

    breakdown_list: List[Dict[str, float]] = []
    total = 0.0

    for s in surfaces:
        q = compute_surface_loss(s, temp_inside_C, temp_outside_C, use_y_value)
        total += q

        breakdown_list.append(
            {
                "id": s.id,
                "U_W_m2K": s.U_W_m2K,
                "Y_W_m2K": s.Y_W_m2K if s.Y_W_m2K is not None else 0.0,
                "area_m2": s.area_m2,
                "dT_K": temp_inside_C - temp_outside_C,
                "Q_W": q,
            }
        )

    return FabricLossBreakdown(surfaces=breakdown_list, total_W=total)


# ---------------------------------------------------------------------------
# Convenience: simple room wrapper
# ---------------------------------------------------------------------------

def compute_room_fabric_loss(
        room_id: str,
        room_surfaces: List[FabricSurface],
        design_temp_inside_C: float,
        design_temp_outside_C: float,
        use_y_value: bool = False,
) -> Dict[str, float]:
    """
    High-level helper for room-based fabric heat-loss.

    Returns a minimal dict suitable for attaching to a Room object
    or feeding into a report generator.

    Example output:
        {
            "room_id": "kitchen",
            "fabric_loss_W": 1200.0
        }
    """

    breakdown = compute_fabric_loss(
        room_surfaces,
        temp_inside_C=design_temp_inside_C,
        temp_outside_C=design_temp_outside_C,
        use_y_value=use_y_value,
    )

    return {
        "room_id": room_id,
        "fabric_loss_W": breakdown.total_W,
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo():
    # Example: simple room with one wall and one window
    wall = FabricSurface(
        id="wall_ext",
        name="External Wall",
        U_W_m2K=0.25,
        area_m2=12.0,
    )
    window = FabricSurface(
        id="win1",
        name="Window",
        U_W_m2K=1.4,
        area_m2=2.0,
    )

    surfaces = [wall, window]

    result = compute_fabric_loss(surfaces, temp_inside_C=21.0, temp_outside_C=-3.0)

    print("Total fabric loss:", round(result.total_W), "W")
    for s in result.surfaces:
        print(s)


if __name__ == "__main__":
    _demo()
