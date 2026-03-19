"""
Project Gooee — Domain Model
----------------------------
# ⚠️ FROZEN — DO NOT EXTEND

Role:
• Defines the declarative structure of an HVACgooee project
• Carries project intent only (no results)

Rules:
• No calculations
• No file IO
• No GUI imports
• No ProjectState usage
• No defaults or inference

This module is part of the Project Gooee persistence layer.
"""


from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

from HVAC.spaces.space_types import Space


# ======================================================================
# PROJECT CLASS (v1)
# ======================================================================
@dataclass
class Project:
    """
    HVACgooee Project (v1 stable definition)

    Mandatory:
        name: str
        spaces: List[Space]

    Optional v1 fields:
        default_design_temp_C: float
        default_tei_C: float
        metadata: Dict[str, Any]
        hydronics_payload: Any
        fenestration_payload: Any
    """

    name: str = "Untitled Project"

    # Core spatial definition
    spaces: List[Space] = field(default_factory=list)

    # Default design temperatures
    default_design_temp_C: float = 21.0      # T_i
    default_tei_C: float = 19.0              # legacy TEI for t_ai overlay (optional)

    # Optional metadata bucket (user, project notes, timestamps etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional “attach points” for other engines
    hydronics_payload: Any = None
    fenestration_payload: Any = None

    # ==================================================================
    # Utility Methods
    # ==================================================================
    def add_space(self, space: Space) -> None:
        """Append a new space to the project."""
        self.spaces.append(space)

    def remove_space(self, name: str) -> None:
        """Remove a space by name (safe if it doesn't exist)."""
        self.spaces = [s for s in self.spaces if s.name != name]

    def get_space(self, name: str) -> Optional[Space]:
        """Retrieve a space by name."""
        for s in self.spaces:
            if s.name == name:
                return s
        return None

    def list_space_names(self) -> List[str]:
        return [s.name for s in self.spaces]

    # ==================================================================
    # SERIALIZATION (v1 stable)
    # ==================================================================
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a serializable dictionary suitable for
        saving via project_io. Spaces provide their own to_dict().
        """
        return {
            "name": self.name,
            "default_design_temp_C": self.default_design_temp_C,
            "default_tei_C": self.default_tei_C,
            "metadata": self.metadata,
            "spaces": [s.to_dict() for s in self.spaces],
            "hydronics_payload": self.hydronics_payload,      # may be further structured later
            "fenestration_payload": self.fenestration_payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Project:
        """
        Create a Project from a dictionary previously produced by to_dict().
        Safely ignores unknown keys.
        """
        name = data.get("name", "Unnamed Project")
        default_design_temp_C = data.get("default_design_temp_C", 21.0)
        default_tei_C = data.get("default_tei_C", 19.0)
        metadata = data.get("metadata", {})

        # Construct spaces
        spaces_data = data.get("spaces", [])
        spaces: List[Space] = []
        for sd in spaces_data:
            try:
                spaces.append(Space.from_dict(sd))
            except Exception:
                # fail-safe: skip badly formatted space entries
                continue

        proj = cls(
            name=name,
            spaces=spaces,
            default_design_temp_C=default_design_temp_C,
            default_tei_C=default_tei_C,
            metadata=metadata,
        )

        # Optional payloads
        proj.hydronics_payload = data.get("hydronics_payload", None)
        proj.fenestration_payload = data.get("fenestration_payload", None)

        return proj

    # ==================================================================
    # Pretty-print helpers
    # ==================================================================
    def summary(self) -> str:
        """
        Human-readable summary (helpful in debugging).
        """
        return (
            f"Project: {self.name}\n"
            f"  Spaces: {len(self.spaces)}\n"
            f"  Default T_i: {self.default_design_temp_C} °C\n"
            f"  Default TEI: {self.default_tei_C} °C\n"
            f"  Metadata keys: {list(self.metadata.keys())}\n"
        )
