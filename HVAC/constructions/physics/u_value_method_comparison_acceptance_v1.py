from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
)


U_VALUE_METHOD_ACCEPTANCE_SCHEMA_V1 = "u_value_method_acceptance_intent_v1"
NOT_SET_U_VALUE_METHOD = "not_set"
SUPPORTED_U_VALUE_METHODS = frozenset(
    {
        LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
        ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
    }
)


@dataclass(frozen=True, slots=True)
class UValueMethodComparisonRowV1:
    method: str
    label: str
    ready: bool
    u_value_W_m2K: float | None = None
    resistance_m2K_W: float | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UValueMethodComparisonV1:
    ready: bool
    construction_id: str
    evidence_fingerprint: str
    rows: tuple[UValueMethodComparisonRowV1, ...]
    iso_minus_legacy_W_m2K: float | None = None
    iso_minus_legacy_percent: float | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "U-value method comparison not resolved"


@dataclass(frozen=True, slots=True)
class UValueMethodAcceptanceIntentV1:
    construction_id: str
    evidence_fingerprint: str
    selected_method: str = NOT_SET_U_VALUE_METHOD
    schema: str = U_VALUE_METHOD_ACCEPTANCE_SCHEMA_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "construction_id": self.construction_id,
            "evidence_fingerprint": self.evidence_fingerprint,
            "selected_method": self.selected_method,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UValueMethodAcceptanceIntentV1":
        return cls(
            schema=str(data.get("schema") or ""),
            construction_id=str(data.get("construction_id") or ""),
            evidence_fingerprint=str(data.get("evidence_fingerprint") or ""),
            selected_method=str(
                data.get("selected_method") or NOT_SET_U_VALUE_METHOD
            ),
        )


@dataclass(frozen=True, slots=True)
class AcceptedUValueMethodResultV1:
    ready: bool
    construction_id: str = ""
    selected_method: str = NOT_SET_U_VALUE_METHOD
    accepted_u_value_W_m2K: float | None = None
    accepted_resistance_m2K_W: float | None = None
    evidence_fingerprint: str = ""
    comparison: UValueMethodComparisonV1 | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "U-value method acceptance not resolved"


def construction_evidence_fingerprint_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> str:
    if not isinstance(evidence, SharedConstructionLayerPathEvidenceV1):
        return ""
    payload = json.dumps(
        evidence.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_u_value_method_comparison_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
) -> UValueMethodComparisonV1:
    fingerprint = construction_evidence_fingerprint_v1(evidence)
    construction_id = str(getattr(evidence, "construction_id", "") or "")
    legacy = resolve_legacy_compatible_u_value_v1(evidence)
    iso = resolve_iso_6946_combined_u_value_v1(evidence)

    rows = (
        UValueMethodComparisonRowV1(
            method=LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1,
            label="Legacy area-weighted straight paths",
            ready=legacy.ready,
            u_value_W_m2K=legacy.u_value_W_m2K,
            resistance_m2K_W=legacy.effective_resistance_m2K_W,
            blockers=legacy.blockers,
            warnings=legacy.warnings,
        ),
        UValueMethodComparisonRowV1(
            method=ISO_6946_COMBINED_LIMITS_BASE_METHOD_V1,
            label="ISO 6946 combined limits — uncorrected base",
            ready=iso.ready,
            u_value_W_m2K=iso.uncorrected_u_value_W_m2K,
            resistance_m2K_W=iso.combined_resistance_m2K_W,
            blockers=iso.blockers,
            warnings=iso.warnings,
        ),
    )
    blockers = tuple(
        f"{row.label}: {blocker}"
        for row in rows
        for blocker in row.blockers
    )
    warnings = _unique(
        warning for row in rows for warning in row.warnings
    )
    ready = all(row.ready for row in rows)
    if not ready:
        return UValueMethodComparisonV1(
            ready=False,
            construction_id=construction_id,
            evidence_fingerprint=fingerprint,
            rows=rows,
            blockers=_unique(blockers) or (
                "Both U-value methods must resolve for side-by-side comparison",
            ),
            warnings=warnings,
            status="Blocked — side-by-side U-value comparison is incomplete",
        )

    legacy_u = float(rows[0].u_value_W_m2K)
    iso_u = float(rows[1].u_value_W_m2K)
    difference = iso_u - legacy_u
    return UValueMethodComparisonV1(
        ready=True,
        construction_id=construction_id,
        evidence_fingerprint=fingerprint,
        rows=rows,
        iso_minus_legacy_W_m2K=difference,
        iso_minus_legacy_percent=(difference / legacy_u) * 100.0,
        warnings=warnings,
        status="Ready — legacy and ISO 6946 U-values can be compared",
    )


