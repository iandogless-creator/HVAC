"""Pure design-point liquid Kv arithmetic; no valve or product selection.

Kv in m³/h at 1 bar; delta-p = 1e5 * (rho / 1000) * (Q / Kv)^2.
Reference: Spirax Sarco, Control Valve Sizing for Water Systems, Eq. 6.3.1.
This relation assumes non-cavitating liquid flow; viscosity corrections and
manufacturer-specific characteristics remain outside this parameter model.
"""
import math


def valve_loss_Pa_v1(*, mass_flow_kg_s: float, density_kg_m3: float, kv: float) -> float:
    values = (mass_flow_kg_s, density_kg_m3, kv)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Positive finite flow, density and Kv required")
    try:
        volume = mass_flow_kg_s / density_kg_m3 * 3600.0
        loss = 100_000.0 * (density_kg_m3 / 1000.0) * (volume / kv) ** 2
    except (OverflowError, ZeroDivisionError):
        raise ValueError("Valve inputs exceed the numerical range") from None
    if not math.isfinite(loss) or loss <= 0:
        raise ValueError("Valve inputs exceed the numerical range")
    return loss
