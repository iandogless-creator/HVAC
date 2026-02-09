"""
window_calculation_engine.py
----------------------------

HVACgooee — Window Calculation Engine v1

Purpose
=======
Computational core for window / fenestration U-value calculations.
No GUI code. Designed to be imported by controllers and GUIs.

Supports (v1):
    • Single glazing (legacy / marine hopper)
    • Double / triple / quad glazing
    • Custom n-layer systems
    • Simple Low-E and solar coatings model
    • Multiple gas fills
    • Frame and edge corrections
    • Scandinavian-style presets (basic examples)
    • Override hooks for Ug, Uf, and ψ

Two calculation pathways:
    1) Legacy mode — simple single pane (cabin, boat, historic).
    2) Modern mode — EN 673 / ISO 10077-1 inspired structure
       (v1 uses simplified conduction + correction factors, but
        the data model is ready for higher fidelity EN 673 later).

This is a CORE physics engine and must remain GPL / immutable.
"""

# ================================================================
# BEGIN IMPORTS
# ================================================================
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt
from typing import List, Optional, Dict
# END IMPORTS
# ================================================================


# ================================================================
# BEGIN CONSTANTS
# ================================================================
# Surface resistances for vertical windows (approximate, typical):
DEFAULT_R_SE_M2K_W = 0.04  # external surface resistance
DEFAULT_R_SI_M2K_W = 0.13  # internal surface resistance

# Reasonable default conductivities (W/m·K) at ~10–20 °C
DEFAULT_GLASS_LAMBDA_W_MK = 1.0  # float glass, order-of-magnitude
GAS_CONDUCTIVITIES_W_MK: Dict["GasType", float] = {}

# Simple Low-E / gas correction factors for Ug (multipliers).
# These are deliberately coarse; the structure is EN 673–ready.
LOW_E_UG_FACTOR = 0.90     # ~10 % Ug improvement per low-E layer (soft coat)
SOLAR_CONTROL_UG_FACTOR = 0.98  # Ug almost unchanged; mostly affects g-value

GAS_UG_FACTORS = {
    "AIR": 1.00,
    "ARGON": 0.85,
    "KRYPTON": 0.70,
    "XENON": 0.60,
}

# Populate gas conductivity lookup once the enum is defined
# (we reassign in _initialise_gas_conductivities()).
# END CONSTANTS
# ================================================================


# ================================================================
# BEGIN ENUMS
# ================================================================
class CoatingType(Enum):
    """Simplified coating taxonomy."""
    NONE = auto()
    LOW_E_SOFT = auto()
    LOW_E_HARD = auto()
    SOLAR_CONTROL = auto()
    CUSTOM = auto()


class GasType(Enum):
    """Supported gas fills for cavities."""
    AIR = auto()
    ARGON = auto()
    KRYPTON = auto()
    XENON = auto()
    CUSTOM = auto()
# END ENUMS
# ================================================================


# ================================================================
# BEGIN DATA STRUCTURES
# ================================================================
@dataclass
class GlassLayer:
    """
    Single pane of glass within an IGU.

    thickness_m
        Actual glass thickness (m), e.g. 0.004 for 4 mm.
    conductivity_W_mK
        Thermal conductivity λ (W/m·K). Typical float glass ~1.0 W/m·K.
    coating
        Coating type. For modern IGUs, typically one Low-E layer.
    coating_ug_factor: Optional[float]
        Optional per-layer Ug multiplier to override the generic model
        (e.g. vendor-specific performance). If None, generic factors apply.
    """
    thickness_m: float
    conductivity_W_mK: float = DEFAULT_GLASS_LAMBDA_W_MK
    coating: CoatingType = CoatingType.NONE
    coating_ug_factor: Optional[float] = None


@dataclass
class Cavity:
    """
    Gas cavity between glass panes.

    width_m
        Cavity thickness (m), e.g. 0.016 for 16 mm.
    gas
        Gas type (Air, Argon, etc.).
    custom_conductivity_W_mK
        Optional λ for CUSTOM gas type.
    """
    width_m: float
    gas: GasType = GasType.AIR
    custom_conductivity_W_mK: Optional[float] = None


@dataclass
class FrameProperties:
    """
    Frame thermal properties.

    Uf_W_m2K
        Frame U-value (W/m²K).
    frame_fraction
        Fraction of total window area occupied by frame (0–1).
        glass_fraction = 1 - frame_fraction.
    """
    Uf_W_m2K: float
    frame_fraction: float


@dataclass
class SpacerProperties:
    """
    Spacer / edge seal properties.

    psi_W_mK
        Linear thermal transmittance at the glass edge (W/m·K).
    """
    psi_W_mK: float


