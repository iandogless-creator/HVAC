"""
HVACgooee — Fenestration Educational Concepts (Static)

Text-only, read-only concepts.

Used when:
- entering Fenestration mode
- reviewing window-related heat-loss assumptions

Fenestration affects:
- fabric heat loss
- solar gains
- comfort perception

It does NOT size plant.
"""

from __future__ import annotations
from typing import Dict


FENESTRATION_CONCEPTS: Dict[str, Dict[str, str]] = {

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    "overview": {
        "title": "Fenestration Overview",
        "summary": "How windows affect heat loss and solar gains.",
        "body": (
            "Fenestration refers to windows, glazed doors, rooflights, "
            "and other transparent building elements.\n\n"
            "They influence building performance in two main ways:\n"
            "• Heat loss through transmission\n"
            "• Heat gain from solar radiation\n\n"
            "Fenestration does not generate heat.\n"
            "It modifies how the building interacts with the external environment."
        ),
    },

    # ------------------------------------------------------------------
    # U-values
    # ------------------------------------------------------------------

    "fen_u_value": {
        "title": "Window U-values",
        "summary": "How frame, glazing and edges combine.",
        "body": (
            "A window U-value represents the overall rate of heat transfer "
            "through the complete window assembly.\n\n"
            "It includes:\n"
            "• Glazing performance (double, triple, coatings)\n"
            "• Frame material and geometry\n"
            "• Edge effects at spacers\n\n"
            "Window U-values are always higher (worse) than wall U-values.\n"
            "This is normal and unavoidable.\n\n"
            "In HVACgooee, window U-values are applied directly to "
            "window areas during fabric heat-loss calculations."
        ),
    },

    # ------------------------------------------------------------------
    # Solar gains
    # ------------------------------------------------------------------

    "fen_g_value": {
        "title": "g-value (Solar Factor)",
        "summary": "How much solar energy enters the building.",
        "body": (
            "The g-value (also called the solar factor) describes how much "
            "incident solar radiation passes through glazing and contributes "
            "to internal heat gains.\n\n"
            "A higher g-value means:\n"
            "• More useful solar gain in winter\n"
            "• Greater risk of overheating in summer\n\n"
            "Lower g-values reduce solar gain but also reduce passive benefits.\n\n"
            "Choosing g-values is a balance between energy efficiency "
            "and thermal comfort."
        ),
    },

    # ------------------------------------------------------------------
    # Orientation & shading
    # ------------------------------------------------------------------

    "fen_orientation": {
        "title": "Orientation and Solar Exposure",
        "summary": "Why window direction matters.",
        "body": (
            "Solar gains depend strongly on orientation.\n\n"
            "In the northern hemisphere:\n"
            "• South-facing windows receive the most winter sun\n"
            "• East and west windows receive low-angle sun\n"
            "• North-facing windows receive little direct solar gain\n\n"
            "Shading devices, overhangs, and reveals can significantly "
            "reduce unwanted solar gains without affecting winter performance."
        ),
    },

    # ------------------------------------------------------------------
    # Scope boundary
    # ------------------------------------------------------------------

    "scope_v1": {
        "title": "Fenestration v1 Scope",
        "summary": "What fenestration does and does not control.",
        "body": (
            "In HVACgooee v1:\n\n"
            "Included:\n"
            "• Window heat-loss contribution\n"
            "• Solar gain inputs to comfort interpretation\n\n"
            "Not included:\n"
            "• Dynamic shading control\n"
            "• Overheating simulation\n"
            "• Daylighting analysis\n\n"
            "Fenestration feeds heat-loss and comfort models.\n"
            "It does not size heating or cooling systems directly."
        ),
    },
}
