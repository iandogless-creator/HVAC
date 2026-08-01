from __future__ import annotations

import math
from types import SimpleNamespace

from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.proportioning.circuit_return_path_comparison_v1 import (
    _RRSectionPressureBasisV1,
    _rr_added_length_pressure_drop_Pa,
)


def main() -> None:
    # The deliberately non-numeric label proves the calculation consumes the
    # exact typed steel family/size identity rather than display wording.
    basis = _RRSectionPressureBasisV1(
        mass_flow_kg_s=0.12,
        pipe_size_label="display wording is not hydraulic authority",
        material_key="steel",
        pipe_size_key=32,
    )
    actual = _rr_added_length_pressure_drop_Pa(
        project_state=SimpleNamespace(),
        section_pressure_basis_by_id={"section-1": basis},
        candidate_section_ids=("section-1",),
        length_m=7.5,
    )
    expected = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=0.12,
        material="steel",
        dn=32,
        length_m=7.5,
        friction_method="colebrook",
    )
    assert actual > 0.0
    assert math.isclose(
        actual,
        expected.pressure_drop_pa,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    )

    print(
        "OK — H-S63-B2B1 RR added-length preview uses exact Basic PS "
        "material and catalogue-size identity."
    )


if __name__ == "__main__":
    main()
