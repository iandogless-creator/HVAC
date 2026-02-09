"""
radiator_sizer_v1.py
--------------------

HVACgooee — Radiator Sizer (v1)

Purpose
-------
Sizes a radiator to meet a required heat output (QT)
under given hydronic conditions.

Implements:
    EmitterSizer (Hydronics → Emitters interface)

Design Rules (v1)
-----------------
✔ No project knowledge
✔ No geometry
✔ No pipe network logic
✔ No manufacturer lock-in
✔ Uses standard radiator correction law
"""

from __future__ import annotations

from dataclasses import dataclass

from HVAC_legacy.hydronics.emitters.emitter_result_v1 import EmitterResult
from HVAC_legacy.hydronics.interfaces.hydronics_to_emitters_v1 import EmitterSizer


# ---------------------------------------------------------------------------
# Radiator sizing constants (v1 defaults)
# ---------------------------------------------------------------------------

REFERENCE_DELTA_T_K = 50.0
RADIATOR_EXPONENT_N = 1.3


@dataclass(frozen=True)
class RadiatorSizerV1(EmitterSizer):
    """
    Radiator sizing engine (v1).

    This class sizes an equivalent radiator output requirement
    using standard correction methodology.

    It does NOT select manufacturer models.
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
        Size a radiator to meet the required heat output.

        Returns an EmitterResult describing the
        equivalent radiator requirement.
        """

        if required_output_W <= 0:
            raise ValueError("required_output_W must be positive")

        if mean_water_deltaT_K <= 0:
            raise ValueError("mean_water_deltaT_K must be positive")

        # ------------------------------------------------------------------
        # Radiator correction law
        # ------------------------------------------------------------------

        correction_factor = (
            mean_water_deltaT_K / REFERENCE_DELTA_T_K
        ) ** RADIATOR_EXPONENT_N

        equivalent_output_at_dt50_W = required_output_W / correction_factor

        # ------------------------------------------------------------------
        # Assemble result
        # ------------------------------------------------------------------

        return EmitterResult(
            emitter_type="radiator",
            required_output_W=required_output_W,
            delivered_output_W=required_output_W,
            mean_water_deltaT_K=mean_water_deltaT_K,
            flow_rate_m3_s=flow_rate_m3_s,
            pressure_drop_Pa=available_pressure_Pa,
            geometry_descriptor="Equivalent radiator sized at ΔT50",
            notes=(
                f"Equivalent radiator output at ΔT50 = "
                f"{equivalent_output_at_dt50_W:.1f} W "
                f"(n={RADIATOR_EXPONENT_N})"
            ),
            extra={
                "equivalent_output_at_dt50_W": equivalent_output_at_dt50_W,
                "radiator_exponent_n": RADIATOR_EXPONENT_N,
            },
        )
