from __future__ import annotations

from HVAC.hydronics_v3.catalogues.local_valve_catalogue_loader_v1 import (
    load_bundled_local_valve_catalogue_v1,
)


def main() -> None:
    catalogue = load_bundled_local_valve_catalogue_v1()
    assert catalogue.catalog_id == "local-generic-valves-v1"

    by_kv = {float(option.kv_m3_h): option for option in catalogue.kv_options}
    assert tuple(sorted(by_kv)) == (1.6, 2.5, 6.3, 10.0, 16.0)

    for accepted_kvs in (1.6, 2.5):
        option = by_kv[accepted_kvs]
        assert float(option.kv_m3_h) == accepted_kvs
        assert option.valve_ref == f"LOCAL-GENERIC-KV-{accepted_kvs:g}"
        assert "no manufacturer" in option.note.lower()

    # Existing wider generic evidence remains available; this stage only
    # fills the exact current-duty gaps and does not alter matching tolerance.
    assert 6.3 in by_kv
    assert 10.0 in by_kv
    assert 16.0 in by_kv

    print(
        "OK — H-S50-E local generic catalogue contains exact Kvs 1.6 and "
        "2.5 duty candidates."
    )


if __name__ == "__main__":
    main()
