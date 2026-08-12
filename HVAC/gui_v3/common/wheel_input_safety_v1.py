from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QScrollBar,
    QWidget,
)


def redirect_unsafe_input_wheel_event_v1(obj, event) -> bool:
    """Protect editable values and pass wheel intent to the surrounding page."""

    if event.type() != QEvent.Wheel or not _is_wheel_protected_input(obj):
        return False
    if isinstance(obj, QComboBox) and obj.view().isVisible():
        return False

    scroll_area = _nearest_scroll_area(obj)
    if scroll_area is not None:
        viewport = scroll_area.viewport()
        local_position = QPointF(
            viewport.mapFromGlobal(event.globalPosition().toPoint())
        )
        forwarded = QWheelEvent(
            local_position,
            event.globalPosition(),
            event.pixelDelta(),
            event.angleDelta(),
            event.buttons(),
            event.modifiers(),
            event.phase(),
            event.inverted(),
            event.source(),
            event.pointingDevice(),
        )
        QApplication.sendEvent(viewport, forwarded)

    event.accept()
    return True


def _is_wheel_protected_input(obj) -> bool:
    return bool(
        isinstance(obj, (QComboBox, QAbstractSpinBox))
        or (
            isinstance(obj, QAbstractSlider)
            and not isinstance(obj, QScrollBar)
        )
    )


def _nearest_scroll_area(obj) -> QAbstractScrollArea | None:
    parent = obj.parentWidget() if isinstance(obj, QWidget) else None
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            return parent
        parent = parent.parentWidget()
    return None
