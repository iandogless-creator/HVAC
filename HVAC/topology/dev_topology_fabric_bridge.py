# ======================================================================
# HVAC/topology/dev_topology_fabric_bridge.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from HVAC.topology.topology_resolver_v1 import TopologyResolverV1
from HVAC.topology.adjacency_delta_t_resolver import AdjacencyDeltaTResolver


@dataclass(slots=True)
class DevFabricRow:
    element_id: str
    room_id: str
    surface_class: str
    area_m2: float
    length_m: float
    height_m: float
    geometry_ref: str

    boundary_kind: str | None = None
    adjacent_room_id: str | None = None
    delta_t_K: float | None = None


def generate_fabric_from_topology(project_state: Any, room: Any) -> list[DevFabricRow]:
    """
    Phase IV-A DEV bridge.

    Behaviour
    ---------
    • Resolve authoritative boundary segments if present
    • Fall back to external-edge generation if absent
    • Continue generating floor + roof from room geometry
    """

    rows: list[DevFabricRow] = []

    room_id = getattr(room, "room_id", None) or getattr(room, "id", None)
    if not room_id:
        return rows

    # --------------------------------------------------
    # Geometry inputs
    # --------------------------------------------------
    geometry = getattr(room, "geometry", None)
    polygon = getattr(geometry, "polygon", None) if geometry else None

    height_m = getattr(geometry, "height_m", None) if geometry else None
    if height_m is None:
        height_m = getattr(project_state.environment, "default_room_height_m", 0.0)

    # --------------------------------------------------
    # Boundary-derived wall rows
    # --------------------------------------------------
    segments = TopologyResolverV1.resolve_room_boundaries(project_state, room)

    for seg in segments:
        area_m2 = seg.length_m * height_m

        if seg.boundary_kind == "EXTERNAL":
            surface_class = "external_wall"
        elif seg.boundary_kind == "INTER_ROOM":
            surface_class = "internal_partition"
        elif seg.boundary_kind == "ADIABATIC":
            surface_class = "adiabatic_wall"
        else:
            surface_class = "unknown_wall"

        delta_t_K = AdjacencyDeltaTResolver.resolve_delta_t_K(
            project_state=project_state,
            owner_room=room,
            boundary_kind=seg.boundary_kind,
            adjacent_room_id=seg.adjacent_room_id,
        )

        rows.append(
            DevFabricRow(
                element_id=seg.segment_id,
                room_id=room_id,
                surface_class=surface_class,
                area_m2=area_m2,
                length_m=seg.length_m,
                height_m=height_m,
                geometry_ref=seg.geometry_ref,
                boundary_kind=seg.boundary_kind,
                adjacent_room_id=seg.adjacent_room_id,
                delta_t_K=delta_t_K,
            )
        )

    # --------------------------------------------------
    # Floor + roof from geometry
    # --------------------------------------------------
    area_m2 = _polygon_area_m2(polygon)
    if area_m2 and area_m2 > 0.0:
        rows.append(
            DevFabricRow(
                element_id=f"{room_id}:floor",
                room_id=room_id,
                surface_class="floor",
                area_m2=area_m2,
                length_m=0.0,
                height_m=0.0,
                geometry_ref=f"{room_id}:floor",
                boundary_kind=None,
                adjacent_room_id=None,
                delta_t_K=_resolve_default_envelope_delta_t(project_state, room),
            )
        )

        rows.append(
            DevFabricRow(
                element_id=f"{room_id}:roof",
                room_id=room_id,
                surface_class="roof",
                area_m2=area_m2,
                length_m=0.0,
                height_m=0.0,
                geometry_ref=f"{room_id}:roof",
                boundary_kind=None,
                adjacent_room_id=None,
                delta_t_K=_resolve_default_envelope_delta_t(project_state, room),
            )
        )

    return rows


def _polygon_area_m2(polygon: list[tuple[float, float]] | None) -> float | None:
    if not polygon or len(polygon) < 3:
        return None

    area = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        area += x1 * y2 - x2 * y1

    return abs(area) * 0.5


def _resolve_default_envelope_delta_t(project_state: Any, room: Any) -> float | None:
    return AdjacencyDeltaTResolver.resolve_delta_t_K(
        project_state=project_state,
        owner_room=room,
        boundary_kind="EXTERNAL",
        adjacent_room_id=None,
    )