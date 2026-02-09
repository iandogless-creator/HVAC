# ======================================================================
# HVACgooee — GUI v3 Sizing Constants
#
# PURPOSE
# -------
# Canonical sizing rules for GUI v3 widgets.
#
# These values express *intent*, not style.
# Widgets must opt-in to expansion explicitly.
#
# RULES (LOCKED)
# --------------
# • Labels size to content
# • Combos size to contents
# • Toggles consume minimum space
# • Entry / result fields declare width explicitly
# ======================================================================

from PySide6.QtWidgets import QSizePolicy


# ----------------------------------------------------------------------
# Label sizing
# ----------------------------------------------------------------------
LABEL_POLICY = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)


# ----------------------------------------------------------------------
# Toggle sizing (checkboxes, switches)
# ----------------------------------------------------------------------
TOGGLE_POLICY = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


# ----------------------------------------------------------------------
# Combo box sizing
# ----------------------------------------------------------------------
COMBO_POLICY = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


# ----------------------------------------------------------------------
# Entry / result field widths (pixels)
# ----------------------------------------------------------------------
FIELD_WIDTH_XS = 48     # flags, tiny numeric results
FIELD_WIDTH_S  = 64     # temperatures, ΔT
FIELD_WIDTH_M  = 96     # areas, powers
FIELD_WIDTH_L  = 140    # flow rates, capacities
FIELD_WIDTH_XL = 180    # descriptions, references


# ----------------------------------------------------------------------
# Helper functions (optional, safe)
# ----------------------------------------------------------------------
def apply_label_policy(widget) -> None:
    widget.setSizePolicy(LABEL_POLICY)


def apply_toggle_policy(widget) -> None:
    widget.setSizePolicy(TOGGLE_POLICY)


def apply_combo_policy(combo) -> None:
    combo.setSizeAdjustPolicy(combo.AdjustToContents)
    combo.setSizePolicy(COMBO_POLICY)


def apply_field_width(widget, width: int) -> None:
    widget.setFixedWidth(width)
