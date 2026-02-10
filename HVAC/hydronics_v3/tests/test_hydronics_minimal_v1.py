# ======================================================================
# HVAC/hydronics_v3/tests/test_hydronics_minimal_v1.py
# ======================================================================

"""
Minimal hydronics v3 tests.

Purpose
-------
Prove that:
• HydronicLeg structural rules are valid
• HydronicTopologyDTO validates correctly
• Index path engine can operate on the simplest topology

NO physics.
NO pressure drop.
NO sizing.
"""

from HVAC.hydronics_v3.models.hydronic_leg import HydronicLeg
from HVAC.hydronics_v3.dto.hydronic_topology_dto import HydronicTopologyDTO
from HVAC.hydronics_v3.engines.hydronic_index_path_engine_v1 import (
    HydronicIndexPathEngineV1,
)


# ----------------------------------------------------------------------
# Test: single leg system
# ----------------------------------------------------------------------
def test_minimal_single_leg_index_path() -> None:
    """
    Expected:
    • One leg
    • That leg is the index path
    """

    # -------------------------------------------------
    # Build minimal topology (ONE leg, ONE room)
    # -------------------------------------------------
    boiler_leg = HydronicLeg(
        leg_id="L1",
        design_qt_w=1000.0,
        pipe_segments=[],
        parent_leg_id=None,
        child_legs=[],
        room_names=["Room-1"],
    )

    topology = HydronicTopologyDTO(
        system_id="TEST-SYSTEM-1",
        legs={"L1": boiler_leg},
        boiler_leg_ids=["L1"],
    )

    # -------------------------------------------------
    # Structural validation MUST pass
    # -------------------------------------------------
    topology.validate()

    # -------------------------------------------------
    # Run index-path engine
    # -------------------------------------------------
    result = HydronicIndexPathEngineV1.run(topology)

    # -------------------------------------------------
    # Assertions (minimal + strict)
    # -------------------------------------------------
    assert result is not None
    assert result.index_leg_id == "L1"
    assert result.index_path_leg_ids == ["L1"]
    assert result.total_index_length_m == 0.0


# ----------------------------------------------------------------------
# Test: simple branch (boiler → leaf)
# ----------------------------------------------------------------------
def test_two_leg_chain_index_path() -> None:
    """
    Boiler leg feeding one leaf leg.

    Expected:
    • Index path = boiler → leaf
    """

    leaf_leg = HydronicLeg(
        leg_id="L2",
        design_qt_w=500.0,
        pipe_segments=[],
        parent_leg_id="L1",
        child_legs=[],
        room_names=["Room-2"],
    )

    boiler_leg = HydronicLeg(
        leg_id="L1",
        design_qt_w=500.0,
        pipe_segments=[],
        parent_leg_id=None,
        child_legs=[leaf_leg],
        room_names=[],
    )

    topology = HydronicTopologyDTO(
        system_id="TEST-SYSTEM-2",
        legs={
            "L1": boiler_leg,
            "L2": leaf_leg,
        },
        boiler_leg_ids=["L1"],
    )

    topology.validate()

    result = HydronicIndexPathEngineV1.run(topology)

    assert result.index_leg_id == "L2"
    assert result.index_path_leg_ids == ["L1", "L2"]
