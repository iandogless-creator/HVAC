# ======================================================================
# HVAC/gui_v3/panels/hlpe_overlay_panel.py
# ======================================================================
# HVACgooee — HLPEOverlayPanel (GUI v3)
# Phase: G-A — Overlay shell
# Status: ACTIVE (skeleton)
# ======================================================================

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class HLPEOverlayPanel(QWidget):
    """
    HLPEOverlayPanel — GUI v3

    Phase G-A:
    • Visual overlay shell only
    • No edit widgets yet
    • No authority
    • Hidden by default
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.hide()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        banner = QLabel("EDIT MODE")
        banner.setStyleSheet(
            """
            QLabel {
                background-color: #d9822b;
                color: white;
                font-weight: 600;
                padding: 6px;
            }
            """
        )

        root.addWidget(banner)
        root.addStretch(1)


    def close(self) -> None:
        self._panel.exit()

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _on_applied(self, payload: dict) -> None:
        """
        Phase G-A:
        • Close only
        • No commit
        """
        self.close()

    def _on_cancelled(self) -> None:
        self.close()

    # ------------------------------------------------------------------
    # ESC handling
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if self._panel.isVisible():
                self.close()
                return True
        return False
