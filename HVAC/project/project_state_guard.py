# ======================================================================
# HVAC/project/project_state_guard.py
# ======================================================================

"""
ProjectState Guard — GUI Vitiation Rules (CANONICAL)

Purpose
-------
Explicitly nullify any attempt to promote GUI-calculated values
into authoritative engineering state.

RULES (LOCKED)
--------------
• GUI values are always provisional (preview only)
• ONLY engine runners may mark validity True
• Guard is idempotent (safe to call repeatedly)
• No prints by default (optional trace flag)
"""

from __future__ import annotations

from HVAC.project.project_state import ProjectState

TRACE_GUARD = False


def vitiate_gui_heatloss(ps: ProjectState, *, reason: str = "") -> None:
    """
    GUI vitiation for heat-loss.

    Call this whenever GUI changes anything that could affect heat-loss,
    OR whenever GUI calculates preview Qt.

    Effects:
    - heatloss_valid = False
    - heatloss_qt_w = None  (because it did not come from engine)
    - downstream hydronics invalidated
    """

    if ps is None:
        return

    ps.heatloss_valid = False
    ps.heatloss_qt_w = None

    # Downstream must be invalid if upstream is not authoritative
    ps.hydronics_valid = False
    ps.hydronics_estimate_result = None

    if TRACE_GUARD and reason:
        print(f"🧨 vitiate_gui_heatloss: {reason}")


def vitiate_gui_hydronics(ps: ProjectState, *, reason: str = "") -> None:
    """
    Optional future hook: GUI invalidation for hydronics-only edits.

    Safe default now: invalidate hydronics results.
    """
    if ps is None:
        return

    ps.hydronics_valid = False
    ps.hydronics_estimate_result = None

    if TRACE_GUARD and reason:
        print(f"🧨 vitiate_gui_hydronics: {reason}")
