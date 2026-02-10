# HVAC/orchestration/headless_runner_v1.py

from HVAC.constructions.runner_v1 import resolve_constructions_v1
from HVAC.heatloss_v3.heatloss_runner_v3 import HeatLossRunnerV3


class HeadlessRunnerV1:
    def __init__(self, project):
        self.project = project

    # ------------------------------------------------------------------
    # Constructions
    # ------------------------------------------------------------------

    def resolve_constructions(self) -> None:
        assert self.project is not None

        # Resolve intent → DTOs (domain step)
        resolve_constructions_v1(self.project)

        # Commit into ProjectState (authority step)
        self.project.project_state.constructions.results = {
            dto.surface_class: dto
            for dto in self.project.constructions.results
        }
        self.project.project_state.constructions.valid = True

    # ------------------------------------------------------------------
    # Heat-loss
    # ------------------------------------------------------------------

    def run_heatloss(self) -> float:
        """
        Runs authoritative heat-loss and commits results to the project.

        Returns:
            Qt (float, W)
        """
        assert self.project is not None

        # Preconditions (hard gate)
        if not self.project.project_state.constructions:
            raise RuntimeError("Constructions not resolved")

        qt_w = HeatLossRunnerV3.run_authoritative_qt(self.project)

        # Commit (this is where authority is set)
        self.project.heatloss.qt_w = qt_w
        self.project.heatloss.valid = True

        return qt_w