def build_u_value_method_acceptance_intent_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    selected_method: str,
) -> UValueMethodAcceptanceIntentV1:
    return UValueMethodAcceptanceIntentV1(
        construction_id=str(getattr(evidence, "construction_id", "") or ""),
        evidence_fingerprint=construction_evidence_fingerprint_v1(evidence),
        selected_method=str(selected_method or NOT_SET_U_VALUE_METHOD),
    )


def resolve_accepted_u_value_method_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    intent: UValueMethodAcceptanceIntentV1,
) -> AcceptedUValueMethodResultV1:
    comparison = build_u_value_method_comparison_v1(evidence)
    if not isinstance(intent, UValueMethodAcceptanceIntentV1):
        return _acceptance_blocked(
            comparison,
            ("UValueMethodAcceptanceIntentV1 is required",),
        )
    if intent.schema != U_VALUE_METHOD_ACCEPTANCE_SCHEMA_V1:
        return _acceptance_blocked(
            comparison,
            (f"Unsupported U-value acceptance schema: {intent.schema}",),
        )
    if intent.construction_id != comparison.construction_id:
        return _acceptance_blocked(
            comparison,
            ("Acceptance construction identity does not match current evidence",),
        )
    if intent.evidence_fingerprint != comparison.evidence_fingerprint:
        return _acceptance_blocked(
            comparison,
            ("U-value method acceptance is stale after construction change",),
        )
    if intent.selected_method == NOT_SET_U_VALUE_METHOD:
        return _acceptance_blocked(
            comparison,
            ("U-value calculation method is not set",),
        )
    if intent.selected_method not in SUPPORTED_U_VALUE_METHODS:
        return _acceptance_blocked(
            comparison,
            (f"Unsupported U-value calculation method: {intent.selected_method}",),
        )
    if not comparison.ready:
        return _acceptance_blocked(
            comparison,
            comparison.blockers,
        )

    selected = next(
        row for row in comparison.rows if row.method == intent.selected_method
    )
    warnings = list(selected.warnings)
    if intent.selected_method == LEGACY_AREA_WEIGHTED_PATH_U_METHOD_V1:
        warnings.append(
            "Legacy method explicitly selected instead of the ISO comparison"
        )
    return AcceptedUValueMethodResultV1(
        ready=True,
        construction_id=comparison.construction_id,
        selected_method=intent.selected_method,
        accepted_u_value_W_m2K=selected.u_value_W_m2K,
        accepted_resistance_m2K_W=selected.resistance_m2K_W,
        evidence_fingerprint=comparison.evidence_fingerprint,
        comparison=comparison,
        warnings=_unique(warnings),
        status=f"Ready — explicitly accepted {selected.label}",
    )


def _acceptance_blocked(
    comparison: UValueMethodComparisonV1,
    blockers: tuple[str, ...],
) -> AcceptedUValueMethodResultV1:
    return AcceptedUValueMethodResultV1(
        ready=False,
        construction_id=comparison.construction_id,
        evidence_fingerprint=comparison.evidence_fingerprint,
        comparison=comparison,
        blockers=_unique(blockers) or ("U-value method acceptance is blocked",),
        warnings=comparison.warnings,
        status="Blocked — no U-value calculation method is accepted",
    )


def _unique(values) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))
