# ======================================================================
# BEGIN FILE: HVAC/heatloss/physics/room_heatloss_engine.py
# ======================================================================
"""
room_heatloss_engine.py
-----------------------

Master room-level heat-loss engine for HVACgooee.

Combines:
    - U-value & Y-value driven fabric losses
    - Ventilation / infiltration losses
    - Room metadata (temps only; legacy Room owns NO geometry)
    - Produces HeatLossResult dataclass

RULES (LOCKED)
--------------
✔ Room is temperature-only (no area, no volume)
✔ Fabric geometry comes from FabricSurface list
✔ Ventilation volume must be supplied explicitly by caller
✔ If volume is missing, ventilation loss is 0.0 (no guessing)
✔ If fabric breakdown is missing, fabric loss is 0.0 (TEMP wiring safe)
✔ Function MUST always return HeatLossResult
"""

from __future__ import annotations

from typing import List, Optional

from heatloss.engines.fabric_heatloss_engine import (
    FabricSurface,
    compute_fabric_loss,
)
from heatloss.physics.ventilation_heatloss_engine import (
    VentilationParams,
    compute_ventilation_loss,
)
from HVAC.models.hvac_dataclasses import HeatLossResult, Room


def compute_room_heatloss(
    room: Room,
    surfaces: List[FabricSurface],
    ventilation: Optional[VentilationParams],
    temp_inside_C: float | None = None,
    temp_outside_C: float | None = None,
    use_y_values: bool = False,
    room_volume_m3: float | None = None,
) -> HeatLossResult:
    """
    Compute total room heat-loss:

        Q_total = Q_fabric + Q_ventilation

    Notes
    -----
    - Legacy Room does not own geometry.
    - room_volume_m3 must be provided explicitly by the caller if ACH is used.
    """

    # Temperatures
    Ti = float(temp_inside_C) if temp_inside_C is not None else float(room.design_temp)
    Te = float(temp_outside_C) if temp_outside_C is not None else float(getattr(room, "outside_temp", -3.0))

    # Fallback defaults if missing
    if Ti is None:
        Ti = 21.0  # typical CIBSE default
    if Te is None:
        Te = -3.0  # typical UK external winter design

    # ------------------------------------------------------------
    # Fabric losses (guarded)
    # ------------------------------------------------------------
    Q_fabric = 0.0

    try:
        fabric_breakdown = compute_fabric_loss(
            surfaces or [],
            temp_inside_C=Ti,
            temp_outside_C=Te,
            use_y_value=use_y_values,
        )
    except Exception:
        fabric_breakdown = None

    if fabric_breakdown is not None:
        # Some legacy variants may use total_W; keep it strict but safe.
        Q_fabric = float(getattr(fabric_breakdown, "total_W", 0.0))

    # ------------------------------------------------------------
    # Ventilation losses (explicit volume; no guessing)
    # ------------------------------------------------------------
    Q_vent = 0.0

    if ventilation is not None and room_volume_m3 is not None:
        Q_vent = float(
            compute_ventilation_loss(
                ventilation,
                room_volume_m3=float(room_volume_m3),
                temp_inside_C=Ti,
                temp_outside_C=Te,
            )
        )

    # Total
    Q_total = Q_fabric + Q_vent

    # MUST return a result dataclass (never None)
    return HeatLossResult(
        fabric_loss_W=float(Q_fabric),
        ventilation_loss_W=float(Q_vent),
        total_loss_W=float(Q_total),
    )


# ------------------------------------------------------------
# Demo (kept valid under legacy Room contract)
# ------------------------------------------------------------
def _demo():
    room = Room(id="kitchen", name="Kitchen", design_temp=21.0, outside_temp=-3.0)

    surfaces = [
        FabricSurface(id="wall", name="Ext Wall", U_W_m2K=0.25, area_m2=10.0),
        FabricSurface(id="win", name="Window", U_W_m2K=1.4, area_m2=2.0),
    ]

    ventilation = VentilationParams(ach=0.5)

    result = compute_room_heatloss(
        room,
        surfaces,
        ventilation,
        temp_outside_C=-3.0,
        room_volume_m3=30.0,  # explicit volume required for ACH
        use_y_values=False,
    )

    print(result)


if __name__ == "__main__":
    _demo()

# ======================================================================
# END FILE: HVAC/heatloss/physics/room_heatloss_engine.py
# ======================================================================
