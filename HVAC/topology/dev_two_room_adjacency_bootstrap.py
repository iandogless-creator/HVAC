from __future__ import annotations

from HVAC.topology.boundary_segment_v1 import BoundarySegmentV1


def apply_two_room_adjacency_bootstrap(project) -> None:
    """
    DEV bootstrap — 2-room shared wall

    Assumptions:
    • Exactly 2 rooms
    • Rectangular geometry
    • Shared wall along WIDTH

    Result:
    • 1 INTER_ROOM segment per room (paired)
    • Remaining segments EXTERNAL
    """

    rooms = list(project.rooms.values())
    if len(rooms) != 2:
        return

    r1, r2 = rooms

    g1 = r1.geometry
    g2 = r2.geometry

    if g1 is None or g2 is None:
        return

    L1, W1 = g1.length_m, g1.width_m
    L2, W2 = g2.length_m, g2.width_m

    if not all([L1, W1, L2, W2]):
        return

    # --------------------------------------------------
    # Shared wall length = min widths (robust DEV choice)
    # --------------------------------------------------
    shared_len = float(min(W1, W2))

    # ==================================================
    # ROOM 1
    # ==================================================
    segments_r1 = []

    # External long wall
    segments_r1.append(
        BoundarySegmentV1(
            segment_id=f"{r1.room_id}-wall-ext-1",
            owner_room_id=r1.room_id,
            geometry_ref="edge-L1",
            length_m=float(L1),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        )
    )

    # Shared wall
    segments_r1.append(
        BoundarySegmentV1(
            segment_id=f"{r1.room_id}-wall-int-1",
            owner_room_id=r1.room_id,
            geometry_ref="edge-W1-shared",
            length_m=shared_len,
            boundary_kind="INTER_ROOM",
            adjacent_room_id=r2.room_id,
        )
    )

    # Opposite external wall
    segments_r1.append(
        BoundarySegmentV1(
            segment_id=f"{r1.room_id}-wall-ext-2",
            owner_room_id=r1.room_id,
            geometry_ref="edge-L2",
            length_m=float(L1),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        )
    )

    # Remaining width (ONLY if > 0)
    rem_len_r1 = float(W1 - shared_len)

    if rem_len_r1 > 0.0:
        segments_r1.append(
            BoundarySegmentV1(
                segment_id=f"{r1.room_id}-wall-ext-3",
                owner_room_id=r1.room_id,
                geometry_ref="edge-W1-rem",
                length_m=rem_len_r1,
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )
        )

    # ==================================================
    # ROOM 2 (mirror)
    # ==================================================
    segments_r2 = []

    # External long wall
    segments_r2.append(
        BoundarySegmentV1(
            segment_id=f"{r2.room_id}-wall-ext-1",
            owner_room_id=r2.room_id,
            geometry_ref="edge-L1",
            length_m=float(L2),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        )
    )

    # Shared wall
    segments_r2.append(
        BoundarySegmentV1(
            segment_id=f"{r2.room_id}-wall-int-1",
            owner_room_id=r2.room_id,
            geometry_ref="edge-W2-shared",
            length_m=shared_len,
            boundary_kind="INTER_ROOM",
            adjacent_room_id=r1.room_id,
        )
    )

    # Opposite external wall
    segments_r2.append(
        BoundarySegmentV1(
            segment_id=f"{r2.room_id}-wall-ext-2",
            owner_room_id=r2.room_id,
            geometry_ref="edge-L2",
            length_m=float(L2),
            boundary_kind="EXTERNAL",
            adjacent_room_id=None,
        )
    )

    # Remaining width (ONLY if > 0)
    rem_len_r2 = float(W2 - shared_len)

    if rem_len_r2 > 0.0:
        segments_r2.append(
            BoundarySegmentV1(
                segment_id=f"{r2.room_id}-wall-ext-3",
                owner_room_id=r2.room_id,
                geometry_ref="edge-W2-rem",
                length_m=rem_len_r2,
                boundary_kind="EXTERNAL",
                adjacent_room_id=None,
            )
        )

    # --------------------------------------------------
    # Apply
    # --------------------------------------------------
    project.set_boundary_segments_for_room(r1.room_id, segments_r1)
    project.set_boundary_segments_for_room(r2.room_id, segments_r2)