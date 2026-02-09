"""
hydronics_to_emitters_v1.py
---------------------------

HVACgooee — Hydronics → Emitters Interface (v1)

Purpose
-------
Defines the formal contract between hydronics calculations
and emitter sizing modules (radiators, UFH, fan coils).

This module contains:
✔ Protocols / abstract interfaces only
✔ No physics
✔ No sizing logic
✔ No project knowledge

Hydronics produces:
    - QT (W)
    - Flow rate
    - Available pressure

Emitters produce:
    - EmitterResult
"""

from __future__ import annotations

from typing import Protocol

from HVAC_legacy.hydronics.emitters.emitter_result_v1 import EmitterResult


class EmitterSizer(Protocol):
    """
    Protocol for all emitter sizing implementations (v1).

    Implementations may include:
        - RadiatorSizer
        - UFHSizer
        - FanCoilSizer
    """

    def size_emitter(
        self,
        *,
        required_output_W: float,
        flow_rate_m3_s: float,
        available_pressure_Pa: float,
        mean_water_deltaT_K: float,
    ) -> EmitterResult:
        """
        Size an emitter to satisfy the required heat output.

        Parameters
        ----------
        required_output_W:
            Heat demand to be met by the emitter (QT).

        flow_rate_m3_s:
            Design flow rate available to the emitter.

        available_pressure_Pa:
            Pressure available across the emitter at design flow.

        mean_water_deltaT_K:
            Mean water temperature difference used for sizing
            (e.g. ΔT50, ΔT30, UFH effective ΔT).

        Returns
        -------
        EmitterResult
            Immutable result describing the sized emitter.
        """
        ...
