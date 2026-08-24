# ======================================================================
# HVACgooee — Context-sensitive Workspace Education v1
# H-S69-B3I — read-only programme help and engineering guidance
# ======================================================================

"""Compact text-only guidance selected by GUI workspace presentation."""

from __future__ import annotations


EDUCATION_MODES_V1 = ("beginner", "standard", "classical")


_GUIDANCE_V1 = {
    "heat_loss": {
        "title": "Heat-Loss",
        "programme": (
            "Use this view to select a room, check its fabric and ventilation "
            "evidence, then calculate the room heat loss."
        ),
        "next": "Resolve any red or missing inputs, then select Calculate.",
        "beginner": (
            "Heat leaves through the building fabric and through exchanged air. "
            "The room total combines both losses."
        ),
        "standard": (
            "ΣQf is fabric transmission, Qv is ventilation loss and Qt is their "
            "room total. Check area, U-value, temperature basis and ACH."
        ),
        "classical": (
            "ΣQf = Σ(U·A·ΔT), Qv = 0.33·n·V·ΔT and Qt = ΣQf + Qv. "
            "U is W/m²·K, A is m², n is h⁻¹, V is m³ and each result is W."
        ),
    },
    "building_edit": {
        "title": "Building Edit",
        "programme": (
            "Use this view to define constructions, inspect U-values and assign "
            "the appropriate construction to room surfaces."
        ),
        "next": "Check the selected construction before assigning it to a surface.",
        "beginner": (
            "A construction describes the layers forming a wall, floor or roof. "
            "A lower U-value usually means less heat passes through it."
        ),
        "standard": (
            "Layer resistance and surface resistance combine into the overall "
            "U-value. Repeating members may create parallel heat-flow paths."
        ),
        "classical": (
            "For one path, Rᵢ = dᵢ/λᵢ and U = 1/(Rsi + ΣRᵢ + Rse). "
            "For parallel paths, U = Σ(fⱼ·Uⱼ), with Σfⱼ = 1."
        ),
    },
    "openings": {
        "title": "Openings",
        "programme": (
            "Use this view to define windows and doors and review how their areas "
            "reduce the parent wall's net opaque area."
        ),
        "next": "Confirm opening dimensions, type and declared whole-product U-value.",
        "beginner": (
            "Windows and doors normally lose heat differently from the wall around "
            "them, so they are entered separately."
        ),
        "standard": (
            "External openings contribute their own U·A·ΔT loss; their area is "
            "deducted once from the gross external-wall area."
        ),
        "classical": (
            "Awall,net = Awall,gross − ΣAopening and Q = U·A·ΔT. Declared Uw or "
            "Ud is whole-product authority and must not be decomposed implicitly."
        ),
    },
    "hydronics_setup": {
        "title": "Hydronics Setup",
        "programme": (
            "Use this view to establish the heat-source location, design "
            "temperatures, emitters and ordered system topology."
        ),
        "next": "Complete the topology and emitter demand before Basic Sizing.",
        "beginner": (
            "The topology describes how water reaches each room and returns to the "
            "heat source. It is the map used by later hydraulic work."
        ),
        "standard": (
            "Heat-source location, flow/return temperatures, emitters and topology "
            "form the input basis; topology alone is not sizing readiness."
        ),
        "classical": (
            "Emitter demand relates to mass flow through Q = ṁ·cp·ΔT. Therefore "
            "ṁ = Q/(cp·ΔT); topology assigns that carried flow to later sections."
        ),
    },
    "basic_sizing": {
        "title": "Basic Sizing",
        "programme": (
            "Use this view to inspect first-capacity pipe candidates and their "
            "velocity and resistance evidence."
        ),
        "next": "Resolve readiness warnings before passing a basis to Proportioning.",
        "beginner": (
            "Each pipe must carry the required water flow without excessive speed "
            "or resistance. The first suitable size is still a design basis."
        ),
        "standard": (
            "Candidate size depends on carried mass flow, internal diameter, water "
            "properties, velocity limit and pressure-loss evidence."
        ),
        "classical": (
            "A = πDᵢ²/4, v = ṁ/(ρA), and Δp = [f(L/Dᵢ) + ΣK]·ρv²/2. "
            "The friction factor and candidate limits must retain their stated basis."
        ),
    },
    "proportioning": {
        "title": "Proportioning",
        "programme": (
            "Use this view to compare route pressure evidence against the accepted "
            "return-arrangement and sizing basis."
        ),
        "next": "Review the controlling route and shortfall evidence before acceptance.",
        "beginner": (
            "Water favours the easier route. Proportioning compares routes so the "
            "designer can see where additional control may be required."
        ),
        "standard": (
            "Route totals combine shared and downstream section losses. Comparison "
            "evidence does not automatically choose return arrangement or balancing."
        ),
        "classical": (
            "Δproute = ΣΔpsection. Relative balancing burden may be expressed as "
            "Δpcontrol − Δproute, using the same accepted flow and section basis."
        ),
    },
    "results": {
        "title": "Proportioned Results",
        "programme": (
            "Use this view to review the clean proportioned schematic, route summary "
            "and accepted or committed output evidence."
        ),
        "next": "Check status wording and basis identity before treating output as final.",
        "beginner": (
            "This view gathers the result in a cleaner form. A displayed result is "
            "not automatically a final pump, valve or balancing selection."
        ),
        "standard": (
            "Confirm whether each value is preview, candidate, accepted or committed. "
            "Retain the controlling route and section identities with the result."
        ),
        "classical": (
            "This view introduces no new governing equation; it reports upstream "
            "mass-flow, velocity and Δp evaluations on their recorded design basis."
        ),
    },
    "user": {
        "title": "User Workspace",
        "programme": (
            "Use this floating workspace to assemble only the panels needed for the "
            "current task, position them, then save the current view."
        ),
        "next": "Choose panels, arrange them, then use Save Current View.",
        "beginner": (
            "Moving or hiding a panel changes only the screen layout; it does not "
            "alter the project calculation."
        ),
        "standard": (
            "Panel membership and validated window geometry are GUI settings. The "
            "selected panels retain their normal input and result responsibilities."
        ),
        "classical": (
            "Workspace persistence stores recognised panel identities and bounded "
            "geometry only; it stores no opaque Qt dock state or engineering basis."
        ),
    },
}


