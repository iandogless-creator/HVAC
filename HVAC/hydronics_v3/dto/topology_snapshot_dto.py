from dataclasses import dataclass
from typing import List, Literal

NodeKind = Literal[
    "plant",
    "pump",
    "emitter",
    "junction",
    "sensor",
]

EdgeDirection = Literal[
    "FLOW",
    "RETURN",
    "BIDIRECTIONAL",
]


@dataclass(frozen=True, slots=True)
class TopologyNodeDTO:
    id: str
    kind: NodeKind


@dataclass(frozen=True, slots=True)
class TopologyEdgeDTO:
    from_node_id: str
    to_node_id: str
    direction: EdgeDirection
    classification: str  # "primary", "branch", etc.


@dataclass(frozen=True, slots=True)
class TopologySnapshotDTO:
    nodes: List[TopologyNodeDTO]
    edges: List[TopologyEdgeDTO]
