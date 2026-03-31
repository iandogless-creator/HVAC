# ======================================================================
# HVAC/gui_v3/panels/dev_settings_panel.py
# ======================================================================

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox


class DevSettingsPanel(QWidget):
    """
    DEV panel — topology mode switch

    Authority
    ---------
    • Emits intent only
    • No ProjectState access
    """

    topology_mode_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        label = QLabel("Topology Mode (DEV)")
        layout.addWidget(label)

        self._combo = QComboBox(self)
        self._combo.addItems(["bootstrap", "resolver"])
        layout.addWidget(self._combo)

        self._combo.currentTextChanged.connect(self._emit_mode_changed)

    def _emit_mode_changed(self, mode: str) -> None:
        self.topology_mode_changed.emit(mode)