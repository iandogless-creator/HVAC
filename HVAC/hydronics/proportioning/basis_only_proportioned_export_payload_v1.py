# ======================================================================
# HVAC/hydronics/proportioning/basis_only_proportioned_export_payload_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from HVAC.hydronics.proportioning.proportioned_basis_snapshot_v1 import (
    ProportionedBasisSnapshotV1,
    proportioned_basis_snapshot_to_dict_v1,
)


_EXCLUSIONS_V1: tuple[str, ...] = (
    "No pump selection",
    "No valve selection",
    "No final balancing",
    "No pipe resizing",
    "No final hydraulic result",
)


@dataclass(frozen=True, slots=True)
class BasisOnlyProportionedExportPayloadV1:
    """
    H-S30-H:
    Basis-only Proportioned export payload preview.

    This is a serialisable evidence bundle for later export/report work.

    It is not an export writer.

    It does not:
        • write PDF
        • write CSV
        • select a pump
        • select valves
        • perform final balancing
        • resize pipes
        • create a final hydraulic result
    """

    schema: str = "basis_only_proportioned_export_payload_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()

    committed_basis_snapshot: dict[str, Any] | None = None
    resolved_return_arrangement_basis: tuple[dict[str, Any], ...] = ()
    chosen_basis_route_pressure_evidence: tuple[dict[str, Any], ...] = ()
    chosen_basis_controlling_shortfall_evidence: tuple[dict[str, Any], ...] = ()
    provisional_proportioning_burden: tuple[dict[str, Any], ...] = ()

    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Basis-only Proportioned export payload preview — "
        "final hydraulics not included."
    )


def _jsonable_v1(value: object) -> object:
    if value is None:
        return None

    if isinstance(value, (bool, int, float, str)):
        return value

    if isinstance(value, dict):
        return {
            str(key): _jsonable_v1(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return tuple(_jsonable_v1(item) for item in value)

    return str(value)


def _normalise_row_v1(row: object) -> dict[str, Any]:
    if row is None:
        return {}

    if isinstance(row, dict):
        raw = dict(row)
    elif is_dataclass(row):
        raw = asdict(row)
    else:
        raw = {}

        for name in (
                "scope",
                "target",
                "effective_basis",
                "source",
                "route",
                "basis",
                "chosen_dp",
                "chosen_dp_pa",
                "controlling",
                "is_controlling",
                "required_added_dp",
                "dp_below_controlling_pa",
                "flow_kg_s",
                "resistance_pa_per_kg_s2",
                "action",
                "status",
                "item",
                "note",
        ):
            if hasattr(row, name):
                raw[name] = getattr(row, name)

        if not raw:
            raw = {"value": str(row)}

    return {
        str(key): _jsonable_v1(value)
        for key, value in raw.items()
    }


def _normalise_rows_v1(rows: object) -> tuple[dict[str, Any], ...]:
    return tuple(
        _normalise_row_v1(row)
        for row in list(rows or ())
    )


def build_basis_only_proportioned_export_payload_preview_v1(
        *,
        snapshot: ProportionedBasisSnapshotV1 | None,
        resolved_return_arrangement_basis_rows: object = (),
        chosen_basis_route_pressure_rows: object = (),
        chosen_basis_controlling_shortfall_rows: object = (),
        provisional_proportioning_burden_rows: object = (),
) -> BasisOnlyProportionedExportPayloadV1:
    """
    Build the H-S30-H basis-only Proportioned export payload preview.

    This function is deliberately pure:
        • no ProjectState mutation
        • no files written
        • no GUI dependency
        • no pump / valve / balancing / pipe-resize authority
    """
    blockers: list[str] = []

    if snapshot is None:
        blockers.append("Committed basis-only Proportioned snapshot required")
        snapshot_payload = None
    else:
        snapshot_payload = proportioned_basis_snapshot_to_dict_v1(snapshot)

        if not bool(getattr(snapshot, "basis_only_output_ready", False)):
            blockers.append(
                "Committed snapshot is not ready for basis-only output export"
            )

    ready = not blockers

    status = (
        "Ready — basis-only Proportioned export payload preview built"
        if ready
        else "Blocked — " + "; ".join(blockers)
    )

    return BasisOnlyProportionedExportPayloadV1(
        ready=ready,
        status=status,
        blockers=tuple(blockers),
        committed_basis_snapshot=snapshot_payload,
        resolved_return_arrangement_basis=_normalise_rows_v1(
            resolved_return_arrangement_basis_rows
        ),
        chosen_basis_route_pressure_evidence=_normalise_rows_v1(
            chosen_basis_route_pressure_rows
        ),
        chosen_basis_controlling_shortfall_evidence=_normalise_rows_v1(
            chosen_basis_controlling_shortfall_rows
        ),
        provisional_proportioning_burden=_normalise_rows_v1(
            provisional_proportioning_burden_rows
        ),
    )


def basis_only_proportioned_export_payload_to_dict_v1(
        payload: BasisOnlyProportionedExportPayloadV1 | None,
) -> dict[str, Any] | None:
    if payload is None:
        return None

    return {
        "schema": payload.schema,
        "ready": payload.ready,
        "status": payload.status,
        "blockers": tuple(payload.blockers),
        "committed_basis_snapshot": payload.committed_basis_snapshot,
        "resolved_return_arrangement_basis": tuple(
            payload.resolved_return_arrangement_basis
        ),
        "chosen_basis_route_pressure_evidence": tuple(
            payload.chosen_basis_route_pressure_evidence
        ),
        "chosen_basis_controlling_shortfall_evidence": tuple(
            payload.chosen_basis_controlling_shortfall_evidence
        ),
        "provisional_proportioning_burden": tuple(
            payload.provisional_proportioning_burden
        ),
        "exclusions": tuple(payload.exclusions),
        "note": payload.note,
    }
