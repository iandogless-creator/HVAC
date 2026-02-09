"""
about_panel.py
---------------

HVACgooee — About Panel (GUI v2)

Responsibilities (LOCKED)
-------------------------
- Display static project / version information
- Never compute
- Never call engines
- Never depend on GuiViewState
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class AboutPanel(QWidget):
    """
    About / information panel.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("HVACgooee"))
        layout.addWidget(QLabel("Version: v2 (foundation)"))
        layout.addWidget(QLabel("Open-source HVAC engineering toolkit"))
        layout.addStretch(1)

