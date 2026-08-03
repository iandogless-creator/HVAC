import json
from pathlib import Path
from tempfile import TemporaryDirectory

from HVAC.hydronics_v3.catalogues.local_valve_catalogue_loader_v1 import (
    LOCAL_GENERIC_VALVE_CATALOGUE_PATH_V1,
    load_bundled_local_valve_catalogue_v1,
    load_local_valve_catalogue_v1,
)


def _expect_value_error(path: Path, payload: object, expected: str) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        load_local_valve_catalogue_v1(path)
    except ValueError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError(f"Expected ValueError containing: {expected}")


def main() -> None:
    catalogue = load_bundled_local_valve_catalogue_v1()
    assert LOCAL_GENERIC_VALVE_CATALOGUE_PATH_V1.exists()
    assert catalogue.catalog_id == "local-generic-valves-v1"
    assert [option.valve_ref for option in catalogue.kv_options] == [
        "LOCAL-GENERIC-KV-1.6",
        "LOCAL-GENERIC-KV-2.5",
        "LOCAL-GENERIC-KV-6.3",
        "LOCAL-GENERIC-KV-10",
        "LOCAL-GENERIC-KV-16",
    ]
    assert [option.kv_m3_h for option in catalogue.kv_options] == [
        1.6,
        2.5,
        6.3,
        10.0,
        16.0,
    ]
    assert all("no manufacturer" in option.note.lower() for option in catalogue.kv_options)

    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "catalogue.json"
        _expect_value_error(path, [], "root must be an object")
        _expect_value_error(
            path,
            {"schema": "wrong", "catalog_id": "x", "kv_options": [{}]},
            "schema must be",
        )
        _expect_value_error(
            path,
            {
                "schema": "local_valve_catalogue_v1",
                "catalog_id": "x",
                "kv_options": [
                    {"valve_ref": "DUP", "kv_m3_h": 1.0},
                    {"valve_ref": "DUP", "kv_m3_h": 2.0},
                ],
            },
            "Duplicate",
        )
        _expect_value_error(
            path,
            {
                "schema": "local_valve_catalogue_v1",
                "catalog_id": "x",
                "kv_options": [{"valve_ref": "BAD", "kv_m3_h": 0.0}],
            },
            "Positive finite",
        )

    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    assert "load_bundled_local_valve_catalogue_v1()" in adapter_source
    init_pos = adapter_source.index("# H-S50-C — bundled local catalogue evidence")
    refresh_pos = adapter_source.index("self._subscribe_if_present", init_pos)
    assert init_pos < refresh_pos
    init_source = adapter_source[init_pos:refresh_pos]
    assert "project." not in init_source
    assert "mark_dirty" not in init_source

    print("OK — H-S50-C explicit local valve catalogue loader passed.")


if __name__ == "__main__":
    main()
