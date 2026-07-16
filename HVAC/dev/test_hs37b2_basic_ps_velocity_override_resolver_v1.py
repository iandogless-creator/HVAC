# ======================================================================
# HVAC/dev/test_hs37b2_basic_ps_velocity_override_resolver_v1.py
# H-S37-B2 — Local section velocity override intent/resolution
# ======================================================================

from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.hydronics.models.basic_hydronic_sizing_intent_v1 import (
    BasicHydronicSizingIntentV1,
)
from HVAC.hydronics.sizing.basic_ps_velocity_limit_resolver_v1 import (
    ENVIRONMENT_DEFAULT_SOURCE,
    LOCAL_SECTION_OVERRIDE_SOURCE,
    resolve_basic_ps_max_velocity_v1,
)
from HVAC.project.project_state import ProjectState


SECTION_ID = "leg-001-primary-subleg-section-002"


def main() -> None:
    project = ProjectState(
        project_id="dev-hs37b2-velocity-override",
        name="DEV H-S37-B2 Velocity Override",
    )
    project.environment = EnvironmentStateV1(
        basic_ps_max_velocity_m_s=1.05,
    )
    project.basic_hydronic_sizing_intent = BasicHydronicSizingIntentV1()

    inherited = resolve_basic_ps_max_velocity_v1(
        project,
        section_id=SECTION_ID,
    )
    assert inherited.effective_max_velocity_m_s == 1.05
    assert inherited.source == ENVIRONMENT_DEFAULT_SOURCE
    assert inherited.environment_default_m_s == 1.05
    assert inherited.local_override_m_s is None

    intent = project.basic_hydronic_sizing_intent
    assert intent is not None
    intent.set_section_max_velocity_override(SECTION_ID, 1.10)

    overridden = resolve_basic_ps_max_velocity_v1(
        project,
        section_id=SECTION_ID,
    )
    assert overridden.effective_max_velocity_m_s == 1.10
    assert overridden.source == LOCAL_SECTION_OVERRIDE_SOURCE
    assert overridden.environment_default_m_s == 1.05
    assert overridden.local_override_m_s == 1.10

    restored = ProjectState.from_dict(project.to_dict())
    restored_intent = restored.basic_hydronic_sizing_intent
    assert restored_intent is not None
    assert restored_intent.get_section_max_velocity_override(SECTION_ID) == 1.10

    restored_resolution = resolve_basic_ps_max_velocity_v1(
        restored,
        section_id=SECTION_ID,
    )
    assert restored_resolution.effective_max_velocity_m_s == 1.10
    assert restored_resolution.source == LOCAL_SECTION_OVERRIDE_SOURCE

    restored_intent.clear_section_max_velocity_override(SECTION_ID)
    assert restored_intent.get_section_max_velocity_override(SECTION_ID) is None

    cleared = resolve_basic_ps_max_velocity_v1(
        restored,
        section_id=SECTION_ID,
    )
    assert cleared.effective_max_velocity_m_s == 1.05
    assert cleared.source == ENVIRONMENT_DEFAULT_SOURCE
    assert cleared.local_override_m_s is None

    legacy_intent = BasicHydronicSizingIntentV1.from_dict(
        {"basis_mode": "INDEX_LENGTH"}
    )
    assert legacy_intent.section_max_velocity_overrides_m_s == {}

    try:
        intent.set_section_max_velocity_override(SECTION_ID, 0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Non-positive local override was not rejected")

    print(
        "OK — H-S37-B2 local Basic PS velocity override "
        "intent/resolution passed."
    )


if __name__ == "__main__":
    main()
