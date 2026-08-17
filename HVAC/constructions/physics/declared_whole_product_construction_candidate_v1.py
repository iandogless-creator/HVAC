from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Mapping

from HVAC.constructions.physics.declared_whole_product_u_value_authority_v1 import (
    DeclaredWholeProductUValueAcceptanceIntentV1,
    DeclaredWholeProductUValueEvidenceV1,
    build_declared_whole_product_u_value_acceptance_intent_v1,
    resolve_accepted_declared_whole_product_u_value_v1,
)


@dataclass(frozen=True, slots=True)
class DeclaredWholeProductConstructionCandidateV1:
    ready: bool
    construction_id: str = ""
    name: str = ""
    u_value_W_m2K: float | None = None
    evidence: DeclaredWholeProductUValueEvidenceV1 | None = None
    acceptance: DeclaredWholeProductUValueAcceptanceIntentV1 | None = None
    blockers: tuple[str, ...] = ()
    status: str = "Declared whole-product construction candidate not resolved"


def build_declared_whole_product_construction_candidate_v1(
    *,
    opening_type: str,
    name: str,
    declared_u_value_W_m2K: float,
    source_kind: str,
    source_ref: str,
    source_version: str = "",
    existing_constructions: Mapping[str, object] | None = None,
) -> DeclaredWholeProductConstructionCandidateV1:
    """Build one explicitly accepted whole-window or whole-door construction."""

    clean_type = str(opening_type or "").strip().upper()
    clean_name = " ".join(str(name or "").split())
    clean_source_kind = str(source_kind or "").strip()
    clean_source_ref = " ".join(str(source_ref or "").split())
    clean_source_version = " ".join(str(source_version or "").split())
    blockers: list[str] = []

    if clean_type not in {"WINDOW", "DOOR"}:
        blockers.append("Opening type must be Window or External door")
    if not clean_name:
        blockers.append("A construction name is required")
    elif len(clean_name) > 120:
        blockers.append("Construction name must not exceed 120 characters")
    if not clean_source_kind:
        blockers.append("A source type is required")
    if not clean_source_ref:
        blockers.append("A source reference is required")

    try:
        clean_u = float(declared_u_value_W_m2K)
    except (TypeError, ValueError):
        clean_u = float("nan")
    if not math.isfinite(clean_u) or clean_u <= 0.0:
        blockers.append("Declared whole-product U-value must be positive and finite")

    existing = dict(existing_constructions or {})
    existing_names = {
        str(getattr(item, "name", "") or "").strip().casefold()
        for item in existing.values()
    }
    if clean_name and clean_name.casefold() in existing_names:
        blockers.append("Construction name already exists")

    if blockers:
        return _blocked(tuple(dict.fromkeys(blockers)))

    identity_payload = json.dumps(
        {
            "opening_type": clean_type,
            "name": clean_name,
            "declared_u_value_W_m2K": clean_u,
            "source_kind": clean_source_kind,
            "source_ref": clean_source_ref,
            "source_version": clean_source_version,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    identity_fingerprint = hashlib.sha256(identity_payload).hexdigest()
    slug = re.sub(r"[^A-Z0-9]+", "-", clean_name.upper()).strip("-")
    slug = slug[:42] or clean_type
    construction_id = (
        f"USR-DECLARED-{clean_type}-{slug}-"
        f"{identity_fingerprint[:10].upper()}"
    )
    if construction_id in existing:
        return _blocked(("Generated construction identity already exists",))

    evidence = DeclaredWholeProductUValueEvidenceV1(
        construction_id=construction_id,
        opening_type=clean_type,
        declared_u_value_W_m2K=clean_u,
        source_kind=clean_source_kind,
        source_ref=clean_source_ref,
        source_version=clean_source_version,
        notes=(
            "Whole-window Uw declared product value"
            if clean_type == "WINDOW"
            else "Whole-door Ud declared product value"
        ),
    )
    acceptance = build_declared_whole_product_u_value_acceptance_intent_v1(
        evidence,
        accepted=True,
    )
    accepted = resolve_accepted_declared_whole_product_u_value_v1(
        evidence,
        acceptance,
    )
    if not accepted.ready or accepted.accepted_u_value_W_m2K is None:
        return _blocked(
            accepted.blockers
            or ("Declared whole-product U-value did not resolve",)
        )

    return DeclaredWholeProductConstructionCandidateV1(
        ready=True,
        construction_id=construction_id,
        name=clean_name,
        u_value_W_m2K=float(accepted.accepted_u_value_W_m2K),
        evidence=evidence,
        acceptance=acceptance,
        status=f"Ready — save declared {clean_type.lower()} construction",
    )


def _blocked(
    blockers: tuple[str, ...],
) -> DeclaredWholeProductConstructionCandidateV1:
    return DeclaredWholeProductConstructionCandidateV1(
        ready=False,
        blockers=tuple(dict.fromkeys(blockers)),
        status="Blocked — declared opening construction was not saved",
    )
