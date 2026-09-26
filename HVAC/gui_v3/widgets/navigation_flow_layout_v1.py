from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import QLayout


class NavigationFlowLayoutV1(QLayout):
    """Lay compact controls left to right and wrap at the available width."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(5)

    def addItem(self, item) -> None:
        self._items.append(item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._arrange(QRect(0, 0, width, 0), measure=True)

    def setGeometry(self, rect) -> None:
        super().setGeometry(rect)
        self._arrange(rect, measure=False)

    def sizeHint(self) -> QSize:
        return QSize(520, self.heightForWidth(520))

    def minimumSize(self) -> QSize:
        # A scroll area owns overflow; never enlarge the floating dock.
        return QSize(0, max((item.sizeHint().height() for item in self._items), default=0))

    def _arrange(self, rect, *, measure: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        available = max(1, rect.width() - left - right)
        x, y, row_height = 0, top, 0
        for item in self._items:
            hint = item.sizeHint()
            width = min(hint.width(), available)
            if x and x + width > available:
                x = 0
                y += row_height + self.spacing()
                row_height = 0
            if not measure:
                item.setGeometry(QRect(rect.x() + left + x, rect.y() + y, width, hint.height()))
            x += width + self.spacing()
            row_height = max(row_height, hint.height())
        return y + row_height + bottom
