# ======================================================================
# HVAC/hydronics/sizing/basic_ps_schematic_projection_v1.py
# ======================================================================

from __future__ import annotations

from typing import Any

from HVAC.core.room_identity import room_short_label
from HVAC.gui_v3.widgets.common_main_leg_subleg_schematic_widget_v1 import (
    CommonMainLegSublegRouteV1,
    CommonMainLegSublegRoomEvidenceV1,
    CommonMainLegSublegSchematicV1,
    CommonMainLegSublegSectionEvidenceV1,
)


def _shown_optional(value: object, suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value}{suffix}"


def build_basic_ps_schematic_projection_v1(
    project_state: Any,
    basic_ps_projection: Any,
) -> CommonMainLegSublegSchematicV1:
    """Build display-only shared-schematic evidence for one Basic PS route."""

    sections_projection = basic_ps_projection.sections_projection
    sections = tuple(sections_projection.sections or ())
    sizing_by_id = {
        str(row.section_id): row
        for row in tuple(basic_ps_projection.pipe_sizing_projection.results or ())
    }
    pressure_by_id = {
        str(row.section_id): row
        for row in tuple(basic_ps_projection.pressure_preview_projection.rows or ())
    }

    route_id = (
        f"{sections_projection.leg_id}:{sections_projection.subleg_id}"
    )
    room_evidence = tuple(
        CommonMainLegSublegRoomEvidenceV1(
            room_id=str(section.to_room_id),
            room_label=str(section.to_room_label),
            emitter_flow_kg_s=f"{float(section.carried_flow_kg_s):.4f} kg/s",
            flow_basis="Basic PS carried-flow evidence",
            status="Read-only Basic PS route room",
        )
        for section in sections
    )

    section_evidence = []
    for section in sections:
        section_id = str(section.section_id)
        sizing = sizing_by_id.get(section_id)
        pressure = pressure_by_id.get(section_id)
        if sizing is None:
            continue

        length_m = getattr(pressure, "section_length_m", None)
        section_dp = getattr(pressure, "section_pressure_drop_Pa", None)
        pressure_status = str(getattr(pressure, "status", "") or "")
        velocity_text = f"v={float(sizing.velocity_m_s):.3f} m/s"

        section_evidence.append(
            CommonMainLegSublegSectionEvidenceV1(
                section_id=section_id,
                section_ordinal=int(section.order),
                trace_index=max(0, int(section.order) - 1),
                trace_room_id=str(section.to_room_id),
                route_id=route_id,
                leg_id=str(section.leg_id),
                subleg_id=str(section.subleg_id),
                from_label=str(section.from_label),
                to_label=str(section.to_room_label),
                flow_kg_s=f"{float(sizing.carried_flow_kg_s):.4f} kg/s",
                pipe_dn=str(sizing.pipe_size_label),
                dp_per_m=(
                    f"{float(sizing.pressure_gradient_Pa_per_m):.1f} Pa/m"
                ),
                length=(
                    "—" if length_m is None else f"{float(length_m):.2f} m"
                ),
                k="Not included in Basic PS v1",
                section_dp=(
                    "—" if section_dp is None else f"{float(section_dp):.1f} Pa"
                ),
                iter="Haaland",
                status="; ".join(
                    value
                    for value in (
                        str(sizing.status),
                        velocity_text,
                        pressure_status,
                    )
                    if value
                ),
            )
        )

    topology = getattr(project_state, "hydronic_topology", None)
    heat_source_room_id = str(
        getattr(topology, "heat_source_room_id", "") or ""
    )
    room_lookup = getattr(project_state, "rooms", {}) or {}
    heat_source_room = room_lookup.get(heat_source_room_id)
    heat_source_label = (
        room_short_label(heat_source_room_id, heat_source_room)
        if heat_source_room_id and heat_source_room is not None
        else "Remote Heat Source"
    )

    route = CommonMainLegSublegRouteV1(
        leg_id=str(sections_projection.leg_id),
        leg_label=str(sections_projection.leg_label),
        subleg_id=str(sections_projection.subleg_id),
        subleg_label=str(sections_projection.subleg_label),
        role="Basic PS route",
        room_labels=tuple(str(section.to_room_label) for section in sections),
        room_evidence=room_evidence,
        section_evidence=tuple(section_evidence),
    )

    return CommonMainLegSublegSchematicV1(
        heat_source_label=heat_source_label,
        common_main_label="Common main",
        routes=(route,),
        status=(
            "Basic PS read-only schematic — calculation evidence accumulates "
            "from index towards the Heat Source; topology is drawn from the "
            "Heat Source outwards. No Local K, balancing, pump, valve, final "
            "proportioning or pipe-resize authority."
        ),
    )
