from __future__ import annotations

from typing import Dict, List

from HVAC_legacy.constructions.construction_preset import (
    ConstructionPreset,
    SurfaceClass,
)


class ConstructionPresetRegistry:
    """
    Read-only registry of ConstructionPreset objects.

    Responsibilities (LOCKED):
    • Store presets by ref
    • Lookup by ref
    • Filter by SurfaceClass

    No engines
    No adapters
    No GUI logic
    """

    def __init__(self, presets: List[ConstructionPreset]):
        if not isinstance(presets, list):
            raise TypeError(
                "ConstructionPresetRegistry expects List[ConstructionPreset]"
            )

        for p in presets:
            if not isinstance(p, ConstructionPreset):
                raise TypeError(
                    f"Invalid preset supplied: {p!r}"
                )

        self._by_ref: Dict[str, ConstructionPreset] = {
            p.ref: p for p in presets
        }

    def get(self, ref: str) -> ConstructionPreset:
        return self._by_ref[ref]

    def list_for_surface(
            self, surface_class: SurfaceClass
    ) -> List[ConstructionPreset]:
        return [
            p for p in self._by_ref.values()
            if p.surface_class == surface_class
            #if p.surface_class == surface_class
        ]



