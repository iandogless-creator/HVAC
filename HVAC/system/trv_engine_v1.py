# ================================================================
# BEGIN MODULE: trv_engine_v1.py
# ================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TRVType(Enum):
    """
    Types of TRV behaviour that HVACgooee can model.

    NONE
        No TRVs in the circuit. Flow is governed only by balancing
        valves and pump curve. This is closest to continental
        "full circuit always open" practice.

    UK_COARSE
        Typical UK mechanical TRV with relatively high hysteresis and
        "bang-bang" style throttling. Often installed on oversized
        radiators in on/off boiler systems.

    EU_PROPORTIONAL
        Higher quality TRVs (often electronic or proportional) that
        modulate more smoothly and are intended to work *with* weather
        compensation and fully modulating boilers.
    """
    NONE = auto()
    UK_COARSE = auto()
    EU_PROPORTIONAL = auto()


@dataclass
class TRVConfig:
    """
    Configuration of TRV behaviour for a given emitter or space.

    This is not the emitter physics itself (that belongs to the
    hydronics / radiator model) but a behavioural overlay for
    comfort vs compliance diagnostics.
    """

    trv_type: TRVType = TRVType.NONE

    # Nominal saturation point relative to room design temperature.
    # Example: 0.0 → TRV aims right at T_design.
    #          -1.0 → TRV tends to be "over eager" and shuts a bit early.
    setpoint_offset_C: float = 0.0

    # Approximate hysteresis band (°C) around the setpoint.
    # Large hysteresis → coarse open/close cycles.
    hysteresis_C: float = 1.0

    # Dimensionless "authority" 0–1:
    #   0 → TRV almost irrelevant (tiny kv, parallel bypass),
    #   1 → TRV fully determines local flow.
    authority: float = 0.8

    # Whether this TRV has been installed on *most* emitters in the space.
    installed_on_primary_emitters: bool = True


