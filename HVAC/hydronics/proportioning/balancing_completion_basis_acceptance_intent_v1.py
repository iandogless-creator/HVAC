# ======================================================================
# H-S70-B1 — Explicit balancing completion basis acceptance intent
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math

from HVAC.hydronics.proportioning.balancing_completion_readiness_v1 import (
    BalancingCompletionReadinessV1,
)
from HVAC.hydronics.proportioning.balancing_method_design_v1 import (
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
)
from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
)


_ACCEPTABLE_METHOD_IDS_V1 = {
    NONE_REQUIRED,
    PROPORTIONAL_ADDED_RESISTANCE,
}


@dataclass(frozen=True, slots=True)
class AcceptedPointBalancingCompletionBasisV1:
    """Manual confirmation of one exact committed point basis."""

    balancing_point_id: str
    accepted_method_id: str
    accepted_kvs_basis: float | None
    basis_fingerprint: str


@dataclass(slots=True)
class BalancingCompletionBasisAcceptanceIntentV1:
    """Persisted designer intent only; never valve-product authority."""

    schema: str = "balancing_completion_basis_acceptance_intent_v1"
    accepted_by_point_id: dict[
        str, AcceptedPointBalancingCompletionBasisV1
    ] = field(default_factory=dict)

    def accept_point_basis(
        self,
        *,
        balancing_point_id: str,
        accepted_method_id: str,
        accepted_kvs_basis: float | None,
        basis_fingerprint: str,
    ) -> None:
        point_id = _stable_text_v1(balancing_point_id)
        method_id = _stable_text_v1(accepted_method_id)
        fingerprint = _fingerprint_text_v1(basis_fingerprint)
        kvs = _positive_finite_v1(accepted_kvs_basis)
        if not point_id:
            raise ValueError("balancing_point_id is required")
        if method_id not in _ACCEPTABLE_METHOD_IDS_V1:
            raise ValueError("Accepted balancing method is not available in v1")
        if not fingerprint:
            raise ValueError("basis_fingerprint must be a SHA-256 identity")
        if method_id == PROPORTIONAL_ADDED_RESISTANCE and kvs is None:
            raise ValueError(
                "Proportional added resistance requires positive accepted Kvs"
            )
        if method_id == NONE_REQUIRED and accepted_kvs_basis is not None:
            raise ValueError("NONE_REQUIRED must not carry an accepted Kvs")
        self.accepted_by_point_id[point_id] = (
            AcceptedPointBalancingCompletionBasisV1(
                balancing_point_id=point_id,
                accepted_method_id=method_id,
                accepted_kvs_basis=kvs,
                basis_fingerprint=fingerprint,
            )
        )

    def clear_point_basis(self, balancing_point_id: str) -> bool:
        point_id = _stable_text_v1(balancing_point_id)
        if not point_id:
            return False
        return self.accepted_by_point_id.pop(point_id, None) is not None

    def to_dict(self) -> dict:
        return balancing_completion_basis_acceptance_intent_to_dict_v1(self)

    @classmethod
    def from_dict(
        cls,
        data: dict | None,
    ) -> "BalancingCompletionBasisAcceptanceIntentV1":
        return balancing_completion_basis_acceptance_intent_from_dict_v1(data)


@dataclass(frozen=True, slots=True)
class ResolvedPointBalancingCompletionBasisV1:
    balancing_point_id: str = ""
    valve_duty_required: bool = False
    required_method_id: str = ""
    accepted_method_id: str = ""
    committed_kvs_basis: float | None = None
    accepted_kvs_basis: float | None = None
    accepted: bool = False
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResolvedBalancingCompletionBasisAcceptanceV1:
    schema: str = "resolved_balancing_completion_basis_acceptance_v1"
    ready: bool = False
    basis_fingerprint: str = ""
    rows: tuple[ResolvedPointBalancingCompletionBasisV1, ...] = ()
    status: str = "Balancing completion basis acceptance not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No automatic balancing-method acceptance",
        "No new Kv or Kvs selection",
        "No valve product, size or setting selected",
        "No manufacturer catalogue used",
        "No hydraulic mutation",
        "No final balancing schedule committed",
        "No pump duty or pump selection",
        "No pipe resizing",
        "No ProjectState mutation by the resolver",
    )
    note: str = (
        "Manual intent confirms the permitted v1 method and already-approved "
        "generic-Kvs basis against one exact H-S70-A-ready committed basis."
    )


