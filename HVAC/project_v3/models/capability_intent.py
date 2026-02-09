# ======================================================================
# HVACgooee — Capability Intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CapabilityIntent:
    """
    Declares project-level capability intent.

    Intent only:
    - No engine selection
    - No availability checks
    - No licensing logic
    """

    heatloss: str = "simple"
    hydronics: str = "simple"

    # Future domains may be added safely:
    # acoustics: str = "simple"
    # lighting: str = "simple"
