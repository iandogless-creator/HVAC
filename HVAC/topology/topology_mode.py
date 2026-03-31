# ======================================================================
# HVAC/topology/topology_mode.py
# ======================================================================

from __future__ import annotations

import os
from typing import Literal


TopologyMode = Literal["bootstrap", "resolver"]


def get_topology_mode() -> TopologyMode:
    """
    Determines which topology strategy to use.

    Priority:
    1. Environment variable HVAC_TOPOLOGY_MODE
    2. Default = "bootstrap"
    """

    mode = os.getenv("HVAC_TOPOLOGY_MODE", "bootstrap").lower()

    if mode not in ("bootstrap", "resolver"):
        return "bootstrap"

    return mode