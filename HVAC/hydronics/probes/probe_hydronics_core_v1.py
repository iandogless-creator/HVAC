"""
HVACgooee — Hydronics Physics Core Probe (v1)

Purpose:
Prove hydronics physics is callable with:
✔ no project
✔ no heat-loss
✔ no GUI
✔ pure numeric inputs
"""

from HVAC.hydronics.physics.colebrook import (
    colebrook,
    reynolds_number,
    darcy_weisbach,
    CalcPipe,
)

# ------------------------------------------------------------
# Raw engineering inputs (NOT project data)
# ------------------------------------------------------------

# Fluid (water ~20°C)
density = 998.0                  # kg/m³
nu = 1.004e-6                    # m²/s (kinematic viscosity)

# Pipe
diameter = 0.020                 # m (20 mm)
roughness = 1.5e-6               # m (copper)
length = 10.0                    # m

# Flow
flow_rate = 0.0003               # m³/s (0.3 L/s)

# ------------------------------------------------------------
# Explicit calculations
# ------------------------------------------------------------

area = 3.14159 * (diameter / 2) ** 2
velocity = flow_rate / area

Re = reynolds_number(velocity, diameter, nu)
eD = roughness / diameter
f = colebrook(Re, eD)

dp = darcy_weisbach(f, length, diameter, density, velocity)

# ------------------------------------------------------------
# Combined solver (sanity check)
# ------------------------------------------------------------

pipe = CalcPipe(
    flow_rate=flow_rate,
    diameter=diameter,
    length=length,
    roughness=roughness,
    density=density,
    kinematic_viscosity=nu,
)

# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

print("=== HVACgooee Hydronics Probe v1 ===")
print(f"Velocity           : {velocity:.3f} m/s")
print(f"Reynolds number    : {Re:,.0f}")
print(f"Friction factor f  : {f:.5f}")
print(f"Pressure drop      : {dp:.2f} Pa")
print("--- Combined CalcPipe ---")
for k, v in pipe.items():
    print(f"{k:16s}: {v}")
