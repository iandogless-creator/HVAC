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

def build_proportioning_schematic_v1(
    project_state: Any,
    *,
    selected_leg_id: str | None = None,
    selected_subleg_id: str | None = None,
    selected_route_label: str | None = None,
) -> ProportioningSchematicV1:
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
    topology = getattr(project_state, "hydronic_topology", None)

    if topology is not None:
        return _build_from_hydronic_topology(
            project_state,
            topology,
            selected_leg_id=selected_leg_id,
            selected_subleg_id=selected_subleg_id,
            selected_route_label=selected_route_label,
        )
    summary_rows = build_branch_proportioning_summary_v1(project_state)
    index_room_label = _resolve_index_room_label(project_state)

    def _is_index_node(label: str) -> bool:
        return _is_index_label(label, index_room_label)

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
    # Selected index-route subleg spine
    # --------------------------------------------------
    selected_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Selected index route"
    ]

    route_order = 2

    first_route_node_id: str | None = None
    # --------------------------------------------------
    # Common-side route nodes
    # --------------------------------------------------
    common_route_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") in {
            "Common-side route",
            "Non-index branch terminals",
        }
    ]

    common_route_node_ids: list[str] = []

    for common_index, row in enumerate(common_route_rows, start=1):
        label = str(getattr(row, "from_label", "") or "—")
        node_id = _node_id("common-route", label)

        common_route_node_ids.append(node_id)

        nodes_by_id[node_id] = ProportioningSchematicNodeV1(
            node_id=node_id,
            label=label,
            role=NODE_ROLE_COMMON_MAIN,
            lane=0,
            order=route_order,
            status="Common-side route node",
        )
        route_order += 1
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
                is_index_node=_is_index_node(from_label),
                role=NODE_ROLE_SELECTED_INDEX_ROUTE,
                lane=0,
                order=route_order,
                status="Selected index-route subleg",
            )
            route_order += 1

        if to_node_id not in nodes_by_id:
            nodes_by_id[to_node_id] = ProportioningSchematicNodeV1(
                node_id=to_node_id,
                label=to_label,
                is_index_node=_is_index_node(to_label),
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

    selected_entry_flow_label = "—"

    if selected_rows:
        selected_entry_flow_label = (
            str(getattr(selected_rows[-1], "flow_label", "") or "—")
        )

    # --------------------------------------------------
    # Link common/main through common-side route nodes into
    # the selected index-route entry.
    # --------------------------------------------------
    entry_chain = [common_main_id, *common_route_node_ids]

    if first_route_node_id is not None:
        entry_chain.append(first_route_node_id)

    for entry_index, (from_node_id, to_node_id) in enumerate(
            zip(entry_chain, entry_chain[1:]),
            start=1,
    ):
        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id=f"edge-common-main-selected-route-entry-{entry_index}",
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                role=EDGE_ROLE_SELECTED_INDEX_ROUTE,
                flow_label=selected_entry_flow_label,
                basis="Selected index route entry",
                status="Projection only",
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
        title="Selected route trace — boiler → index",
        basis="Derived from hydronic proportioning summary — route shown to calculated index point",
    )
def _build_from_hydronic_topology(
    project_state: Any,
    topology: Any,
    *,
    selected_leg_id: str | None = None,
    selected_subleg_id: str | None = None,
    selected_route_label: str | None = None,
) -> ProportioningSchematicV1:
    """
    Build schematic projection from HydronicTopologyV1 route authority.

    Display/projection only:
    - no pipe sizing
    - no pressure loss
    - no balancing
    - no ProjectState mutation
    """

    rooms = getattr(project_state, "rooms", {}) or {}
    intent = getattr(project_state, "basic_hydronic_sizing_intent", None)
    index_room_id = getattr(intent, "index_room_id", None) if intent else None

    nodes_by_id: dict[str, ProportioningSchematicNodeV1] = {}
    edges: list[ProportioningSchematicEdgeV1] = []

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

    edges.append(
        ProportioningSchematicEdgeV1(
            edge_id="edge-heat-source-common-main",
            from_node_id=heat_source_id,
            to_node_id=common_main_id,
            role=EDGE_ROLE_COMMON_MAIN,
            flow_label="—",
            basis="Hydronic topology route authority",
            status="Projection only",
        )
    )

    selected_leg, selected_subleg = _resolve_trace_leg_subleg(
        topology=topology,
        selected_leg_id=selected_leg_id,
        selected_subleg_id=selected_subleg_id,
    )

    if selected_subleg is not None:
        route_room_ids = list(getattr(selected_subleg, "route_room_ids", []) or [])
        route_index_room_id = getattr(selected_subleg, "index_room_id", None)
    elif selected_leg is not None:
        route_room_ids = list(getattr(selected_leg, "route_room_ids", []) or [])
        route_index_room_id = getattr(selected_leg, "index_room_id", None)
    else:
        route_room_ids = []
        route_index_room_id = None

    if not index_room_id or str(index_room_id) not in {str(x) for x in route_room_ids}:
        index_room_id = route_index_room_id

    route_label = str(
        selected_route_label
        or getattr(selected_subleg, "label", None)
        or getattr(selected_leg, "label", None)
        or "selected topology route"
    )

    previous_node_id = common_main_id
    route_order = 2

    for route_index, room_id in enumerate(route_room_ids, start=1):
        room_id = str(room_id)
        node_id = _node_id("route", room_id)
        label = _room_route_label(rooms.get(room_id), room_id)

        nodes_by_id[node_id] = ProportioningSchematicNodeV1(
            node_id=node_id,
            label=label,
            role=NODE_ROLE_SELECTED_INDEX_ROUTE,
            lane=0,
            order=route_order,
            status="Hydronic topology route node",
            is_index_node=(room_id == index_room_id),
        )

        edges.append(
            ProportioningSchematicEdgeV1(
                edge_id=f"edge-topology-route-{route_index}",
                from_node_id=previous_node_id,
                to_node_id=node_id,
                role=EDGE_ROLE_SELECTED_INDEX_ROUTE,
                flow_label="—",
                basis="Hydronic topology route authority",
                status="Projection only",
            )
        )

        previous_node_id = node_id
        route_order += 1

    return ProportioningSchematicV1(
        nodes=tuple(
            sorted(
                nodes_by_id.values(),
                key=lambda node: (node.lane, node.order, node.node_id),
            )
        ),
        edges=tuple(edges),
        title="Selected route trace — boiler → index",
        basis=f"Derived from hydronic topology — selected route trace: {route_label}",
    )


