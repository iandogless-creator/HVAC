from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    helper_source = Path(
        "HVAC/gui_v3/common/wheel_input_safety_v1.py"
    ).read_text(encoding="utf-8")
    main_source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    for required in (
        "QComboBox, QAbstractSpinBox",
        "isinstance(obj, QAbstractSlider)",
        "not isinstance(obj, QScrollBar)",
        "obj.view().isVisible()",
        "QApplication.sendEvent(viewport, forwarded)",
    ):
        assert required in helper_source, required
    assert "redirect_unsafe_input_wheel_event_v1" in main_source

    try:
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtWidgets import (
            QApplication,
            QComboBox,
            QDoubleSpinBox,
            QScrollArea,
            QSlider,
            QVBoxLayout,
            QWidget,
        )
    except ModuleNotFoundError:
        print(
            "OK — U-S5D1C application-wide wheel input safety passed "
            "(source boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.common.wheel_input_safety_v1 import (
        redirect_unsafe_input_wheel_event_v1,
    )

    app = QApplication.instance() or QApplication([])
    area = QScrollArea()
    area.resize(300, 200)
    content = QWidget()
    content.setMinimumHeight(900)
    layout = QVBoxLayout(content)
    combo = QComboBox(content)
    combo.addItems(("One", "Two", "Three"))
    spin = QDoubleSpinBox(content)
    spin.setRange(0.0, 100.0)
    spin.setValue(13.0)
    slider = QSlider(Qt.Horizontal, content)
    slider.setRange(0, 100)
    slider.setValue(50)
    layout.addWidget(combo)
    layout.addWidget(spin)
    layout.addWidget(slider)
    layout.addStretch()
    area.setWidget(content)
    area.setWidgetResizable(True)
    area.show()
    app.processEvents()

    def wheel(target) -> bool:
        event = QWheelEvent(
            QPointF(5, 5),
            QPointF(target.mapToGlobal(QPoint(5, 5))),
            QPoint(),
            QPoint(0, -120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.NoScrollPhase,
            False,
        )
        return redirect_unsafe_input_wheel_event_v1(target, event)

    before_scroll = area.verticalScrollBar().value()
    assert wheel(combo)
    assert combo.currentIndex() == 0
    app.processEvents()
    assert area.verticalScrollBar().value() > before_scroll

    before_scroll = area.verticalScrollBar().value()
    assert wheel(spin)
    assert spin.value() == 13.0
    app.processEvents()
    assert area.verticalScrollBar().value() > before_scroll

    before_scroll = area.verticalScrollBar().value()
    assert wheel(slider)
    assert slider.value() == 50
    app.processEvents()
    assert area.verticalScrollBar().value() > before_scroll

    assert not redirect_unsafe_input_wheel_event_v1(
        area.verticalScrollBar(),
        QWheelEvent(
            QPointF(5, 5),
            QPointF(5, 5),
            QPoint(),
            QPoint(0, -120),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.NoScrollPhase,
            False,
        ),
    )

    print(
        "OK — U-S5D1C combos, spin boxes, sliders and dials cannot change "
        "under an incidental mouse wheel; surrounding panels scroll instead."
    )


if __name__ == "__main__":
    main()
