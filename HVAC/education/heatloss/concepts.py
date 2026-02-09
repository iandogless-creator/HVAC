# ======================================================================
# HVAC/gui_v2/modes/education/heatloss_education.py
# ======================================================================

"""
HVACgooee — Heat-Loss Educational Concepts

Textual content only — no GUI, no engines.

Used by GUI overlays to explain:
- Heat-loss fundamentals
- U-values and Y-values
- Comfort vs compliance
- Ti / tei / tai temperature semantics
"""

from __future__ import annotations

from typing import Dict


HEATLOSS_CONCEPTS = {
"overview": {
    "title": "Heat Loss — Education",
    "summary": "How heat loss is calculated and interpreted in HVACgooee.",
    "body": (
        "Heat loss in HVACgooee is separated into:\n"
        "• Fabric transmission (ΣQf)\n"
        "• Ventilation losses (Qv)\n\n"
        "Compliance calculations use Ti.\n"
        "Comfort interpretation uses tei and tai.\n\n"
        "Select a topic to explore details."
    ),
},

    # ------------------------------------------------------------------
    # Fundamentals
    # ------------------------------------------------------------------

    "hl_basics": {
        "title": "Heat-Loss Basics",
        "summary": "How heat leaves a building through fabric and ventilation.",
        "body": (
            "Heat is lost from buildings mainly by:\n"
            "• Conduction through walls, roofs, floors and windows\n"
            "• Ventilation and infiltration (air changes)\n\n"
            "Fabric heat-loss is estimated using U-values (W/m²·K) multiplied "
            "by area and temperature difference.\n\n"
            "Ventilation heat-loss depends on air volume, air change rate, "
            "and temperature difference between inside and outside.\n"
        ),
    },

    "hl_facade_exposure": {
        "title": "Façade Exposure & Heat Loss",
        "summary": "How orientation and façades affect wall and window heat loss.",
        "body": (
            "In HVACgooee, geometry defines area only. It is not a drawing and is never rotated.\n\n"
            "The orientation of a space places the building on the compass. "
            "North is 0°, East 90°, South 180°, and West 270°. "
            "Orientation is stored once on the Space and applied mathematically.\n\n"
            "Each wall is represented by an edge of the footprint. "
            "Using the space orientation, each edge is assigned a compass-facing façade "
            "(N, NE, E, SE, S, SW, W, NW).\n\n"
            "In version 1, each wall edge belongs to one façade only. "
            "Walls are not split between multiple directions.\n\n"
            "Gross wall area is calculated as wall length multiplied by room height. "
            "Window and door areas on that façade are then subtracted to give the net wall area.\n\n"
            "Heat loss is calculated using:\n"
            "U-value × area = heat-loss coefficient (W/K).\n\n"
            "Temperature difference and climate data are applied later by the heat-loss solver."
        ),
    },

    # ------------------------------------------------------------------
    # Fabric physics
    # ------------------------------------------------------------------

    "hl_u_values": {
        "title": "Understanding U-values",
        "summary": "What U-values mean and why lower is usually better.",
        "body": (
            "A U-value is the overall heat transfer coefficient of a building element.\n"
            "It combines conduction through materials with internal and external "
            "surface resistances.\n\n"
            "U [W/m²·K] = 1 / (Rsi + Σ(layer thickness / conductivity) + Rse)\n\n"
            "Lower U-values mean less heat loss for a given temperature difference.\n"
        ),
    },

    "hl_y_values": {
        "title": "Y-values and Thermal Bridges",
        "summary": "Repeating thermal bridges such as joists and studs.",
        "body": (
            "Y-values represent repeating thermal bridges within an element, "
            "such as timber studs in a wall or joists in a roof.\n\n"
            "They account for mixed heat-flow paths that are not captured "
            "by simple one-dimensional U-values.\n\n"
            "In HVACgooee, Y-values are handled as corrections to fabric performance, "
            "not as separate heat-loss elements.\n"
        ),
    },

    # ------------------------------------------------------------------
    # Comfort vs Compliance (NEW — CANONICAL)
    # ------------------------------------------------------------------

    "hl_design_temperature_ti": {
        "title": "Design Temperature (Ti)",
        "summary": "The temperature used for compliance heat-loss calculations.",
        "body": (
            "Ti is the design air temperature used for regulatory and compliance "
            "heat-loss calculations.\n\n"
            "It is used for:\n"
            "• Fabric transmission losses (ΣQf)\n"
            "• Ventilation losses (Qv) when comfort correction is not applied\n"
            "• Total heat-loss reporting (Qt)\n\n"
            "Ti is a compliance temperature, not a comfort guarantee. "
            "A room at Ti may still feel cold or warm depending on surface temperatures.\n\n"
            "Canonical rule:\n"
            "Fabric heat-loss always uses Ti.\n"
        ),
    },

    "hl_fabric_heat_loss": {
        "title": "Fabric Heat Loss (ΣQf)",
        "summary": "Why fabric losses never use comfort corrections.",
        "body": (
            "Fabric heat-loss (ΣQf) represents heat lost through walls, floors, roofs "
            "and windows by conduction and radiation.\n\n"
            "It depends on:\n"
            "• U-values\n"
            "• Surface areas\n"
            "• Temperature difference (Ti − To)\n\n"
            "Radiant effects are already embedded in U-values and surface resistances.\n\n"
            "Applying comfort corrections here would double-count radiation.\n\n"
            "Canonical rule:\n"
            "ΣQf always uses Ti, never tai.\n"
        ),
    },

    "hl_ventilation_heat_loss": {
        "title": "Ventilation Heat Loss (Qv)",
        "summary": "The only heat-loss component that may use tai.",
        "body": (
            "Ventilation heat-loss (Qv) represents heat lost through air exchange, "
            "including ventilation and infiltration.\n\n"
            "Because ventilation losses are air-based, they may optionally use "
            "a comfort-corrected air temperature.\n\n"
            "Possible temperature bases:\n"
            "• Ti − To (standard compliance)\n"
            "• tai − To (comfort-aware ventilation)\n\n"
            "Which is used depends on the project and room tai settings.\n"
        ),
    },

    "hl_comfort_reference_tei": {
        "title": "Comfort Reference Temperature (tei)",
        "summary": "How warm the room is intended to feel.",
        "body": (
            "tei represents the intended comfort temperature of a room.\n\n"
            "It reflects how warm the space should feel to occupants, "
            "not the air temperature used for compliance calculations.\n\n"
            "Comfort depends strongly on surface temperatures, "
            "mean radiant temperature, and human factors.\n"
        ),
    },

    "hl_required_air_temp_tai": {
        "title": "Required Air Temperature (tai)",
        "summary": "The air temperature needed to achieve comfort.",
        "body": (
            "tai is the air temperature required to achieve the intended "
            "comfort temperature (tei).\n\n"
            "It accounts for radiant heat loss to cold surfaces using a "
            "simplified engineering correction.\n\n"
            "Legacy UK formulation preserved in HVACgooee:\n\n"
            "tai = Ti + (ΣQf / A) / k\n\n"
            "tai is diagnostic and optional.\n"
            "It does not replace Ti for transmission heat-loss or compliance.\n"
        ),
    },

    "hl_comfort_vs_compliance": {
        "title": "Comfort vs Compliance",
        "summary": "Why HVACgooee separates physics from experience.",
        "body": (
            "Compliance answers:\n"
            "“Is the building sized correctly under defined conditions?”\n\n"
            "Comfort answers:\n"
            "“Will the room feel right to occupants?”\n\n"
            "Compliance uses Ti and regulatory physics.\n"
            "Comfort uses tei and tai to describe experience.\n\n"
            "Canonical statement:\n"
            "Ti is truth for physics.\n"
            "tei is truth for intent.\n"
            "tai is truth for experience.\n"
        ),
    },
}

# ======================================================================
# END FILE
# ======================================================================
