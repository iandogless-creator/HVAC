# ======================================================================
# H-S66-F — Persisted committed-section thermal-condition basis intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    BarePipeThermalConditionBasisV1,
    build_explicit_bare_pipe_thermal_condition_basis_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


SCHEMA_V1 = "committed_pipe_section_thermal_condition_basis_intent_v1"
_USE_BASIS_EMISSIVITY_AS_OVERRIDE_V1 = object()


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionThermalConditionBasisEntryV1:
    """One explicit persisted external thermal basis keyed by section ID."""

    section_id: str
    surface_temperature_C: float
    ambient_air_temperature_C: float
    mean_radiant_temperature_C: float
    emissivity: float
    external_convection_coefficient_W_m2K: float

    def to_thermal_basis(self) -> BarePipeThermalConditionBasisV1:
        return build_explicit_bare_pipe_thermal_condition_basis_v1(
            surface_temperature_C=self.surface_temperature_C,
            ambient_air_temperature_C=self.ambient_air_temperature_C,
            mean_radiant_temperature_C=self.mean_radiant_temperature_C,
            emissivity=self.emissivity,
            external_convection_coefficient_W_m2K=(
                self.external_convection_coefficient_W_m2K
            ),
        )


@dataclass(slots=True)
class CommittedPipeSectionThermalConditionBasisIntentV1:
    """Persisted manual thermal bases for one exact committed schedule.

    The record does not infer temperatures, emissivity or convection, and it
    does not calculate or commit heat loss. A different schedule fingerprint
    must be cleared and reviewed explicitly before new section bases are set.
    """

    schema: str = SCHEMA_V1
    committed_schedule_fingerprint: str = ""
    basis_by_section_id: dict[
        str, CommittedPipeSectionThermalConditionBasisEntryV1
    ] = field(default_factory=dict)
    emissivity_override_by_section_id: dict[str, float] = field(
        default_factory=dict
    )

    def set_section_basis(
            self,
            *,
            section_id: str,
            committed_schedule_fingerprint: str,
            thermal_basis: BarePipeThermalConditionBasisV1,
            emissivity_override: object = (
                _USE_BASIS_EMISSIVITY_AS_OVERRIDE_V1
            ),
    ) -> None:
        stable_section_id = _stable_text_v1(section_id)
        fingerprint = _stable_text_v1(committed_schedule_fingerprint)
        if not stable_section_id:
            raise ValueError("Committed pipe section identity is required")
        if not fingerprint:
            raise ValueError("Committed pipe schedule fingerprint is required")
        if not isinstance(thermal_basis, BarePipeThermalConditionBasisV1):
            raise TypeError("BarePipeThermalConditionBasisV1 required")
        if (
            self.committed_schedule_fingerprint
            and self.committed_schedule_fingerprint != fingerprint
        ):
            raise ValueError(
                "Persisted section thermal bases are stale; clear them before "
                "recording a different committed schedule"
            )

        self.committed_schedule_fingerprint = fingerprint
        self.basis_by_section_id[stable_section_id] = (
            CommittedPipeSectionThermalConditionBasisEntryV1(
                section_id=stable_section_id,
                surface_temperature_C=thermal_basis.surface_temperature_C,
                ambient_air_temperature_C=(
                    thermal_basis.ambient_air_temperature_C
                ),
                mean_radiant_temperature_C=(
                    thermal_basis.mean_radiant_temperature_C
                ),
                emissivity=thermal_basis.emissivity,
                external_convection_coefficient_W_m2K=(
                    thermal_basis.external_convection_coefficient_W_m2K
                ),
            )
        )
        if emissivity_override is _USE_BASIS_EMISSIVITY_AS_OVERRIDE_V1:
            # Pre-H-S66-K callers supplied a complete explicit basis. Preserve
            # that accepted emissivity as a local override during migration.
            self.emissivity_override_by_section_id[stable_section_id] = (
                thermal_basis.emissivity
            )
        elif emissivity_override is None:
            self.emissivity_override_by_section_id.pop(
                stable_section_id, None
            )
        else:
            self.emissivity_override_by_section_id[stable_section_id] = (
                _emissivity_v1(emissivity_override)
            )

    def clear_section_basis(self, section_id: str) -> bool:
        stable_section_id = _stable_text_v1(section_id)
        if not stable_section_id:
            return False
        removed = self.basis_by_section_id.pop(stable_section_id, None)
        self.emissivity_override_by_section_id.pop(stable_section_id, None)
        if not self.basis_by_section_id:
            self.committed_schedule_fingerprint = ""
        return removed is not None

    def clear_all(self) -> None:
        self.basis_by_section_id.clear()
        self.emissivity_override_by_section_id.clear()
        self.committed_schedule_fingerprint = ""

    def to_dict(self) -> dict:
        return committed_pipe_section_thermal_condition_basis_intent_to_dict_v1(
            self
        )

    @classmethod
    def from_dict(
            cls,
            data: dict | None,
    ) -> "CommittedPipeSectionThermalConditionBasisIntentV1":
        return (
            committed_pipe_section_thermal_condition_basis_intent_from_dict_v1(
                data
            )
        )


