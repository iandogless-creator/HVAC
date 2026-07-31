# ======================================================================
# H-S63-A — Current thin-wall copper-tube dimensional authority
# ======================================================================

import math

from HVAC.core.materials.pipe_materials_library import (
    get_internal_diameter,
    get_material,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)


EXPECTED = {
    10: (10.0, 0.6, 8.8),
    15: (15.0, 0.7, 13.6),
    22: (22.0, 0.9, 20.2),
    28: (28.0, 0.9, 26.2),
    35: (35.0, 1.0, 33.0),
    42: (42.0, 1.0, 40.0),
    54: (54.0, 1.2, 51.6),
}


def main() -> None:
    copper = get_material("copper")
    assert copper is not None
    assert copper.dimensional_series_label == (
        "Copper tube EN 1057 — current thin-wall series"
    )
    assert tuple(sorted(copper.sizes)) == tuple(EXPECTED)
    assert 6 not in copper.sizes
    assert 8 not in copper.sizes

    for size_key, (expected_od, expected_wall, expected_id) in EXPECTED.items():
        size = copper.sizes[size_key]
        assert size.dn == size_key
        assert math.isclose(size.od_mm, expected_od, abs_tol=1.0e-12)
        assert math.isclose(size.thickness_mm, expected_wall, abs_tol=1.0e-12)
        assert math.isclose(
            size.id_mm,
            size.od_mm - (2.0 * size.thickness_mm),
            abs_tol=1.0e-12,
        )
        assert math.isclose(size.id_mm, expected_id, abs_tol=1.0e-12)
        assert math.isclose(
            get_internal_diameter("copper", size_key),
            expected_id,
            abs_tol=1.0e-12,
        )

    hydraulic = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
        mass_flow_kg_s=0.05,
        material="copper",
        dn=10,
        length_m=5.0,
        friction_method="colebrook",
    )
    assert math.isclose(
        hydraulic.internal_diameter_m,
        0.0088,
        abs_tol=1.0e-12,
    )
    assert hydraulic.colebrook_converged is True
    assert hydraulic.velocity_m_s > 0.0
    assert hydraulic.pressure_gradient_pa_per_m > 0.0

    print(
        "OK — H-S63-A current thin-wall copper-tube dimensional "
        "authority passed."
    )


if __name__ == "__main__":
    main()
