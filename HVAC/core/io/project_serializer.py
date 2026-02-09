"""
HVACgooee — Project Serializer (Core v1)
=======================================

Purpose
-------
Provide a single backend mechanism to take a "snapshot" of the
current project and restore it later.

A snapshot includes:

- Building model:
    • Building → Rooms → Elements → Openings
    • Constructions + layers
- Hydronic network:
    • Plant → Legs → Sublegs → Emitters
- App settings:
    • Simple key/value dict (theme, mode, units, etc.)
- Materials database:
    • As JSON string via MaterialsDatabase.to_json()

Design Rules
------------
- Pure backend: NO GUI, NO DXF, NO file I/O.
  The caller is responsible for writing/reading the JSON string to disk.

- JSON format is stable, human-readable, and versioned.

Usage (example)
---------------
from HVAC.core.io.project_serializer import (
    create_project_snapshot,
    snapshot_to_json,
    snapshot_from_json,
)

# Save:
snapshot = create_project_snapshot(building, plant, settings_dict, materials_db)
json_str = snapshot_to_json(snapshot)
# → caller writes json_str to a .gooee file

# Load:
snapshot2 = snapshot_from_json(json_str)
building2, plant2 = snapshot2.restore_objects(materials_db, settings_dict)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, Tuple, Optional

# Heat-loss + constructions
from HVAC_legacy.heatloss.room_model.building_model import Building
from HVAC_legacy.heatloss.room_model.room_model import Room, RoomElement, RoomOpening
from heatloss.physics.constructions import (
    Construction,
    ConstructionLayer,
)

# Hydronics
from HVAC_legacy.hydronics.network.hydronics_controller import (
    HydronicPlant,
    HydronicLeg,
    HydronicSubleg,
    HydronicEmitter,
)

# Materials DB
from HVAC_legacy.core.materials.materials_database import MaterialsDatabase


# ---------------------------------------------------------------------------
# Helper serializers — Building & Constructions
# ---------------------------------------------------------------------------

def construction_to_dict(con: Construction) -> Dict[str, Any]:
    return {
        "layers": [
            {
                "name": l.name,
                "thickness_m": l.thickness_m,
                "conductivity_W_mK": l.conductivity_W_mK,
                "density_kg_m3": l.density_kg_m3,
                "specific_heat_J_kgK": l.specific_heat_J_kgK,
            }
            for l in con.layers
        ],
        "internal_surface_resistance": con.internal_surface_resistance,
        "external_surface_resistance": con.external_surface_resistance,
        "bridging_fraction": con.bridging_fraction,
        "bridging_conductivity": con.bridging_conductivity,
        "mode": con.mode,
    }


def construction_from_dict(data: Dict[str, Any]) -> Construction:
    layers = [
        ConstructionLayer(
            name=l.get("name", "layer"),
            thickness_m=float(l["thickness_m"]),
            conductivity_W_mK=float(l["conductivity_W_mK"]),
            density_kg_m3=l.get("density_kg_m3"),
            specific_heat_J_kgK=l.get("specific_heat_J_kgK"),
        )
        for l in data.get("layers", [])
    ]
    return Construction(
        layers=layers,
        internal_surface_resistance=data.get("internal_surface_resistance", 0.13),
        external_surface_resistance=data.get("external_surface_resistance", 0.04),
        bridging_fraction=data.get("bridging_fraction", 0.0),
        bridging_conductivity=data.get("bridging_conductivity", 0.0),
        mode=data.get("mode", "advanced"),
    )


def opening_to_dict(op: RoomOpening) -> Dict[str, Any]:
    # Advanced fenestration systems are referenced by ID in v1
    # (actual FenestrationSystem library is handled elsewhere).
    return {
        "area_m2": op.area_m2,
        "system_ref": getattr(op.system, "id", None) if op.system is not None else None,
        "u_value_override": op.u_value_override,
    }


def element_to_dict(elem: RoomElement) -> Dict[str, Any]:
    return {
        "construction": construction_to_dict(elem.construction),
        "area_m2": elem.area_m2,
        "openings": [opening_to_dict(o) for o in elem.openings],
    }


def room_to_dict(room: Room) -> Dict[str, Any]:
    return {
        "name": room.name,
        "elements": [element_to_dict(e) for e in room.elements],
        "ventilation_rate_ach": room.ventilation_rate_ach,
        "infiltration_rate_ach": room.infiltration_rate_ach,
        "volume_m3": room.volume_m3,
        "mode": room.mode,
    }


def building_to_dict(b: Building) -> Dict[str, Any]:
    return {
        "name": b.name,
        "mode": b.mode,
        "T_inside_design": b.T_inside_design,
        "T_outside_design": b.T_outside_design,
        "rooms": [room_to_dict(r) for r in b.rooms],
    }


def room_from_dict(data: Dict[str, Any]) -> Room:
    elems = []
    for e in data.get("elements", []):
        con = construction_from_dict(e["construction"])
        openings = [
            RoomOpening(
                area_m2=o["area_m2"],
                system=None,                 # system_ref handled at higher level later
                u_value_override=o.get("u_value_override"),
            )
            for o in e.get("openings", [])
        ]
        elems.append(
            RoomElement(
                construction=con,
                area_m2=e["area_m2"],
                openings=openings,
            )
        )

    return Room(
        name=data["name"],
        elements=elems,
        ventilation_rate_ach=data.get("ventilation_rate_ach", 0.5),
        infiltration_rate_ach=data.get("infiltration_rate_ach", 0.1),
        volume_m3=data.get("volume_m3"),
        mode=data.get("mode", "advanced"),
    )


def building_from_dict(data: Dict[str, Any]) -> Building:
    rooms = [room_from_dict(r) for r in data.get("rooms", [])]
    return Building(
        name=data.get("name", "Building"),
        rooms=rooms,
        mode=data.get("mode", "advanced"),
        T_inside_design=data.get("T_inside_design", 21.0),
        T_outside_design=data.get("T_outside_design", -3.0),
    )


# ---------------------------------------------------------------------------
# Helper serializers — Hydronic Plant
# ---------------------------------------------------------------------------

def emitter_to_dict(e: HydronicEmitter) -> Dict[str, Any]:
    return {
        "id": e.id,
        "flow_rate_lph": e.flow_rate_lph,
        "design_deltaT": e.design_deltaT,
        "power_W": e.power_W,
    }


def subleg_to_dict(s: HydronicSubleg) -> Dict[str, Any]:
    return {
        "id": s.id,
        "emitters": [emitter_to_dict(e) for e in s.emitters],
    }


def leg_to_dict(l: HydronicLeg) -> Dict[str, Any]:
    return {
        "id": l.id,
        "sublegs": [subleg_to_dict(s) for s in l.sublegs],
    }


def plant_to_dict(p: HydronicPlant) -> Dict[str, Any]:
    return {
        "id": p.id,
        "legs": [leg_to_dict(l) for l in p.legs],
    }


def emitter_from_dict(d: Dict[str, Any]) -> HydronicEmitter:
    return HydronicEmitter(
        id=d["id"],
        flow_rate_lph=d["flow_rate_lph"],
        design_deltaT=d["design_deltaT"],
        power_W=d["power_W"],
    )


def subleg_from_dict(d: Dict[str, Any]) -> HydronicSubleg:
    return HydronicSubleg(
        id=d["id"],
        emitters=[emitter_from_dict(e) for e in d.get("emitters", [])],
    )


def leg_from_dict(d: Dict[str, Any]) -> HydronicLeg:
    return HydronicLeg(
        id=d["id"],
        sublegs=[subleg_from_dict(s) for s in d.get("sublegs", [])],
    )


def plant_from_dict(d: Dict[str, Any]) -> HydronicPlant:
    return HydronicPlant(
        id=d.get("id", "PLANT"),
        legs=[leg_from_dict(l) for l in d.get("legs", [])],
    )


# ---------------------------------------------------------------------------
# Snapshot Dataclass
# ---------------------------------------------------------------------------

@dataclass
class ProjectSnapshot:
    """
    A full HVACgooee project snapshot, ready for JSON serialisation.

    Note: This is a backend transport structure, not a runtime object.
    """
    schema_version: str = "1.0"
    created_utc: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    # Core project objects in dict form
    building: Dict[str, Any] = field(default_factory=dict)
    hydronic_plant: Dict[str, Any] = field(default_factory=dict)

    # Settings and materials
    settings: Dict[str, Any] = field(default_factory=dict)
    materials_json: str = ""   # JSON string of MaterialsDatabase

    # Optional free-form metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Rehydration helpers
    # ------------------------------------------------------------------

    def restore_objects(
        self,
        materials_db: Optional[MaterialsDatabase] = None,
        settings_target: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Building, HydronicPlant]:
        """
        Recreate Building + HydronicPlant objects from the snapshot.

        If a MaterialsDatabase is provided, we load materials_json into it
        (merge mode). If settings_target is provided, it is updated with
        snapshot settings.
        """
        b = building_from_dict(self.building)
        p = plant_from_dict(self.hydronic_plant)

        if materials_db is not None and self.materials_json:
            try:
                materials_db.load_json(self.materials_json, overwrite=False)
            except Exception:
                # Non-fatal: caller may choose to re-load separately
                pass

        if settings_target is not None:
            settings_target.update(self.settings)

        return b, p


# ---------------------------------------------------------------------------
# Snapshot Creation & JSON Conversion
# ---------------------------------------------------------------------------

def create_project_snapshot(
    building: Building,
    plant: HydronicPlant,
    settings: Dict[str, Any],
    materials_db: MaterialsDatabase,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProjectSnapshot:
    """
    Build a ProjectSnapshot from current runtime objects.

    Caller is expected to then call snapshot_to_json(...) and write
    the resulting string to a file.
    """
    b_dict = building_to_dict(building)
    p_dict = plant_to_dict(plant)
    mat_json = materials_db.to_json(indent=None)

    snap = ProjectSnapshot(
        building=b_dict,
        hydronic_plant=p_dict,
        settings=dict(settings),
        materials_json=mat_json,
        metadata=metadata or {},
    )
    return snap


def snapshot_to_json(snapshot: ProjectSnapshot, indent: int = 2) -> str:
    """
    Convert a ProjectSnapshot to JSON string.
    """
    data = asdict(snapshot)
    return json.dumps(data, indent=indent)


def snapshot_from_json(json_str: str) -> ProjectSnapshot:
    """
    Parse JSON string into a ProjectSnapshot.

    Does not automatically re-create runtime objects; use
    snapshot.restore_objects(...) for that.
    """
    data = json.loads(json_str)
    return ProjectSnapshot(
        schema_version=data.get("schema_version", "1.0"),
        created_utc=data.get("created_utc", datetime.utcnow().isoformat() + "Z"),
        building=data.get("building", {}),
        hydronic_plant=data.get("hydronic_plant", {}),
        settings=data.get("settings", {}),
        materials_json=data.get("materials_json", ""),
        metadata=data.get("metadata", {}),
    )
