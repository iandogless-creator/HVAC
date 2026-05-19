# ======================================================================
# HVAC/hydronics/proportioning/proportioning_schematic_dto_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


# ======================================================================
# Role constants
# ======================================================================

NODE_ROLE_HEAT_SOURCE = "HEAT_SOURCE"
NODE_ROLE_COMMON_MAIN = "COMMON_MAIN"
NODE_ROLE_SELECTED_INDEX_ROUTE = "SELECTED_INDEX_ROUTE"
NODE_ROLE_NON_INDEX_BRANCH_TERMINAL = "NON_INDEX_BRANCH_TERMINAL"
NODE_ROLE_NO_EMITTER_UNRESOLVED = "NO_EMITTER_UNRESOLVED"

EDGE_ROLE_COMMON_MAIN = "COMMON_MAIN"
EDGE_ROLE_SELECTED_INDEX_ROUTE = "SELECTED_INDEX_ROUTE"
EDGE_ROLE_NON_INDEX_BRANCH_TERMINAL = "NON_INDEX_BRANCH_TERMINAL"
EDGE_ROLE_UNRESOLVED = "NO_EMITTER_UNRESOLVED"


# ======================================================================
# DTOs
# ======================================================================

@dataclass(frozen=True, slots=True)
class ProportioningSchematicNodeV1:
    """
    Read-only proportioning schematic node.

    This is a logic/proportioning node, not a CAD coordinate.
    """

    node_id: str
    label: str
    role: str
    lane: int
    order: int
    status: str = ""


@dataclass(frozen=True, slots=True)
class ProportioningSchematicEdgeV1:
    """
    Read-only proportioning schematic edge.

    This represents flow/proportioning responsibility, not physical pipework.
    """

    edge_id: str
    from_node_id: str
    to_node_id: str
    role: str
    flow_label: str
    basis: str
    status: str


@dataclass(frozen=True, slots=True)
class ProportioningSchematicV1:
    """
    Read-only proportioning schematic projection.

    Authority
    ---------
    Display/projection only.

    It does not:
    • mutate ProjectState
    • size pipework
    • calculate pressure loss
    • select pumps
    • balance branches
    """

    nodes: tuple[ProportioningSchematicNodeV1, ...]
    edges: tuple[ProportioningSchematicEdgeV1, ...]
    title: str
    basis: str