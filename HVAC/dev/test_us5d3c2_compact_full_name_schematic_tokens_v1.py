from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
    ConstructionPathDropRowV1,
    _compact_schematic_layer_label,
    _schematic_layer_tooltip,
)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    expected = {
        "Plasterboard lining": "Lining",
        "Service void": "Service void",
        "Air and vapour control layer": "AVCL",
        "Mineral wool between studs": "Insulation",
        "Timber stud — 38 × 140 mm finished CLS": "Stud",
        "Structural OSB sheathing": "OSB",
        "Continuous insulation outside frame": "Ext. insulation",
        "Breather membrane": "Membrane",
        "External cavity — declared R basis": "Cavity",
        "Brick outer leaf": "Brick",
        "Rainscreen cladding alternative": "Rainscreen",
        "Render carrier-board alternative": "Render board",
    }
    for full_label, compact_label in expected.items():
        assert _compact_schematic_layer_label(full_label) == compact_label
    assert _compact_schematic_layer_label("User material") == "User material"
    assert _compact_schematic_layer_label(
        "A deliberately very long custom material name"
    ) == "A deliberately very long custom material name"
    assert _schematic_layer_tooltip("Structural OSB sheathing", "") == (
        "Structural OSB sheathing"
    )

    layers = [
        ("lining", "Plasterboard lining", "", True, True),
        ("service-void", "Service void", "Optional service zone", True, False),
        ("avcl", "Air and vapour control layer", "", True, True),
        ("insulation", "Mineral wool between studs", "", False, True),
        ("sheathing", "Structural OSB sheathing", "", True, True),
        (
            "continuous-external-insulation",
            "Continuous insulation outside frame",
            "",
            True,
            True,
        ),
        ("breather-membrane", "Breather membrane", "", True, True),
        (
            "external-cavity",
            "External cavity — declared R basis",
            "",
            True,
            True,
        ),
        ("brick-outer-leaf", "Brick outer leaf", "", True, True),
        (
            "rainscreen-cladding",
            "Rainscreen cladding alternative",
            "",
            True,
            False,
        ),
        (
            "render-carrier-board",
            "Render carrier-board alternative",
            "",
            True,
            False,
        ),
    ]
    row = ConstructionPathDropRowV1("insulated-bay")
    row.set_path(
        path_label="Insulated bay",
        area_fraction=0.85,
        layers=layers,
        internal_surface_resistance_m2K_W=0.13,
        external_surface_resistance_m2K_W=0.04,
    )
    texts = [token.text() for token in row._tokens]
    assert texts == [
        "Lining",
        "Service void\nOff",
        "AVCL",
        "Insulation",
        "OSB",
        "Ext. insulation",
        "Membrane",
        "Cavity",
        "Brick",
        "Rainscreen\nOff",
        "Render board\nOff",
    ]
    tooltips = [token.toolTip() for token in row._tokens]
    for _layer_id, full_label, _detail, _shared, _included in layers:
        assert any(full_label in tooltip for tooltip in tooltips)
    assert "Optional service zone" in tooltips[1]
    assert row.minimumWidth() <= 1250
    app.processEvents()
    print(
        "OK — U-S5D3C2 compact schematic tokens retain full material "
        "names on hover and preserve inclusion/drag evidence."
    )


if __name__ == "__main__":
    main()