def _iter_sublegs(sublegs: Any):
    for subleg in list(sublegs or []):
        yield subleg
        yield from _iter_sublegs(getattr(subleg, "sublegs", []) or [])


def _resolve_trace_leg_subleg(
    *,
    topology: Any,
    selected_leg_id: str | None,
    selected_subleg_id: str | None,
) -> tuple[Any | None, Any | None]:
    """
    H-S25-E:
    Resolve the topology leg/subleg to draw in the selected route trace.

    Preferred authority:
    - controlling/selected route pressure row leg_id + subleg_id

    Fallback:
    - first leg / first subleg only when no selected route authority exists
    """

    legs = list(getattr(topology, "legs", []) or [])

    wanted_leg_id = str(selected_leg_id or "")
    wanted_subleg_id = str(selected_subleg_id or "")

    if wanted_leg_id or wanted_subleg_id:
        for leg in legs:
            leg_id = str(getattr(leg, "leg_id", "") or "")

            if wanted_leg_id and leg_id != wanted_leg_id:
                continue

            for subleg in _iter_sublegs(getattr(leg, "sublegs", []) or []):
                subleg_id = str(getattr(subleg, "subleg_id", "") or "")

                if wanted_subleg_id and subleg_id != wanted_subleg_id:
                    continue

                return leg, subleg

            if wanted_leg_id and not wanted_subleg_id:
                return leg, None

    first_leg = legs[0] if legs else None

    if first_leg is None:
        return None, None

    first_sublegs = list(getattr(first_leg, "sublegs", []) or [])

    if first_sublegs:
        return first_leg, first_sublegs[0]

    return first_leg, None


def _room_route_label(room: Any, room_id: str) -> str:
    """
    Resolve schematic room label.

    Keeps the schematic compact by stripping leading room notation such as:
    'R2 Hall' -> 'Hall'
    """

    raw_label = getattr(room, "name", None) if room is not None else None
    label = str(raw_label or room_id).strip()

    parts = label.split(maxsplit=1)

    if len(parts) == 2:
        prefix = parts[0].strip()

        if len(prefix) >= 2 and prefix[0].upper() == "R" and prefix[1:].isdigit():
            return parts[1].strip()

    return label

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

def _resolve_index_room_label(project_state: Any) -> str | None:
    """
    Resolve the current index room label for schematic annotation.

    Priority:
    1. Basic Hydronics sizing intent index_room_id
    2. Existing index-route accumulator fallback
    """

    # --------------------------------------------------
    # Preferred authority: Basic Hydronics sizing intent
    # --------------------------------------------------
    intent = getattr(project_state, "basic_hydronic_sizing_intent", None)
    index_room_id = getattr(intent, "index_room_id", None) if intent else None

    rooms = getattr(project_state, "rooms", {}) or {}

    if index_room_id and index_room_id in rooms:
        room = rooms[index_room_id]
        label = getattr(room, "name", None)

        if label:
            return str(label).strip()

    # --------------------------------------------------
    # Fallback: existing accumulator route label
    # --------------------------------------------------
    try:
        from HVAC.hydronics.routing.index_route_accumulator_v1 import (
            build_index_route_accumulator_v1,
        )

        route = build_index_route_accumulator_v1(project_state)
        label = getattr(route, "index_room_label", None)

        if label:
            return str(label).strip()

    except Exception:
        return None

    return None

def _is_index_label(label: str, index_room_label: str | None) -> bool:
    if not index_room_label:
        return False

    label = str(label).strip()
    index_room_label = str(index_room_label).strip()

    return (
        label == index_room_label
        or index_room_label.endswith(f" {label}")
    )