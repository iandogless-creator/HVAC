"""
HVACgooee — Education Glossary

Shared HVAC glossary used by educational overlays and help panels.
This is intentionally small to start; you can expand it over time.
"""

from __future__ import annotations

from typing import Dict


GLOSSARY: Dict[str, str] = {
    "U-value": (
        "Overall heat transfer coefficient of a building element, "
        "measured in W/m²·K. Lower = better insulation."
    ),
    "Y-value": (
        "Linear thermal transmittance due to repeating thermal bridges "
        "such as joists or studs, expressed in W/m²·K contribution."
    ),
    "psi-value": (
        "Linear thermal transmittance at a junction (e.g., wall–floor, "
        "wall–roof), measured in W/m·K."
    ),
    "ΔP": "Pressure difference, often used for hydronic circuits (Pa or kPa).",
    "Kv": (
        "Flow coefficient of a valve — the flow rate through a valve at a "
        "specified pressure drop (usually 1 bar)."
    ),
    "g-value": (
        "Total solar energy transmittance of glazing, including both direct "
        "transmission and inward secondary heat emission."
    ),
}


def get_glossary_items() -> Dict[str, str]:
    """Return the full glossary dictionary."""
    return GLOSSARY
