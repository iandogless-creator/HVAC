# ======================================================================
# HVAC/gui_v2/modes/hydronics/hydronic_skeleton_view.py
# ======================================================================

"""
HVACgooee — Hydronic Skeleton View (GUI)
---------------------------------------

Read-only visualisation of hydronic system intent.
NO mutation.
NO calculations.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
)

from HVAC.hydronics.models.hydronic_skeleton_v1 import HydronicSkeletonV1


class HydronicSkeletonView(QWidget):
    """
    Displays the current hydronic skeleton (intent only).
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._skeleton: HydronicSkeletonV1 | None = None

        self._layout = QVBoxLayout(self)

        # Persistent status label (NEVER deleted)
        self._lbl_status = QLabel("No hydronic system defined.")
        self._lbl_status.setStyleSheet("color: #888;")
        self._layout.addWidget(self._lbl_status)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def load_skeleton(self, skeleton: HydronicSkeletonV1) -> None:
        self._clear_dynamic()
        self._skeleton = skeleton

        self._lbl_status.hide()

        # ---- Boiler ----
        boiler_box = QGroupBox("Boiler")
        boiler_layout = QVBoxLayout(boiler_box)
        boiler_layout.addWidget(QLabel(f"• {skeleton.boiler.name}"))
        self._layout.addWidget(boiler_box)

        # ---- Terminals ----
        terminals_box = QGroupBox("Terminals")
        terminals_layout = QVBoxLayout(terminals_box)

        for term in skeleton.terminals.values():
            terminals_layout.addWidget(
                QLabel(
                    f"• {term.room_name} — "
                    f"{term.design_heat_loss_w:.0f} W"
                )
            )

        self._layout.addWidget(terminals_box)
        self._layout.addStretch(1)

    def clear(self) -> None:
        self._clear_dynamic()
        self._lbl_status.setText("No hydronic system defined.")
        self._lbl_status.show()

    # ------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------

    def _clear_dynamic(self) -> None:
        """
        Remove all widgets EXCEPT the persistent status label.
        """
        for i in reversed(range(self._layout.count())):
            item = self._layout.itemAt(i)
            widget = item.widget()

            if widget is None:
                continue

            if widget is self._lbl_status:
                continue

            self._layout.removeWidget(widget)
            widget.deleteLater()
