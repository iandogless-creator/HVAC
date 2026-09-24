from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QSizePolicy,
    QStyle,
    QToolButton,
    QWidget,
)


class WorkspaceNavigationPanelV1(QWidget):
    """Compact GUI-only route selector for the named workspace views."""

    view_requested = Signal(str)
    presentation_mode_requested = Signal(str)
    education_toggled = Signal(bool)
    preferences_requested = Signal()

    _ROUTES = (
        (
            "heat_loss_edit",
            "HL Edit",
            "Heat Loss — Edit",
            QStyle.StandardPixmap.SP_FileDialogContentsView,
        ),
        (
            "heat_loss_presentation",
            "HL View",
            "Heat Loss — Presentation",
            QStyle.StandardPixmap.SP_FileDialogInfoView,
        ),
        (
            "pipe_estimate",
            "Pipe Est.",
            "Pipe Estimate",
            QStyle.StandardPixmap.SP_ComputerIcon,
        ),
        (
            "proportioning_schematic",
            "Prop. Sch.",
            "Proportioning Schematic",
            QStyle.StandardPixmap.SP_DirIcon,
        ),
        (
            "return_schematic",
            "RR View",
            "Return Schematic",
            QStyle.StandardPixmap.SP_BrowserReload,
        ),
        (
            "results",
            "Results",
            "Results",
            QStyle.StandardPixmap.SP_DialogApplyButton,
        ),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceNavigationPanelV1")

        root = QGridLayout(self)
        root.setContentsMargins(6, 3, 6, 3)
        root.setSpacing(5)
        self._button_grid = root

        self._view_group = QButtonGroup(self)
        self._view_group.setExclusive(True)
        self._view_buttons: dict[str, QToolButton] = {}
        self._ordered_buttons: list[QToolButton] = []

        for route_id, label, full_label, icon in self._ROUTES:
            button = QToolButton(self)
            button.setText(label)
            button.setIcon(self.style().standardIcon(icon))
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            )
            button.setCheckable(True)
            button.setAutoRaise(False)
            button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            button.setProperty("hvacNavigationRole", "view")
            button.setToolTip(f"Open {full_label}")
            button.setAccessibleName(f"Open {full_label}")
            button.clicked.connect(
                lambda _checked=False, selected=route_id: (
                    self.view_requested.emit(selected)
                )
            )
            self._view_group.addButton(button)
            self._view_buttons[route_id] = button
            self._ordered_buttons.append(button)

        self._presentation_button = QToolButton(self)
        self._presentation_button.setText("Explode")
        self._presentation_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_TitleBarMaxButton
            )
        )
        self._presentation_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._presentation_button.setCheckable(True)
        self._presentation_button.setAutoRaise(False)
        self._presentation_button.setProperty(
            "hvacNavigationRole", "presentation"
        )
        self._presentation_button.toggled.connect(
            self._on_presentation_mode_toggled_v1
        )
        self._ordered_buttons.append(self._presentation_button)
        self.set_presentation_mode_v1("main")

        self._education_button = QToolButton(self)
        self._education_button.setText("Edu")
        self._education_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_MessageBoxInformation
            )
        )
        self._education_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._education_button.setCheckable(True)
        self._education_button.setAutoRaise(False)
        self._education_button.setProperty(
            "hvacNavigationRole", "education"
        )
        self._education_button.setToolTip(
            "Show or hide Education for the current view"
        )
        self._education_button.setAccessibleName("Toggle Education panel")
        self._education_button.toggled.connect(self.education_toggled)
        self._ordered_buttons.append(self._education_button)

        self._preferences_button = QToolButton(self)
        self._preferences_button.setText("⚙")
        self._preferences_button.setAutoRaise(False)
        self._preferences_button.setProperty(
            "hvacNavigationRole", "preferences"
        )
        self._preferences_button.setToolTip("View preferences")
        self._preferences_button.setAccessibleName("Open view preferences")
        self._preferences_button.clicked.connect(
            self.preferences_requested.emit
        )
        self._ordered_buttons.append(self._preferences_button)
        self._reflow_buttons_v1()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow_buttons_v1()

    def _reflow_buttons_v1(self) -> None:
        """Wrap navigation controls into more rows as width reduces."""
        buttons = tuple(getattr(self, "_ordered_buttons", ()))
        if not buttons:
            return
        available = max(self.width() - 12, 1)
        columns = max(2, min(len(buttons), available // 105))
        for button in buttons:
            self._button_grid.removeWidget(button)
        for column in range(len(buttons) + 1):
            self._button_grid.setColumnStretch(column, 0)
        for index, button in enumerate(buttons):
            row, column = divmod(index, columns)
            self._button_grid.addWidget(
                button,
                row,
                column,
                Qt.AlignmentFlag.AlignLeft,
            )
        self._button_grid.setColumnStretch(columns, 1)

    def set_active_route_v1(self, route_id: str) -> None:
        """Highlight one direct route without emitting navigation intent."""
        button = self._view_buttons.get(str(route_id or ""))
        if button is None:
            self._view_group.setExclusive(False)
            try:
                for candidate in self._view_buttons.values():
                    candidate.setChecked(False)
            finally:
                self._view_group.setExclusive(True)
            return
        button.setChecked(True)

    def active_route_v1(self) -> str:
        """Return the selected direct route without changing GUI state."""
        for route_id, button in self._view_buttons.items():
            if button.isChecked():
                return route_id
        return ""

    def _on_presentation_mode_toggled_v1(self, exploded: bool) -> None:
        mode = "floating" if bool(exploded) else "main"
        self._update_presentation_button_v1(mode)
        self.presentation_mode_requested.emit(mode)

    def _update_presentation_button_v1(self, mode: str) -> None:
        exploded = str(mode or "").strip().lower() == "floating"
        self._presentation_button.setText(
            "Main" if exploded else "Explode"
        )
        if exploded:
            tooltip = "Return this view to the Main Window"
            accessible_name = "Return view to Main Window"
        else:
            tooltip = "Explode this view into separate panel windows"
            accessible_name = "Explode view into separate panel windows"
        self._presentation_button.setToolTip(tooltip)
        self._presentation_button.setAccessibleName(accessible_name)

    def set_presentation_mode_v1(self, mode: str) -> None:
        """Mirror Main/Exploded state without re-emitting user intent."""
        exploded = str(mode or "").strip().lower() == "floating"
        self._presentation_button.blockSignals(True)
        try:
            self._presentation_button.setChecked(exploded)
            self._update_presentation_button_v1(
                "floating" if exploded else "main"
            )
        finally:
            self._presentation_button.blockSignals(False)

    def presentation_mode_v1(self) -> str:
        return (
            "floating"
            if self._presentation_button.isChecked()
            else "main"
        )

    def set_education_enabled_v1(self, enabled: bool) -> None:
        """Mirror Education visibility without re-emitting user intent."""
        self._education_button.blockSignals(True)
        try:
            self._education_button.setChecked(bool(enabled))
        finally:
            self._education_button.blockSignals(False)

    def button_for_route_v1(self, route_id: str) -> QToolButton | None:
        """Return a route button for focused GUI tests."""
        return self._view_buttons.get(str(route_id or ""))

    def education_button_v1(self) -> QToolButton:
        return self._education_button

    def presentation_button_v1(self) -> QToolButton:
        return self._presentation_button

    def preferences_button_v1(self) -> QToolButton:
        return self._preferences_button
