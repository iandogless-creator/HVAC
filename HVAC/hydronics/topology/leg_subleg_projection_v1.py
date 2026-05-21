# ======================================================================
# HVAC/hydronics/topology/leg_subleg_projection_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from HVAC.hydronics.proportioning.branch_proportioning_summary_v1 import (
    build_branch_proportioning_summary_v1,
)
from HVAC.hydronics.topology.leg_subleg_dto_v1 import (
    HYDRO_ROUTE_ROLE_COMMON_LEG,
    HYDRO_ROUTE_ROLE_SUBLEG_CIRCUIT,
    HYDRO_ROUTE_ROLE_TERMINAL_BRANCH,
    HYDRO_TERMINATION_CONTINUES,
    HYDRO_TERMINATION_EMITTER,
    HydronicLegSublegTopologyV1,
    HydronicRouteNodeV1,
    HydronicRouteSectionV1,
    HydronicTerminalCircuitV1,
)


# ======================================================================
# Public builder
# ======================================================================

def build_leg_subleg_topology_v1(project_state: Any) -> HydronicLegSublegTopologyV1:
    """
    Build a read-only H-T2 leg/subleg topology projection.

    Source
    ------
    Uses existing H-R branch/proportioning summary rows.

    H-T2 scope
    ----------
    • project current H-R rows into H-T1 DTOs
    • create Leg 1 / Common leg
    • create selected index-route subleg sections
    • create non-index terminal/radiator branch sections
    • create provisional terminal circuits

    Explicitly out of scope
    -----------------------
    • pressure-loss calculation
    • true index-circuit selection
    • pump sizing
    • balancing order
    • branch attachment authority
    • pipe sizing
    • ProjectState mutation
    """

    summary_rows = list(build_branch_proportioning_summary_v1(project_state) or [])

    nodes_by_id: dict[str, HydronicRouteNodeV1] = {}
    sections: list[HydronicRouteSectionV1] = []
    terminal_circuits: list[HydronicTerminalCircuitV1] = []

    # --------------------------------------------------
    # Anchor nodes
    # --------------------------------------------------
    heat_source_node_id = "node-heat-source"
    common_main_node_id = "node-common-main"

    nodes_by_id[heat_source_node_id] = HydronicRouteNodeV1(
        node_id=heat_source_node_id,
        system_label="Boiler / Heat Source",
    )

    nodes_by_id[common_main_node_id] = HydronicRouteNodeV1(
        node_id=common_main_node_id,
        system_label="Common main",
    )

    # --------------------------------------------------
    # Leg 1 / Common leg
    # --------------------------------------------------
    common_row = _first_row(summary_rows, group="Common/main")

    common_leg_section_id = "section-leg-1-common"

    sections.append(
        HydronicRouteSectionV1(
            section_id=common_leg_section_id,
            system_label="Leg 1 / Common leg",
            from_node_id=heat_source_node_id,
            to_node_id=common_main_node_id,
            role=HYDRO_ROUTE_ROLE_COMMON_LEG,
            flow_kg_s=_parse_flow_kg_s(
                getattr(common_row, "flow_label", None)
                if common_row is not None
                else None
            ),
            flow_basis=(
                getattr(common_row, "basis", "")
                if common_row is not None
                else "Common leg projected from H-R summary"
            ),
            termination=HYDRO_TERMINATION_CONTINUES,
            note="H-T2 projection only; carries combined common-leg flow where available.",
        )
    )

    # --------------------------------------------------
    # Selected index route as subleg circuit
    # --------------------------------------------------
    selected_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Selected index route"
    ]

    selected_section_ids: list[str] = []
    previous_section_id: Optional[str] = common_leg_section_id

    selected_circuit_id = "circuit-selected-index-route"

    for index, row in enumerate(selected_rows, start=1):
        from_label = str(getattr(row, "from_label", "") or "Unknown")
        to_label = str(getattr(row, "to_label", "") or "Unknown")

        from_node_id = _node_id("route", from_label)
        to_node_id = _node_id("route", to_label)

        nodes_by_id.setdefault(
            from_node_id,
            HydronicRouteNodeV1(
                node_id=from_node_id,
                system_label=from_label,
            ),
        )
        nodes_by_id.setdefault(
            to_node_id,
            HydronicRouteNodeV1(
                node_id=to_node_id,
                system_label=to_label,
            ),
        )

        section_id = f"section-selected-index-route-{index}"

        selected_section_ids.append(section_id)

        sections.append(
            HydronicRouteSectionV1(
                section_id=section_id,
                system_label=f"Selected index route section {index}",
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                role=HYDRO_ROUTE_ROLE_SUBLEG_CIRCUIT,
                parent_section_id=previous_section_id,
                flow_kg_s=_parse_flow_kg_s(getattr(row, "flow_label", None)),
                flow_basis=(
                    str(getattr(row, "basis", "") or "")
                    or "Selected index route accumulated subleg flow"
                ),
                termination=HYDRO_TERMINATION_CONTINUES,
                note="Selected/assumed index route only; not true calculated index circuit.",
            )
        )

        previous_section_id = section_id

    if selected_section_ids:
        terminal_node_id = sections[-1].to_node_id

        terminal_circuits.append(
            HydronicTerminalCircuitV1(
                circuit_id=selected_circuit_id,
                system_label="Selected index route",
                terminal_node_id=terminal_node_id,
                section_ids=tuple([common_leg_section_id, *selected_section_ids]),
                is_selected_index_route=True,
                is_true_index_circuit=False,
                note="H-T2 selected/assumed route; true index circuit requires Δp ranking later.",
            )
        )

    # --------------------------------------------------
    # Non-index terminal/radiator branches
    # --------------------------------------------------
    branch_rows = [
        row for row in summary_rows
        if getattr(row, "group", "") == "Non-index branch terminals"
    ]

    branch_section_ids: list[str] = []

    for index, row in enumerate(branch_rows, start=1):
        from_label = str(getattr(row, "from_label", "") or "Unknown")

        branch_node_id = _node_id("terminal-branch", from_label)

        nodes_by_id.setdefault(
            branch_node_id,
            HydronicRouteNodeV1(
                node_id=branch_node_id,
                system_label=from_label,
            ),
        )

        section_id = f"section-terminal-branch-{index}"
        branch_section_ids.append(section_id)

        sections.append(
            HydronicRouteSectionV1(
                section_id=section_id,
                system_label=f"Terminal/radiator branch {index}",
                from_node_id=common_main_node_id,
                to_node_id=branch_node_id,
                role=HYDRO_ROUTE_ROLE_TERMINAL_BRANCH,
                parent_section_id=common_leg_section_id,
                flow_kg_s=_parse_flow_kg_s(getattr(row, "flow_label", None)),
                flow_basis=(
                    str(getattr(row, "basis", "") or "")
                    or "Terminal/radiator branch flow"
                ),
                termination=HYDRO_TERMINATION_EMITTER,
                note="Terminal/radiator branch projected from non-index H-R branch row.",
            )
        )

        terminal_circuits.append(
            HydronicTerminalCircuitV1(
                circuit_id=f"circuit-terminal-branch-{index}",
                system_label=f"Terminal circuit {index}",
                terminal_node_id=branch_node_id,
                section_ids=(common_leg_section_id, section_id),
                is_selected_index_route=False,
                is_true_index_circuit=False,
                note="H-T2 terminal circuit placeholder; Δp not calculated.",
            )
        )

    return HydronicLegSublegTopologyV1(
        nodes=tuple(nodes_by_id.values()),
        sections=tuple(sections),
        terminal_circuits=tuple(terminal_circuits),
        common_leg_section_id=common_leg_section_id,
        selected_index_route_circuit_id=(
            selected_circuit_id if selected_section_ids else None
        ),
        true_index_circuit_id=None,
        basis="H-T2 read-only projection from H-R branch/proportioning summary",
    )


# ======================================================================
# Helpers
# ======================================================================

def _first_row(rows: list[Any], *, group: str) -> Any | None:
    for row in rows:
        if getattr(row, "group", "") == group:
            return row
    return None


def _parse_flow_kg_s(value: Any) -> float | None:
    """
    Parse display flow strings such as '0.0323 kg/s'.

    H-T2 deliberately reuses H-R projected display values.
    Later phases should carry numeric flow authority directly.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text or text == "—":
        return None

    text = text.replace("kg/s", "").strip()

    try:
        return float(text)
    except ValueError:
        return None


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

    return f"node-{prefix}-{slug}"