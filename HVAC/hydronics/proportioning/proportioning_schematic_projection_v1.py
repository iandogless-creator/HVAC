# ======================================================================
# HVAC/hydronics/proportioning/proportioning_schematic_projection_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.hydronics.proportioning.branch_proportioning_summary_v1 import (
    build_branch_proportioning_summary_v1,
)
from HVAC.hydronics.proportioning.proportioning_schematic_dto_v1 import (
    EDGE_ROLE_COMMON_MAIN,
    EDGE_ROLE_NON_INDEX_BRANCH_TERMINAL,
    EDGE_ROLE_SELECTED_INDEX_ROUTE,
    EDGE_ROLE_UNRESOLVED,
    NODE_ROLE_COMMON_MAIN,
    NODE_ROLE_HEAT_SOURCE,
    NODE_ROLE_NON_INDEX_BRANCH_TERMINAL,
    NODE_ROLE_NO_EMITTER_UNRESOLVED,
    NODE_ROLE_SELECTED_INDEX_ROUTE,
    ProportioningSchematicEdgeV1,
    ProportioningSchematicNodeV1,
    ProportioningSchematicV1,
)


# ======================================================================
# Public builder
# ======================================================================

def build_proportioning_schematic_v1(project_state: Any) -> ProportioningSchematicV1:
    """
    Build a read-only proportioning logic schematic.

    H-S1 scope:
    • derive from H-R branch/proportioning summary rows
    • create schematic nodes and edges
    • no GUI rendering
    • no ProjectState mutation
    • no pressure loss
    • no pipe sizing
    • no balancing
    """

    summary_rows = build_branch_proportioning_summary_v1(project_state)

    nodes_by_id: dict[str, ProportioningSchematicNodeV1] = {}
    edges: list[ProportioningSchematicEdgeV1] = []

    # --------------------------------------------------
    # Fixed v1 anchor nodes
    # --------------------------------------------------
    heat_source_id = "heat-source"
    common_main_id = "common-main"

    nodes_by_id[heat_source_id] = ProportioningSchematicNodeV1(
        node_id=heat_source_id,
        label="Boiler / Heat Source",
        role=NODE_ROLE_HEAT_SOURCE,
        lane=0,
        order=0,
        status="Projection only",
    )

    nodes_by_id[common_main_id] = ProportioningSchematicNodeV1(
        node_id=common_main_id,
        label="Common main",
        role=NODE_ROLE_COMMON_MAIN,
        lane=0,
        order=1,
        status="Projection only",
    )

    # --------------------------------------------------
    # Common/main edge
    # --------------------------------------------------
    common_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Common/main"
    ]

    common_row = common_rows[0] if common_rows else None

    edges.append(
        ProportioningSchematicEdgeV1(
            edge_id="edge-heat-source-common-main",
            from_node_id=heat_source_id,
            to_node_id=common_main_id,
            role=EDGE_ROLE_COMMON_MAIN,
            flow_label=(
                getattr(common_row, "flow_label", "—")
                if common_row is not None
                else "—"
            ),
            basis=(
                getattr(common_row, "basis", "Common/main projection")
                if common_row is not None
                else "Common/main projection"
            ),
            status=(
                getattr(common_row, "status", "Projection only")
                if common_row is not None
                else "Projection only"
            ),
        )
    )

    # --------------------------------------------------
    # Selected index route spine
    # --------------------------------------------------
    selected_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Selected index route"
    ]

    route_order = 2

    first_route_node_id: str | None = None

    for row_index, row in enumerate(selected_rows, start=1):
        from_label = str(getattr(row, "from_label", "") or "—")
        to_label = str(getattr(row, "to_label", "") or "—")

        from_node_id = _node_id("route", from_label)
        to_node_id = _node_id("route", to_label)

        if first_route_node_id is None:
            first_route_node_id = from_node_id

        if from_node_id not in nodes_by_id:
            nodes_by_id[from_node_id] = ProportioningSchematicNodeV1(
                node_id=from_node_id,
                label=from_label,
                role=NODE_ROLE_SELECTED_INDEX_ROUTE,
                lane=0,
                order=route_order,
                status="Selected index route",
            )
            route_order += 1

        if to_node_id not in nodes_by_id:
            nodes_by_id[to_node_id] = ProportioningSchematicNodeV1(
                node_id=to_node_id,
                label=to_label,
                role=NODE_ROLE_SELECTED_INDEX_ROUTE,
                lane=0,
                order=route_order,
                status="Selected index route",
            )
            route_order += 1

        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id=f"edge-selected-index-route-{row_index}",
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                role=EDGE_ROLE_SELECTED_INDEX_ROUTE,
                flow_label=str(getattr(row, "flow_label", "—") or "—"),
                basis=str(getattr(row, "basis", "") or ""),
                status=str(getattr(row, "status", "") or ""),
            )
        )

    # Link common main to the first selected route node for visual continuity.
    if first_route_node_id is not None:
        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id="edge-common-main-selected-route-entry",
                from_node_id=common_main_id,
                to_node_id=first_route_node_id,
                role=EDGE_ROLE_SELECTED_INDEX_ROUTE,
                flow_label="—",
                basis="Selected index route entry",
                status="Projection only",
            )
        )

    # --------------------------------------------------
    # Non-index branch terminals
    # --------------------------------------------------
    branch_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Non-index branch terminals"
    ]

    for branch_index, row in enumerate(branch_rows, start=1):
        label = str(getattr(row, "from_label", "") or "—")
        node_id = _node_id("branch", label)

        nodes_by_id[node_id] = ProportioningSchematicNodeV1(
            node_id=node_id,
            label=label,
            role=NODE_ROLE_NON_INDEX_BRANCH_TERMINAL,
            lane=-1,
            order=branch_index,
            status="Non-index branch terminal",
        )

        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id=f"edge-non-index-branch-terminal-{branch_index}",
                from_node_id=node_id,
                to_node_id=common_main_id,
                role=EDGE_ROLE_NON_INDEX_BRANCH_TERMINAL,
                flow_label=str(getattr(row, "flow_label", "—") or "—"),
                basis=str(getattr(row, "basis", "") or ""),
                status=str(getattr(row, "status", "") or ""),
            )
        )

    # --------------------------------------------------
    # No-emitter / unresolved
    # --------------------------------------------------
    unresolved_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "No-emitter / unresolved"
    ]

    for unresolved_index, row in enumerate(unresolved_rows, start=1):
        label = str(getattr(row, "from_label", "") or "—")
        node_id = _node_id("unresolved", label)

        nodes_by_id[node_id] = ProportioningSchematicNodeV1(
            node_id=node_id,
            label=label,
            role=NODE_ROLE_NO_EMITTER_UNRESOLVED,
            lane=1,
            order=unresolved_index,
            status="No-emitter / unresolved",
        )

        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id=f"edge-no-emitter-unresolved-{unresolved_index}",
                from_node_id=node_id,
                to_node_id=common_main_id,
                role=EDGE_ROLE_UNRESOLVED,
                flow_label=str(getattr(row, "flow_label", "—") or "—"),
                basis=str(getattr(row, "basis", "") or ""),
                status=str(getattr(row, "status", "") or ""),
            )
        )

    nodes = tuple(
        sorted(
            nodes_by_id.values(),
            key=lambda node: (node.lane, node.order, node.label),
        )
    )

    return ProportioningSchematicV1(
        nodes=nodes,
        edges=tuple(edges),
        title="Proportioning schematic",
        basis="Derived from H-R branch/proportioning summary",
    )


# ======================================================================
# Helpers
# ======================================================================

def _node_id(prefix: str, label: str) -> str:
    slug = (
        str(label)
        .strip()
        .lower()
        .replace("/", "-")
        .replace(" ", "-")
        .replace("—", "-")
    )

    slug = "".join(
        char for char in slug
        if char.isalnum() or char in {"-"}
    )

    while "--" in slug:
        slug = slug.replace("--", "-")

    slug = slug.strip("-") or "unknown"

    return f"{prefix}-{slug}"