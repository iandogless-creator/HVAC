# ======================================================================
# HVAC/project/project_state.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.project_v3.dto.heatloss_readiness import HeatLossReadiness
from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1
from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1

# ======================================================================
# ProjectState
# ======================================================================

@dataclass(slots=True)
class ProjectState:
    project_id: str
    name: str

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------
    rooms: Dict[str, RoomStateV1] = field(default_factory=dict)
    environment: Optional[EnvironmentStateV1] = None
    boundary_segments: Dict[str, list[BoundarySegmentV1]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # v1 Construction library (minimal, stable)
    # construction_id -> u_value_W_m2K
    # ------------------------------------------------------------------
    construction_library: Dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    heatloss_results: Optional[dict[str, Any]] = None
    heatloss_valid: bool = False

    hydronics_results: Optional[dict[str, Any]] = None
    hydronics_valid: bool = False

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

        required = {"result", "fabric", "ventilation"}
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
                # Geometry / space
                # --------------------------------------------------
                space = room.space
                if space is None:
                    reasons.append(f"Room '{room_id}' has no space")
                    continue

                area = space.floor_area_m2()
                if area is None or float(area) <= 0.0:
                    reasons.append(f"Room '{room_id}' has invalid floor area")

                height_m, _ = resolve_effective_height_m(self, room)
                if height_m is None or float(height_m) <= 0.0:
                    reasons.append(f"Room '{room_id}' has no valid height")

                ach, _ = resolve_effective_ach(self, room)
                if ach is None or float(ach) <= 0.0:
                    reasons.append(f"Room '{room_id}' has no valid ACH")

                # --------------------------------------------------
                # Fabric via topology -> segments -> rows
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

                    u = self.construction_library.get(str(cid))
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
            "schema_version": 3,
            "project_id": self.project_id,
            "name": self.name,
            "environment": self.environment.to_dict() if self.environment else None,
            "rooms": {rid: room.to_dict() for rid, room in self.rooms.items()},
            "boundary_segments": {
                seg_id: seg.to_dict()
                for seg_id, seg in self.boundary_segments.items()
            },
            "construction_library": {
                cid: float(u) for cid, u in (self.construction_library or {}).items()
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
        if data.get("schema_version") != 3:
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

        lib = data.get("construction_library", {}) or {}
        instance.construction_library = {str(k): float(v) for k, v in lib.items()}

        hl = data.get("heatloss", {}) or {}
        instance.heatloss_valid = bool(hl.get("valid", False))
        instance.heatloss_results = hl.get("results")

        if instance.heatloss_valid:
            try:
                instance.mark_heatloss_valid()
            except Exception:
                instance.heatloss_valid = False

        hyd = data.get("hydronics", {}) or {}
        instance.hydronics_valid = bool(hyd.get("valid", False))
        instance.hydronics_results = hyd.get("results")

        return instance

    # inside ProjectState

    # ------------------------------------------------------------------
    # Boundary Segments (Topology — Phase IV)
    # ------------------------------------------------------------------

    def get_boundary_segments_for_room(
            self,
            room_id: str,
    ) -> list[BoundarySegmentV1]:
        return list(self.iter_boundary_segments_for_room(room_id))

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

    # ==================================================================
    # Topology / adjacency (Phase IV-A)
    # ==================================================================
    def iter_boundary_segments_for_room(self, room_id: str):
        for seg in self.boundary_segments.values():
            if seg.owner_room_id == room_id:
                yield seg

    def set_boundary_segments_for_room(
            self,
            room_id: str,
            segments: list[BoundarySegmentV1],
    ) -> None:
        # --------------------------------------------------
        # Remove existing segments for this room
        # --------------------------------------------------
        to_delete = [
            seg_id
            for seg_id, seg in self.boundary_segments.items()
            if seg.owner_room_id == room_id
        ]

        for seg_id in to_delete:
            del self.boundary_segments[seg_id]

        # --------------------------------------------------
        # Insert new segments (with validation)
        # --------------------------------------------------
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