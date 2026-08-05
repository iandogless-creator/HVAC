from __future__ import annotations

from pathlib import Path

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.heatloss.physics.environment_pipe_pair_spacing_defaults_v1 import (
    MOULDED_PLASTIC_DOUBLE_CLIP_V1,
    PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1,
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
    STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1,
    default_environment_pipe_pair_spacing_defaults_v1,
    normalise_environment_pipe_pair_spacing_defaults_v1,
    resolve_environment_pipe_pair_spacing_default_v1,
)


def main() -> None:
    defaults = default_environment_pipe_pair_spacing_defaults_v1()
    assert tuple(map(int, defaults)) == STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1
    assert defaults["10"] == {
        "support_type": MOULDED_PLASTIC_DOUBLE_CLIP_V1,
        "centre_spacing_mm": 25.0,
    }
    assert defaults["22"]["centre_spacing_mm"] == 40.0
    assert defaults["28"]["support_type"] == (
        PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1
    )
    assert defaults["54"]["centre_spacing_mm"] == 90.0

    environment = EnvironmentStateV1()
    assert environment.bare_pipe_pair_spacing_defaults_by_nominal_od_mm == defaults
    round_trip = EnvironmentStateV1.from_dict(environment.to_dict())
    assert round_trip.bare_pipe_pair_spacing_defaults_by_nominal_od_mm == defaults
    legacy = EnvironmentStateV1.from_dict({})
    assert legacy.bare_pipe_pair_spacing_defaults_by_nominal_od_mm == defaults

    edited = default_environment_pipe_pair_spacing_defaults_v1()
    edited["22"] = {
        "support_type": PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1,
        "centre_spacing_mm": 43.0,
    }
    clean = normalise_environment_pipe_pair_spacing_defaults_v1(edited)
    stacked = resolve_environment_pipe_pair_spacing_default_v1(
        raw_defaults=clean,
        nominal_outside_diameter_mm=22,
        external_arrangement=STACKED_FLOW_RETURN_PAIR_V1,
    )
    assert stacked is not None
    assert stacked.centre_spacing_mm == 43.0
    assert stacked.support_type == PAIRED_INDIVIDUAL_PLASTIC_CLIPS_V1

    # The universal c/c authority is deliberately dormant for separate RR.
    separate = resolve_environment_pipe_pair_spacing_default_v1(
        raw_defaults=clean,
        nominal_outside_diameter_mm=22,
        external_arrangement=SEPARATE_PIPE_V1,
    )
    assert separate is None

    incomplete = dict(clean)
    incomplete.pop("54")
    try:
        normalise_environment_pipe_pair_spacing_defaults_v1(incomplete)
    except ValueError as exc:
        assert "missing 54 mm" in str(exc)
    else:
        raise AssertionError("Incomplete universal spacing defaults were accepted")

    invalid = default_environment_pipe_pair_spacing_defaults_v1()
    invalid["22"]["centre_spacing_mm"] = 22.0
    try:
        normalise_environment_pipe_pair_spacing_defaults_v1(invalid)
    except ValueError as exc:
        assert "must exceed pipe OD" in str(exc)
    else:
        raise AssertionError("Overlapping stacked pipes were accepted")

    root = Path(__file__).resolve().parents[2]
    panel_source = (
        root / "HVAC/gui_v3/panels/environment_panel.py"
    ).read_text(encoding="utf-8")
    adapter_source = (
        root / "HVAC/gui_v3/adapters/environment_panel_adapter.py"
    ).read_text(encoding="utf-8")
    assert "Stacked flow/return pairs only" in panel_source
    assert "Universal pair support basis" in panel_source
    assert "Universal pipe centre spacing" in panel_source
    assert "bare_pipe_pair_spacing_default_changed = Signal(int, str, float)" in panel_source
    assert "_on_bare_pipe_pair_spacing_default_changed" in adapter_source
    assert "bare_pipe_pair_spacing_defaults_by_nominal_od_mm" in adapter_source
    assert "external_convection" not in Path(__file__).name

    print(
        "OK — H-S66-N1A Environment universal stacked pipe-pair "
        "support and c/c defaults passed."
    )


if __name__ == "__main__":
    main()
