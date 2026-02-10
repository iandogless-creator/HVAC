# ======================================================================
# HVAC/hydronics/run/hydronics_run_result_v1.py
# ======================================================================

"""
HVACgooee — Hydronics Run Result v1
----------------------------------

Authoritative output of a hydronics calculation run.
Consumed by DTO adapters only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from HVAC.hydronics.pipes.dp.pressure_drop_path_v1 import PressureDropPathV1
from HVAC.hydronics.pumps.dto.pump_duty_point_v1 import PumpDutyPointV1
from HVAC.hydronics.balancing.models.balancing_v1 import BalancingSummaryV1
from HVAC.hydronics.dto.topology_snapshot_dto import TopologySnapshotDTO



@dataclass(frozen=True, slots=True)
class HydronicsRunResultV1:
    """
    Immutable hydronics run output.
    """
    pressure_drop_paths: Dict[str, PressureDropPathV1]
    pump_result: PumpDutyPointV1
    balancing: Optional[BalancingSummaryV1]

    # NEW — authoritative topology snapshot (structure only)
    topology_snapshot: TopologySnapshotDTO
