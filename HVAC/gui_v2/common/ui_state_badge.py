from __future__ import annotations

from PySide6.QtWidgets import QLabel


def apply_badge_state(
    badge: QLabel,
    *,
    text: str,
    tooltip: str,
    bg: str,
    fg: str,
    border: str,
) -> None:
    """
    Canonical badge state helper.

    LOCKED:
    • Sets visual state + tooltip together
    • Prevents colour/meaning drift
    • GUI-only

    Colours are CSS strings.
    """
    badge.setText(text)
    badge.setToolTip(tooltip)
    badge.setStyleSheet(
        f"""
        QLabel {{
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            font-weight: bold;
            padding: 2px 6px;
        }}
        """
    )
