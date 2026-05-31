# ======================================================================
# HVAC/hydronics/local_losses/local_k_intent_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LocalKSectionIntentV1:
    """
    Persisted Local K / fittings intent for one hydronic section.

    Authority
    ---------
    Stores user-visible fitting counts and straight length only.

    Does not store calculated pressure-drop outputs as authority.
    """

    section_id: str

    bend_90_count: int = 0
    bend_45_count: int = 0
    tee_through_count: int = 0
    tee_branch_count: int = 0
    isolation_valve_count: int = 0
    trv_count: int = 0
    lockshield_count: int = 0

    misc_k: float = 0.0
    length_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "bend_90_count": int(self.bend_90_count),
            "bend_45_count": int(self.bend_45_count),
            "tee_through_count": int(self.tee_through_count),
            "tee_branch_count": int(self.tee_branch_count),
            "isolation_valve_count": int(self.isolation_valve_count),
            "trv_count": int(self.trv_count),
            "lockshield_count": int(self.lockshield_count),
            "misc_k": float(self.misc_k),
            "length_m": self.length_m,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalKSectionIntentV1":
        return cls(
            section_id=str(data.get("section_id") or ""),
            bend_90_count=int(data.get("bend_90_count") or 0),
            bend_45_count=int(data.get("bend_45_count") or 0),
            tee_through_count=int(data.get("tee_through_count") or 0),
            tee_branch_count=int(data.get("tee_branch_count") or 0),
            isolation_valve_count=int(data.get("isolation_valve_count") or 0),
            trv_count=int(data.get("trv_count") or 0),
            lockshield_count=int(data.get("lockshield_count") or 0),
            misc_k=float(data.get("misc_k") or 0.0),
            length_m=(
                None
                if data.get("length_m") is None
                else float(data.get("length_m"))
            ),
        )


@dataclass(slots=True)
class LocalKIntentV1:
    """
    Persisted Local K / fittings schedule.

    Keyed by Basic PS section_id.
    """

    sections: dict[str, LocalKSectionIntentV1] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sections": {
                section_id: section.to_dict()
                for section_id, section in self.sections.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalKIntentV1":
        raw_sections = data.get("sections", {}) or {}

        sections: dict[str, LocalKSectionIntentV1] = {}

        if isinstance(raw_sections, dict):
            for key, raw in raw_sections.items():
                if not isinstance(raw, dict):
                    continue

                section = LocalKSectionIntentV1.from_dict(raw)

                if not section.section_id:
                    section.section_id = str(key)

                if section.section_id:
                    sections[section.section_id] = section

        return cls(sections=sections)

    def get_or_create_section(
        self,
        section_id: str,
    ) -> LocalKSectionIntentV1:
        section_id = str(section_id or "")

        if not section_id:
            raise ValueError("section_id is required")

        if section_id not in self.sections:
            self.sections[section_id] = LocalKSectionIntentV1(
                section_id=section_id
            )

        return self.sections[section_id]