from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any


DECLARED_WHOLE_PRODUCT_U_VALUE_EVIDENCE_SCHEMA_V1 = (
    "declared_whole_product_u_value_evidence_v1"
)
DECLARED_WHOLE_PRODUCT_U_VALUE_ACCEPTANCE_SCHEMA_V1 = (
    "declared_whole_product_u_value_acceptance_intent_v1"
)
SUPPORTED_DECLARED_WHOLE_PRODUCT_OPENING_TYPES_V1 = frozenset(
    {"WINDOW", "DOOR"}
)


@dataclass(frozen=True, slots=True)
class DeclaredWholeProductUValueEvidenceV1:
    """Candidate whole-window Uw or whole-door Ud product evidence."""

    construction_id: str
    opening_type: str
    declared_u_value_W_m2K: float
    source_kind: str
    source_ref: str
    source_version: str = ""
    notes: str = ""
    schema: str = DECLARED_WHOLE_PRODUCT_U_VALUE_EVIDENCE_SCHEMA_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "construction_id": self.construction_id,
            "opening_type": self.opening_type,
            "declared_u_value_W_m2K": self.declared_u_value_W_m2K,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_version": self.source_version,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "DeclaredWholeProductUValueEvidenceV1":
        return cls(
            schema=str(data.get("schema") or ""),
            construction_id=str(data.get("construction_id") or ""),
            opening_type=str(data.get("opening_type") or ""),
            declared_u_value_W_m2K=float(
                data.get("declared_u_value_W_m2K", float("nan"))
            ),
            source_kind=str(data.get("source_kind") or ""),
            source_ref=str(data.get("source_ref") or ""),
            source_version=str(data.get("source_version") or ""),
            notes=str(data.get("notes") or ""),
        )


@dataclass(frozen=True, slots=True)
class DeclaredWholeProductUValueAcceptanceIntentV1:
    construction_id: str
    evidence_fingerprint: str
    accepted: bool = False
    schema: str = DECLARED_WHOLE_PRODUCT_U_VALUE_ACCEPTANCE_SCHEMA_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "construction_id": self.construction_id,
            "evidence_fingerprint": self.evidence_fingerprint,
            "accepted": bool(self.accepted),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "DeclaredWholeProductUValueAcceptanceIntentV1":
        return cls(
            schema=str(data.get("schema") or ""),
            construction_id=str(data.get("construction_id") or ""),
            evidence_fingerprint=str(data.get("evidence_fingerprint") or ""),
            accepted=bool(data.get("accepted", False)),
        )


@dataclass(frozen=True, slots=True)
class AcceptedDeclaredWholeProductUValueResultV1:
    ready: bool
    construction_id: str = ""
    opening_type: str = ""
    accepted_u_value_W_m2K: float | None = None
    evidence_fingerprint: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Declared whole-product U-value acceptance not resolved"


def declared_whole_product_u_value_evidence_fingerprint_v1(
    evidence: DeclaredWholeProductUValueEvidenceV1,
) -> str:
    if not isinstance(evidence, DeclaredWholeProductUValueEvidenceV1):
        return ""
    try:
        payload = json.dumps(
            evidence.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return ""
    return hashlib.sha256(payload).hexdigest()


def build_declared_whole_product_u_value_acceptance_intent_v1(
    evidence: DeclaredWholeProductUValueEvidenceV1,
    *,
    accepted: bool,
) -> DeclaredWholeProductUValueAcceptanceIntentV1:
    return DeclaredWholeProductUValueAcceptanceIntentV1(
        construction_id=str(getattr(evidence, "construction_id", "") or ""),
        evidence_fingerprint=(
            declared_whole_product_u_value_evidence_fingerprint_v1(evidence)
        ),
        accepted=bool(accepted),
    )


def resolve_accepted_declared_whole_product_u_value_v1(
    evidence: DeclaredWholeProductUValueEvidenceV1,
    intent: DeclaredWholeProductUValueAcceptanceIntentV1,
) -> AcceptedDeclaredWholeProductUValueResultV1:
    blockers: list[str] = []

    if not isinstance(evidence, DeclaredWholeProductUValueEvidenceV1):
        return _blocked(("Declared whole-product U-value evidence is required",))
    if evidence.schema != DECLARED_WHOLE_PRODUCT_U_VALUE_EVIDENCE_SCHEMA_V1:
        blockers.append("Declared whole-product evidence schema is unsupported")

    construction_id = str(evidence.construction_id or "").strip()
    if not construction_id:
        blockers.append("Construction identity is required")

    opening_type = str(evidence.opening_type or "").strip().upper()
    if opening_type not in SUPPORTED_DECLARED_WHOLE_PRODUCT_OPENING_TYPES_V1:
        blockers.append("Opening type must be WINDOW or DOOR")

    try:
        declared_u = float(evidence.declared_u_value_W_m2K)
    except (TypeError, ValueError):
        declared_u = float("nan")
    if not math.isfinite(declared_u) or declared_u <= 0.0:
        blockers.append("Declared whole-product U-value must be positive and finite")

    if not str(evidence.source_kind or "").strip():
        blockers.append("Declared whole-product source kind is required")
    if not str(evidence.source_ref or "").strip():
        blockers.append("Declared whole-product source reference is required")

    if not isinstance(intent, DeclaredWholeProductUValueAcceptanceIntentV1):
        blockers.append("Explicit declared whole-product acceptance is required")
    else:
        if intent.schema != DECLARED_WHOLE_PRODUCT_U_VALUE_ACCEPTANCE_SCHEMA_V1:
            blockers.append("Declared whole-product acceptance schema is unsupported")
        if not bool(intent.accepted):
            blockers.append("Declared whole-product U-value has not been accepted")
        if str(intent.construction_id or "") != construction_id:
            blockers.append("Acceptance construction identity does not match evidence")

        fingerprint = declared_whole_product_u_value_evidence_fingerprint_v1(
            evidence
        )
        if not fingerprint or intent.evidence_fingerprint != fingerprint:
            blockers.append("Accepted declared whole-product evidence is stale")

    if blockers:
        return _blocked(tuple(dict.fromkeys(blockers)))

    fingerprint = declared_whole_product_u_value_evidence_fingerprint_v1(evidence)
    return AcceptedDeclaredWholeProductUValueResultV1(
        ready=True,
        construction_id=construction_id,
        opening_type=opening_type,
        accepted_u_value_W_m2K=declared_u,
        evidence_fingerprint=fingerprint,
        status=(
            f"Ready — accepted declared whole-{opening_type.lower()} "
            f"U-value {declared_u:.3f} W/m²K"
        ),
    )


def _blocked(
    blockers: tuple[str, ...],
) -> AcceptedDeclaredWholeProductUValueResultV1:
    return AcceptedDeclaredWholeProductUValueResultV1(
        ready=False,
        blockers=tuple(dict.fromkeys(blockers)),
        status="Blocked — declared whole-product U-value is not accepted",
    )
