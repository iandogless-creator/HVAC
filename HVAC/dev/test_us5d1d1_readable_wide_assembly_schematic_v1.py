from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea
    except ModuleNotFoundError:
        source = Path(
            "HVAC/gui_v3/widgets/"
            "construction_layer_path_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        assert "def _natural_text_width(" in source
        assert "widget.fontMetrics().horizontalAdvance(line)" in source
        assert "self.layout_row.sizeHint().width()" in source
        assert "self.setFixedHeight(" in source
        panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        expected_scroll_block = (
            'teaching_scroll.setObjectName("uValueTeachingSchematicScroll")\n'
            "        teaching_scroll.setWidgetResizable(False)"
        )
        assert expected_scroll_block in panel_source
        assert "def _resize_teaching_schematic_viewport(" in panel_source
        assert "Qt.ScrollBarAlwaysOff" in panel_source
        assert "required_width = max(" in source
        print(
            "OK — U-S5D1D1 readable wide assembly schematic passed "
            "(source boundary; Qt unavailable)."
        )
        return

    from HVAC.constructions.physics.u_value_teaching_models_v1 import (
        CAVITY_WALL_MODEL_ID,
        teaching_model_by_id_v1,
    )
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel
    from HVAC.gui_v3.widgets.construction_layer_path_schematic_widget_v1 import (
        BASE_SCHEMATIC_MINIMUM_WIDTH,
        ConstructionLayerDragTokenV1,
        ConstructionLayerPathSchematicWidgetV1,
        ConstructionPathDropRowV1,
    )

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(CAVITY_WALL_MODEL_ID)
    viewport = panel._teaching_scroll
    assert isinstance(viewport, QScrollArea)
    assert not viewport.widgetResizable()
    assert viewport.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    viewport.resize(720, 240)
    panel.show()
    app.processEvents()

    schematic = panel._teaching_schematic
    assert isinstance(schematic, ConstructionLayerPathSchematicWidgetV1)
    assert schematic.candidate_evidence() == teaching_model_by_id_v1(
        CAVITY_WALL_MODEL_ID
    ).evidence

    expected_labels = {
        "Internal plaster",
        "Blockwork inner leaf",
        "Cavity insulation",
        "Residual unventilated air cavity",
        "Outer brick leaf",
    }
    tokens = schematic.findChildren(ConstructionLayerDragTokenV1)
    assert {token.text() for token in tokens} == expected_labels
    assert all(
        token.minimumWidth()
        >= max(
            token.fontMetrics().horizontalAdvance(line)
            for line in token.text().splitlines()
        ) + 30
        for token in tokens
    )

    rows = schematic.findChildren(ConstructionPathDropRowV1)
    assert len(rows) == 1
    assert rows[0].minimumWidth() >= rows[0].layout_row.sizeHint().width()
    assert rows[0].minimumHeight() >= rows[0].layout_row.sizeHint().height()
    assert all(
        token.geometry().bottom() <= rows[0].contentsRect().bottom()
        for token in tokens
    )
    assert schematic.minimumWidth() > BASE_SCHEMATIC_MINIMUM_WIDTH

    headings = schematic.findChildren(QPushButton)
    path_heading = next(
        heading for heading in headings
        if heading.objectName() == "constructionPathFocusButton"
    )
    assert path_heading.minimumWidth() >= (
        path_heading.fontMetrics().horizontalAdvance("Masonry cavity wall path")
        + 18
    )
    assert viewport.horizontalScrollBar().maximum() > 0
    assert viewport.verticalScrollBar().maximum() == 0
    assert viewport.viewport().height() >= schematic.height()

    print(
        "OK — U-S5D1D1 wide masonry path uses natural-width labels and "
        "horizontal scrolling without clipping assembly tokens."
    )


if __name__ == "__main__":
    main()
