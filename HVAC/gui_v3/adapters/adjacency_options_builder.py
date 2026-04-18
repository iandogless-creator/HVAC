# ======================================================================
# HVAC/gui_v3/adapters/adjacency_options_builder.py
# ======================================================================

from __future__ import annotations
from typing import Dict, List

from HVAC.gui_v3.dto.adjacency_options import RoomOption, SegmentOption


TOL = 1e-6


def build_adjacency_options(project, source_segment_id: str):
    seg_src = project.boundary_segments[source_segment_id]
    src_len = seg_src.length_m
    src_room = seg_src.owner_room_id

    # --- collect free segments by room ---
    segments_by_room: Dict[str, List[SegmentOption]] = {}

    for seg in project.boundary_segments.values():
        if seg.owner_room_id == src_room:
            continue

        if seg.adjacent_segment_id is not None:
            continue

        # length compatibility (pre-filter for UX)
        enabled = abs(seg.length_m - src_len) <= TOL

        lst = segments_by_room.setdefault(seg.owner_room_id, [])
        lst.append(
            SegmentOption(
                segment_id=seg.segment_id,
                label=_segment_label(seg.segment_id),
                length_m=seg.length_m,
                enabled=enabled,
            )
        )

    # --- build room options ---
    room_options: List[RoomOption] = []

    for room_id, segs in segments_by_room.items():
        enabled_segs = [s for s in segs if s.enabled]
        room_options.append(
            RoomOption(
                room_id=room_id,
                name=_room_name(project, room_id),
                available_count=len(enabled_segs),
                enabled=len(enabled_segs) > 0,
            )
        )

    return room_options, segments_by_room


# ----------------------------------------------------------------------

def _segment_label(segment_id: str) -> str:
    # simple v1 label
    return segment_id.split("-")[-1]  # or "Wall 1/2/3/4"


def _room_name(project, room_id: str) -> str:
    room = project.rooms.get(room_id)
    return room.name if room else room_id