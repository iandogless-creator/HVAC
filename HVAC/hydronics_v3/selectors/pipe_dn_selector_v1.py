# ======================================================================
# HVAC/hydronics_v3/selectors/pipe_dn_selector_v1.py
# ======================================================================

"""
pipe_dn_selector_v1.py
----------------------

HVACgooee — Pipe DN Selector v1 (SKELETON)

Purpose
-------
Deterministic selection of nominal pipe diameter (DN)
from flow rate and design constraints.

RULES (v1)
----------
• Lookup-based
• No pressure drop calculation
• No topology knowledge
• Stateless
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


# ----------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PipeDNOption:
    dn: int
    max_flow_l_s: float
    """
    Maximum recommended flow for this DN.
    """


# ----------------------------------------------------------------------
# Selector
# ----------------------------------------------------------------------

class PipeDNSelectorV1:
    """
    DN selector based on maximum flow thresholds.
    """

    def __init__(self, options: Iterable[PipeDNOption]):
        self._options = sorted(
            options,
            key=lambda o: o.max_flow_l_s
        )

    def select_dn(self, flow_l_s: float) -> int:
        """
        Select the smallest DN capable of carrying the flow.
        """
        for opt in self._options:
            if flow_l_s <= opt.max_flow_l_s:
                return opt.dn

        # Fallback: largest DN
        return self._options[-1].dn
