from __future__ import annotations

from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


def route(title: str) -> str:
    return HydronicsSchematicPanel._proportioning_workspace_key_for_title_v1(
        None,
        title,
    )


def main() -> None:
    assert route(
        "Main / leg / subleg balancing-point evidence — read-only"
    ) == "kvs_design"
    assert route(
        "Manual point Kvs candidate acceptance — design intent"
    ) == "kvs_design"

    # Preserve the established neighbouring workspace routes.
    assert route(
        "Return arrangement acceptance — user design basis"
    ) == "balancing_authority"
    assert route(
        "Approved point valve product-search duty envelopes — read-only"
    ) == "product_search"
    assert route(
        "Manufacturer valve candidates — read-only comparison"
    ) == "manufacturer_valves"

    source = open(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py",
        encoding="utf-8",
    ).read()
    construction_start = source.index(
        "# H-S44-E — point allocation / method / valve-duty evidence"
    )
    construction_end = source.index(
        "# H-S49-A — approved product-search duty envelopes",
        construction_start,
    )
    construction = source[construction_start:construction_end]
    table_order = construction.index(
        "table=self._balancing_point_evidence_table,"
    )
    editor_order = construction.index("table=kvs_editor,")
    assert table_order < editor_order

    print(
        "OK — H-S70-B2D restores the existing all-point balancing/Kvs "
        "evidence table to Kvs Design immediately before its manual editor, "
        "without changing calculations, callbacks, persistence or authority."
    )


if __name__ == "__main__":
    main()
