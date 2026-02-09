# ======================================================================
# HVACgooee — Environment Panel (GUI v3)
# Phase: GUI v3 — Observer
# Sub-Phase: Phase B (Static Layout)
# Status: FROZEN
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,   # ← ADD THIS
    QLabel,
    QSpacerItem,
    QSizePolicy,
)

class EnvironmentPanel(QWidget):
    """
    GUI v3 — Environment Panel (Observer)

    Phase B:
    • Static layout only
    • Displays project-level boundary conditions
    • No room data
    • No setters
    • No authority
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.setMinimumWidth(260)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # ------------------------------
        # Environment
        # ------------------------------
        header_env = QLabel("Environment")
        header_env.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(header_env)

        self._row_external = self._row("External design temperature:", "—")
        self._external_temp_value = self._row_external._value_label
        root.addWidget(self._row_external)

        root.addWidget(self._row_external)

        root.addItem(QSpacerItem(1, 16, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ------------------------------
        # Calculation
        # ------------------------------
        header_calc = QLabel("Calculation")
        header_calc.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(header_calc)

        self._row_dt = self._row("ΔT (reference):", "—")
        self._row_method = self._row("Method:", "—")

        root.addWidget(self._row_dt)
        root.addWidget(self._row_method)

        root.addStretch(1)

    # ------------------------------------------------------------------
    # Helpers (layout only)
    # ------------------------------------------------------------------

    def _row(self, label_text: str, value_text: str) -> QWidget:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        value = QLabel(value_text)

        layout.addWidget(label)
        layout.addWidget(value)
        layout.addStretch(1)

        # Allow caller to bind value later
        row._value_label = value  # intentional, internal use only

        return row

    # ------------------------------------------------------------------
    # Presentation setters (GUI v3)
    # ------------------------------------------------------------------
    def set_external_temperature(self, outside_c: float | None) -> None:
        """
        Display external design temperature.

        Presentation only.
        No authority.
        """
        if outside_c is None:
            self._external_temp_value.setText("—")
        else:
            self._external_temp_value.setText(f"{outside_c:.1f} °C")