@dataclass
class WindowConstruction:
    """
    Complete window construction description for the engine.

    glass_layers
        Ordered list of glass layers from outside → inside.
    cavities
        Ordered list of cavities; length must be len(glass_layers) - 1
        for a fully specified IGU in modern mode.
    frame
        Frame properties (Uf and frame fraction).
    spacer
        Spacer / edge properties.
    use_legacy
        Force legacy single-pane mode when True (if compatible).
    name
        Human-friendly identifier for presets, schedules, etc.
    """
    name: str
    glass_layers: List[GlassLayer]
    cavities: List[Cavity]
    frame: FrameProperties
    spacer: SpacerProperties
    use_legacy: bool = False


@dataclass
class WindowCalculationResult:
    """
    Result payload returned by the engine.
    """
    Ug_W_m2K: float           # centre-of-glass U
    Uf_W_m2K: float           # frame U
    psi_edge_W_mK: float      # edge linear transmittance
    Uw_W_m2K: float           # overall window U

    glass_fraction: float     # Ag / Atotal
    frame_fraction: float     # Af / Atotal

    # Optional / placeholder outputs for future enrichment:
    g_value: Optional[float] = None          # solar factor
    Rw_dB: Optional[float] = None            # sound insulation
    condensation_index: Optional[float] = None   # 0–1 or other metric
# END DATA STRUCTURES
# ================================================================


# ================================================================
# BEGIN INTERNAL HELPERS
# ================================================================
def _initialise_gas_conductivities() -> None:
    """Initialise the gas conductivity lookup using the GasType enum."""
    global GAS_CONDUCTIVITIES_W_MK

    GAS_CONDUCTIVITIES_W_MK = {
        GasType.AIR: 0.025,     # W/m·K (order of magnitude)
        GasType.ARGON: 0.016,
        GasType.KRYPTON: 0.009,
        GasType.XENON: 0.006,
        GasType.CUSTOM: 0.020,  # fallback if custom λ is not supplied
    }


_initialise_gas_conductivities()


def _gas_lambda(cavity: Cavity) -> float:
    """Return gas conductivity λ (W/m·K) for a cavity."""
    if cavity.gas is GasType.CUSTOM and cavity.custom_conductivity_W_mK is not None:
        return cavity.custom_conductivity_W_mK
    return GAS_CONDUCTIVITIES_W_MK.get(cavity.gas, GAS_CONDUCTIVITIES_W_MK[GasType.AIR])


def _should_use_legacy(construction: WindowConstruction) -> bool:
    """
    Decide whether to run in legacy mode.

    Legacy mode is intended for:
        • Single pane
        • No coatings
        • No gas cavities (or caller deliberately forces use_legacy)
        • Very small frame fraction (but we only check obvious things here).
    """
    # Forced by caller:
    if construction.use_legacy:
        return True

    # Single pane, no cavities, no coatings:
    single_pane = len(construction.glass_layers) == 1
    no_cavities = len(construction.cavities) == 0
    no_coatings = construction.glass_layers[0].coating == CoatingType.NONE

    return single_pane and no_cavities and no_coatings


def _compute_legacy_ug(construction: WindowConstruction,
                       R_se: float = DEFAULT_R_SE_M2K_W,
                       R_si: float = DEFAULT_R_SI_M2K_W) -> float:
    """
    Legacy centre-of-glass U for simple single glazing:

        R_glass = thickness / λ
        R_total = Rse + R_glass + Rsi
        U = 1 / R_total
    """
    layer = construction.glass_layers[0]
    if layer.conductivity_W_mK <= 0.0:
        raise ValueError("Glass conductivity must be positive in legacy mode.")

    R_glass = layer.thickness_m / layer.conductivity_W_mK
    R_total = R_se + R_glass + R_si
    return 1.0 / R_total


def _coating_factor_for_layer(layer: GlassLayer) -> float:
    """
    Return a multiplicative Ug factor for the given layer.

    Values < 1 improve performance (reduce U).
    """
    if layer.coating_ug_factor is not None:
        return layer.coating_ug_factor

    if layer.coating in (CoatingType.LOW_E_SOFT, CoatingType.LOW_E_HARD):
        return LOW_E_UG_FACTOR
    if layer.coating is CoatingType.SOLAR_CONTROL:
        return SOLAR_CONTROL_UG_FACTOR
    return 1.0