def balancing_completion_basis_acceptance_intent_to_dict_v1(
    intent: BalancingCompletionBasisAcceptanceIntentV1 | None,
) -> dict:
    source = intent or BalancingCompletionBasisAcceptanceIntentV1()
    return {
        "schema": source.schema,
        "accepted_by_point_id": {
            point_id: {
                "balancing_point_id": entry.balancing_point_id,
                "accepted_method_id": entry.accepted_method_id,
                "accepted_kvs_basis": entry.accepted_kvs_basis,
                "basis_fingerprint": entry.basis_fingerprint,
            }
            for point_id, entry in sorted(source.accepted_by_point_id.items())
        },
    }


def balancing_completion_basis_acceptance_intent_from_dict_v1(
    data: dict | None,
) -> BalancingCompletionBasisAcceptanceIntentV1:
    intent = BalancingCompletionBasisAcceptanceIntentV1()
    if not isinstance(data, dict):
        return intent
    raw_entries = data.get("accepted_by_point_id", {})
    if not isinstance(raw_entries, dict):
        return intent
    for raw_point_id, raw in raw_entries.items():
        if not isinstance(raw, dict):
            continue
        point_id = _stable_text_v1(
            raw.get("balancing_point_id") or raw_point_id
        )
        method_id = _stable_text_v1(raw.get("accepted_method_id"))
        fingerprint = _fingerprint_text_v1(raw.get("basis_fingerprint"))
        raw_kvs = raw.get("accepted_kvs_basis")
        kvs = _positive_finite_v1(raw_kvs)
        valid = bool(point_id and fingerprint)
        if method_id == PROPORTIONAL_ADDED_RESISTANCE:
            valid = valid and kvs is not None
        elif method_id == NONE_REQUIRED:
            valid = valid and raw_kvs is None
        else:
            valid = False
        if not valid:
            continue
        intent.accepted_by_point_id[point_id] = (
            AcceptedPointBalancingCompletionBasisV1(
                balancing_point_id=point_id,
                accepted_method_id=method_id,
                accepted_kvs_basis=kvs,
                basis_fingerprint=fingerprint,
            )
        )
    return intent


