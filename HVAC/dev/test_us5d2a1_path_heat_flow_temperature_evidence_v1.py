from __future__ import annotations

from HVAC.constructions.physics.construction_path_heat_flow_temperature_evidence_v1 import (
    build_construction_path_heat_flow_temperature_evidence_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    model = teaching_model_by_id_v1(TWO_PATH_MODEL_ID)
    result = build_construction_path_heat_flow_temperature_evidence_v1(
        model.evidence,
        internal_temperature_C=21.0,
        external_temperature_C=-3.0,
    )
    assert result.ready, result.blockers
    assert len(result.paths) == 2
    assert result.total_weighted_heat_flow_W_m2 is not None
    assert result.total_weighted_heat_flow_W_m2 > 0.0
    for path in result.paths:
        assert path.points[0].label == "tai"
        assert path.points[0].temperature_C == 21.0
        assert path.points[1].label == "Rsi"
        assert path.points[-1].label == "Rso"
        assert abs(path.points[-1].temperature_C - (-3.0)) < 1.0e-9
        assert all(
            upper.temperature_C > lower.temperature_C
            for upper, lower in zip(path.points, path.points[1:])
        )
        assert abs(
            path.heat_flow_W_m2
            - 24.0 / path.total_resistance_m2K_W
        ) < 1.0e-12

    blocked = build_construction_path_heat_flow_temperature_evidence_v1(
        model.evidence,
        internal_temperature_C=None,
        external_temperature_C=-3.0,
    )
    assert not blocked.ready
    assert any("Internal design temperature" in item for item in blocked.blockers)
    print(
        "OK — U-S5D2A1 candidate path heat flow, Rsi/layers/Rso and "
        "interface temperatures resolved deterministically."
    )


if __name__ == "__main__":
    main()