@dataclass
class TRVEffect:
    """
    Result of applying a TRV behaviour model at a given operating condition.

    This is intended for:
        - Comfort vs compliance diagnostics
        - Guidance to designers (e.g. "TRVs are fighting weather comp")
        - Boiler cycling / return temperature risk indications

    All fields are heuristics in v1, not strict physics.
    """

    # 0.0–1.0: fraction of "ideal" design flow actually reaching the emitter.
    flow_fraction: float

    # Approximate increase in return temperature (°C) due to TRV throttling
    # at this operating condition. Positive means "less condensing".
    return_temp_penalty_C: float

    # 0–10: higher means more likely to cause noticeable boiler/pump cycling
    # and audible hydronic noise in the circuit.
    cycling_risk_index: float

    # 0–10: higher means greater risk that the room "feels wrong" compared
    # to its TEI / T_design, especially during transient periods (morning).
    comfort_lag_index: float

    # Optional explanatory string for diagnostics / report.
    note: str = ""


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def estimate_trv_effect(
        *,
        trv_config: TRVConfig,
        load_fraction: float,
        dp_bar: float,
        has_weather_comp: bool,
) -> TRVEffect:
    """
    Estimate the effect of TRVs at a given operating condition.

    Parameters
    ----------
    trv_config:
        Behaviour configuration for the TRV type.

    load_fraction:
        Fraction of design heat load currently demanded by the space/emitter.
        1.0 → design day, 0.3 → mild day, 0.1 → trickle heat season.

    dp_bar:
        Approximate differential pressure across the TRV (bar).
        Used to estimate risk of noise and over-throttling.

    has_weather_comp:
        True if the system is using weather compensation / proper
        flow temperature modulation. False if the system behaves
        like a typical UK on/off, fixed-flow system.

    Returns
    -------
    TRVEffect
        Heuristic indicators for:
            - flow reduction
            - return temperature penalty
            - cycling risk
            - comfort lag
    """

    # Normalise inputs
    lf = _clamp(load_fraction, 0.0, 1.5)  # allow slight overload >1.0
    dp = max(0.0, dp_bar)

    # Case 1 — No TRVs
    if trv_config.trv_type == TRVType.NONE or not trv_config.installed_on_primary_emitters:
        return TRVEffect(
            flow_fraction=1.0,
            return_temp_penalty_C=0.0,
            cycling_risk_index=0.0,
            comfort_lag_index=0.0,
            note="No TRV influence at this emitter.",
        )

    # Base parameters depending on TRV type
    if trv_config.trv_type == TRVType.UK_COARSE:
        # Coarse, high hysteresis TRVs
        base_hysteresis = max(trv_config.hysteresis_C, 1.0)
        authority = _clamp(trv_config.authority, 0.3, 1.0)
        # UK coarse TRVs cause more trouble at low loads
        low_load_sensitivity = 1.0
    else:
        # EU proportional TRVs
        base_hysteresis = _clamp(trv_config.hysteresis_C, 0.1, 0.7)
        authority = _clamp(trv_config.authority, 0.3, 1.0)
        # Better behaved at low loads
        low_load_sensitivity = 0.4

    # ------------------------------------------------------------
    # Estimate flow fraction (0–1)
    # ------------------------------------------------------------
    # At high load we expect TRVs to be relatively open.
    # At low load, coarse TRVs tend to pinch flow more aggressively.
    # Very high dp also encourages throttling.
    #
    # Heuristic:
    #   flow_fraction ≈ 1 - authority * f(load_fraction, dp)
    #

    # As load_fraction drops below ~0.4, coarse TRVs start closing.
    load_factor = 1.0 - lf  # 0 at full load, ~0.6 at lf=0.4, 0.9 at lf=0.1

    # dp influence: treat >0.3 bar as "high", typical small UK circuits
    dp_factor = _clamp(dp / 0.3, 0.0, 2.0)  # 0..2

    # Combined throttling tendency
    throttling_score = low_load_sensitivity * load_factor * (0.5 + 0.5 * dp_factor)

    flow_fraction = 1.0 - authority * throttling_score
    flow_fraction = _clamp(flow_fraction, 0.1, 1.0)  # don't drop below 10% in v1

    # ------------------------------------------------------------
    # Return temperature penalty (°C)
    # ------------------------------------------------------------
    # When TRVs throttle, less water is cooled by the emitter,
    # raising return temperature and reducing condensing potential.
    #
    # Rough heuristic:
    #   penalty ≈ (1 - flow_fraction) * K
    #   K larger for coarse TRVs.
    if trv_config.trv_type == TRVType.UK_COARSE:
        K_penalty = 8.0  # up to ~8°C penalty at heavy throttling
    else:
        K_penalty = 4.0  # up to ~4°C penalty for proportional TRVs

    return_temp_penalty_C = (1.0 - flow_fraction) * K_penalty
    return_temp_penalty_C = max(0.0, return_temp_penalty_C)

    # ------------------------------------------------------------
    # Cycling risk index (0–10)
    # ------------------------------------------------------------
    # High dp + coarse TRVs + low load = cycling & noise risk.
    #
    # Normalise pieces into 0..1 then scale to 0..10.
    dp_norm = _clamp(dp / 0.3, 0.0, 2.0) / 2.0            # 0..1
    hysteresis_norm = _clamp(base_hysteresis / 2.0, 0.0, 1.0)  # ~0..1
    low_load_norm = _clamp(1.0 - lf, 0.0, 1.0)            # 0..1

    cycling_risk = (dp_norm * 0.4 + hysteresis_norm * 0.3 + low_load_norm * 0.3)
    if trv_config.trv_type == TRVType.UK_COARSE:
        cycling_risk *= 1.4  # exaggerate for coarse TRVs
    cycling_risk_index = _clamp(cycling_risk * 10.0, 0.0, 10.0)

    # ------------------------------------------------------------
    # Comfort lag index (0–10)
    # ------------------------------------------------------------
    # Comfort lag is worst when:
    #   - TRV authority is high
    #   - hysteresis is large
    #   - load is low (TRV shuts early)
    #   - system does NOT have weather compensation
    #
    # Weather compensation reduces lag significantly.
    authority_norm = _clamp(authority, 0.0, 1.0)
    # Inverse effect for weather comp: 1.0 → UK/no-comp, 0.3 → good comp
    comp_factor = 1.0 if not has_weather_comp else 0.4

    comfort_lag = (
                          authority_norm * 0.4 +
                          hysteresis_norm * 0.3 +
                          low_load_norm * 0.3
                  ) * comp_factor

    comfort_lag_index = _clamp(comfort_lag * 10.0, 0.0, 10.0)

    # ------------------------------------------------------------
    # Note for diagnostics
    # ------------------------------------------------------------
    if trv_config.trv_type == TRVType.UK_COARSE:
        note = (
            "UK-style coarse TRV: at low loads and high dp this valve is likely "
            "to throttle aggressively, increasing return temperature and "
            "raising cycling and comfort lag risk."
        )
    else:
        note = (
            "Proportional TRV: better suited to weather-compensated, modulating "
            "systems. Effects are milder but still present at low loads and "
            "high dp."
        )

    return TRVEffect(
        flow_fraction=flow_fraction,
        return_temp_penalty_C=return_temp_penalty_C,
        cycling_risk_index=cycling_risk_index,
        comfort_lag_index=comfort_lag_index,
        note=note,
    )


# ================================================================
# END MODULE
# ================================================================