def _compute_modern_ug(construction: WindowConstruction,
                       R_se: float = DEFAULT_R_SE_M2K_W,
                       R_si: float = DEFAULT_R_SI_M2K_W) -> float:
    """
    Simplified EN 673-style Ug calculator for multi-layer IGUs.

    Structure matches EN 673 (glass + gas conduction, + radiative term),
    but v1 approximates radiative effects via correction factors:

        R_cond = Σ (t_glass / λ_glass) + Σ (t_gas / λ_gas)
        U_base = 1 / (R_se + R_cond + R_si)
        U_corr = U_base * (coating_factor * gas_factor)

    This keeps the code structure ready for a future full EN 673
    implementation while remaining lightweight for v1.
    """
    if not construction.glass_layers:
        raise ValueError("At least one glass layer is required for modern mode.")

    # 1) Conduction through glass layers
    R_glass = 0.0
    for layer in construction.glass_layers:
        if layer.conductivity_W_mK <= 0.0:
            raise ValueError("Glass conductivity must be positive.")
        R_glass += layer.thickness_m / layer.conductivity_W_mK

    # 2) Conduction through gas cavities
    R_gas = 0.0
    for cavity in construction.cavities:
        lam = _gas_lambda(cavity)
        if lam <= 0.0:
            raise ValueError("Gas conductivity must be positive.")
        R_gas += cavity.width_m / lam

    R_cond = R_glass + R_gas
    R_total = R_se + R_cond + R_si
    U_base = 1.0 / R_total

    # 3) Apply simple coating & gas correction factors
    coating_factor = 1.0
    for layer in construction.glass_layers:
        coating_factor *= _coating_factor_for_layer(layer)

    gas_factor = 1.0
    if construction.cavities:
        # Use the "worst" cavity (highest performance gas) as the main factor.
        # This is intentionally simplistic.
        best_factor = 1.0
        for cavity in construction.cavities:
            name = cavity.gas.name
            best_factor = min(best_factor, GAS_UG_FACTORS.get(name, 1.0))
        gas_factor = best_factor

    return U_base * coating_factor * gas_factor


def _approximate_glass_edge_length(Ag: float) -> float:
    """
    Approximate glass edge length L (m) from glass area Ag (m²)
    assuming a square pane:

        side = sqrt(Ag)
        L ≈ 4 * side

    This is a pragmatic default when we don't know actual edge length.
    """
    if Ag <= 0.0:
        return 0.0
    side = sqrt(Ag)
    return 4.0 * side
# END INTERNAL HELPERS
# ================================================================


# ================================================================
# BEGIN PUBLIC API
# ================================================================
def compute_window_performance(
        construction: WindowConstruction,
        width_m: float,
        height_m: float,
        *,
        glass_edge_length_m: Optional[float] = None,
        override_ug_W_m2K: Optional[float] = None,
        override_uf_W_m2K: Optional[float] = None,
        override_psi_W_mK: Optional[float] = None,
        R_se: float = DEFAULT_R_SE_M2K_W,
        R_si: float = DEFAULT_R_SI_M2K_W,
) -> WindowCalculationResult:
    """
    Main entry-point: compute window U-values and fractions.

    Parameters
    ----------
    construction
        WindowConstruction describing glass, frame, and spacer.
    width_m, height_m
        Overall window opening dimensions (m).
    glass_edge_length_m
        Optional explicit glass edge length L (m). If not provided,
        it is estimated from the glass area (rough square assumption).
    override_ug_W_m2K
        If provided, use this Ug value instead of computed legacy/modern.
    override_uf_W_m2K
        If provided, use this Uf instead of construction.frame.Uf_W_m2K.
    override_psi_W_mK
        If provided, use this ψ instead of construction.spacer.psi_W_mK.
    R_se, R_si
        Surface resistances (m²K/W).

    Returns
    -------
    WindowCalculationResult
        Ug, Uf, ψ_edge, Uw, and area fractions.
    """
    if width_m <= 0.0 or height_m <= 0.0:
        raise ValueError("Window dimensions must be positive.")

    Atotal = width_m * height_m
    frame_fraction = construction.frame.frame_fraction
    if not (0.0 <= frame_fraction < 1.0):
        raise ValueError("Frame fraction must be within [0, 1).")

    Af = frame_fraction * Atotal
    Ag = Atotal - Af
    glass_fraction = Ag / Atotal if Atotal > 0.0 else 0.0

    # --- Ug ---
    if override_ug_W_m2K is not None:
        Ug = override_ug_W_m2K
    else:
        if _should_use_legacy(construction):
            Ug = _compute_legacy_ug(construction, R_se=R_se, R_si=R_si)
        else:
            Ug = _compute_modern_ug(construction, R_se=R_se, R_si=R_si)

    # --- Uf ---
    Uf = override_uf_W_m2K if override_uf_W_m2K is not None else construction.frame.Uf_W_m2K

    # --- ψ (edge) ---
    psi_edge = override_psi_W_mK if override_psi_W_mK is not None else construction.spacer.psi_W_mK

    # --- Edge length L ---
    if glass_edge_length_m is not None:
        L_edge = glass_edge_length_m
    else:
        # Pragmatic default: approximate from glass area.
        L_edge = _approximate_glass_edge_length(Ag)

    # --- Uw ---
    if Atotal <= 0.0:
        raise ValueError("Total window area must be positive.")

    Uw = (Ag * Ug + Af * Uf + L_edge * psi_edge) / Atotal

    # Legacy note: original cabin/boat formula was:
    #   Uw_legacy = Ug * glass_fraction + Uf * frame_fraction
    # If you want that value as well, you can compute it externally
    # from the returned fractions and U-values.

    return WindowCalculationResult(
        Ug_W_m2K=Ug,
        Uf_W_m2K=Uf,
        psi_edge_W_mK=psi_edge,
        Uw_W_m2K=Uw,
        glass_fraction=glass_fraction,
        frame_fraction=frame_fraction,
    )
