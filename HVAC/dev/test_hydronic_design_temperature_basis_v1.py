# ======================================================================
# HVAC/dev/test_hydronic_design_temperature_basis_v1.py
# H-S23-A — Shared hydronic design-temperature basis helper test
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.design_conditions.hydronic_design_temperature_basis_v1 import (
    resolve_hydronic_design_temperature_basis_v1,
)
from HVAC.project.project_state import ProjectState


def _project_with_environment(
    *,
    flow_temp_c,
    return_temp_c,
) -> ProjectState:
    project = ProjectState(
        project_id="dev-hs23a-temperature-basis",
        name="DEV H-S23-A Temperature Basis",
    )

    project.environment = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        default_room_height_m=2.4,
        default_ach=0.5,
        design_flow_temp_c=flow_temp_c,
        design_return_temp_c=return_temp_c,
    )

    return project


def main() -> None:
    valid_project = _project_with_environment(
        flow_temp_c=75.0,
        return_temp_c=65.0,
    )

    basis = resolve_hydronic_design_temperature_basis_v1(valid_project)

    print()
    print("H-S23-A — Hydronic design-temperature basis")
    print("===========================================")
    print(f"flow_temp_c  = {basis.flow_temp_c}")
    print(f"return_temp_c = {basis.return_temp_c}")
    print(f"delta_t_k    = {basis.delta_t_k}")
    print(f"source       = {basis.source}")
    print(f"status       = {basis.status}")
    print(f"display      = {basis.display_label()}")

    assert basis.is_resolved is True
    assert basis.flow_temp_c == 75.0
    assert basis.return_temp_c == 65.0
    assert basis.delta_t_k == 10.0
    assert basis.source == "Environment"

    invalid_project = _project_with_environment(
        flow_temp_c=55.0,
        return_temp_c=65.0,
    )

    invalid_basis = resolve_hydronic_design_temperature_basis_v1(invalid_project)

    assert invalid_basis.is_resolved is False
    assert invalid_basis.delta_t_k is None
    assert invalid_basis.status == "Environment hydronic ΔT invalid"

    missing_environment_project = ProjectState(
        project_id="dev-hs23a-no-environment",
        name="DEV H-S23-A No Environment",
    )

    missing_basis = resolve_hydronic_design_temperature_basis_v1(
        missing_environment_project
    )

    assert missing_basis.is_resolved is False
    assert missing_basis.status == "Environment not available"

    print()
    print("OK — shared hydronic design-temperature basis helper passed.")


if __name__ == "__main__":
    main()
