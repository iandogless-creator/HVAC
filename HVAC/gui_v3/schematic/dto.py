# ======================================================================
# HVAC/gui_v3/schematic/dto.py
# ======================================================================

"""
HVACgooee — GUI v3
Hydronics Schematic DTOs — Phase C / D / E

Defines the maximum information allowed to cross from
authoritative hydronics state into the GUI schematic.

• No physics
• No behaviour
• No ProjectState access
• Read-only by convention
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal


# ----------------------------------------------------------------------
# Type aliases
# ----------------------------------------------------------------------

NodeRole = Literal[
    "PLANT",
    "PUMP",
    "DISTRIBUTOR",
    "EMITTER",
    "JUNCTION",
    "SENSOR",
]

EdgeDirection = Literal[
    "FLOW",
    "RETURN",
    "BIDIRECTIONAL",
]

EdgeStyle = Literal[
    "PRIMARY",
    "SECONDARY",
    "BRANCH",
    "SERVICE",
]

# ----------------------------------------------------------------------
# Phase E — Visual shape hint (GUI-only)
# ----------------------------------------------------------------------

NodeShape = Literal[
    "CIRCLE",
    "RECT",
    "OBLONG",
    "TRIANGLE",
]


# ----------------------------------------------------------------------
# Hover Payload DTOs (Phase D)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NodeHoverDTO:
    title: str

    qf_w: float | None
    qt_w: float | None

    flow_kg_s: float | None
    target_cv: float | None


@dataclass(frozen=True, slots=True)
class EdgeHoverDTO:
    pipe_ref: str

    size_mm: float | None
    length_m: float | None
    material: str | None

    flow_kg_s: float | None
    velocity_m_s: float | None
    dp_pa: float | None


# ----------------------------------------------------------------------
# Topology DTOs (Phase C + D + E)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SchematicNodeDTO:
    id: str
    x: float
    y: float
    role: NodeRole

    # Phase E — visual hints (GUI-only)
    shape: Literal["CIRCLE", "RECT", "OBLONG", "TRIANGLE"] = "CIRCLE"
    orientation_deg: float | None = None

    # Phase D — hover payload
    hover: NodeHoverDTO | None = None





@dataclass(frozen=True, slots=True)
class SchematicEdgeDTO:
    from_node_id: str
    to_node_id: str
    direction: EdgeDirection
    style: EdgeStyle

    # Phase D: optional hover payload
    hover: EdgeHoverDTO | None = None


@dataclass(frozen=True, slots=True)
class SchematicLabelDTO:
    x: float
    y: float
    text: str


# ----------------------------------------------------------------------
# Root DTO (Phase C / D / E)
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HydronicsSchematicDTO:
    nodes: List[SchematicNodeDTO]
    edges: List[SchematicEdgeDTO]
    annotations: List[SchematicLabelDTO]
