"""
fluid_properties.py
-------------------

HVACgooee — FluidProperties v1.0 (final form)

Purpose
=======
Provide a unified object describing the thermophysical properties of the
working hydronic fluid. Designed for water, glycol mixes, and commercial
heat-transfer fluids (Fernox, Sentinel, Glysac, Solar-HTF, etc).

This is the ONLY class the hydronic_flow_solver uses.

Key design points:
------------------
• Every FluidProperties object exposes:
      - density(T_C)  -> kg/m³
      - viscosity(T_C)-> Pa·s
      - cp(T_C)       -> kJ/(kg·K)
      - k(T_C)        -> W/(m·K)
      - prandtl(T_C)  -> dimensionless
      - freeze_point_C
      - brand / product_line / concentration

• Optional temperature-dependent models:
      If density_fn_C / viscosity_fn_C / cp_fn_C / k_fn_C are supplied,
      the corresponding methods call those functions.
      Otherwise, they return the stored static values.

• All brand mixes consolidated into ONE lookup table:
      FLUID_LIBRARY = { "WATER", "WATER_60C", "PG_30", "FERNOX_ALPHI11_30", ... }

• No external dependencies.

Public entry point for solvers:
-------------------------------
    fp = FluidProperties.from_key("PG_30")
    rho = fp.density(T_C=55)
    mu  = fp.viscosity(T_C=55)
    cp  = fp.cp(T_C=55)
    k   = fp.k(T_C=55)
    pr  = fp.prandtl(T_C=55)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict


# ---------------------------------------------------------------------------
# Helper: simple linear interpolation for small engineering tables
# ---------------------------------------------------------------------------

def _interp1d(points: Dict[float, float], x: float) -> float:
    """
    Simple 1D linear interpolation over a dict of {T: value} points.
    Extrapolates linearly beyond the table ends.
    """
    if not points:
        raise ValueError("Interpolation table is empty.")

    xs = sorted(points.keys())
    # Below range
    if x <= xs[0]:
        x0, x1 = xs[0], xs[1] if len(xs) > 1 else xs[0]
    # Above range
    elif x >= xs[-1]:
        x0, x1 = xs[-2] if len(xs) > 1 else xs[-1], xs[-1]
    else:
        # Inside range
        x0, x1 = xs[0], xs[1]
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                x0, x1 = xs[i], xs[i + 1]
                break

    if x0 == x1:
        return points[x0]

    y0, y1 = points[x0], points[x1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# ---------------------------------------------------------------------------
# Water reference models (simple engineering approximations)
# ---------------------------------------------------------------------------

def water_density_polynomial(T_C: float) -> float:
    """
    Simple polynomial approximation of water density at T_C (°C).
    Valid approx 0–100°C. Returns [kg/m³].
    """
    t = T_C
    return (
        999.84
        - 0.06426 * t
        - 0.0085043 * t ** 2
        + 0.0000679 * t ** 3
        - 0.0000004 * t ** 4
    )


# viscosity of water [Pa·s] vs T (°C), coarse table for engineering use
_WATER_VISCOSITY_TABLE = {
    0.0: 1.79e-3,
    20.0: 1.00e-3,
    40.0: 0.65e-3,
    60.0: 0.47e-3,
    80.0: 0.36e-3,
    100.0: 0.28e-3,
}


def water_viscosity_interp(T_C: float) -> float:
    """Interpolated dynamic viscosity of water [Pa·s] from 0–100°C."""
    return _interp1d(_WATER_VISCOSITY_TABLE, T_C)


# cp and k of water are weakly temperature-dependent; we keep them nearly flat
def water_cp_kJ_kgK(T_C: float) -> float:
    """Approximate cp of water [kJ/(kg·K)] across 0–100°C."""
    # Slight increase with temperature, but keep simple
    return 4.18


def water_k_W_mK(T_C: float) -> float:
    """Approximate thermal conductivity of water [W/(m·K)] across 0–100°C."""
    return 0.6


# ---------------------------------------------------------------------------
# FluidProperties Class
# ---------------------------------------------------------------------------

@dataclass
class FluidProperties:
    """
    A complete thermophysical definition of a hydronic fluid.

    All units:
        density       -> kg/m³
        viscosity     -> Pa·s
        cp            -> kJ/(kg·K)
        k             -> W/(m·K)
        prandtl       -> dimensionless
        temperature   -> °C
    """

    # Identifier / naming
    name: str
    key: str

    # Static reference values (fallbacks)
    density_kg_m3: float
    dynamic_viscosity_Pas: float
    cp_kJ_kgK: float
    thermal_conductivity_W_mK: float
    prandtl_ref: float

    # Optional temperature-dependent functions
    density_fn_C: Optional[Callable[[float], float]] = None
    viscosity_fn_C: Optional[Callable[[float], float]] = None
    cp_fn_C: Optional[Callable[[float], float]] = None
    k_fn_C: Optional[Callable[[float], float]] = None

    # Brand info (for Fernox, Sentinel, Glysac, Solar-HTF)
    brand: Optional[str] = None
    product_line: Optional[str] = None
    concentration_pct: Optional[float] = None  # e.g. 30 for 30%

    # Extra info
    freeze_point_C: Optional[float] = None
    boiling_point_C: Optional[float] = None
    ph: Optional[float] = None

    # ------------------------------------------------------------------
    # API for hydronic_flow_solver
    # ------------------------------------------------------------------
    def density(self, T_C: Optional[float] = None) -> float:
        """
        Return density [kg/m³] at temperature T_C (°C) if a model exists,
        otherwise return the static density_kg_m3.
        """
        if T_C is not None and self.density_fn_C is not None:
            try:
                return float(self.density_fn_C(T_C))
            except Exception:
                pass
        return float(self.density_kg_m3)

    def viscosity(self, T_C: Optional[float] = None) -> float:
        """
        Return dynamic viscosity [Pa·s] at temperature T_C (°C)
        if a model exists, otherwise the static reference value.
        """
        if T_C is not None and self.viscosity_fn_C is not None:
            try:
                return float(self.viscosity_fn_C(T_C))
            except Exception:
                pass
        return float(self.dynamic_viscosity_Pas)

    def cp(self, T_C: Optional[float] = None) -> float:
        """
        Return specific heat [kJ/(kg·K)] at temperature T_C (°C)
        if a model exists, otherwise the static reference value.
        """
        if T_C is not None and self.cp_fn_C is not None:
            try:
                return float(self.cp_fn_C(T_C))
            except Exception:
                pass
        return float(self.cp_kJ_kgK)

    def k(self, T_C: Optional[float] = None) -> float:
        """
        Return thermal conductivity [W/(m·K)] at temperature T_C (°C)
        if a model exists, otherwise the static reference value.
        """
        if T_C is not None and self.k_fn_C is not None:
            try:
                return float(self.k_fn_C(T_C))
            except Exception:
                pass
        return float(self.thermal_conductivity_W_mK)

    def prandtl(self, T_C: Optional[float] = None) -> float:
        """
        Return Prandtl number at temperature T_C (°C).
        If we have all three functions (mu, cp, k), compute dynamically.
        Otherwise fall back to the stored reference value.
        """
        if T_C is not None and (
            self.viscosity_fn_C is not None
            or self.cp_fn_C is not None
            or self.k_fn_C is not None
        ):
            try:
                mu = self.viscosity(T_C)
                cp_J_kgK = self.cp(T_C) * 1000.0  # kJ -> J
                k_W_mK = self.k(T_C)
                if k_W_mK > 0.0:
                    return float(mu * cp_J_kgK / k_W_mK)
            except Exception:
                pass
        return float(self.prandtl_ref)

    # ------------------------------------------------------------------
    # Constructors / lookup
    # ------------------------------------------------------------------
    @classmethod
    def from_key(cls, fluid_key: str, T_C: Optional[float] = None) -> "FluidProperties":
        """
        Factory for solvers.

        fluid_key: case-insensitive key, e.g. "water", "PG_30",
                   "FERNOX_ALPHI11_30", "SOLAR_HTF_50".
        T_C: not used to modify the object itself; included for convenience
             so call sites can always pass a temperature. Properties are
             still queried via .density(T_C), .viscosity(T_C), etc.
        """
        key = fluid_key.strip().upper()
        if key not in FLUID_LIBRARY:
            raise KeyError(f"Unknown fluid key: {fluid_key}")
        return FLUID_LIBRARY[key]

    def summary_dict(self) -> Dict[str, float]:
        """
        Lightweight serializable summary (static values only).
        Intended for reports / payloads, not full physics.
        """
        return {
            "name": self.name,
            "key": self.key,
            "density_kg_m3": self.density_kg_m3,
            "dynamic_viscosity_Pas": self.dynamic_viscosity_Pas,
            "cp_kJ_kgK": self.cp_kJ_kgK,
            "thermal_conductivity_W_mK": self.thermal_conductivity_W_mK,
            "prandtl_ref": self.prandtl_ref,
            "brand": self.brand or "",
            "product_line": self.product_line or "",
            "concentration_pct": self.concentration_pct or 0.0,
            "freeze_point_C": self.freeze_point_C if self.freeze_point_C is not None else 0.0,
            "boiling_point_C": self.boiling_point_C if self.boiling_point_C is not None else 0.0,
            "ph": self.ph if self.ph is not None else 0.0,
        }


# ---------------------------------------------------------------------------
# FLUID LIBRARY
# ---------------------------------------------------------------------------

FLUID_LIBRARY: Dict[str, FluidProperties] = {}


def _register(fluid: FluidProperties) -> None:
    """Internal helper to register a fluid by its .key."""
    FLUID_LIBRARY[fluid.key.upper()] = fluid


# -----------------------------
# Pure Water (reference cases)
# -----------------------------
_register(
    FluidProperties(
        name="Pure Water (nominal)",
        key="WATER",
        density_kg_m3=998.2,
        dynamic_viscosity_Pas=1.002e-3,
        cp_kJ_kgK=4.187,
        thermal_conductivity_W_mK=0.598,
        prandtl_ref=6.9,
        density_fn_C=water_density_polynomial,
        viscosity_fn_C=water_viscosity_interp,
        cp_fn_C=water_cp_kJ_kgK,
        k_fn_C=water_k_W_mK,
        freeze_point_C=0.0,
        boiling_point_C=100.0,
    )
)

_register(
    FluidProperties(
        name="Pure Water 60°C",
        key="WATER_60C",
        density_kg_m3=983.2,
        dynamic_viscosity_Pas=0.466e-3,
        cp_kJ_kgK=4.182,
        thermal_conductivity_W_mK=0.653,
        prandtl_ref=3.0,
        density_fn_C=water_density_polynomial,
        viscosity_fn_C=water_viscosity_interp,
        cp_fn_C=water_cp_kJ_kgK,
        k_fn_C=water_k_W_mK,
        freeze_point_C=0.0,
        boiling_point_C=100.0,
    )
)


# -----------------------------
# Propylene Glycol Mixes (PG)
# Generic hydronic mixes (0–60%)
# -----------------------------
_register(
    FluidProperties(
        name="Propylene Glycol 20%",
        key="PG_20",
        brand="Generic",
        product_line="Propylene Glycol",
        concentration_pct=20.0,
        density_kg_m3=1015.0,
        dynamic_viscosity_Pas=2.0e-3,
        cp_kJ_kgK=3.9,
        thermal_conductivity_W_mK=0.48,
        prandtl_ref=8.2,
        freeze_point_C=-10.0,
    )
)

_register(
    FluidProperties(
        name="Propylene Glycol 30%",
        key="PG_30",
        brand="Generic",
        product_line="Propylene Glycol",
        concentration_pct=30.0,
        density_kg_m3=1030.0,
        dynamic_viscosity_Pas=3.0e-3,
        cp_kJ_kgK=3.8,
        thermal_conductivity_W_mK=0.44,
        prandtl_ref=12.0,
        freeze_point_C=-15.0,
    )
)

_register(
    FluidProperties(
        name="Propylene Glycol 40%",
        key="PG_40",
        brand="Generic",
        product_line="Propylene Glycol",
        concentration_pct=40.0,
        density_kg_m3=1047.0,
        dynamic_viscosity_Pas=5.2e-3,
        cp_kJ_kgK=3.65,
        thermal_conductivity_W_mK=0.42,
        prandtl_ref=18.0,
        freeze_point_C=-23.0,
    )
)

_register(
    FluidProperties(
        name="Propylene Glycol 50%",
        key="PG_50",
        brand="Generic",
        product_line="Propylene Glycol",
        concentration_pct=50.0,
        density_kg_m3=1065.0,
        dynamic_viscosity_Pas=8.0e-3,
        cp_kJ_kgK=3.4,
        thermal_conductivity_W_mK=0.40,
        prandtl_ref=25.0,
        freeze_point_C=-32.0,
    )
)


# -----------------------------
# Ethylene Glycol (EG) mixes
# -----------------------------
_register(
    FluidProperties(
        name="Ethylene Glycol 30%",
        key="EG_30",
        brand="Generic",
        product_line="Ethylene Glycol",
        concentration_pct=30.0,
        density_kg_m3=1050.0,
        dynamic_viscosity_Pas=2.5e-3,
        cp_kJ_kgK=3.4,
        thermal_conductivity_W_mK=0.37,
        prandtl_ref=10.0,
        freeze_point_C=-12.0,
    )
)

_register(
    FluidProperties(
        name="Ethylene Glycol 40%",
        key="EG_40",
        brand="Generic",
        product_line="Ethylene Glycol",
        concentration_pct=40.0,
        density_kg_m3=1065.0,
        dynamic_viscosity_Pas=3.8e-3,
        cp_kJ_kgK=3.2,
        thermal_conductivity_W_mK=0.36,
        prandtl_ref=14.0,
        freeze_point_C=-23.0,
    )
)


# -----------------------------
# Fernox (Alphi-11 etc)
# -----------------------------
_register(
    FluidProperties(
        name="Fernox Alphi-11 20%",
        key="FERNOX_ALPHI11_20",
        brand="Fernox",
        product_line="Alphi-11",
        concentration_pct=20.0,
        density_kg_m3=1025.0,
        dynamic_viscosity_Pas=1.9e-3,
        cp_kJ_kgK=3.9,
        thermal_conductivity_W_mK=0.47,
        prandtl_ref=7.5,
        freeze_point_C=-10.0,
    )
)

_register(
    FluidProperties(
        name="Fernox Alphi-11 30%",
        key="FERNOX_ALPHI11_30",
        brand="Fernox",
        product_line="Alphi-11",
        concentration_pct=30.0,
        density_kg_m3=1042.0,
        dynamic_viscosity_Pas=3.0e-3,
        cp_kJ_kgK=3.7,
        thermal_conductivity_W_mK=0.43,
        prandtl_ref=12.0,
        freeze_point_C=-15.0,
    )
)


# -----------------------------
# Sentinel (X-series, e.g. X500)
# -----------------------------
_register(
    FluidProperties(
        name="Sentinel X500 30%",
        key="SENTINEL_X500_30",
        brand="Sentinel",
        product_line="X500",
        concentration_pct=30.0,
        density_kg_m3=1040.0,
        dynamic_viscosity_Pas=3.2e-3,
        cp_kJ_kgK=3.7,
        thermal_conductivity_W_mK=0.44,
        prandtl_ref=11.2,
        freeze_point_C=-15.0,
    )
)


# -----------------------------
# Glysac Heat Transfer Fluids
# -----------------------------
_register(
    FluidProperties(
        name="Glysac HTF 30%",
        key="GLYSAC_30",
        brand="Glysac",
        product_line="HTF",
        concentration_pct=30.0,
        density_kg_m3=1035.0,
        dynamic_viscosity_Pas=3.1e-3,
        cp_kJ_kgK=3.8,
        thermal_conductivity_W_mK=0.46,
        prandtl_ref=10.0,
        freeze_point_C=-14.0,
    )
)


# -----------------------------
# Solar HTF (high-temperature fluids)
# -----------------------------
_register(
    FluidProperties(
        name="Solar High-Temp HTF",
        key="SOLAR_HTF",
        brand="SolarHTF",
        product_line="Synthetic HTF",
        concentration_pct=None,
        density_kg_m3=1070.0,
        dynamic_viscosity_Pas=12e-3,
        cp_kJ_kgK=2.3,
        thermal_conductivity_W_mK=0.10,
        prandtl_ref=300.0,
        freeze_point_C=-30.0,
        boiling_point_C=300.0,
    )
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_fluid(fluid_key: str) -> FluidProperties:
    """
    Lookup helper. Returns FluidProperties object or raises KeyError.

    This is a thin wrapper around FluidProperties.from_key(...).
    """
    return FluidProperties.from_key(fluid_key)
