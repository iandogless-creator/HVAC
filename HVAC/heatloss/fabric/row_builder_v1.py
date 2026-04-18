# ======================================================================
# HVAC/heatloss/fabric/row_builder_v1.py
# ======================================================================

from __future__ import annotations

from typing import Tuple, List, Dict

from HVAC.heatloss.fabric.fabric_from_segments_v1 import FabricFromSegmentsV1
from HVAC.topology.topology_validator_v1 import TopologyValidatorV1
from HVAC.gui_v3.common.worksheet_row_meta import (
    WorksheetRowMeta,
    WorksheetCellMeta,
)


def build_rows_with_meta(
    project,
    room,
) -> Tuple[List[dict], List[WorksheetRowMeta]]:
    """
    Canonical row builder (Phase IV-B stable)

    Authority
    ---------
    • Builds rows from topology + fabric
    • Computes ΔT via resolver (inside FabricFromSegmentsV1)
    • Attaches segment for UI use
    • Produces WorksheetRowMeta (UI-safe)

    Returns:
        rows: list[dict]
        metas: list[WorksheetRowMeta]
    """

    rows: List[dict] = []
    metas: List[WorksheetRowMeta] = []

    # --------------------------------------------------
    # Validation (topology-aware)
    # --------------------------------------------------
    validation = TopologyValidatorV1.validate_room_adjacency(
        project,
        room.room_id,
    )
    lookup = {v.surface_id: v for v in validation}

    # --------------------------------------------------
    # Fabric rows (single source)
    # --------------------------------------------------
    fabric_rows = FabricFromSegmentsV1.build_rows_for_room(
        project,
        room,
    )

    for src in fabric_rows:
        # --------------------------------------------------
        # Row
        # --------------------------------------------------
        row = {
            "surface_id": src.surface_id,
            "element": src.element,
            "A": src.area_m2,
            "U": src.u_value_W_m2K,
            "dT": src.delta_t_K,
            "Qf": src.qf_W,
            "_segment": getattr(src, "_segment", None),  # critical for adjacency UI
        }

        rows.append(row)
        segment = getattr(src, "_segment", None)
        boundary_kind = getattr(segment, "boundary_kind", None)
        adjacency_editable = boundary_kind in ("EXTERNAL", "INTER_ROOM")

        # --------------------------------------------------
        # Validation → state
        # --------------------------------------------------
        v = lookup.get(src.surface_id)

        if v is None:
            state = "GREEN"
            message = None
        elif v.severity == "ERROR":
            state = "RED"
            message = v.message
        elif v.severity == "WARNING":
            state = "ORANGE"
            message = v.message
        else:
            state = "GREEN"
            message = None

        print(src.surface_id, getattr(src._segment, "boundary_kind", None))
        # --------------------------------------------------
        # Meta (STRICT TYPE)
        # --------------------------------------------------
        # --------------------------------------------------
        # Meta (STRICT TYPE)
        # --------------------------------------------------
        segment = getattr(src, "_segment", None)
        boundary_kind = getattr(segment, "boundary_kind", None)

        adjacency_editable = boundary_kind in ("EXTERNAL", "INTER_ROOM")

        metas.append(
            WorksheetRowMeta(
                surface_id=str(src.surface_id),
                element=str(src.element),
                state=state,
                message=message,
                adjacency_editable=adjacency_editable,
                columns={
                    0: WorksheetCellMeta(None, False, "readonly"),
                    1: WorksheetCellMeta("A", True, "cell"),
                    2: WorksheetCellMeta("U", True, "cell"),
                    3: WorksheetCellMeta(None, False, "derived"),
                    4: WorksheetCellMeta(None, False, "derived"),
                },
            )
        )
    print(src.surface_id, getattr(src._segment, "boundary_kind", None))
    return rows, metas