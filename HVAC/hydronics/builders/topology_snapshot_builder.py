# ======================================================================
# HVAC/hydronics/builders/topology_snapshot_builder.py
# ======================================================================

"""
HVACgooee — Hydronics Topology Snapshot Builder

Extracts a pure structural snapshot from the resolved
hydronics domain model.

This is the ONLY place that adapts hydronics internals
to the TopologySnapshotDTO.
"""

from __future__ import annotations

from HVAC_legacy.hydronics.dto.topology_snapshot_dto import (
    TopologySnapshotDTO,
    TopologyNodeDTO,
    TopologyEdgeDTO,
)


class HydronicsTopologySnapshotBuilder:
    """
    Build a TopologySnapshotDTO from a resolved hydronics model.

    Rules
    -----
    • Read-only
    • No calculations
    • No mutation
    • Structure only
    """

    @staticmethod
    def build(network) -> TopologySnapshotDTO:
        """
        Build snapshot from hydronics network.

        Expected (example) network shape:
        - network.nodes
        - network.edges
        """

        nodes = tuple(
            TopologyNodeDTO(
                id=node.id,
                kind=node.kind,
            )
            for node in network.nodes
        )

        edges = tuple(
            TopologyEdgeDTO(
                from_node_id=edge.from_node_id,
                to_node_id=edge.to_node_id,
                direction=getattr(edge, "direction", None),
                classification=getattr(edge, "classification", None),
            )
            for edge in network.edges
        )

        return TopologySnapshotDTO(
            nodes=nodes,
            edges=edges,
        )
