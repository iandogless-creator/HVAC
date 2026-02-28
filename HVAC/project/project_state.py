# ======================================================================
# HVAC/project/project_state.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Iterable, Any

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.project_v3.dto.heatloss_readiness import HeatLossReadiness
from HVAC.heatloss.fabric.resolved_fabric_surface import ResolvedFabricSurface

@dataclass(slots=True)
class ProjectState:
    """
    Authoritative project container.

    Responsibilities (LOCKED)
    -------------------------
    • Owns authoritative project intent
    • Owns heat-loss results lifecycle
    • Tracks heat-loss validity explicitly
    • Performs NO calculations
    • Performs NO GUI logic
    """

    # ------------------------------------------------------------------
    # Core identity
    # ------------------------------------------------------------------
    project_id: str
    name: str

    # ------------------------------------------------------------------
    # Authoritative intent
    # ------------------------------------------------------------------
    rooms: Dict[str, RoomStateV1] = field(default_factory=dict)

    # Environment is injected by loader / GUI (not owned here)
    environment: Optional[EnvironmentStateV1] = None

    # ------------------------------------------------------------------
    # Heat-loss results lifecycle (Phase I-A → II-D)
    # ------------------------------------------------------------------
    # Canonical container: leave flexible until ResultDTO is introduced.
    # Expected shape (current):
    #   {"fabric": <engine-result-dict>}
    heatloss_results: Optional[dict] = None

    # Explicit validity flag (authoritative)
    heatloss_valid: bool = False

    # ------------------------------------------------------------------
    # Phase I-B — Explicit invalidation (CANONICAL)
    # ------------------------------------------------------------------
    def mark_heatloss_dirty(self) -> None:
        """
        Explicitly invalidate heat-loss results.

        • No calculation
        • No GUI effects
        • No side effects beyond flag mutation
        """
        self.heatloss_valid = False

    # ------------------------------------------------------------------
    # Phase II-D — Explicit validity marking (CANONICAL)
    # ------------------------------------------------------------------
    def mark_heatloss_valid(self) -> None:
        if not self.heatloss_results:
            raise RuntimeError("No heat-loss results present")

        required_keys = {"fabric", "ventilation", "room_totals"}

        missing = required_keys - set(self.heatloss_results.keys())
        if missing:
            raise RuntimeError(
                f"Heat-loss container incomplete. Missing keys: {sorted(missing)}"
            )

        self.heatloss_valid = True

    # ==================================================================
    # Phase I-C — Readiness evaluation (CANONICAL)
    # ==================================================================
    def evaluate_heatloss_readiness(self) -> HeatLossReadiness:
        """
        Explicit heat-loss execution readiness evaluation.

        Rules:
        • No side effects (no mutation)
        • No calculation
        • Always callable
        """
        reasons: list[str] = []

        # --------------------------------------------------
        # Environment
        # --------------------------------------------------
        env = self.environment
        if env is None:
            reasons.append("Environment not defined")
        elif getattr(env, "external_design_temperature", None) is None:
            reasons.append("External design temperature not set")

        # --------------------------------------------------
        # Rooms & declared space intent
        # --------------------------------------------------
        if not self.rooms:
            reasons.append("No rooms defined")
        else:
            for room_id, room in self.rooms.items():
                space = getattr(room, "space", None)
                if space is None:
                    reasons.append(f"Room '{room_id}' has no space")
                    continue

                if float(getattr(space, "floor_area_m2", 0.0) or 0.0) <= 0.0:
                    reasons.append(f"Room '{room_id}' has invalid floor area")

                if float(getattr(space, "height_m", 0.0) or 0.0) <= 0.0:
                    reasons.append(f"Room '{room_id}' has invalid height")

        # --------------------------------------------------
        # Fabric surfaces — U-value readiness (Phase II-A)
        # --------------------------------------------------
        for resolved in self.iter_fabric_surfaces():
            # ResolvedFabricSurface convention:
            #   resolved.surface  -> has name/surface_id
            #   resolved.u_value_W_m2K -> float|None
            u = getattr(resolved, "u_value_W_m2K", None)
            if u is None or float(u) <= 0.0:
                surface_obj = getattr(resolved, "surface", None)
                sid = (
                    getattr(surface_obj, "name", None)
                    or getattr(surface_obj, "surface_id", None)
                    or "unknown surface"
                )
                reasons.append(f"Surface '{sid}' has no valid U-value")

        return HeatLossReadiness(
            is_ready=(len(reasons) == 0),
            blocking_reasons=reasons,
        )

    # ==================================================================
    # Phase II-A — Fabric intent access (READ-ONLY)
    # ==================================================================
    def iter_fabric_surfaces(self) -> Iterable[ResolvedFabricSurface]:
        ...
        """
        Iterate over all fabric surfaces that participate in heat-loss.

        Canonical rules:
        • Read-only
        • No calculation
        • No validation
        • No GUI knowledge
        • Order-stable (room insertion order, then surface list order)
        """
        for _room_id, room in self.rooms.items():
            # Room may exist before surfaces are declared
            surfaces = getattr(room, "fabric_surfaces", None)
            if not surfaces:
                continue

            for resolved in surfaces:
                if resolved is None:
                    continue

                # Optional future hook:
                # if not getattr(resolved, "participates_in_heatloss", True):
                #     continue

                yield resolved

    # ------------------------------------------------------------------
    # Phase II-A/II-D — Fabric heat-loss results commit (authoritative)
    # ------------------------------------------------------------------
    def set_fabric_heatloss_result(self, result: dict) -> None:
        """
        Commit fabric heat-loss results (engine output).

        Rules:
        • Authoritative storage only
        • No calculation
        • No validation beyond None check
        • No GUI logic
        • Does NOT mark valid (separate call)
        """
        if result is None:
            raise RuntimeError("set_fabric_heatloss_result: result is None")

        # Replace fabric payload atomically (dict container is temporary)
        self.heatloss_results = {"fabric": result}

        # New results are not considered valid until explicitly marked.
        self.heatloss_valid = False