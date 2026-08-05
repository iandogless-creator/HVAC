# ======================================================================
# H-S66-N1B — Persisted committed-section pipe-pair spacing overrides
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import math

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.heatloss.physics.committed_pipe_section_thermal_condition_basis_intent_v1 import (
    build_committed_pipe_schedule_thermal_fingerprint_v1,
)
from HVAC.heatloss.physics.environment_pipe_pair_spacing_defaults_v1 import (
    PIPE_PAIR_SUPPORT_LABELS_V1,
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
    STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1,
    resolve_environment_pipe_pair_spacing_default_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


SCHEMA_V1 = "committed_pipe_pair_spacing_override_intent_v1"


@dataclass(frozen=True, slots=True)
class CommittedPipePairSpacingOverrideEntryV1:
    section_id: str
    support_type: str
    centre_spacing_mm: float


@dataclass(slots=True)
class CommittedPipePairSpacingOverrideIntentV1:
    """Sparse local support/c/c overrides for one committed schedule."""

    schema: str = SCHEMA_V1
    committed_schedule_fingerprint: str = ""
    override_by_section_id: dict[
        str, CommittedPipePairSpacingOverrideEntryV1
    ] = field(default_factory=dict)

    def set_section_override(
            self,
            *,
            section_id: str,
            committed_schedule_fingerprint: str,
            support_type: str,
            centre_spacing_mm: float,
    ) -> None:
        stable_section_id = _text_v1(section_id)
        fingerprint = _text_v1(committed_schedule_fingerprint)
        support = _support_type_v1(support_type)
        spacing = _centre_spacing_v1(centre_spacing_mm)
        if not stable_section_id:
            raise ValueError("Committed pipe section identity is required")
        if not fingerprint:
            raise ValueError("Committed pipe schedule fingerprint is required")
        if (
            self.committed_schedule_fingerprint
            and self.committed_schedule_fingerprint != fingerprint
        ):
            raise ValueError(
                "Persisted pipe-pair spacing overrides are stale; clear them "
                "before recording a different committed schedule"
            )
        self.committed_schedule_fingerprint = fingerprint
        self.override_by_section_id[stable_section_id] = (
            CommittedPipePairSpacingOverrideEntryV1(
                section_id=stable_section_id,
                support_type=support,
                centre_spacing_mm=spacing,
            )
        )

    def clear_section_override(self, section_id: str) -> bool:
        removed = self.override_by_section_id.pop(_text_v1(section_id), None)
        if not self.override_by_section_id:
            self.committed_schedule_fingerprint = ""
        return removed is not None

    def clear_all(self) -> None:
        self.override_by_section_id.clear()
        self.committed_schedule_fingerprint = ""

    def to_dict(self) -> dict:
        return committed_pipe_pair_spacing_override_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
            cls,
            data: dict | None,
    ) -> "CommittedPipePairSpacingOverrideIntentV1":
        return committed_pipe_pair_spacing_override_intent_from_dict_v1(data)


@dataclass(frozen=True, slots=True)
class EffectiveCommittedPipePairSpacingV1:
    section_id: str
    external_arrangement: str
    actual_outside_diameter_mm: float
    nominal_default_outside_diameter_mm: int
    support_type: str
    support_label: str
    centre_spacing_mm: float
    locally_overridden: bool
    source: str
    status: str


def build_committed_pipe_pair_spacing_fingerprint_v1(
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
) -> str:
    """Reuse the exact committed schedule identity already owned by H-S66-F."""

    return build_committed_pipe_schedule_thermal_fingerprint_v1(
        committed_authority
    )


