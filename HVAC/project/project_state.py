# ======================================================================
# HVAC/project/project_state.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from HVAC.project_v3.dto.project_surface_defaults_dto import (
    ProjectSurfaceDefaultsDTO,
)
from HVAC.project_v3.dto.surface_intent_dto import SurfaceIntentDTO
from HVAC.project_v3.dto.room_geometry_dto import RoomGeometryDTO

@dataclass
class ProjectState:
    """
    Authoritative in-memory representation of an HVACgooee project.

    Rules
    -----
    • Owns deserialization
    • Accepts partial / incomplete projects
    • Performs NO calculations
    • Performs NO validation beyond structural sanity
    """

    # ------------------------------------------------------------------
    # Core identity (REQUIRED)
    # ------------------------------------------------------------------
    project_id: str
    name: str

    # ------------------------------------------------------------------
    # Optional metadata
    # ------------------------------------------------------------------
    reference: Optional[str] = None
    revision: Optional[str] = None

    # ------------------------------------------------------------------
    # Intent containers (may be empty)
    # ------------------------------------------------------------------
    environment: Dict[str, Any] = field(default_factory=dict)
    rooms: Dict[str, Any] = field(default_factory=dict)
    constructions: Dict[str, Any] = field(default_factory=dict)
    emitters: Dict[str, Any] = field(default_factory=dict)
    hydronics: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # v3 Intent (geometry + surface defaults)
    # ------------------------------------------------------------------
    surface_defaults: ProjectSurfaceDefaultsDTO = field(
        default_factory=ProjectSurfaceDefaultsDTO
    )

    # ------------------------------------------------------------------
    # Results (authoritative, populated only after run)
    # ------------------------------------------------------------------
    heatloss_results: Optional[Dict[str, Any]] = None
    hydronics_results: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Lifecycle flags
    # ------------------------------------------------------------------
    heatloss_status: str = "not_run"
    hydronics_status: str = "not_run"

    # ==================================================================
    # Deserialization (CANONICAL ENTRY POINT)
    # ==================================================================
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> ProjectState:
        """
        Construct ProjectState from a persisted project dictionary.

        This method:
        • Accepts partial projects
        • Normalises missing sections
        • Performs NO calculations
        • Performs NO run-readiness validation
        """

        if "project" not in payload:
            raise ValueError("Invalid project: missing 'project' section")

        project_meta = payload["project"]

        try:
            project_id = project_meta["id"]
            name = project_meta["name"]
        except KeyError as exc:
            raise ValueError(
                "Invalid project: 'project.id' and 'project.name' are required"
            ) from exc

        return cls(
            project_id=project_id,
            name=name,
            reference=project_meta.get("reference"),
            revision=project_meta.get("revision"),

            environment=payload.get("environment", {}),
            rooms=payload.get("rooms", {}),
            constructions=payload.get("constructions", {}),
            emitters=payload.get("emitters", {}),
            hydronics=payload.get("hydronics", {}),

            heatloss_results=payload.get("heatloss_results"),
            hydronics_results=payload.get("hydronics_results"),

            heatloss_status=payload.get("heatloss_status", "not_run"),
            hydronics_status=payload.get("hydronics_status", "not_run"),
        )

    # ------------------------------------------------------------------
    # Room creation helpers (v3 intent)
    # ------------------------------------------------------------------
    def _instantiate_surfaces_from_defaults(self) -> Dict[str, SurfaceIntentDTO]:
        """
        Create surface intents using project-level defaults.
        Geometry is empty; intent only.
        """
        d = self.surface_defaults

        def surf(element: str, cid: Optional[str]) -> SurfaceIntentDTO:
            return SurfaceIntentDTO(
                element_class=element,
                construction_id=cid,
            )

        return {
            "external_wall": surf("external_wall", d.external_wall),
            "internal_wall": surf("internal_wall", d.internal_wall),
            "floor": surf("floor", d.floor),
            "ceiling": surf("ceiling", d.ceiling),
            "roof": surf("roof", d.roof),
            "window": surf("window", d.window),
            "door": surf("door", d.door),
        }

    # ------------------------------------------------------------------
    # Room creation (v3 intent)
    # ------------------------------------------------------------------
    def create_room_v3(self, room_id: str) -> None:
        """
        Create a new room with default surface intent.

        Rules:
        • Intent assembly only
        • No validation
        • No calculations
        • Safe to call multiple times with different IDs
        """

        if room_id in self.rooms:
            raise ValueError(f"Room '{room_id}' already exists")

        # Instantiate default surface intents
        surfaces = self._instantiate_surfaces_from_defaults()

        # Minimal room intent container
        self.rooms[room_id] = {
            "surfaces": surfaces,
        }


