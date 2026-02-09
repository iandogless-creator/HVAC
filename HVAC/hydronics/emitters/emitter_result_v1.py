"""
emitter_result_v1.py
--------------------

HVACgooee — Emitter Result Dataclass (v1)

Purpose
-------
Represents the result of sizing an emitter (radiator, UFH loop,
fan coil, etc.) to satisfy a required heat demand (QT).

Design Rules (v1)
-----------------
✔ Data-only
✔ Immutable
✔ No physics
✔ No project / geometry / heat-loss imports
✔ Safe to serialize
✔ Safe to display in GUI
✔ Safe to compare / report

This is a CONTRACT object between:
    Hydronics  →  Emitters  →  GUI / Reports
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class EmitterResult:
    """
    Canonical emitter sizing result (v1).

    All values are OUTPUTS of hydronics/emitter sizing,
    not inputs to heat-loss or hydronics physics.
    """

    # ==============================================================
    # REQUIRED CORE OUTPUTS (NO DEFAULTS — MUST COME FIRST)
    # ==============================================================

    emitter_type: str
    """
    Type of emitter.
    Examples:
        'radiator'
        'ufh_loop'
        'fan_coil'
        'panel_heater'
    """

    required_output_W: float
    """
    Heat output required from this emitter (W).
    """

    # ==============================================================
    # OPTIONAL IDENTIFIERS / DESCRIPTORS (DEFAULTS ONLY)
    # ==============================================================

    emitter_id: Optional[str] = None
    """
    Optional identifier (e.g. 'Rad-01', 'UFH-Living-Loop-2').
    GUI / project layer concern.
    """

    model_reference: Optional[str] = None
    """
    Manufacturer / catalogue reference, if applicable.
    """

    geometry_descriptor: Optional[str] = None
    """
    Free-form descriptor:
        e.g. '600x1000 double panel',
             '100 m UFH loop',
             '2-row FCU'
    """

    notes: Optional[str] = None
    """
    Human-readable notes or warnings.
    """

    # ==============================================================
    # EXTENSIBILITY (NUMERIC-ONLY, SAFE)
    # ==============================================================

    extra: Optional[Dict[str, float]] = None
    """
    Optional dictionary for emitter-specific metrics.

    Examples:
        - surface_temperature_C
        - air_flow_m3_s
        - loop_length_m

    Must remain numeric-only.
    """
