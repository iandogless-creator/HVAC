"""
HVACgooee — Hydronics Educational Concepts (Static)

Text-only, read-only concepts.

Used when:
- entering Hydronics mode
- no results yet
"""

from __future__ import annotations
from typing import Dict


# ----------------------------------------------------------------------
# Canonical education content (Hydronics)
#
# Structure:
#   topic -> mode -> { title, summary?, body }
#
# Modes:
#   - standard   (modern / explanatory)
#   - classical  (traditional / formula-based)
# ----------------------------------------------------------------------

HYDRONICS_CONCEPTS: Dict[str, Dict[str, Dict[str, str]]] = {

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------
    "overview": {
        "standard": {
            "title": "Hydronics — Overview",
            "body": (
                "Hydronic systems distribute heat using water as a carrier.\n\n"
                "In HVACgooee, hydronics follows heat-loss results and focuses on:\n"
                "• Flow rates\n"
                "• Pipe sizing\n"
                "• Pressure loss\n\n"
                "Hydronics does not create heat.\n"
                "It distributes heat calculated elsewhere."
            ),
        },
        "classical": {
            "title": "Hydronics — Overview (Classical)",
            "body": (
                "Hydronic system design is based on the energy balance:\n\n"
                "Q = ṁ × c × ΔT\n\n"
                "Where:\n"
                "• Q is heat transfer (W)\n"
                "• ṁ is mass flow rate (kg/s)\n"
                "• c is specific heat capacity (J/kg·K)\n"
                "• ΔT is temperature drop (K)\n\n"
                "This formulation underpins traditional pipe sizing "
                "and pump selection methods."
            ),
        },
    },

    # ------------------------------------------------------------------
    # Flow basics
    # ------------------------------------------------------------------
    "flow_basics": {
        "standard": {
            "title": "Flow and Heat Transfer",
            "summary": "How heat demand becomes water flow.",
            "body": (
                "Water flow is derived from heat demand using:\n\n"
                "Q = ṁ · c · ΔT\n\n"
                "Where:\n"
                "• Q is heat (W)\n"
                "• ṁ is mass flow (kg/s)\n"
                "• c is specific heat capacity\n"
                "• ΔT is system temperature drop\n"
            ),
        },
        "classical": {
            "title": "Flow and Heat Transfer (Classical)",
            "summary": "Traditional formulation.",
            "body": (
                "Rearranging the energy equation gives:\n\n"
                "ṁ = Q / (c · ΔT)\n\n"
                "This is the basis of classical flow sizing tables."
            ),
        },
    },

    # ------------------------------------------------------------------
    # Velocity limits
    # ------------------------------------------------------------------
    "velocity_limits": {
        "standard": {
            "title": "Velocity Limits",
            "summary": "Why pipe velocity is limited.",
            "body": (
                "Pipe velocity is limited to control:\n"
                "• Noise\n"
                "• Erosion\n"
                "• Excessive pressure loss\n\n"
                "Typical first-pass limits are below 0.8–1.0 m/s."
            ),
        },
        "classical": {
            "title": "Velocity Limits (Classical)",
            "summary": "Empirical limits from practice.",
            "body": (
                "Traditional design guidance limits velocity based on experience\n"
                "to avoid noise, erosion, and unacceptable pressure loss.\n\n"
                "These limits were historically tabulated by pipe material and size."
            ),
        },
    },

    # ------------------------------------------------------------------
    # Pressure drop
    # ------------------------------------------------------------------
    "pressure_drop": {
        "standard": {
            "title": "Pressure Drop",
            "summary": "Why pumps are required.",
            "body": (
                "As water flows through pipes and fittings, friction causes pressure loss.\n\n"
                "This loss must be overcome by a pump.\n"
                "Hydronics sizing ensures the pump can deliver the required flow "
                "against the system resistance."
            ),
        },
        "classical": {
            "title": "Pressure Drop (Classical)",
            "summary": "Friction and resistance.",
            "body": (
                "Pressure loss is traditionally calculated using empirical or\n"
                "semi-empirical relationships such as Darcy–Weisbach.\n\n"
                "Total system resistance defines the required pump head."
            ),
        },
    },

    # ------------------------------------------------------------------
    # Scope notes
    # ------------------------------------------------------------------
    "scope_v1": {
        "standard": {
            "title": "Hydronics v1 Scope",
            "summary": "What this version does and does not do.",
            "body": (
                "Hydronics v1 is intentionally limited.\n\n"
                "Included:\n"
                "• Single-path flow sizing\n"
                "• Pipe diameter selection\n"
                "• Pressure loss and head\n\n"
                "Not included:\n"
                "• Network balancing\n"
                "• Multiple branches\n"
                "• Control strategies\n"
            ),
        },
        "classical": {
            "title": "Hydronics v1 Scope (Classical)",
            "summary": "Deliberate simplification.",
            "body": (
                "Hydronics v1 reflects early-stage or single-path design practice.\n\n"
                "More complex network effects are intentionally excluded."
            ),
        },
    },
}
