class AdjacencyMiniPanelAdapter:

    def __init__(self, *, context, refresh_all_callback):
        self._context = context
        self._refresh_all = refresh_all_callback

    # ------------------------------------------------------------------
    # Build context (DATA ONLY)
    # ------------------------------------------------------------------
    def build_context(self, segment_id: str):

        ps = self._context.project_state
        seg = ps.boundary_segments.get(segment_id)

        if not seg:
            return None

        owner_room_id = seg.owner_room_id

        room_options = [
            r.room_id
            for r in ps.rooms.values()
            if r.room_id != owner_room_id
        ]

        print("[CTX]", room_options)

        return {
            "segment_id": segment_id,
            "current_adjacent_room_id": seg.adjacent_room_id,
            "room_options": room_options,
        }

    def _find_pair_segment(self, ps, source_seg, target_room_id):

        if not source_seg.geometry_ref:
            return None

        # Extract edge properly
        parts = source_seg.geometry_ref.split("-")

        if len(parts) < 3:
            return None

        source_edge = f"edge-{parts[-1]}"
        target_edge = self._opposite_edge(source_edge)

        if not target_edge:
            return None

        for seg in ps.boundary_segments.values():
            if (
                    seg.owner_room_id == target_room_id
                    and seg.length_m == source_seg.length_m
                    and isinstance(seg.geometry_ref, str)
                    and seg.geometry_ref.endswith(target_edge)
            ):
                return seg

        return None

    def _opposite_edge(self, edge: str) -> str:
        return {
            "edge-1": "edge-3",
            "edge-2": "edge-4",
            "edge-3": "edge-1",
            "edge-4": "edge-2",
        }.get(edge)

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------
    def commit(self, segment_id: str, adjacent_room_id):

        ps = self._context.project_state
        seg = ps.boundary_segments.get(segment_id)

        if not seg:
            return

        # --------------------------------------------------
        # CLEAR CASE
        # --------------------------------------------------
        if not adjacent_room_id:
            seg.adjacent_room_id = None
            seg.boundary_kind = "EXTERNAL"
            ps.mark_heatloss_dirty()
            self._refresh_all()
            return

        # --------------------------------------------------
        # PRIMARY ASSIGN
        # --------------------------------------------------
        seg.adjacent_room_id = adjacent_room_id
        seg.boundary_kind = "INTER_ROOM"

        # --------------------------------------------------
        # SYMMETRIC PAIRING
        # --------------------------------------------------
        pair = self._find_pair_segment(ps, seg, adjacent_room_id)

        if pair:
            pair.adjacent_room_id = seg.owner_room_id
            pair.boundary_kind = "INTER_ROOM"

        # --------------------------------------------------
        # FINALISE
        # --------------------------------------------------
        ps.mark_heatloss_dirty()
        self._refresh_all()