from __future__ import annotations

from HVAC.core.environment_state import EnvironmentStateV1


def main() -> None:
    default = EnvironmentStateV1()
    assert default.use_internal_environmental_temperature is False

    enabled = EnvironmentStateV1(
        external_design_temp_C=-3.0,
        default_internal_temp_C=21.0,
        use_internal_environmental_temperature=True,
    )
    payload = enabled.to_dict()
    assert payload["use_internal_environmental_temperature"] is True

    restored = EnvironmentStateV1.from_dict(payload)
    assert restored.use_internal_environmental_temperature is True
    assert restored.external_design_temp_C == -3.0
    assert restored.default_internal_temp_C == 21.0

    legacy = EnvironmentStateV1.from_dict(
        {
            "external_design_temp_C": -3.0,
            "default_internal_temp_C": 21.0,
        }
    )
    assert legacy.use_internal_environmental_temperature is False

    explicit_off = EnvironmentStateV1.from_dict(
        {"use_internal_environmental_temperature": False}
    )
    assert explicit_off.use_internal_environmental_temperature is False

    print(
        "OK — HL-S1A optional internal environmental-temperature mode "
        "intent persists and legacy projects remain on the existing Ti path."
    )


if __name__ == "__main__":
    main()
