from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Mapping

from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    NOT_SET_U_VALUE_METHOD,
    UValueMethodAcceptanceIntentV1,
    build_u_value_method_acceptance_intent_v1,
    construction_evidence_fingerprint_v1,
    resolve_accepted_u_value_method_v1,
)


USER_CONSTRUCTION_MODEL_SOURCE = "user_construction_model"


@dataclass(frozen=True, slots=True)
class ConstructionModelSaveCandidateV1:
    ready: bool
    construction_id: str = ""
    name: str = ""
    u_value_W_m2K: float | None = None
    evidence: SharedConstructionLayerPathEvidenceV1 | None = None
    method_acceptance: UValueMethodAcceptanceIntentV1 | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    status: str = "Construction model save candidate not resolved"


def build_construction_model_save_candidate_v1(
    evidence: SharedConstructionLayerPathEvidenceV1,
    *,
    name: str,
    selected_method: str,
    existing_constructions: Mapping[str, object] | None = None,
) -> ConstructionModelSaveCandidateV1:
    """Build one new, explicitly named construction model without mutation."""

    if not isinstance(evidence, SharedConstructionLayerPathEvidenceV1):
        return _blocked(("Complete construction layer/path evidence is required",))

    clean_name = " ".join(str(name or "").split())
    if not clean_name:
        return _blocked(("A new construction model name is required",))
    if len(clean_name) > 120:
        return _blocked(("Construction model name must not exceed 120 characters",))
    if str(selected_method or NOT_SET_U_VALUE_METHOD) == NOT_SET_U_VALUE_METHOD:
        return _blocked(("An explicit U-value calculation method is required",))

    existing = dict(existing_constructions or {})
    existing_names = {
        str(getattr(item, "name", "") or "").strip().casefold()
        for item in existing.values()
    }
    if clean_name.casefold() in existing_names:
        return _blocked(("Construction model name already exists",))

    source_fingerprint = construction_evidence_fingerprint_v1(evidence)
    slug = re.sub(r"[^A-Z0-9]+", "-", clean_name.upper()).strip("-")
    slug = slug[:48] or "MODEL"
    construction_id = f"USR-{slug}-{source_fingerprint[:10].upper()}"
    if construction_id in existing:
        return _blocked(("Generated construction model identity already exists",))

    saved_evidence = replace(
        evidence,
        construction_id=construction_id,
        label=clean_name,
        source_kind=USER_CONSTRUCTION_MODEL_SOURCE,
        source_ref=f"Saved from candidate {evidence.construction_id}",
        source_version="v1",
    )
    intent = build_u_value_method_acceptance_intent_v1(
        saved_evidence,
        str(selected_method or NOT_SET_U_VALUE_METHOD),
    )
    accepted = resolve_accepted_u_value_method_v1(saved_evidence, intent)
    if not accepted.ready or accepted.accepted_u_value_W_m2K is None:
        return _blocked(
            accepted.blockers or ("Selected U-value method did not resolve",),
            accepted.warnings,
        )

    return ConstructionModelSaveCandidateV1(
        ready=True,
        construction_id=construction_id,
        name=clean_name,
        u_value_W_m2K=float(accepted.accepted_u_value_W_m2K),
        evidence=saved_evidence,
        method_acceptance=intent,
        warnings=accepted.warnings,
        status=f"Ready — save new construction model {clean_name}",
    )


def _blocked(
    blockers: tuple[str, ...],
    warnings: tuple[str, ...] = (),
) -> ConstructionModelSaveCandidateV1:
    return ConstructionModelSaveCandidateV1(
        ready=False,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        status="Blocked — construction model was not saved",
    )