# END PUBLIC API
# ================================================================


# ================================================================
# BEGIN PRESETS
# ================================================================
def preset_legacy_single_pane_cabin(
        name: str = "Legacy single-pane cabin",
        pane_thickness_m: float = 0.005,  # 5 mm toughened
        frame_fraction: float = 0.10,
        Uf_W_m2K: float = 5.0,
) -> WindowConstruction:
    """
    Simple helper preset for marine / cabin / hopper-type single glazing.

    This uses:
        • Single glass layer (no coatings)
        • No cavities
        • Basic frame Uf and small frame fraction
        • Spacer ψ assumed negligible (0.00 W/m·K)
    """
    glass = GlassLayer(thickness_m=pane_thickness_m,
                       conductivity_W_mK=DEFAULT_GLASS_LAMBDA_W_MK,
                       coating=CoatingType.NONE)
    frame = FrameProperties(Uf_W_m2K=Uf_W_m2K, frame_fraction=frame_fraction)
    spacer = SpacerProperties(psi_W_mK=0.0)
    return WindowConstruction(
        name=name,
        glass_layers=[glass],
        cavities=[],
        frame=frame,
        spacer=spacer,
        use_legacy=True,
    )


def preset_scandi_triple_low_e_argon(
        name: str = "Scandinavian triple, Low-E, Argon",
        pane_thickness_m: float = 0.004,
        cavity_width_m: float = 0.016,
        frame_fraction: float = 0.25,
        Uf_W_m2K: float = 1.2,
        psi_W_mK: float = 0.040,
) -> WindowConstruction:
    """
    Example Scandinavian-style triple glazing with Low-E and Argon.

    IGU configuration:
        4 / 16 / 4 / 16 / 4 (outer → inner)
        All cavities Argon, all inner surfaces Low-E.

    This is a convenience factory; actual project data should be
    supplied by the controller or GUI where possible.
    """
    glass_layers = [
        GlassLayer(thickness_m=pane_thickness_m,
                   conductivity_W_mK=DEFAULT_GLASS_LAMBDA_W_MK,
                   coating=CoatingType.NONE),
        GlassLayer(thickness_m=pane_thickness_m,
                   conductivity_W_mK=DEFAULT_GLASS_LAMBDA_W_MK,
                   coating=CoatingType.LOW_E_SOFT),
        GlassLayer(thickness_m=pane_thickness_m,
                   conductivity_W_mK=DEFAULT_GLASS_LAMBDA_W_MK,
                   coating=CoatingType.LOW_E_SOFT),
    ]

    cavities = [
        Cavity(width_m=cavity_width_m, gas=GasType.ARGON),
        Cavity(width_m=cavity_width_m, gas=GasType.ARGON),
    ]

    frame = FrameProperties(Uf_W_m2K=Uf_W_m2K, frame_fraction=frame_fraction)
    spacer = SpacerProperties(psi_W_mK=psi_W_mK)

    return WindowConstruction(
        name=name,
        glass_layers=glass_layers,
        cavities=cavities,
        frame=frame,
        spacer=spacer,
        use_legacy=False,
    )
# END PRESETS
# ================================================================


# ================================================================
# BEGIN MODULE EXPORTS
# ================================================================
__all__ = [
    "CoatingType",
    "GasType",
    "GlassLayer",
    "Cavity",
    "FrameProperties",
    "SpacerProperties",
    "WindowConstruction",
    "WindowCalculationResult",
    "compute_window_performance",
    "preset_legacy_single_pane_cabin",
    "preset_scandi_triple_low_e_argon",
]
# END MODULE EXPORTS
# ================================================================
