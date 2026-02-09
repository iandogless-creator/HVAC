# ------------------
# HVAC/core/colebrook.py
# CANONICAL v1 — DO NOT BYPASS

import math


# ---------------------------------------------------------------------------
# Colebrook equation solver for friction factor
# ---------------------------------------------------------------------------
def colebrook(Re, eD, tol=1e-6, max_iter=100):
    """
    Solve the Colebrook equation for friction factor f.
    Re = Reynolds number
    eD = relative roughness (epsilon / diameter)
    """
    if Re < 2000:  # laminar flow
        return 64 / Re

    # Initial guess (Swamee-Jain)
    f = 0.02
    for _ in range(max_iter):
        f_old = f
        f = (-2 * math.log10(eD / 3.7 + 2.51 / (Re * math.sqrt(f)))) ** -2
        if abs(f - f_old) < tol:
            break
    return f


# ---------------------------------------------------------------------------
# Reynolds number
# ---------------------------------------------------------------------------
def reynolds_number(velocity, diameter, kinematic_viscosity):
    """Compute Reynolds number."""
    return velocity * diameter / kinematic_viscosity


def CalcPipe(flow_rate, diameter, length, roughness, density, kinematic_viscosity):
    """
    Combined pipe flow calculator:
    - Computes velocity, Reynolds number, friction factor, and pressure drop.
    Returns a dictionary with all key values.
    """
    # Cross-sectional area (m²)
    area = math.pi * (diameter / 2) ** 2
    velocity = flow_rate / area

    # Reynolds number
    Re = reynolds_number(velocity, diameter, kinematic_viscosity)

    # Relative roughness
    eD = roughness / diameter

    # Friction factor (Colebrook)
    f = colebrook(Re, eD)

    # Pressure drop (Pa)
    dp = darcy_weisbach(f, length, diameter, density, velocity)

    return {
        "velocity": velocity,
        "Re": Re,
        "friction_factor": f,
        "pressure_drop": dp,
    }


# ---------------------------------------------------------------------------
# Darcy-Weisbach pressure drop
# ---------------------------------------------------------------------------
def darcy_weisbach(f, length, diameter, density, velocity):
    """Compute pressure drop (Pa) using the Darcy–Weisbach equation."""
    return f * (length / diameter) * 0.5 * density * velocity**2


#
