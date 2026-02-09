# ======================================================================
# HVACgooee — Project State
# Phase: D.2 — Authoritative State & Commit Semantics
# Status: ACTIVE
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# NOTE:
# RoomStateV1 is referenced as a forward type only.
# Import here only if already stable and lightweight.
from HVAC_legacy.project.room_state_v1 import RoomStateV1
from HVAC_legacy.project_v3.models.capability_intent import CapabilityIntent

# ----------------------------------------------------------------------
# Heat-Loss State (v1)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class HeatLossStateV1:
    """
    Authoritative committed heat-loss results (v1).

    Owned by ProjectState.
    Mutated only by controllers.
    Read by adapters and diagnostics.

    No calculations occur here.
    """

    # Per-room committed results
    room_results: Dict[str, float] = field(default_factory=dict)

    # Optional project aggregate
    project_qt_w: Optional[float] = None

    # Aggregate validity
    project_valid: bool = False

    # --------------------------------------------------
    # Commit API (Phase D.2)
    # --------------------------------------------------

    def commit_room_result(self, *, room_id: str, qt_w: float) -> None:
        """
        Commit heat-loss result for a single room.

        Effects:
        • Overwrites this room's result
        • Marks project aggregate as stale
        """
        self.room_results[room_id] = qt_w
        self.project_valid = False

    def commit_project_results(
        self,
        *,
        room_results: Dict[str, float],
        project_qt_w: Optional[float] = None,
    ) -> None:
        """
        Commit authoritative project-wide heat-loss results.

        Effects:
        • Replaces all room results
        • Commits project aggregate (if supplied)
        • Clears project stale state
        """
        self.room_results = dict(room_results)
        self.project_qt_w = project_qt_w
        self.project_valid = project_qt_w is not None

    def mark_project_stale(self) -> None:
        """Explicitly mark project aggregate as invalid."""
        self.project_valid = False

    # --------------------------------------------------
    # Read-only helpers
    # --------------------------------------------------

    def get_room_result(self, room_id: str) -> Optional[float]:
        return self.room_results.get(room_id)

    def get_project_result(self) -> Optional[float]:
        return self.project_qt_w

    def is_project_stale(self) -> bool:
        return not self.project_valid

# ----------------------------------------------------------------------
# Environment State (v1)
# ----------------------------------------------------------------------

@dataclass(slots=True)
class EnvironmentStateV1:
    """
    Authoritative environment inputs (v1).

    Owned by ProjectState.
    Mutated by factories / controllers.
    Read by GUI adapters.

    No calculations occur here.
    """

    outside_temperature_c: Optional[float] = None
    method: Optional[str] = None

# ----------------------------------------------------------------------
# ProjectState (authoritative root)
# ----------------------------------------------------------------------

@dataclass
class ProjectState:
    project_id: str
    name: str

    # Rooms (authoritative intent)
    rooms: Dict[str, RoomStateV1] = field(default_factory=dict)
    active_room_id: Optional[str] = None

    # Environment (authoritative intent)
    environment: EnvironmentStateV1 = field(default_factory=EnvironmentStateV1)

    # Heat-loss (authoritative results)
    heatloss: HeatLossStateV1 = field(default_factory=HeatLossStateV1)

    # existing fields continue unchanged