_PANEL_GUIDANCE_V1 = {
    "project": {
        "title": "Project",
        "programme": (
            "Use this panel to identify the open project and check its Heat-Loss "
            "and Hydronics status."
        ),
        "next": "Resolve the earliest incomplete status before relying on later results.",
        "beginner": (
            "The project holds the rooms and design information used throughout "
            "HVACgooee. Status shows which work is ready or still incomplete."
        ),
        "standard": (
            "Heat-Loss and Hydronics readiness are separate. A valid Heat-Loss "
            "basis does not by itself mean the hydraulic design is complete."
        ),
        "classical": (
            "This panel reports lifecycle state rather than a governing equation. "
            "Treat NOT RUN, DIRTY, VALID, preview and committed as distinct states."
        ),
    },
    "environment": {
        "title": "Environment",
        "programme": (
            "Use this panel to set external and internal design conditions and the "
            "project-level hydronic defaults."
        ),
        "next": "Confirm temperatures, ACH and hydronic defaults before calculation.",
        "beginner": (
            "These values describe the design conditions the building and heating "
            "system must meet."
        ),
        "standard": (
            "External temperature, Ti or tei, room height and ACH affect Heat-Loss; "
            "flow/return temperatures and velocity limit form hydronic input intent."
        ),
        "classical": (
            "Thermal driving difference is ΔT = Tin − Tout. Hydronic temperature "
            "drop later relates demand and mass flow through Q = ṁ·cp·ΔT."
        ),
    },
    "rooms": {
        "title": "Rooms",
        "programme": (
            "Use this panel to choose the current room. Other room-sensitive panels "
            "then display that same room."
        ),
        "next": "Select the room you intend to inspect or edit.",
        "beginner": (
            "The highlighted row is the room currently in focus; selecting it does "
            "not recalculate or alter the room."
        ),
        "standard": (
            "Room selection is transient GUI context. Stable room identity, not its "
            "display position, links geometry, surfaces and results."
        ),
        "classical": (
            "This panel introduces no equation or engineering authority; it projects "
            "an opaque room identifier into the shared GUI context."
        ),
    },
    "construction": {
        "title": "Construction",
        "programme": (
            "Use this panel to define physical layer build-up and assign a named "
            "construction to the selected surface."
        ),
        "next": "Check layer order and dimensions before assignment.",
        "beginner": (
            "A construction records what a wall, floor or roof is made from. Its "
            "layers determine resistance to heat flow."
        ),
        "standard": (
            "Physical build-up belongs here; thermal properties are resolved and "
            "reviewed through the U-Values panel."
        ),
        "classical": (
            "For a homogeneous layer, R = d/λ. Parallel paths require explicit "
            "fractions rather than averaging conductivities without a basis."
        ),
    },
    "u_values": {
        "title": "U-Values",
        "programme": (
            "Use this panel to review thermal properties, declared opening values "
            "and layer-path evidence."
        ),
        "next": "Select the construction or surface whose thermal basis you need.",
        "beginner": (
            "A U-value describes how readily heat passes through an element. Lower "
            "values normally mean less heat loss."
        ),
        "standard": (
            "Review the accepted construction method and whether a value is derived "
            "from layers or declared for a complete window or door."
        ),
        "classical": (
            "U = 1/(Rsi + ΣRlayer + Rse), with Rlayer = d/λ. Whole-product Uw or "
            "Ud remains declared authority unless explicitly modelled otherwise."
        ),
    },
    "hydronics": {
        "title": "Hydronics",
        "programme": (
            "Use this panel to inspect ordered topology, section evidence, route "
            "comparisons and proportioned output."
        ),
        "next": "Follow the active tab's readiness and basis wording.",
        "beginner": (
            "The schematic follows how water travels through shared pipework and "
            "room circuits. Different tabs show different design stages."
        ),
        "standard": (
            "Keep Basic, Proportioning and Proportioned evidence distinct. Preview "
            "or comparison evidence does not silently become an accepted decision."
        ),
        "classical": (
            "Route pressure is assembled as Δproute = ΣΔpsection on the recorded "
            "flow, pipe identity and return-arrangement basis."
        ),
    },
    "hydronic_emitters": {
        "title": "Hydronic Emitters",
        "programme": (
            "Use this panel to assign room emitters and their design output and "
            "room-pipework intent."
        ),
        "next": "Confirm emitter demand for the current room before Basic Sizing.",
        "beginner": (
            "An emitter supplies the room heat demand. Its required water flow feeds "
            "the later pipe-sizing calculation."
        ),
        "standard": (
            "Emitter output, quantity and design temperature basis determine the "
            "room's carried hydronic flow."
        ),
        "classical": (
            "For water-side duty, Q = ṁ·cp·ΔT and therefore ṁ = Q/(cp·ΔT), using "
            "the accepted design flow/return temperatures."
        ),
    },
    "local_k": {
        "title": "Local K / Fittings",
        "programme": (
            "Use this panel to inspect fittings and local-resistance evidence for "
            "the selected section."
        ),
        "next": "Check that each fitting belongs to the intended pipe section.",
        "beginner": (
            "Bends, tees and valves resist flow as well as straight pipe. Their K "
            "values represent that local effect."
        ),
        "standard": (
            "Local losses use the section velocity and the summed K values of the "
            "included fittings."
        ),
        "classical": (
            "Δplocal = ΣK·ρv²/2. The velocity and density must be from the same "
            "section basis used by the straight-pipe loss."
        ),
    },
    "topology": {
        "title": "Topology Arranger",
        "programme": (
            "Use this panel to order the common main, legs, sublegs, branches and "
            "rooms without performing hydraulic selection."
        ),
        "next": "Complete and check the route order before sizing or proportioning.",
        "beginner": (
            "Topology is the system map. It says what connects to what and in which "
            "order water reaches the rooms."
        ),
        "standard": (
            "Branch load and flow roll back into the parent route at the take-off; "
            "ordered topology alone is not calculation readiness."
        ),
        "classical": (
            "At each junction, carried mass flow follows continuity: incoming flow "
            "equals the sum of outgoing flows on the accepted topology."
        ),
    },
    "geometry": {
        "title": "Geometry",
        "programme": (
            "Use this panel to edit the current room's length, width, height and "
            "internal design temperature."
        ),
        "next": "Confirm dimensions before reviewing areas and Heat-Loss.",
        "beginner": (
            "Room dimensions determine floor area, volume and the starting size of "
            "its enclosing surfaces."
        ),
        "standard": (
            "Geometry supplies area and volume evidence; construction and adjacency "
            "supply separate thermal meaning."
        ),
        "classical": (
            "For the rectangular room basis, Afloor = L·W and V = L·W·H. Surface "
            "areas are resolved from the appropriate dimensions and openings."
        ),
    },
    "ach": {
        "title": "ACH",
        "programme": (
            "Use this panel to edit the current room's air-change rate for "
            "ventilation heat loss."
        ),
        "next": "Check that the ACH represents the intended design condition.",
        "beginner": (
            "ACH is how many room-volumes of air are replaced in one hour. More air "
            "change usually means more heating demand."
        ),
        "standard": (
            "Ventilation loss depends on ACH, room volume and the applicable air "
            "temperature difference."
        ),
        "classical": (
            "Qv = 0.33·n·V·ΔT, where n is h⁻¹, V is m³ and Qv is W for the adopted "
            "air-property approximation."
        ),
    },
    "education": {
        "title": "Programme Help",
        "programme": (
            "Choose the explanation level here; selecting another panel loads "
            "its relevant help."
        ),
        "next": "Select the panel you want explained.",
        "beginner": "Beginner uses plain practical guidance.",
        "standard": (
            "Standard adds concise design context and programme terminology."
        ),
        "classical": (
            "Classical adds governing relationships, formulae and stated "
            "engineering limits."
        ),
    },
    "dev": {
        "title": "Dev",
        "programme": (
            "Use this panel only for development diagnostics and presentation modes."
        ),
        "next": "Leave diagnostic controls unchanged during ordinary project work.",
        "beginner": "This panel is not required for normal design work.",
        "standard": (
            "Diagnostic display state must not be mistaken for project or "
            "engineering authority."
        ),
        "classical": (
            "This panel introduces no calculation; it exposes development-only GUI "
            "state and evidence."
        ),
    },
}


