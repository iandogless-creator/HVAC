# HVAC/hydronics/tests/build_test_topology_snapshot.py

from HVAC.hydronics_v3.dto.topology_snapshot_dto import (
    TopologySnapshotDTO,
    TopologyNodeDTO,
    TopologyEdgeDTO,
)

def build_test_snapshot() -> TopologySnapshotDTO:
    return TopologySnapshotDTO(
        nodes=[
            TopologyNodeDTO(id="Boiler", kind="plant"),
            TopologyNodeDTO(id="Pump-1", kind="pump"),
            TopologyNodeDTO(id="Rad-101", kind="emitter"),
        ],
        edges=[
            TopologyEdgeDTO(
                from_node_id="Boiler",
                to_node_id="Pump-1",
                direction="FLOW",
                classification="primary",
            ),
            TopologyEdgeDTO(
                from_node_id="Pump-1",
                to_node_id="Rad-101",
                direction="FLOW",
                classification="branch",
            ),
        ],
    )
