# ======================================================================
# HVAC/heatloss/fabric/row_builder_v1.py
# ======================================================================

from __future__ import annotations

from typing import Tuple, List

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
    Canonical row builder (Phase IV-B / V-C stable)

    Authority
    ---------
    • Builds rows from topology + fabric
    • Uses generate_fabric_from_topology as the active fabric bridge
    • Carries BoundarySegmentV1 through as _segment for UI projection
    • Produces WorksheetRowMeta for HLP row identity/editability

    Notes
    -----
    Rows are plain dicts.
    GUI adapters must read dict keys, not only object attributes.
    """

    rows: List[dict] = []
    metas: List[WorksheetRowMeta] = []

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    validation = TopologyValidatorV1.validate_room_adjacency(
        project,
        room.room_id,
    )
    lookup = {v.surface_id: v for v in validation}

    # --------------------------------------------------
    # Fabric rows
    # --------------------------------------------------

    from HVAC.topology.dev_topology_fabric_bridge import generate_fabric_from_topology

    fabric_rows = generate_fabric_from_topology(
        project,
        room,
    )

    for src in fabric_rows:
        segment = getattr(src, "_segment", None)
        boundary_kind = getattr(segment, "boundary_kind", None)
        geometry_ref = getattr(segment, "geometry_ref", None)
        adjacent_room_id = getattr(segment, "adjacent_room_id", None)

        # --------------------------------------------------
        # Row projection
        # --------------------------------------------------

        row = {
            "surface_id": src.surface_id,
            "element": src.element,
            "A": src.area_m2,
            "U": src.u_value_W_m2K,
            "dT": src.delta_t_K,
            "Qf": src.qf_W,

            # Critical topology projection fields
            "_segment": segment,
            "boundary_kind": boundary_kind,
            "geometry_ref": geometry_ref,
            "adjacent_room_id": adjacent_room_id,
        }

        rows.append(row)

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

        # --------------------------------------------------
        # Editability
        # --------------------------------------------------

        adjacency_editable = boundary_kind in ("EXTERNAL", "INTER_ROOM")

        # --------------------------------------------------
        # Meta
        # --------------------------------------------------

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

    return rows, metas