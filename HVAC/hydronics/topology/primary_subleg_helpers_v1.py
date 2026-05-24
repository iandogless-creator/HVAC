# ======================================================================
# HVAC/hydronics/topology/primary_subleg_helpers_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.hydronics.topology.hydronic_topology_v1 import (
    HydronicLegV1,
    HydronicSublegV1,
    HydronicTopologyV1,
)


# ======================================================================
# Constants
# ======================================================================

PRIMARY_SUBLEG_ID_SUFFIX = "primary-subleg"
PRIMARY_SUBLEG_LABEL = "Primary subleg"


# ======================================================================
# Public helpers
# ======================================================================

def primary_subleg_id_for_leg(leg_id: str) -> str:
    """
    Return the conventional primary-subleg id for a leg.
    """

    return f"{leg_id}-{PRIMARY_SUBLEG_ID_SUFFIX}"


def find_primary_subleg_for_leg(
    leg: HydronicLegV1,
) -> HydronicSublegV1 | None:
    """
    Return the primary subleg for a leg, if present.

    H-S7 transitional rule:
    - Prefer explicit primary subleg id.
    - Fall back to first subleg if there is no explicit match.
    """

    if not leg.sublegs:
        return None

    expected_id = primary_subleg_id_for_leg(leg.leg_id)

    for subleg in leg.sublegs:
        if subleg.subleg_id == expected_id:
            return subleg

    return leg.sublegs[0]


def ensure_primary_subleg_for_leg(
    leg: HydronicLegV1,
) -> HydronicSublegV1:
    """
    Ensure a leg has a primary room-carrying subleg.

    Transitional behaviour:
    - If a primary subleg already exists, return it.
    - If legacy leg.route_room_ids exists, migrate those route rooms into
      the new primary subleg.
    - Keep legacy leg.route_room_ids untouched for compatibility during H-S7.
    """

    existing = find_primary_subleg_for_leg(leg)

    if existing is not None:
        return existing

    route_room_ids = list(getattr(leg, "route_room_ids", []) or [])
    index_room_id = getattr(leg, "index_room_id", None)

    primary_subleg = HydronicSublegV1(
        subleg_id=primary_subleg_id_for_leg(leg.leg_id),
        label=PRIMARY_SUBLEG_LABEL,
        origin_room_id="",
        route_room_ids=route_room_ids,
        index_room_id=index_room_id,
        sublegs=[],
    )

    leg.sublegs.insert(0, primary_subleg)

    return primary_subleg


def ensure_primary_sublegs_for_topology(
    topology: HydronicTopologyV1,
) -> HydronicTopologyV1:
    """
    Ensure every leg in the topology has a primary subleg.

    Returns the same topology object for convenient chaining.
    """

    for leg in topology.legs:
        ensure_primary_subleg_for_leg(leg)

    return topology


def primary_subleg_for_leg_id(
    topology: HydronicTopologyV1,
    leg_id: str,
) -> HydronicSublegV1:
    """
    Return the primary subleg for a leg id, creating it if needed.
    """

    leg = _require_leg(topology, leg_id)
    return ensure_primary_subleg_for_leg(leg)


def primary_route_room_ids_for_leg(
    topology: HydronicTopologyV1,
    leg_id: str,
) -> list[str]:
    """
    Return the route_room_ids for a leg's primary subleg.

    This is the H-S7-safe replacement for direct leg.route_room_ids reads.
    """

    subleg = primary_subleg_for_leg_id(topology, leg_id)
    return subleg.route_room_ids


def set_primary_route_room_ids_for_leg(
    topology: HydronicTopologyV1,
    leg_id: str,
    room_ids: list[str],
) -> HydronicTopologyV1:
    """
    Replace the route_room_ids on a leg's primary subleg.

    Transitional compatibility:
    - Writes the primary subleg route.
    - Also mirrors to legacy leg.route_room_ids if that field exists.
    """

    leg = _require_leg(topology, leg_id)
    subleg = ensure_primary_subleg_for_leg(leg)

    clean_room_ids = [str(room_id) for room_id in room_ids]

    subleg.route_room_ids[:] = clean_room_ids

    if hasattr(leg, "route_room_ids"):
        leg.route_room_ids[:] = list(clean_room_ids)

    return topology


def primary_index_room_id_for_leg(
    topology: HydronicTopologyV1,
    leg_id: str,
) -> str | None:
    """
    Return the index room id for the primary subleg of a leg.
    """

    subleg = primary_subleg_for_leg_id(topology, leg_id)
    return subleg.index_room_id


def set_primary_index_room_id_for_leg(
    topology: HydronicTopologyV1,
    leg_id: str,
    room_id: str | None,
) -> HydronicTopologyV1:
    """
    Set the index room id on a leg's primary subleg.

    Transitional compatibility:
    - Writes primary subleg index_room_id.
    - Also mirrors to legacy leg.index_room_id.
    """

    leg = _require_leg(topology, leg_id)
    subleg = ensure_primary_subleg_for_leg(leg)

    clean_room_id = str(room_id) if room_id else None

    subleg.index_room_id = clean_room_id
    leg.index_room_id = clean_room_id

    return topology


# ======================================================================
# Internal helpers
# ======================================================================

def _require_leg(
    topology: HydronicTopologyV1,
    leg_id: str,
) -> HydronicLegV1:
    for leg in topology.legs:
        if leg.leg_id == leg_id:
            return leg

    raise ValueError(f"Hydronic leg not found: {leg_id!r}")