# HVAC/dev/bootstrap_registry.py

from typing import Callable, Dict
from HVAC.project.project_state import ProjectState

from HVAC.dev.bootstrap_project_state import make_dev_bootstrap_project_state
from HVAC.dev.bootstrap_vertical_3room import build_vertical_stack_project_state

BootstrapFn = Callable[[], ProjectState]

BOOTSTRAPS: Dict[str, BootstrapFn] = {
    "simple": make_dev_bootstrap_project_state,
    "vertical_stack": build_vertical_stack_project_state,
}