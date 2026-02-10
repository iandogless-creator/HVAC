from HVAC.hydronics.committed.committed_hydronic_leg import CommittedHydronicLeg
from HVAC.hydronics.pipes.dto.sized_pipe_segment_v1 import SizedPipeSegmentV1
from HVAC.hydronics.pipes.dp.pressure_drop_aggregator_v1 import aggregate_pressure_drop_v1
from HVAC.hydronics.physics.fittings_k_library_v1 import (
    get_fitting_k_value,
)

from HVAC.hydronics.committed.committed_pipe_segment_v1 import (
    CommittedPipeSegmentV1,
)
from HVAC.hydronics.committed.committed_leg_geometry_v1 import (
    CommittedLegGeometryV1,
)

from HVAC.hydronics.pumps.pump_selection_integration_v1 import (
    select_pump_from_hydronics_v1,
)

# ------------------------------------------------------------
# 1) Fake committed leg (single leg test)
# ------------------------------------------------------------
leg = CommittedHydronicLeg(
    leg_id="L1",
    leg_name="Test Main Leg",
    parent_leg_id=None,
    depth_from_source=0,
    design_flow_lps=0.025,      # ≈ 2000 W @ ΔT=20K
    design_heat_w=2000.0,
    nominal_length_m=20.0,
    is_index_leg=True,
)

geometry = CommittedLegGeometryV1(
    leg_id="L1",
    segments=[
        # Pipe run (first half)
        CommittedPipeSegmentV1(
            segment_id="L1-P1",
            leg_id="L1",
            kind="pipe",
            length_m=10.0,
        ),

        # Swept bend (90°)
        CommittedPipeSegmentV1(
            segment_id="L1-B1",
            leg_id="L1",
            kind="fitting",
            k_value=get_fitting_k_value("BEND_90_SWEPT"),
            label="90° swept bend",
        ),

        # Pipe run (second half)
        CommittedPipeSegmentV1(
            segment_id="L1-P2",
            leg_id="L1",
            kind="pipe",
            length_m=10.0,
        ),
    ],
)

# ------------------------------------------------------------
# 2) Fake sizing result (Pa/m)
# (for first test, hard-code this)
# ------------------------------------------------------------
sized_seg = SizedPipeSegmentV1(
    segment_id="SEG_L1",
    leg_id="L1",

    nominal_diameter_mm=15.0,
    internal_diameter_mm=13.6,

    velocity_m_s=0.6,
    reynolds_number=15000.0,

    friction_factor=0.028,
    pressure_drop_Pa_per_m=120.0,

    sizing_method="test_stub",
)


# ------------------------------------------------------------
# 3) Path definition
# ------------------------------------------------------------
paths = {
    "path_1": ["L1"],
}

# ------------------------------------------------------------
# 4) Aggregate ΔP
# ------------------------------------------------------------
dp_paths = aggregate_pressure_drop_v1(
    sized_segments=[sized_seg],
    committed_legs=[leg],
    paths=paths,
)

print("ΔP paths:")
for p in dp_paths:
    print(p)

# ------------------------------------------------------------
# 5) Pump sizing
# ------------------------------------------------------------
# Example: 0.025 L/s ≈ 2.5e-5 m³/s
design_flow_m3_s = 2.5e-5

pump = select_pump_from_hydronics_v1(
    pressure_paths=dp_paths,
    design_flow_m3_s=design_flow_m3_s,
)

print("\nSelected pump:")
print(pump)
