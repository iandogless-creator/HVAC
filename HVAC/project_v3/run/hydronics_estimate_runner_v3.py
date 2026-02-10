# ======================================================================
# HVAC/project_v3/run/hydronics_estimate_runner_v3.py
# ======================================================================

from __future__ import annotations

from HVAC.project.project_state import ProjectState
from HVAC.hydronics_v3.dto.hydronics_estimate_input_dto import (
    HydronicsEstimateInputDTO,
)
from HVAC.hydronics_v3.dto.hydronics_estimate_result_dto import (
    HydronicsEstimateResultDTO,
)
from HVAC.hydronics_v3.enums.hydronic_system_type import (
    HydronicSystemType,
)
from HVAC.hydronics_v3.engines.hydronics_estimate_engine_v3 import (
    HydronicsEstimateEngineV3,
)


class HydronicsEstimateRunnerV3:
    """
    Canonical hydronics estimate runner (v3).

    RULES (LOCKED)
    --------------
    • No GUI imports
    • No Qt
    • Single authoritative commit point
    """

    @staticmethod
    def run(project) -> HydronicsEstimateResultDTO:
        """
        Execute hydronics estimate and commit result.

        Consumes:
            • ProjectState.heatloss_qt_w (committed)

        Produces:
            • ProjectState.hydronics_estimate_result
            • ProjectState.hydronics_valid = True
        """

        project_state: ProjectState = project.project_state

        # --------------------------------------------------
        # Preconditions (LOCKED)
        # --------------------------------------------------
        if not project_state.heatloss_valid:
            raise RuntimeError(
                "Hydronics estimate requested without committed heat-loss."
            )

        if project_state.heatloss_qt_w is None:
            raise RuntimeError(
                "Committed heat-loss Qt is missing."
            )

        # --------------------------------------------------
        # Build intent DTO (v3 defaults)
        # --------------------------------------------------
        intent = HydronicsEstimateInputDTO(
            design_heat_load_w=project_state.heatloss_qt_w,
            flow_temp_c=75.0,
            return_temp_c=65.0,
            system_type=HydronicSystemType.RADIATORS,
            include_balancing=False,
        )

        # --------------------------------------------------
        # Run engine (PURE)
        # --------------------------------------------------
        result = HydronicsEstimateEngineV3.run(intent)

        # --------------------------------------------------
        # Commit (SINGLE AUTHORITY)
        # --------------------------------------------------
        project_state.commit_hydronics_estimate(result)

        return result
