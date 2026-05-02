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

        print(f"[DEV PANEL INIT] id={id(self)} parent={parent}")

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

        print(f"[DEV PANEL ENABLED] {self.isEnabled()}")
        print(f"[DEV PANEL ENABLED TO WINDOW] {self.isEnabledTo(self.window())}")
        print(f"[DEV COMBO COUNT] {self._combo.count()}")
        print(f"[DEV COMBO ENABLED] {self._combo.isEnabled()}")
        print(f"[DEV BUTTON ENABLED] {self._reload_button.isEnabled()}")

    def _on_mode_changed(self, mode: str) -> None:
        print(f"[PANEL TEXT CHANGED] {mode} | id={id(self)}")
        self.mode_changed.emit(mode)

    def _emit_current_mode(self) -> None:
        mode = self._combo.currentText()
        print(f"[PANEL BUTTON FIRED] {mode} | id={id(self)}")
        self.mode_changed.emit(mode)

    def current_mode(self) -> str:
        return self._combo.currentText()