def build_committed_pipe_schedule_thermal_fingerprint_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> str:
    """Fingerprint exact committed section geometry used by thermal intent."""

    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        raise TypeError(
            "CommittedProportioningHydraulicInputAuthorityV1 required"
        )
    if not committed_authority.ready:
        raise ValueError(
            "Committed proportioning hydraulic-input authority is not ready"
        )
    sources = tuple(committed_authority.sections or ())
    if not sources:
        raise ValueError("Committed pipe sections are required")

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for source in sources:
        section_id = _stable_text_v1(getattr(source, "section_id", ""))
        if not section_id:
            raise ValueError(
                "Every committed pipe section requires stable section_id"
            )
        if section_id in seen:
            raise ValueError(
                f"Duplicate committed pipe section identity: {section_id}"
            )
        seen.add(section_id)

        material_key = _stable_text_v1(
            getattr(source, "material_key", "")
        ).lower()
        dn = _positive_int_v1(getattr(source, "dn", None))
        length_m = _positive_finite_v1(getattr(source, "length_m", None))
        if not material_key:
            raise ValueError(f"{section_id}: committed material key required")
        if dn is None:
            raise ValueError(f"{section_id}: committed catalogue size required")
        if length_m is None:
            raise ValueError(f"{section_id}: positive committed length required")

        rows.append(
            {
                "section_id": section_id,
                "section_scope": _stable_text_v1(
                    getattr(source, "section_scope", "")
                ),
                "route_ids": sorted(
                    _stable_text_v1(value)
                    for value in tuple(
                        getattr(source, "route_ids", ()) or ()
                    )
                    if _stable_text_v1(value)
                ),
                "order": int(getattr(source, "order")),
                "from_label": _stable_text_v1(
                    getattr(source, "from_label", "")
                ),
                "to_label": _stable_text_v1(
                    getattr(source, "to_label", "")
                ),
                "material_key": material_key,
                "material_label": _stable_text_v1(
                    getattr(source, "material_label", "")
                ),
                "pipe_size_label": _stable_text_v1(
                    getattr(source, "pipe_size_label", "")
                ),
                "catalogue_size_key": dn,
                "length_m": length_m,
            }
        )

    payload = {
        "schema": "committed_pipe_schedule_thermal_fingerprint_v1",
        "sections": sorted(rows, key=lambda row: str(row["section_id"])),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def committed_pipe_section_thermal_condition_basis_intent_is_current_v1(
        intent: CommittedPipeSectionThermalConditionBasisIntentV1 | None,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> bool:
    if not isinstance(
        intent,
        CommittedPipeSectionThermalConditionBasisIntentV1,
    ):
        return False
    fingerprint = _stable_text_v1(intent.committed_schedule_fingerprint)
    if not fingerprint:
        return False
    try:
        current = build_committed_pipe_schedule_thermal_fingerprint_v1(
            committed_authority
        )
    except (TypeError, ValueError):
        return False
    return fingerprint == current


def committed_pipe_section_thermal_condition_basis_intent_to_dict_v1(
        intent: CommittedPipeSectionThermalConditionBasisIntentV1 | None,
) -> dict:
    source = (
        intent
        if isinstance(
            intent,
            CommittedPipeSectionThermalConditionBasisIntentV1,
        )
        else CommittedPipeSectionThermalConditionBasisIntentV1()
    )
    return {
        "schema": source.schema,
        "committed_schedule_fingerprint": (
            source.committed_schedule_fingerprint
        ),
        "basis_by_section_id": {
            section_id: {
                "section_id": entry.section_id,
                "surface_temperature_C": entry.surface_temperature_C,
                "ambient_air_temperature_C": (
                    entry.ambient_air_temperature_C
                ),
                "mean_radiant_temperature_C": (
                    entry.mean_radiant_temperature_C
                ),
                "emissivity": entry.emissivity,
                "external_convection_coefficient_W_m2K": (
                    entry.external_convection_coefficient_W_m2K
                ),
            }
            for section_id, entry in sorted(
                source.basis_by_section_id.items()
            )
        },
        "emissivity_override_by_section_id": {
            section_id: value
            for section_id, value in sorted(
                source.emissivity_override_by_section_id.items()
            )
        },
    }


def committed_pipe_section_thermal_condition_basis_intent_from_dict_v1(
        data: dict | None,
) -> CommittedPipeSectionThermalConditionBasisIntentV1:
    empty = CommittedPipeSectionThermalConditionBasisIntentV1()
    if not isinstance(data, dict):
        return empty
    schema = _stable_text_v1(data.get("schema") or SCHEMA_V1)
    if schema != SCHEMA_V1:
        return empty
    fingerprint = _stable_text_v1(
        data.get("committed_schedule_fingerprint")
    )
    raw_entries = data.get("basis_by_section_id", {})
    if not isinstance(raw_entries, dict):
        return empty
    if raw_entries and not fingerprint:
        return empty
    overrides_present = "emissivity_override_by_section_id" in data
    raw_overrides = data.get("emissivity_override_by_section_id", {})
    if not isinstance(raw_overrides, dict):
        return empty
    parsed_overrides: dict[str, float] = {}
    try:
        for raw_section_id, raw_value in raw_overrides.items():
            section_id = _stable_text_v1(raw_section_id)
            if not section_id:
                return empty
            parsed_overrides[section_id] = _emissivity_v1(raw_value)
    except (TypeError, ValueError):
        return empty

    intent = CommittedPipeSectionThermalConditionBasisIntentV1(
        schema=schema
    )
    for raw_section_id, raw_entry in sorted(
        raw_entries.items(), key=lambda item: str(item[0])
    ):
        if not isinstance(raw_entry, dict):
            return empty
        section_id = _stable_text_v1(raw_entry.get("section_id"))
        if not section_id or section_id != _stable_text_v1(raw_section_id):
            return empty
        try:
            basis = build_explicit_bare_pipe_thermal_condition_basis_v1(
                surface_temperature_C=raw_entry.get(
                    "surface_temperature_C"
                ),
                ambient_air_temperature_C=raw_entry.get(
                    "ambient_air_temperature_C"
                ),
                mean_radiant_temperature_C=raw_entry.get(
                    "mean_radiant_temperature_C"
                ),
                emissivity=raw_entry.get("emissivity"),
                external_convection_coefficient_W_m2K=raw_entry.get(
                    "external_convection_coefficient_W_m2K"
                ),
            )
            intent.set_section_basis(
                section_id=section_id,
                committed_schedule_fingerprint=fingerprint,
                thermal_basis=basis,
                emissivity_override=(
                    parsed_overrides.get(section_id)
                    if overrides_present
                    else basis.emissivity
                ),
            )
        except (TypeError, ValueError):
            return empty
    if set(parsed_overrides) - set(intent.basis_by_section_id):
        return empty
    return intent


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _positive_int_v1(value: object) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _positive_finite_v1(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _emissivity_v1(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Bare-pipe emissivity must be numeric") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("Bare-pipe emissivity must be between 0 and 1")
    return number
