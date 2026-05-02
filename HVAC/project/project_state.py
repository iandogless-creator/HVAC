# ======================================================================
# HVAC/project/project_state.py
# ======================================================================

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.project_v3.dto.heatloss_readiness import HeatLossReadiness
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1
from HVAC.core.construction_v1 import ConstructionV1
from HVAC.hydronics.emitter_v1 import EmitterV1

# ======================================================================
# ProjectState
# ======================================================================

@dataclass(slots=True)
class ProjectState:
    project_id: str
    name: str

    # 🔥 REQUIRED (do not omit)
    project_dir: Optional[Path] = None

    # existing fields...
    rooms: Dict[str, RoomStateV1] = field(default_factory=dict)
    environment: Optional[EnvironmentStateV1] = None
    boundary_segments: Dict[str, BoundarySegmentV1] = field(default_factory=dict)


    # ------------------------------------------------------------------
    # Phase IV-D — Openings (sub-surfaces)
    # surface_id -> list[OpeningV1]
    # ------------------------------------------------------------------
    openings_by_surface: Dict[str, list[Any]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # v1 Construction library (minimal, stable)
    # ------------------------------------------------------------------
    constructions: Dict[str, ConstructionV1] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Phase V-A — Surface-level construction assignment
    # surface_id -> construction_id
    # ------------------------------------------------------------------
    surface_construction_map: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    heatloss_results: Optional[dict[str, Any]] = None
    heatloss_valid: bool = False

    hydronics_results: Optional[dict[str, Any]] = None
    hydronics_valid: bool = False
    # in project_state.py

    emitters: Dict[str, EmitterV1] = field(default_factory=dict)
    # ------------------------------------------------------------------
    # Execution override (temporary)
    # ------------------------------------------------------------------
    allow_unsafe_heatloss_run: bool = False

    # ==================================================================
    # Lifecycle flags
    # ==================================================================
    def mark_heatloss_dirty(self) -> None:
        self.heatloss_valid = False

    def mark_heatloss_valid(self) -> None:
        if not self.heatloss_results:
            raise RuntimeError("No heat-loss results present")

        required = {"fabric", "ventilation", "room_totals"}
        missing = required - set(self.heatloss_results.keys())
        if missing:
            raise RuntimeError(
                f"Heat-loss container incomplete. Missing keys: {sorted(missing)}"
            )

        self.heatloss_valid = True


    # ==================================================================
    # Readiness
    # ==================================================================
    def evaluate_heatloss_readiness(self) -> HeatLossReadiness:
        reasons: list[str] = []

        env = self.environment
        if env is None:
            reasons.append("Environment not defined")
        else:
            if env.external_design_temp_C is None:
                reasons.append("External design temperature not set")

        if not self.rooms:
            reasons.append("No rooms defined")
        else:
            from HVAC.core.value_resolution import (
                resolve_effective_height_m,
                resolve_effective_ach,
            )

            for room_id, room in self.rooms.items():

                # --------------------------------------------------
                # Geometry
                # --------------------------------------------------
                g = getattr(room, "geometry", None)
                if g is None:
                    reasons.append(f"Room '{room_id}' has no geometry")
                    continue

                area = getattr(g, "floor_area_m2", None)
                if callable(area):
                    area = area()

                if area is None or float(area) <= 0.0:
                    reasons.append(f"Room '{room_id}' has invalid floor area")

                height_m, _ = resolve_effective_height_m(self, room)
                if height_m is None or float(height_m) <= 0.0:
                    reasons.append(f"Room '{room_id}' has no valid height")

                ach, _ = resolve_effective_ach(self, room)
                if ach is None or float(ach) <= 0.0:
                    reasons.append(f"Room '{room_id}' has no valid ACH")

                # --------------------------------------------------
                # Fabric via topology
                # --------------------------------------------------
                fabric_rows = FabricFromSegmentsV1.build_rows_for_room(self, room)

                if not fabric_rows:
                    reasons.append(f"Room '{room_id}' has no fabric surfaces")
                    continue

                for row in fabric_rows:
                    elem = row.element

                    area_m2 = row.area_m2
                    if area_m2 is None or float(area_m2) <= 0.0:
                        reasons.append(
                            f"Room '{room_id}' element '{elem}' has invalid area"
                        )

                    cid = row.construction_id
                    if not cid:
                        reasons.append(
                            f"Room '{room_id}' element '{elem}' has no construction_id"
                        )
                        continue

                    construction = self.constructions.get(str(cid))
                    if construction is None:
                        reasons.append(
                            f"Construction '{cid}' not found "
                            f"(room '{room_id}', element '{elem}')"
                        )
                        continue

                    u = construction.u_value_W_m2K
                    if u is None or float(u) <= 0.0:
                        reasons.append(
                            f"Construction '{cid}' has no valid U-value "
                            f"(room '{room_id}', element '{elem}')"
                        )

        is_ready = len(reasons) == 0

        if not is_ready and self.allow_unsafe_heatloss_run:
            return HeatLossReadiness(
                is_ready=True,
                blocking_reasons=reasons,
            )

        return HeatLossReadiness(
            is_ready=is_ready,
            blocking_reasons=reasons,
        )

    # ==================================================================
    # Serialization
    # ==================================================================
    def to_dict(self) -> dict:
        return {
            "schema_version": 4,
            "project_id": self.project_id,
            "name": self.name,
            "environment": self.environment.to_dict() if self.environment else None,
            "rooms": {rid: room.to_dict() for rid, room in self.rooms.items()},
            "boundary_segments": {
                seg_id: seg.to_dict()
                for seg_id, seg in self.boundary_segments.items()
            },
            "surface_construction_map": dict(self.surface_construction_map),
            "openings": {
                sid: [
                    o.to_dict() if hasattr(o, "to_dict") else vars(o)
                    for o in openings
                ]
                for sid, openings in self.openings_by_surface.items()
            },
            "constructions": {
    cid: {
        "construction_id": c.construction_id,
        "name": c.name,
        "u_value_W_m2K": c.u_value_W_m2K,
    }
    for cid, c in (self.constructions or {}).items()
},
            "heatloss": {
                "valid": self.heatloss_valid,
                "results": self.heatloss_results,
            },
            "hydronics": {
                "valid": self.hydronics_valid,
                "results": self.hydronics_results,
            },
        }

    # ==================================================================
    # Deserialization
    # ==================================================================
    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        if data.get("schema_version") not in (3, 4):
            raise ValueError("Unsupported project schema version")

        instance = cls(
            project_id=data["project_id"],
            name=data["name"],
        )

        if data.get("environment"):
            instance.environment = EnvironmentStateV1.from_dict(data["environment"])

        for room_id, room_data in (data.get("rooms", {}) or {}).items():
            instance.rooms[room_id] = RoomStateV1.from_dict(room_id, room_data)

        instance.boundary_segments = {
            seg_id: BoundarySegmentV1.from_dict(seg_data)
            for seg_id, seg_data in (data.get("boundary_segments", {}) or {}).items()
        }
        instance.surface_construction_map = {
            str(k): str(v)
            for k, v in (data.get("surface_construction_map", {}) or {}).items()
        }
        # --------------------------------------------------
        # Openings
        # --------------------------------------------------
        openings = data.get("openings", {}) or {}
        instance.openings_by_surface = {
            sid: list(open_list)
            for sid, open_list in openings.items()
        }

        hl = data.get("heatloss", {}) or {}
        instance.heatloss_valid = bool(hl.get("valid", False))
        instance.heatloss_results = hl.get("results")

        if instance.heatloss_valid:
            try:
                instance.mark_heatloss_valid()
            except Exception:
                instance.heatloss_valid = False

        # --------------------------------------------------
        # Hydronics (clean, no duplication, no hasattr)
        # --------------------------------------------------
        hyd = data.get("hydronics", {}) or {}
        instance.hydronics_valid = bool(hyd.get("valid", False))
        instance.hydronics_results = hyd.get("results")

        # --------------------------------------------------
        # Surface → Construction mapping (IMPORTANT)
        # --------------------------------------------------
        instance.surface_construction_map = {
            str(k): str(v)
            for k, v in (data.get("surface_construction_map", {}) or {}).items()
        }

        # --------------------------------------------------
        # Construction library
        # --------------------------------------------------
        raw_constructions = data.get("constructions", {}) or {}
        if raw_constructions:
            instance.constructions = {
                str(cid): ConstructionV1(
                    construction_id=str(cdata["construction_id"]),
                    name=str(cdata["name"]),
                    u_value_W_m2K=float(cdata["u_value_W_m2K"]),
                )
                for cid, cdata in raw_constructions.items()
            }
        else:
            old_lib = data.get("construction_library", {}) or {}
            instance.constructions = {
                str(cid): ConstructionV1(
                    construction_id=str(cid),
                    name=str(cid),
                    u_value_W_m2K=float(u),
                )
                for cid, u in old_lib.items()
            }

        return instance
    # ==================================================================
    # Openings helpers (Phase IV-D)
    # ==================================================================
    def get_openings_for_surface(self, surface_id: str) -> list[Any]:
        return list(self.openings_by_surface.get(surface_id, []))

    def set_openings_for_surface(
        self,
        surface_id: str,
        openings: list[Any],
    ) -> None:
        self.openings_by_surface[surface_id] = list(openings)

    def add_opening_to_surface(
        self,
        surface_id: str,
        opening: Any,
    ) -> None:
        self.openings_by_surface.setdefault(surface_id, []).append(opening)

    def remove_opening(self, opening_id: str) -> None:
        for surface_id, openings in self.openings_by_surface.items():
            self.openings_by_surface[surface_id] = [
                o for o in openings if getattr(o, "opening_id", None) != opening_id
            ]

    # ==================================================================
    # Topology helpers
    # ==================================================================
    def get_boundary_segments_for_room(self, room_id: str) -> list[BoundarySegmentV1]:
        return list(self.iter_boundary_segments_for_room(room_id))

    def iter_boundary_segments_for_room(self, room_id: str):
        for seg in self.boundary_segments.values():
            if seg.owner_room_id == room_id:
                yield seg

    def set_boundary_segments_for_room(
        self,
        room_id: str,
        segments: list[BoundarySegmentV1],
    ) -> None:
        to_delete = [
            seg_id
            for seg_id, seg in self.boundary_segments.items()
            if seg.owner_room_id == room_id
        ]

        for seg_id in to_delete:
            del self.boundary_segments[seg_id]

        for seg in segments:
            if seg.owner_room_id != room_id:
                raise ValueError(
                    f"Segment owner mismatch: expected {room_id}, got {seg.owner_room_id}"
                )

            self.boundary_segments[seg.segment_id] = seg

    def has_boundary_segments_for_room(self, room_id: str) -> bool:
        return any(
            seg.owner_room_id == room_id
            for seg in self.boundary_segments.values()
        )

    # ==================================================================
    # Authoritative totals reader
    # ==================================================================
    def get_room_heatloss_totals(
        self, room_id: str
    ) -> tuple[float | None, float | None, float | None]:
        if not self.heatloss_valid or not self.heatloss_results:
            return None, None, None

        result = self.heatloss_results.get("result")
        if result is None:
            return None, None, None

        for r in result.rooms:
            if r.room_id == room_id:
                return (
                    r.q_fabric_W,
                    r.q_ventilation_W,
                    r.q_total_W,
                )

        return None, None, None

    def add_room(self, room_id: str, name: str) -> None:
        from HVAC.core.room_state import RoomStateV1
        from HVAC.core.room_geometry import RoomGeometryV1

        self.rooms[room_id] = RoomStateV1(
            room_id=room_id,
            name=name,
            geometry=RoomGeometryV1(
                length_m=6.0,
                width_m=4.0,
                height_m=2.4,
            ),
        )

        self.mark_heatloss_dirty()

class EmitterV1:
    emitter_id: str
    room_id: str
    design_output_W: float