def set_current_committed_section_pipe_pair_spacing_override_v1(
        *,
        intent: CommittedPipePairSpacingOverrideIntentV1,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        section_id: str,
        support_type: str,
        centre_spacing_mm: float,
) -> None:
    """Record one reviewed override only for an exact stacked section."""

    if not isinstance(intent, CommittedPipePairSpacingOverrideIntentV1):
        raise TypeError("CommittedPipePairSpacingOverrideIntentV1 required")
    section, arrangement = _resolve_exact_section_and_arrangement_v1(
        committed_authority=committed_authority,
        external_arrangement_by_section_id=external_arrangement_by_section_id,
        section_id=section_id,
    )
    if arrangement != STACKED_FLOW_RETURN_PAIR_V1:
        raise ValueError(
            "Pipe-pair support/c/c override applies only to a stacked "
            "flow/return pair"
        )
    actual_od = _actual_outside_diameter_mm_v1(section)
    spacing = _centre_spacing_v1(centre_spacing_mm)
    if spacing <= actual_od:
        raise ValueError(
            "Pipe-pair centre spacing must exceed exact catalogue pipe OD"
        )
    intent.set_section_override(
        section_id=section_id,
        committed_schedule_fingerprint=(
            build_committed_pipe_pair_spacing_fingerprint_v1(
                committed_authority
            )
        ),
        support_type=support_type,
        centre_spacing_mm=spacing,
    )


def resolve_effective_committed_pipe_pair_spacing_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        raw_environment_defaults: object,
        local_intent: CommittedPipePairSpacingOverrideIntentV1 | None,
        section_id: str,
) -> EffectiveCommittedPipePairSpacingV1 | None:
    """Resolve local-over-environment spacing; separate RR remains dormant."""

    section, arrangement = _resolve_exact_section_and_arrangement_v1(
        committed_authority=committed_authority,
        external_arrangement_by_section_id=external_arrangement_by_section_id,
        section_id=section_id,
    )
    if arrangement == SEPARATE_PIPE_V1:
        return None

    actual_od = _actual_outside_diameter_mm_v1(section)
    nominal_od = _nearest_nominal_default_od_mm_v1(actual_od)
    inherited = resolve_environment_pipe_pair_spacing_default_v1(
        raw_defaults=raw_environment_defaults,
        nominal_outside_diameter_mm=nominal_od,
        external_arrangement=arrangement,
    )
    if inherited is None:
        return None

    local = None
    if isinstance(local_intent, CommittedPipePairSpacingOverrideIntentV1):
        if local_intent.override_by_section_id:
            expected = build_committed_pipe_pair_spacing_fingerprint_v1(
                committed_authority
            )
            if local_intent.committed_schedule_fingerprint != expected:
                raise ValueError(
                    "Persisted pipe-pair spacing overrides are stale for the "
                    "current committed schedule"
                )
        local = local_intent.override_by_section_id.get(_text_v1(section_id))

    support_type = inherited.support_type
    spacing = inherited.centre_spacing_mm
    overridden = False
    source = inherited.source
    if local is not None:
        support_type = _support_type_v1(local.support_type)
        spacing = _centre_spacing_v1(local.centre_spacing_mm)
        if spacing <= actual_od:
            raise ValueError(
                "Local pipe-pair centre spacing must exceed exact catalogue "
                "pipe OD"
            )
        overridden = True
        source = "Persisted exact committed-section support/c/c override"

    return EffectiveCommittedPipePairSpacingV1(
        section_id=_text_v1(section_id),
        external_arrangement=arrangement,
        actual_outside_diameter_mm=actual_od,
        nominal_default_outside_diameter_mm=nominal_od,
        support_type=support_type,
        support_label=PIPE_PAIR_SUPPORT_LABELS_V1[support_type],
        centre_spacing_mm=spacing,
        locally_overridden=overridden,
        source=source,
        status=(
            "Ready — local committed-section pipe-pair spacing override"
            if overridden
            else "Ready — Environment pipe-pair spacing default inherited"
        ),
    )


def committed_pipe_pair_spacing_override_intent_to_dict_v1(
        intent: CommittedPipePairSpacingOverrideIntentV1 | None,
) -> dict:
    source = (
        intent
        if isinstance(intent, CommittedPipePairSpacingOverrideIntentV1)
        else CommittedPipePairSpacingOverrideIntentV1()
    )
    return {
        "schema": source.schema,
        "committed_schedule_fingerprint": (
            source.committed_schedule_fingerprint
        ),
        "override_by_section_id": {
            section_id: {
                "section_id": entry.section_id,
                "support_type": entry.support_type,
                "centre_spacing_mm": entry.centre_spacing_mm,
            }
            for section_id, entry in sorted(
                source.override_by_section_id.items()
            )
        },
    }