_GUIDANCE_V1.update(_PANEL_GUIDANCE_V1)


PANEL_TOPIC_BY_DOCK_ID_V1 = {
    "dock_project": "project",
    "dock_environment": "environment",
    "dock_rooms": "rooms",
    "dock_construction": "construction",
    "dock_uvp": "u_values",
    "dock_heat_loss": "heat_loss",
    "dock_education": "education",
    "dock_hydronics": "hydronics",
    "dock_hydronic_control": "hydronic_emitters",
    "dock_basic_hydronics": "basic_sizing",
    "dock_local_k": "local_k",
    "dock_topology_arranger": "topology",
    "dock_dev": "dev",
    "dock_geometry": "geometry",
    "dock_ach": "ach",
}


def education_topic_for_dock_id_v1(dock_id: str) -> str | None:
    """Return the recognised contextual-help topic for a dock panel."""
    return PANEL_TOPIC_BY_DOCK_ID_V1.get(str(dock_id or ""))


def _entry_v1(topic: str, mode: str) -> dict[str, str]:
    guidance = _GUIDANCE_V1[topic]
    return {
        "title": f"{guidance['title']} — {mode.title()}",
        "body": (
            f"{guidance['programme']}\n\n"
            f"{guidance[mode]}\n\n"
            f"Next: {guidance['next']}"
        ),
    }


WORKSPACE_GUIDANCE_V1 = {
    topic: {
        mode: _entry_v1(topic, mode)
        for mode in EDUCATION_MODES_V1
    }
    for topic in _GUIDANCE_V1
}
