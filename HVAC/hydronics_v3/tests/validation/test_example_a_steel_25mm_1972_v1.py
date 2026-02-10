# ======================================================================
# HVAC/hydronics_v3/tests/validation/test_example_a_steel_25mm_1972_v1.py
# ======================================================================

from __future__ import annotations

import math

from HVAC.hydronics_v3.tests.validation.example_a_steel_25mm_1972_dataset_v1 import (
    EXAMPLE_ID,
    RHO_WATER_75C_KG_M3,
    MU_WATER_75C_PA_S,
    EPS_STEEL_M,
    PIPE_ID_M,
    LEGACY_POINTS,
    VEL_REL_TOL,
    DP_REL_TOL,
)


def _colebrook_white_friction_factor(re: float, rel_rough: float) -> float:
    """
    Colebrook-White solved by fixed-point iteration (deterministic).
    """
    if re <= 0:
        raise ValueError("Re must be > 0")
    if rel_rough < 0:
        raise ValueError("rel_rough must be >= 0")

    f = 0.02
    for _ in range(25):
        # 1/sqrt(f) = -2 log10( (ε/D)/3.7 + 2.51/(Re*sqrt(f)) )
        inv_sqrt_f = -2.0 * math.log10(
            (rel_rough / 3.7) + (2.51 / (re * math.sqrt(f)))
        )
        f = 1.0 / (inv_sqrt_f * inv_sqrt_f)
    return f


def _dp_per_m_pa(
    q_m3_s: float,
    d_m: float,
    rho: float,
    mu: float,
    eps_m: float,
) -> tuple[float, float, float]:
    """
    Returns: (dp_per_m_pa, velocity_m_s, reynolds)
    Darcy–Weisbach: dp/L = f * (rho/2) * v^2 / D
    """
    area = math.pi * (d_m * d_m) / 4.0
    v = q_m3_s / area
    re = (rho * v * d_m) / mu
    rel_rough = eps_m / d_m
    f = _colebrook_white_friction_factor(re, rel_rough)
    dp_per_m = f * (rho / 2.0) * (v * v) / d_m
    return dp_per_m, v, re


def test_hive_1972_example_a_steel_25mm_dp_validation_v1() -> None:
    """
    Example A — Heavy grade steel, water @ 75°C, nominal 25 mm.

    Locks:
    • dp/m magnitude vs legacy scan points (3 anchor points)
    • velocity sanity vs legacy table velocities
    """

    # Basic deterministic setup guard
    assert EXAMPLE_ID

    for p in LEGACY_POINTS:
        q_m3_s = p.q_l_s / 1000.0

        dp_pa_m, v_m_s, re = _dp_per_m_pa(
            q_m3_s=q_m3_s,
            d_m=PIPE_ID_M,
            rho=RHO_WATER_75C_KG_M3,
            mu=MU_WATER_75C_PA_S,
            eps_m=EPS_STEEL_M,
        )

        # Velocity check (table shows approx v in that sub-column)
        assert math.isclose(
            v_m_s,
            p.v_m_s,
            rel_tol=VEL_REL_TOL,
        ), f"v mismatch at Q={p.q_l_s} L/s (Re={re:.0f})"

        # Pressure drop check (Δpᵢ column interpreted as Pa/m)
        assert math.isclose(
            dp_pa_m,
            p.dp_pa_m,
            rel_tol=DP_REL_TOL,
        ), f"dp/m mismatch at Q={p.q_l_s} L/s (v={v_m_s:.2f}, Re={re:.0f})"
