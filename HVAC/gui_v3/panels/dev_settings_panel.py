# ======================================================================
# HVAC/gui_v3/panels/dev_settings_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)


class DevSettingsPanel(QWidget):
    """
    DEV scenario selector.

    Owns no ProjectState.
    Emits selected DEV mode only.
    """

    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setEnabled(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self._build_ui()

    def mousePressEvent(self, event):
        print(
            f"[DEV PANEL MOUSE PRESS] "
            f"id={id(self)} "
            f"pos={event.position().toPoint()}"
        )
        super().mousePressEvent(event)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("DEV Mode"))

        self._combo = QComboBox(self)
        self._combo.setEnabled(True)
        self._combo.addItems([
            "simple",
            "vertical_stack",
        ])
        layout.addWidget(self._combo)

        self._reload_button = QPushButton("Load selected DEV mode", self)
        self._reload_button.setEnabled(True)
        layout.addWidget(self._reload_button)

        self._combo.currentTextChanged.connect(self._on_mode_changed)

        self._reload_button.pressed.connect(
            lambda: print("[DEV BUTTON PRESSED]")
        )
        self._reload_button.clicked.connect(self._emit_current_mode)


    def _on_mode_changed(self, mode: str) -> None:
        self.mode_changed.emit(mode)

    def _emit_current_mode(self) -> None:
        mode = self._combo.currentText()
        self.mode_changed.emit(mode)

    def current_mode(self) -> str:
        return self._combo.currentText()