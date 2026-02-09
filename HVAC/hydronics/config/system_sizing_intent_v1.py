# ============================================================
# BOUNDARY GUARD (v1)
# ============================================================
# This module MUST ONLY be imported by project orchestration.
#
# It MUST NOT be imported by:
#   - hydronics physics
#   - distribution logic
#   - emitters
#
# Oversizing intent is applied exactly ONCE at QT hand-off.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SystemSizingIntent:
    """
    User-defined hydronic sizing intent (v1).

    All values are FRACTIONS:
        0.20 = +20% oversize
        0.00 = no oversize
    """

    boiler_oversize_fraction: float = 0.0
    """
    Oversizing fraction applied to QT when sizing
    the heat source (boiler / heat pump).
    """

    emitter_oversize_fraction: float = 0.0
    """
    Oversizing fraction applied to QT when sizing
    emitters (radiators, UFH, fan coils).
    """

    notes: Optional[str] = None
    """
    Optional user notes explaining the sizing intent.
    Shown in reports / summaries.
    """

    # ------------------------------------------------------------------
    # Validation helpers (v1-safe, optional use)
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Validate oversize fractions are sane.

        Raises
        ------
        ValueError if values are outside expected bounds.
        """
        if not (0.0 <= self.boiler_oversize_fraction <= 1.0):
            raise ValueError(
                "boiler_oversize_fraction must be between 0.0 and 1.0"
            )

        if not (0.0 <= self.emitter_oversize_fraction <= 1.0):
            raise ValueError(
                "emitter_oversize_fraction must be between 0.0 and 1.0"
            )
