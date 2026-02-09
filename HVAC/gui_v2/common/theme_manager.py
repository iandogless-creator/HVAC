"""
theme_manager_v2.py
-------------------

HVACgooee — Global Theme Manager (v2)

CANONICAL THEME: DARK

Responsibilities (LOCKED):
- Apply ONE global stylesheet
- Define visual topology & hierarchy
- No business logic
- No widget ownership
"""

from __future__ import annotations
from PySide6.QtWidgets import QApplication


class ThemeManagerV2:
    """
    Global GUI theme controller.

    Applied ONCE at application startup.
    """

    @staticmethod
    def apply(app: QApplication) -> None:
        app.setStyleSheet(_DARK_THEME_QSS)


# ============================================================================
# HVACgooee v2 — CANONICAL DARK THEME
# ============================================================================

_DARK_THEME_QSS = """
/* -------------------------------------------------
   Base
------------------------------------------------- */
QMainWindow {
    background-color: #1f1f1f;
}

QWidget {
    background-color: #252525;
    color: #d0d0d0;
    font-size: 13px;
}

/* -------------------------------------------------
   Panels / topology
------------------------------------------------- */
QFrame,
QGroupBox {
    background-color: #2b2b2b;
    border: 1px solid #2a6df4;
    border-radius: 6px;
}

QGroupBox {
    margin-top: 8px;
    padding: 10px;
    font-weight: 600;
}

/* -------------------------------------------------
   Focused topology
------------------------------------------------- */
QWidget:focus,
QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 2px solid #2a6df4;
}

/* -------------------------------------------------
   Inputs
------------------------------------------------- */
QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #2a6df4;
    border-radius: 4px;
    padding: 4px 6px;
}

/* -------------------------------------------------
   Buttons (topology-first)
------------------------------------------------- */
QPushButton {
    background-color: transparent;
    border: 1px solid #2a6df4;
    border-radius: 4px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #2f2f2f;
    border: 2px solid #2a6df4;
}

/* ACTIVE / SELECTED */
QPushButton:checked {
    border: 3px solid #2a6df4;
    background-color: #1a2533;
    font-weight: bold;
}

/* -------------------------------------------------
   Tables
------------------------------------------------- */
QHeaderView::section {
    background-color: #232323;
    color: #d0d0d0;
    font-weight: bold;
    border-bottom: 2px solid #2a6df4;
    padding: 6px;
}

QTableView {
    background-color: #1f1f1f;
    gridline-color: transparent;
}

QTableView::item:selected {
    background-color: #1a2533;
    border: 2px solid #2a6df4;
}

/* -------------------------------------------------
   Labels
------------------------------------------------- */
QLabel[result="true"] {
    font-weight: bold;
}

/* -------------------------------------------------
   Education dock
------------------------------------------------- */
QTextBrowser {
    background-color: #1e1e1e;
    border-left: 3px solid #2a6df4;
    padding: 8px;
    color: #cfd8ff;
}
"""
