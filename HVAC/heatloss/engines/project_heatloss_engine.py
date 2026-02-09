"""
project_heatloss_engine.py
--------------------------

Top-level heat-loss engine for HVACgooee.

Runs:
    - fabric heat loss
    - ventilation heat loss
    - per-room heat-loss
    - building-level aggregation

ENGINE-ONLY MODULE
• No GUI imports
• No DTO imports
• Uses legacy Room + HeatLossResult
"""

from __future__ import annotations

from typing import Dict, Any, List

from HVAC_legacy.models.hvac_dataclasses import (
    Room,
    HeatLossResult,
)

from HVAC_legacy.heatloss.physics.room_heatloss_engine import compute_room_heatloss
from HVAC_legacy.heatloss.engines.fabric_heatloss_engine import FabricSurface
from HVAC_legacy.heatloss.physics.ventilation_heatloss_engine import VentilationParams


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_room(room_id: str, room_dict: Dict[str, Any]) -> Room:
    """
    Convert a room dictionary loaded from JSON into a legacy Room dataclass.

    LOCKED legacy Room contract:
        • id
        • name
        • design_temp
        • outside_temp
    """
    outside_temp = (
        room_dict.get("outside_temp")
        or room_dict.get("temp_outside_C")
        or room_dict.get("design_temp_outside_C")
        or -3.0
    )

    return Room(
        id=room_id,
        name=room_dict.get("name", room_id),
        design_temp=float(room_dict.get("design_temp", 21.0)),
        outside_temp=float(outside_temp),
    )


def _parse_surfaces(room_dict: Dict[str, Any]) -> List[FabricSurface]:
    """
    Parse fabric surfaces from a room definition.
    """
    surfaces: List[FabricSurface] = []

    for s in room_dict.get("surfaces", []):
        surfaces.append(
            FabricSurface(
                id=s["id"],
                name=s.get("name", s["id"]),
                U_W_m2K=s.get("U") or s.get("U_W_m2K"),
                area_m2=s.get("A") or s.get("area_m2"),
                Y_W_m2K=s.get("Y") or s.get("Y_W_m2K") or 0.0,
            )
        )

    return surfaces


def _parse_ventilation(room_dict: Dict[str, Any]) -> VentilationParams:
    """
    Convert room ventilation info into VentilationParams.
    """
    vent = room_dict.get("ventilation", {})

    return VentilationParams(
        ach=vent.get("ach"),
        flow_m3_s=vent.get("flow_m3_s"),
        flow_l_s=vent.get("flow_l_s"),
        flow_m3_h=vent.get("flow_m3_h"),
    )


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def compute_project_heatloss(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute heat loss for every room in the project.

    Returns:
        {
            "rooms": {room_id: HeatLossResult},
            "total_W": float,
            "fabric_W": float,
            "ventilation_W": float,
        }
    """
    rooms_json = project.get("rooms", {})
    results: Dict[str, HeatLossResult] = {}

    total_fabric = 0.0
    total_vent = 0.0
    total_all = 0.0

    for room_id, room_dict in rooms_json.items():
        room = _parse_room(room_id, room_dict)
        surfaces = _parse_surfaces(room_dict)
        ventilation = _parse_ventilation(room_dict)

        result = compute_room_heatloss(
            room=room,
            surfaces=surfaces,
            ventilation=ventilation,
            use_y_values=True,
        )

        results[room_id] = result

        total_fabric += result.fabric_loss_W
        total_vent += result.ventilation_loss_W
        total_all += result.total_loss_W

    return {
        "rooms": results,
        "total_W": total_all,
        "fabric_W": total_fabric,
        "ventilation_W": total_vent,
    }


# ---------------------------------------------------------------------------
# Demo (safe, optional)
# ---------------------------------------------------------------------------

def _demo():
    project = {
        "rooms": {
            "kitchen": {
                "name": "Kitchen",
                "design_temp": 21,
                "surfaces": [
                    {"id": "wall", "U": 0.25, "A": 10.0},
                    {"id": "win", "U": 1.4, "A": 2.0},
                ],
                "ventilation": {"ach": 0.5},
            },
            "lounge": {
                "name": "Lounge",
                "design_temp": 21,
                "surfaces": [
                    {"id": "wall", "U": 0.22, "A": 18.0},
                    {"id": "win", "U": 1.2, "A": 3.0},
                ],
                "ventilation": {"ach": 0.3},
            },
        },
        "settings": {"design_temp_outside_C": -3.0},
    }

    report = compute_project_heatloss(project)

    print("Building total heat loss:", round(report["total_W"]), "W")
    print("Fabric:", round(report["fabric_W"]), "W")
    print("Ventilation:", round(report["ventilation_W"]), "W")

    for rid, res in report["rooms"].items():
        print(rid, "→", round(res.total_loss_W), "W")


if __name__ == "__main__":
    _demo()
