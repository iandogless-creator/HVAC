"""
comfort_panel.py
----------------

HVACgooee — Comfort Panel (GUI v2)

Responsibilities (LOCKED):
- Display comfort-related information
- Never compute
- Never call engines
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ComfortPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Comfort view (v2 foundation)"))
