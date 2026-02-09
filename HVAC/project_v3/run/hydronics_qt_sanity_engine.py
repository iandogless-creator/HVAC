# ======================================================================
# HVAC/project_v3/run/hydronics_qt_sanity_engine.py
# ======================================================================

from __future__ import annotations


def run_hydronics_qt_sanity(project) -> float:
    """
    Hydronics Qt Sanity Engine (v0)

    PURPOSE
    -------
    Verifies that authoritative heat-loss Qt is available to hydronics.

    RULES (LOCKED)
    --------------
    • READ-ONLY
    • NO mutation
    • NO topology use
    • NO physics
    • NO inference
    • FAIL LOUD

    Returns
    -------
    float
        Authoritative Qt (W)

    Raises
    ------
    RuntimeError
        If ProjectState is invalid or Qt is missing.
    """

    # ------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------
    if project is None:
        raise RuntimeError("[HydronicsQtSanity] project is None")

    if not hasattr(project, "project_state"):
        raise RuntimeError("[HydronicsQtSanity] project has no project_state")

    ps = project.project_state

    if ps is None:
        raise RuntimeError("[HydronicsQtSanity] ProjectState is None")

    if not getattr(ps, "heatloss_valid", False):
        raise RuntimeError(
            "[HydronicsQtSanity] heat-loss is not authoritative"
        )

    qt = getattr(ps, "heatloss_qt_w", None)
    if qt is None:
        raise RuntimeError(
            "[HydronicsQtSanity] heatloss_qt_w is None"
        )

    try:
        qt = float(qt)
    except Exception:
        raise RuntimeError(
            f"[HydronicsQtSanity] Qt is not numeric: {qt!r}"
        )

    if qt <= 0.0:
        raise RuntimeError(
            f"[HydronicsQtSanity] Qt is non-positive: {qt}"
        )

    # ------------------------------------------------------------
    # Success
    # ------------------------------------------------------------
    print(
        f"[HydronicsQtSanity] OK — authoritative Qt received: {qt:.2f} W"
    )

    return qt
