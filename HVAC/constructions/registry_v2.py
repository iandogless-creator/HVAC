# ======================================================================
# HVAC/constructions/registry_v2.py
# ======================================================================

"""
HVACgooee — Construction Registry v2 (CANONICAL)

Purpose
-------
Single authoritative entry point for construction selection
and U-value resolution.

RULES (LOCKED)
--------------
• Returns ConstructionUValueResultDTO ONLY (minimal contract)
• No knowledge of rooms, area, ΔT, Qf, or hydronics
• Construction intent ends here
"""

from __future__ import annotations

from typing import Any, Dict, List

from HVAC_legacy.constructions.construction_preset import ConstructionPreset, SurfaceClass
from HVAC_legacy.constructions.construction_preset_registry import ConstructionPresetRegistry
from HVAC_legacy.constructions.presets_v2 import PRESETS_V2

from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)

from HVAC_legacy.constructions.engines.pitched_roof_calculator import PitchedRoof, RoofLayer
from HVAC_legacy.constructions.engines.window_calculation_engine import WindowConstruction

from .adapters.roof_to_uvalue_dto import build_pitched_roof_uvalue_dto
from .adapters.flat_roof_to_uvalue_dto import build_flat_roof_uvalue_dto
from .adapters.external_wall_to_uvalue_dto import build_external_wall_brick_stud_uvalue_dto
from .adapters.floor_to_uvalue_dto import build_floor_uvalue_dto
from .adapters.window_to_uvalue_dto import build_window_uvalue_dto


class ConstructionRegistryV2:
    """
    Canonical construction registry.

    Allowed responsibilities (LOCKED):
    • list presets by surface
    • resolve a preset to a minimal ConstructionUValueResultDTO
    • build engine/adapters-based constructions and return the SAME DTO
    """

    def __init__(self, presets: List[ConstructionPreset]) -> None:
        self._presets = ConstructionPresetRegistry(presets)

    # ------------------------------------------------------------------
    # Discovery API (read-only) — GUI uses this
    # ------------------------------------------------------------------

    def list_presets_for_surface(self, surface_class: SurfaceClass) -> List[ConstructionPreset]:
        return self._presets.list_for_surface(surface_class)

    # ------------------------------------------------------------------
    # Preset resolution API (CANONICAL for GUI preset pickers)
    # ------------------------------------------------------------------

    def build_uvalue_result(self, surface_class: SurfaceClass, preset_ref: str) -> ConstructionUValueResultDTO:
        """
        Resolve a preset into the canonical minimal DTO.

        HARD RULE:
        • registry returns ConstructionUValueResultDTO(surface_class, construction_ref, u_value)
        """
        preset = self._presets.get(preset_ref)

        # Guard: surface_class must be a SurfaceClass enum
        if not isinstance(surface_class, SurfaceClass):
            raise TypeError(
                f"surface_class must be SurfaceClass, got {type(surface_class)}"
            )

        # Enum-safe comparison (SurfaceClass inherits from str)
        if preset.surface_class != surface_class:
            raise ValueError(
                "Preset surface mismatch:\n"
                f"  preset_ref     : {preset.ref}\n"
                f"  preset.surface : {preset.surface_class!r}\n"
                f"  requested      : {surface_class!r}"
            )

        if preset.u_value is None or preset.u_value <= 0.0:
            raise ValueError(
                "Invalid preset U-value:\n"
                f"  preset_ref : {preset.ref}\n"
                f"  u_value    : {preset.u_value}"
            )

        return ConstructionUValueResultDTO(
            surface_class=surface_class,
            construction_ref=preset.ref,
            u_value=float(preset.u_value),
        )

    # ------------------------------------------------------------------
    # Engine/adapters build API (optional in v2; still supported)
    # ------------------------------------------------------------------

    def build_construction(
        self,
        construction_type: str,
        preset_ref: str,
        parameters: Dict[str, Any],
    ) -> ConstructionUValueResultDTO:
        """
        Build an engine/adapters construction and return minimal DTO.

        NOTE:
        This path exists for non-trivial constructions (roof/window engines).
        GUI preset pickers should prefer build_uvalue_result().
        """
        if construction_type == "roof.pitched":
            return self._build_pitched_roof(preset_ref, parameters)

        if construction_type == "roof.flat":
            return self._build_flat_roof(preset_ref, parameters)

        if construction_type == "wall.external.brick_stud":
            return self._build_external_wall_brick_stud(preset_ref, parameters)

        if construction_type == "floor":
            return self._build_floor(preset_ref, parameters)

        if construction_type == "window":
            return self._build_window(preset_ref, parameters)

        raise ValueError(f"Unsupported construction type: {construction_type}")

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_pitched_roof(self, preset_ref: str, parameters: Dict[str, Any]) -> ConstructionUValueResultDTO:
        preset = self._presets.get(preset_ref)

        layers = [RoofLayer(**layer) for layer in parameters.get("layers", [])]

        roof = PitchedRoof(
            pitch_deg=parameters.get("pitch_deg"),
            layers=layers,
            ventilated=parameters.get("ventilated", False),
            bridging=parameters.get("bridging", False),
            thermal_mass=parameters.get("thermal_mass", False),
            mode=parameters.get("mode", "default"),
        )

        # adapter MUST return minimal DTO now
        return build_pitched_roof_uvalue_dto(
            roof=roof,
            construction_ref=preset.ref,
        )

    def _build_flat_roof(self, preset_ref: str, parameters: Dict[str, Any]) -> ConstructionUValueResultDTO:
        preset = self._presets.get(preset_ref)
        return build_flat_roof_uvalue_dto(
            construction_ref=preset.ref,
            **parameters,
        )

    def _build_external_wall_brick_stud(self, preset_ref: str, parameters: Dict[str, Any]) -> ConstructionUValueResultDTO:
        preset = self._presets.get(preset_ref)
        return build_external_wall_brick_stud_uvalue_dto(
            construction_id=preset.ref,
            **parameters,
        )

    def _build_floor(self, preset_ref: str, parameters: Dict[str, Any]) -> ConstructionUValueResultDTO:
        preset = self._presets.get(preset_ref)
        return build_floor_uvalue_dto(
            construction_id=preset.ref,
            **parameters,
        )

    def _build_window(self, preset_ref: str, parameters: Dict[str, Any]) -> ConstructionUValueResultDTO:
        """
        TEMPORARY BYPASS:
        Window adapter can be brittle while stabilising contracts.
        For now we resolve preset Uw directly (if present), otherwise raise.
        """
        preset = self._presets.get(preset_ref)

        # If your PRESETS_V2 includes window Uw, this is the cleanest temporary path.
        if preset.u_value and preset.u_value > 0.0:
            return ConstructionUValueResultDTO(
                surface_class=SurfaceClass.WINDOW,
                construction_ref=preset.ref,
                u_value=float(preset.u_value),
            )

        # If you *must* call the engine, enable this later:
        # window = WindowConstruction(**parameters)
        # return build_window_uvalue_dto(construction=window, construction_ref=preset.ref, **parameters)

        raise ValueError(
            "Window adapter is temporarily bypassed and preset has no valid u_value.\n"
            f"preset_ref={preset.ref}"
        )


# ----------------------------------------------------------------------
# SINGLE AUTHORITATIVE INSTANCE (LOCKED)
# ----------------------------------------------------------------------

CONSTRUCTION_REGISTRY_V2 = ConstructionRegistryV2(PRESETS_V2)
