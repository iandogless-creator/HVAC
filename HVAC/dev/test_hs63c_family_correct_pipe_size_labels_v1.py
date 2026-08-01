from __future__ import annotations

from HVAC.hydronics.proportioning.proportioned_pipe_sizing_authority_v1 import (
    ProportionedPipeSizingCriteriaV1,
    _candidate_family_v1,
    _candidate_pipe_size_label_v1,
)
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    _basic_ps_pipe_size_label_v1,
    build_basic_ps_pipe_candidates_for_material_v1,
)


def main() -> None:
    assert _candidate_pipe_size_label_v1(
        material_key="copper",
        dn=28,
        outside_diameter_mm=28.0,
        thickness_mm=0.9,
    ) == "28 mm"
    assert _candidate_pipe_size_label_v1(
        material_key="mlcp",
        dn=32,
        outside_diameter_mm=32.0,
        thickness_mm=3.0,
    ) == "32×3 mm"
    assert _candidate_pipe_size_label_v1(
        material_key="steel",
        dn=32,
        outside_diameter_mm=42.4,
        thickness_mm=3.65,
    ) == "DN32"

    assert _basic_ps_pipe_size_label_v1(
        material_key="steel",
        size_key=32,
        outside_diameter_mm=42.4,
        thickness_mm=3.65,
    ) == "DN32"

    basic_steel = build_basic_ps_pipe_candidates_for_material_v1("steel")
    assert [row.pipe_size_label for row in basic_steel] == [
        "DN15",
        "DN20",
        "DN25",
        "DN32",
        "DN40",
        "DN50",
        "DN65",
        "DN80",
    ]
    assert basic_steel[3].pipe_size_key == 32
    assert abs(basic_steel[3].internal_diameter_m - 0.0351) < 1.0e-12

    criteria = ProportionedPipeSizingCriteriaV1(material_key="steel")
    proportioned_steel, blockers = _candidate_family_v1(criteria)
    assert blockers == []
    assert [row.pipe_size_label for row in proportioned_steel] == [
        "DN15",
        "DN20",
        "DN25",
        "DN32",
        "DN40",
        "DN50",
    ]
    dn32 = next(row for row in proportioned_steel if row.dn == 32)
    assert abs(dn32.outside_diameter_m - 0.0424) < 1.0e-12
    assert abs(dn32.internal_diameter_m - 0.0351) < 1.0e-12

    print(
        "OK — H-S63-C copper OD, plastic OD×wall and steel DN labels "
        "are family-correct."
    )


if __name__ == "__main__":
    main()
