# ======================================================================
# HVAC/hydronics/proportioning/balancing_point_assumption_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BalancingPointAssumptionV1:
    """
    Explicit v1 balancing point assumption.

    This does not select a valve.
    This does not apply balancing.
    This does not mutate ProjectState.
    """

    scope: str = "route/subleg"
    application_point: str = "route/subleg balancing point"
    added_resistance_basis: str = "required added resistance Δp"
    room_level_control: str = "not used in v1"
    emitter_level_control: str = "not used in v1"
    valve_selection: str = "not selected"
    status: str = "Balancing point assumption defined"


def get_default_balancing_point_assumption_v1() -> BalancingPointAssumptionV1:
    """
    Return the canonical v1 balancing point assumption.

    Authority boundary:
    • no ProjectState mutation
    • no balancing valve selection
    • no lockshield setting
    • no pump selection
    • no pipe resizing
    • no committed return arrangement
    """
    return BalancingPointAssumptionV1()