def build_balancing_completion_basis_fingerprint_v1(
    *,
    readiness: BalancingCompletionReadinessV1,
    snapshot: ProportionedBasisSnapshotV1,
) -> str:
    """Identify the exact committed duties and generic-Kvs bases reviewed."""

    if not isinstance(readiness, BalancingCompletionReadinessV1):
        raise ValueError("H-S70-A balancing completion readiness required")
    if not readiness.ready:
        raise ValueError("H-S70-A balancing completion readiness must be ready")
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        raise ValueError("Committed proportioning snapshot required")

    authority = snapshot.point_allocation_authority
    hydraulic = snapshot.hydraulic_input_authority
    payload = {
        "snapshot": {
            "schema": snapshot.schema,
            "status": snapshot.status,
            "return_arrangement_basis": snapshot.return_arrangement_basis,
        },
        "readiness": {
            "expected_point_ids": list(readiness.expected_point_ids),
            "allocated_point_ids": list(readiness.allocated_point_ids),
            "valve_duty_point_ids": list(readiness.valve_duty_point_ids),
        },
        "hydraulic_routes": [
            {
                "route_id": _stable_text_v1(getattr(row, "route_id", "")),
                "basis": _stable_text_v1(getattr(row, "basis", "")),
                "chosen_pressure_drop_Pa": _float_token_v1(
                    getattr(row, "chosen_pressure_drop_Pa", None)
                ),
                "controlling": bool(getattr(row, "controlling", False)),
                "required_added_pressure_drop_Pa": _float_token_v1(
                    getattr(row, "required_added_pressure_drop_Pa", None)
                ),
            }
            for row in tuple(getattr(hydraulic, "routes", ()) or ())
        ],
        "point_allocations": [
            {
                "balancing_point_id": _stable_text_v1(
                    getattr(row, "balancing_point_id", "")
                ),
                "point_scope": _stable_text_v1(
                    getattr(row, "point_scope", "")
                ),
                "point_role": _stable_text_v1(
                    getattr(row, "point_role", "")
                ),
                "parent_balancing_point_id": _stable_text_v1(
                    getattr(row, "parent_balancing_point_id", "")
                ),
                "downstream_route_ids": list(
                    getattr(row, "downstream_route_ids", ()) or ()
                ),
                "point_flow_kg_s": _float_token_v1(
                    getattr(row, "point_flow_kg_s", None)
                ),
                "allocated_added_pressure_drop_Pa": _float_token_v1(
                    getattr(row, "allocated_added_pressure_drop_Pa", None)
                ),
                "allocated_resistance_Pa_per_kg_s2": _float_token_v1(
                    getattr(row, "allocated_resistance_Pa_per_kg_s2", None)
                ),
            }
            for row in tuple(getattr(authority, "rows", ()) or ())
        ],
        "route_conservation": [
            {
                "route_id": _stable_text_v1(getattr(row, "route_id", "")),
                "required_added_pressure_drop_Pa": _float_token_v1(
                    getattr(row, "required_added_pressure_drop_Pa", None)
                ),
                "allocated_path_pressure_drop_Pa": _float_token_v1(
                    getattr(row, "allocated_path_pressure_drop_Pa", None)
                ),
                "contributing_balancing_point_ids": list(
                    getattr(row, "contributing_balancing_point_ids", ()) or ()
                ),
                "conserved": bool(getattr(row, "conserved", False)),
            }
            for row in tuple(
                getattr(authority, "route_conservation", ()) or ()
            )
        ],
        "point_kvs_bases": [
            {
                "balancing_point_id": _stable_text_v1(
                    getattr(row, "balancing_point_id", "")
                ),
                "accepted_kvs_basis": _float_token_v1(
                    getattr(row, "accepted_kvs_basis", None)
                ),
                "disposition": _stable_text_v1(
                    getattr(row, "disposition", "")
                ),
            }
            for row in tuple(snapshot.committed_point_valve_bases or ())
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resolve_balancing_completion_basis_acceptance_v1(
    *,
    intent: BalancingCompletionBasisAcceptanceIntentV1 | None,
    readiness: BalancingCompletionReadinessV1 | None,
    snapshot: ProportionedBasisSnapshotV1 | None,
) -> ResolvedBalancingCompletionBasisAcceptanceV1:
    """Resolve explicit intent against one current H-S70-A-ready basis."""

    if not isinstance(readiness, BalancingCompletionReadinessV1):
        return _blocked_v1("H-S70-A balancing completion readiness required")
    if not readiness.ready:
        upstream = tuple(readiness.blockers or ()) or (
            "H-S70-A balancing completion readiness is not ready",
        )
        return _blocked_v1(*(f"H-S70-A: {value}" for value in upstream))
    if not isinstance(snapshot, ProportionedBasisSnapshotV1):
        return _blocked_v1("Committed proportioning snapshot required")

    fingerprint = build_balancing_completion_basis_fingerprint_v1(
        readiness=readiness,
        snapshot=snapshot,
    )
    source = intent or BalancingCompletionBasisAcceptanceIntentV1()
    expected_ids = tuple(readiness.allocated_point_ids or ())
    expected_set = set(expected_ids)
    orphan_ids = tuple(
        sorted(set(source.accepted_by_point_id) - expected_set)
    )
    blockers: list[str] = [
        f"{point_id}: accepted balancing basis has no current point"
        for point_id in orphan_ids
    ]
    duty_ids = set(readiness.valve_duty_point_ids or ())
    kvs_by_id = {
        _stable_text_v1(getattr(row, "balancing_point_id", "")): (
            _positive_finite_v1(getattr(row, "accepted_kvs_basis", None))
        )
        for row in tuple(snapshot.committed_point_valve_bases or ())
    }

    rows: list[ResolvedPointBalancingCompletionBasisV1] = []
    for point_id in expected_ids:
        valve_duty = point_id in duty_ids
        required_method = (
            PROPORTIONAL_ADDED_RESISTANCE if valve_duty else NONE_REQUIRED
        )
        committed_kvs = kvs_by_id.get(point_id) if valve_duty else None
        entry = source.accepted_by_point_id.get(point_id)
        row_blockers: list[str] = []
        if entry is None:
            row_blockers.append("Explicit balancing basis acceptance required")
            accepted_method = ""
            accepted_kvs = None
        else:
            accepted_method = entry.accepted_method_id
            accepted_kvs = entry.accepted_kvs_basis
            if entry.basis_fingerprint != fingerprint:
                row_blockers.append(
                    "Accepted balancing basis is stale for current committed duty"
                )
            if accepted_method != required_method:
                row_blockers.append(
                    f"Accepted method must be {required_method}"
                )
            if valve_duty:
                if committed_kvs is None:
                    row_blockers.append(
                        "Positive committed generic-Kvs basis required"
                    )
                elif accepted_kvs is None or not math.isclose(
                    accepted_kvs,
                    committed_kvs,
                    rel_tol=1.0e-9,
                    abs_tol=1.0e-9,
                ):
                    row_blockers.append(
                        "Accepted Kvs must match committed generic-Kvs basis"
                    )
            elif accepted_kvs is not None:
                row_blockers.append(
                    "No accepted Kvs permitted where valve duty is zero"
                )

        clean_row = _unique_v1(tuple(row_blockers))
        blockers.extend(f"{point_id}: {value}" for value in clean_row)
        ready = not clean_row
        rows.append(
            ResolvedPointBalancingCompletionBasisV1(
                balancing_point_id=point_id,
                valve_duty_required=valve_duty,
                required_method_id=required_method,
                accepted_method_id=accepted_method,
                committed_kvs_basis=committed_kvs,
                accepted_kvs_basis=accepted_kvs,
                accepted=ready,
                ready=ready,
                status=(
                    "Accepted — proportional added resistance with exact "
                    "committed generic-Kvs basis"
                    if ready and valve_duty
                    else "Accepted — no balancing resistance required"
                    if ready
                    else "Blocked — " + "; ".join(clean_row)
                ),
                blockers=clean_row,
            )
        )

    clean = _unique_v1(tuple(blockers))
    ready = bool(rows) and not clean and all(row.ready for row in rows)
    return ResolvedBalancingCompletionBasisAcceptanceV1(
        ready=ready,
        basis_fingerprint=fingerprint,
        rows=tuple(rows),
        status=(
            f"Ready — explicit balancing method and generic-Kvs basis "
            f"accepted at {len(rows)} point(s); product selection deferred"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def _blocked_v1(
    *blockers: str,
) -> ResolvedBalancingCompletionBasisAcceptanceV1:
    clean = _unique_v1(tuple(blockers))
    return ResolvedBalancingCompletionBasisAcceptanceV1(
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _float_token_v1(value: object) -> str | None:
    number = _finite_v1(value)
    return number.hex() if number is not None else None


def _finite_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive_finite_v1(value: object) -> float | None:
    number = _finite_v1(value)
    return number if number is not None and number > 0.0 else None


def _stable_text_v1(value: object) -> str:
    return str(value or "").strip()


def _fingerprint_text_v1(value: object) -> str:
    text = _stable_text_v1(value).lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        return ""
    return text


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _stable_text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)