def committed_pipe_pair_spacing_override_intent_from_dict_v1(
        data: dict | None,
) -> CommittedPipePairSpacingOverrideIntentV1:
    empty = CommittedPipePairSpacingOverrideIntentV1()
    if not isinstance(data, dict):
        return empty
    if _text_v1(data.get("schema") or SCHEMA_V1) != SCHEMA_V1:
        return empty
    fingerprint = _text_v1(data.get("committed_schedule_fingerprint"))
    raw_entries = data.get("override_by_section_id", {})
    if not isinstance(raw_entries, dict):
        return empty
    if raw_entries and not fingerprint:
        return empty
    parsed = CommittedPipePairSpacingOverrideIntentV1()
    try:
        for raw_section_id, raw_entry in sorted(
            raw_entries.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(raw_entry, dict):
                return empty
            section_id = _text_v1(raw_entry.get("section_id"))
            if not section_id or section_id != _text_v1(raw_section_id):
                return empty
            parsed.set_section_override(
                section_id=section_id,
                committed_schedule_fingerprint=fingerprint,
                support_type=raw_entry.get("support_type", ""),
                centre_spacing_mm=raw_entry.get("centre_spacing_mm"),
            )
    except (TypeError, ValueError):
        return empty
    return parsed


def _resolve_exact_section_and_arrangement_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_by_section_id: Mapping[str, str],
        section_id: object,
) -> tuple[object, str]:
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ) or not committed_authority.ready:
        raise ValueError(
            "Ready committed proportioning hydraulic-input authority required"
        )
    stable_section_id = _text_v1(section_id)
    matches = tuple(
        row
        for row in tuple(committed_authority.sections or ())
        if _text_v1(getattr(row, "section_id", "")) == stable_section_id
    )
    if len(matches) != 1:
        raise ValueError("Exact committed pipe section identity is required")
    if not isinstance(external_arrangement_by_section_id, Mapping):
        raise ValueError("Committed external-arrangement mapping is required")
    arrangement = _text_v1(
        external_arrangement_by_section_id.get(stable_section_id)
    )
    if arrangement not in {
        STACKED_FLOW_RETURN_PAIR_V1,
        SEPARATE_PIPE_V1,
    }:
        raise ValueError(
            "Current committed pipe external arrangement is required"
        )
    return matches[0], arrangement


def _actual_outside_diameter_mm_v1(section: object) -> float:
    material_key = _text_v1(getattr(section, "material_key", "")).lower()
    material = get_material(material_key)
    if material is None:
        raise ValueError("Committed pipe material is unavailable")
    try:
        size_key = int(getattr(section, "dn"))
    except (TypeError, ValueError):
        raise ValueError("Committed catalogue pipe size is required") from None
    size = material.sizes.get(size_key)
    if size is None:
        raise ValueError("Committed catalogue pipe identity is unavailable")
    outside_diameter = float(size.od_mm)
    if not math.isfinite(outside_diameter) or outside_diameter <= 0.0:
        raise ValueError("Committed catalogue pipe outside diameter is invalid")
    return outside_diameter


def _nearest_nominal_default_od_mm_v1(actual_od_mm: float) -> int:
    nearest = min(
        STACKED_PIPE_PAIR_NOMINAL_OD_MM_V1,
        key=lambda value: (abs(float(value) - actual_od_mm), value),
    )
    difference = abs(float(nearest) - actual_od_mm) / actual_od_mm
    if difference > 0.15:
        raise ValueError(
            "Exact catalogue pipe OD has no representative Environment "
            "stacked-pair default"
        )
    return int(nearest)


def _support_type_v1(value: object) -> str:
    support = _text_v1(value)
    if support not in PIPE_PAIR_SUPPORT_LABELS_V1:
        raise ValueError("Pipe-pair support type is unsupported")
    return support


def _centre_spacing_v1(value: object) -> float:
    try:
        spacing = float(value)
    except (TypeError, ValueError):
        raise ValueError("Pipe-pair centre spacing is required") from None
    if not math.isfinite(spacing) or spacing <= 0.0:
        raise ValueError("Pipe-pair centre spacing must be positive")
    if spacing > 500.0:
        raise ValueError("Pipe-pair centre spacing exceeds 500 mm")
    return spacing


def _text_v1(value: object) -> str:
    return str(value or "").strip()
