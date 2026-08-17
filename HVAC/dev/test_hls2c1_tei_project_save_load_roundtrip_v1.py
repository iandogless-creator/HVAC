from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.core.environment_state import EnvironmentStateV1
from HVAC.core.room_state import RoomStateV1
from HVAC.core.value_resolution import resolve_effective_internal_temp_C
from HVAC.project.project_state import ProjectState
from HVAC.project_v3.persistence.checksum import compute_checksum
from HVAC.project_v3.persistence.loader import load
from HVAC.project_v3.persistence.saver import save


def main() -> None:
    project = ProjectState(project_id="hls2c1", name="Tei persistence")
    project.environment = EnvironmentStateV1(
        external_design_temp_C=-4.0,
        default_internal_temp_C=20.5,
        default_room_height_m=2.4,
        default_ach=0.5,
        use_internal_environmental_temperature=True,
    )
    project.rooms["room-a"] = RoomStateV1(
        room_id="room-a",
        name="Living Room",
        internal_temp_override_C=18.5,
    )
    project.rooms["room-b"] = RoomStateV1(
        room_id="room-b",
        name="Kitchen",
    )

    with TemporaryDirectory(prefix="hls2c1-") as temporary_directory:
        root = Path(temporary_directory)
        current_dir = root / "current"
        legacy_dir = root / "legacy"

        save(project, current_dir)
        restored = load(current_dir)

        assert restored.project_dir == current_dir.resolve()
        assert restored.environment is not None
        assert restored.environment.use_internal_environmental_temperature is True
        assert restored.environment.default_internal_temp_C == 20.5
        assert restored.environment.external_design_temp_C == -4.0
        assert restored.rooms["room-a"].internal_temp_override_C == 18.5
        assert restored.rooms["room-b"].internal_temp_override_C is None

        tei_a, _source_a = resolve_effective_internal_temp_C(
            restored,
            restored.rooms["room-a"],
        )
        tei_b, _source_b = resolve_effective_internal_temp_C(
            restored,
            restored.rooms["room-b"],
        )
        assert tei_a == 20.5
        assert tei_b == 20.5

        restored.environment.use_internal_environmental_temperature = False
        ti_a, _source_ti_a = resolve_effective_internal_temp_C(
            restored,
            restored.rooms["room-a"],
        )
        ti_b, _source_ti_b = resolve_effective_internal_temp_C(
            restored,
            restored.rooms["room-b"],
        )
        assert ti_a == 18.5
        assert ti_b == 20.5

        wrapper = json.loads(
            (current_dir / "project.json").read_text(encoding="utf-8")
        )
        environment_payload = wrapper["payload"]["environment"]
        assert environment_payload["use_internal_environmental_temperature"] is True
        assert environment_payload["default_internal_temp_C"] == 20.5
        assert "tai" not in environment_payload
        assert "tai_C" not in environment_payload

        legacy_payload = project.to_dict()
        legacy_payload["environment"].pop(
            "use_internal_environmental_temperature"
        )
        legacy_wrapper = {
            "schema_version": 4,
            "checksum": compute_checksum(legacy_payload),
            "payload": legacy_payload,
        }
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "project.json").write_text(
            json.dumps(legacy_wrapper, indent=4, sort_keys=True),
            encoding="utf-8",
        )

        legacy = load(legacy_dir)
        assert legacy.environment is not None
        assert legacy.environment.use_internal_environmental_temperature is False
        assert legacy.environment.default_internal_temp_C == 20.5
        assert legacy.rooms["room-a"].internal_temp_override_C == 18.5

    print(
        "OK — HL-S2C1 tei mode, environmental input and inactive room "
        "override survive checksummed project save/load; legacy projects "
        "default to Ti mode and tai remains derived-only intent."
    )


if __name__ == "__main__":
    main()
