from __future__ import annotations

from HVAC.constructions.physics.two_path_member_spacing_fraction_v1 import (
    CALCULATED_REPEATING_MEMBER_FRACTION,
    DECLARED_EFFECTIVE_MEMBER_FRACTION,
    TwoPathMemberSpacingIntentV1,
    resolve_two_path_member_spacing_fraction_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    calculated = resolve_two_path_member_spacing_fraction_v1(
        TwoPathMemberSpacingIntentV1(
            member_path_id="timber-stud",
            clear_path_id="insulated-bay",
            member_label="Timber stud",
            member_width_m=0.038,
            member_centres_m=0.600,
            controlling_basis=CALCULATED_REPEATING_MEMBER_FRACTION,
        )
    )
    assert calculated.ready, calculated.blockers
    assert abs(calculated.controlling_member_fraction - 0.038 / 0.600) < 1e-12

    declared = resolve_two_path_member_spacing_fraction_v1(
        TwoPathMemberSpacingIntentV1(
            member_path_id="timber-stud",
            clear_path_id="insulated-bay",
            member_label="Timber stud",
            member_width_m=0.038,
            member_centres_m=0.600,
            controlling_basis=DECLARED_EFFECTIVE_MEMBER_FRACTION,
            declared_effective_member_fraction=0.15,
        )
    )
    assert declared.ready, declared.blockers
    assert abs(declared.calculated_repeating_member_fraction - 0.06333333333333334) < 1e-12
    assert declared.controlling_member_fraction == 0.15
    assert declared.controlling_clear_fraction == 0.85

    model = teaching_model_by_id_v1(TWO_PATH_MODEL_ID)
    basis = model.member_spacing_intent
    assert basis is not None
    resolved = resolve_two_path_member_spacing_fraction_v1(basis)
    assert resolved.ready, resolved.blockers
    fractions = {path.path_id: path.area_fraction for path in model.evidence.paths}
    assert fractions[basis.member_path_id] == resolved.controlling_member_fraction
    assert fractions[basis.clear_path_id] == resolved.controlling_clear_fraction
    print("OK — U-S5D3A1 member width/centres and controlling two-path fractions passed.")


if __name__ == "__main__":
    main()
