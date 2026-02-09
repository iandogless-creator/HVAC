# ======================================================================
# HVAC/hydronics/run/hydronics_runner_v1.py
# ======================================================================
# ------------------------------------------------------------
# 3) Optional balancing (DISABLED in v1 runner)
# ------------------------------------------------------------
balancing = None
"""
from HVAC.hydronics.balancing.extractors.valve_hydraulics_v1 import (
    extract_valve_hydraulics_v1,
)

from HVAC.hydronics.balancing.runners.lockshield_balancer_v1 import (
    balance_lockshield_presets_v1,
)

from HVAC.hydronics.balancing.library.default_lockshield_library_v1 import (
    build_default_lockshield_library_v1,
)


HVACgooee — Hydronics Runner v1
------------------------------

Single orchestration entry point for hydronics calculations.

Order:
1. Pressure drop aggregation
2. Pump duty resolution
3. (Optional) balancing

NO GUI
NO Qt
NO mutation
"""

"""
from __future__ import annotations

from typing import Dict

from HVAC.hydronics.run.hydronics_run_config_v1 import HydronicsRunConfigV1
from HVAC.hydronics.run.hydronics_run_result_v1 import HydronicsRunResultV1

# ------------------------------------------------------------------
# Pressure drop aggregation (v1)
# ------------------------------------------------------------------
from HVAC.hydronics.pipes.dp.pressure_drop_aggregator_v1 import (
    aggregate_pressure_drop_v1,
)

# ------------------------------------------------------------------
# Pump duty resolution (v1)
# ------------------------------------------------------------------
from HVAC.hydronics.pumps.pump_duty_resolver_v1 import (
    resolve_pump_duty_v1,
)

# ------------------------------------------------------------------
# Optional balancing (v1) — MODEL ONLY
# ------------------------------------------------------------------
from HVAC.hydronics.balancing.models.balancing_v1 import (
    BalancingSummaryV1,
)

from HVAC.hydronics.builders.topology_snapshot_builder import (
    HydronicsTopologySnapshotBuilder,
)

def run_hydronics_v1(
    *,
    committed_legs,
    committed_geometries,
    sized_pipe_segments,
    topology_paths,
    config: HydronicsRunConfigV1,
) -> HydronicsRunResultV1:

    Execute a full hydronics calculation run.


    # ------------------------------------------------------------
    # 1) Pressure drop aggregation
    # ------------------------------------------------------------
    pressure_drop_paths = aggregate_pressure_drop_v1(
        committed_legs=committed_legs,
        committed_geometries=committed_geometries,
        sized_pipe_segments=sized_pipe_segments,
        paths=topology_paths,
    )

    # ------------------------------------------------------------
    # 2) Pump duty resolution
    # ------------------------------------------------------------
    pump_result = resolve_pump_duty_v1(
        pressure_drop_paths=pressure_drop_paths,
        safety_factor=config.pump_safety_factor,
    )

    # ------------------------------------------------------------
    # 3) Optional balancing
    # ------------------------------------------------------------
    balancing = None

    if config.include_balancing:
        dp_by_terminal = {
            k: v.total_dp_pa for k, v in pressure_drop_paths.items()
        }

        valve_hydraulics = extract_valve_hydraulics_v1(
            terminal_leg_geometries=committed_geometries,
            sized_pipe_segments=sized_pipe_segments,
        )

        balancing = balance_lockshield_presets_v1(
            dp_by_terminal_pa=dp_by_terminal,
            valve_hydraulics_by_terminal=valve_hydraulics,
            library=build_default_lockshield_library_v1(),
        )

    return HydronicsRunResultV1(
        pressure_drop_paths=pressure_drop_paths,
        pump_result=pump_result,
        balancing=balancing,
    )
"""