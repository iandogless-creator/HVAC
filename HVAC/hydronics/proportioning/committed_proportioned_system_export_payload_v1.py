# ======================================================================
# H-S59-B — Committed Proportioned-system export/report payload handoff
# ======================================================================

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from HVAC.hydronics.proportioning.committed_proportioned_system_result_package_v1 import (
    CommittedProportionedSystemResultPackageV1,
)


_EXCLUSIONS_V1: tuple[str, ...] = (
    "No ProjectState mutation or additional persistence",
    "No live preview evidence used",
    "No new hydraulic, friction or pressure calculation",
    "No PDF or CSV file written",
    "No pump selection",
    "No valve product selected",
    "No valve setting selected",
    "No automatic generic-Kvs revision",
    "No pipe resizing performed while composing this export payload",
    "No commissioning or final system balancing",
)


@dataclass(frozen=True, slots=True)
class CommittedProportionedSystemExportPayloadV1:
    """
    JSON-safe report/export handoff from one ready H-S59-A package.

    This is an export payload, not an export writer. It contains only frozen
    committed result evidence and does not consult ProjectState or live
    Proportioning previews.
    """

    schema: str = "committed_proportioned_system_export_payload_v1"
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()
    source_package_schema: str = ""
    accepted_return_arrangement_basis: str = "—"
    summary: dict[str, Any] | None = None
    committed_route_results: tuple[dict[str, Any], ...] = ()
    committed_balancing_point_results: tuple[dict[str, Any], ...] = ()
    committed_route_point_reconciliation: (
        tuple[dict[str, Any], ...]
    ) = ()
    committed_section_results: tuple[dict[str, Any], ...] = ()
    exclusions: tuple[str, ...] = _EXCLUSIONS_V1
    note: str = (
        "Committed Proportioned-system report/export payload only; "
        "format-specific PDF/CSV writers remain separate."
    )


def build_committed_proportioned_system_export_payload_v1(
    package: CommittedProportionedSystemResultPackageV1 | None,
) -> CommittedProportionedSystemExportPayloadV1:
    """Flatten one ready committed package into a JSON-safe payload."""
    if not isinstance(
        package,
        CommittedProportionedSystemResultPackageV1,
    ):
        return _blocked_v1(
            "H-S59-A committed Proportioned-system result package required"
        )

    if not package.ready:
        committed_resized_hydraulics = bool(
            getattr(package, "committed_resized_hydraulics", False)
        )
        fresh_generic_kvs_review_required = bool(
            getattr(
                package,
                "fresh_generic_kvs_review_required",
                False,
            )
        )
        scope = (
            (
                "Committed resized hydraulics available; fresh manual "
                "generic-Kvs review required before export"
            ),
        ) if fresh_generic_kvs_review_required else ()
        upstream = tuple(
            f"H-S59-A: {value}"
            for value in tuple(package.blockers or ())
            if _text_v1(value)
        )
        return _blocked_v1(
            *scope,
            *(
                upstream
                or (
                    "H-S59-A: "
                    + (
                        _text_v1(package.status)
                        or "committed result package is not ready"
                    ),
                )
            ),
            source_package_schema=_text_v1(package.schema),
        )

    route_result = package.route_result
    point_result = package.point_reconciliation
    section_result = package.section_result
    completion = package.completion_status
    blockers: list[str] = []
    if route_result is None:
        blockers.append("H-S59-A packaged route result required")
    if point_result is None:
        blockers.append("H-S59-A packaged point reconciliation required")
    if section_result is None:
        blockers.append("H-S59-A packaged section result required")
    if completion is None:
        blockers.append("H-S59-A packaged completion status required")
    if blockers:
        return _blocked_v1(
            *blockers,
            source_package_schema=_text_v1(package.schema),
        )

    route_rows = _normalise_rows_v1(
        getattr(route_result, "rows", ()) or ()
    )
    point_rows = _normalise_rows_v1(
        getattr(point_result, "point_rows", ()) or ()
    )
    route_point_rows = _normalise_rows_v1(
        getattr(point_result, "route_rows", ()) or ()
    )
    section_rows = _normalise_rows_v1(
        getattr(section_result, "rows", ()) or ()
    )

    if len(route_rows) != int(package.route_count):
        blockers.append(
            "Packaged route count must match committed route export rows"
        )
    if len(point_rows) != int(package.balancing_point_count):
        blockers.append(
            "Packaged balancing-point count must match committed point "
            "export rows"
        )
    if (
        len(section_rows)
        != int(package.route_addressable_section_count)
    ):
        blockers.append(
            "Packaged route-addressable section count must match committed "
            "section export rows"
        )
    if (
        int(getattr(completion, "route_count", 0) or 0)
        != int(package.route_count)
    ):
        blockers.append(
            "Completion route count must match H-S59-A package"
        )
    if (
        int(getattr(completion, "balancing_point_count", 0) or 0)
        != int(package.balancing_point_count)
    ):
        blockers.append(
            "Completion balancing-point count must match H-S59-A package"
        )

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(
            *clean,
            source_package_schema=_text_v1(package.schema),
        )

    summary = {
        "package_status": _text_v1(package.status),
        "committed_resized_hydraulics": bool(
            getattr(package, "committed_resized_hydraulics", False)
        ),
        "fresh_generic_kvs_review_required": bool(
            getattr(
                package,
                "fresh_generic_kvs_review_required",
                False,
            )
        ),
        "completion_status": _text_v1(
            getattr(completion, "status", "")
        ),
        "source_snapshot_schema": _text_v1(
            package.source_snapshot_schema
        ),
        "accepted_return_arrangement_basis": _text_v1(
            package.accepted_return_arrangement_basis
        ),
        "controlling_target_pressure_drop_Pa": _jsonable_v1(
            getattr(
                completion,
                "controlling_target_pressure_drop_Pa",
                None,
            )
        ),
        "route_count": int(package.route_count),
        "routes_at_target_count": int(
            getattr(completion, "routes_at_target_count", 0) or 0
        ),
        "balancing_point_count": int(package.balancing_point_count),
        "reconciled_balancing_point_count": int(
            getattr(
                completion,
                "reconciled_balancing_point_count",
                0,
            )
            or 0
        ),
        "valve_duty_point_count": int(
            getattr(completion, "valve_duty_point_count", 0) or 0
        ),
        "unique_section_count": int(package.unique_section_count),
        "route_addressable_section_count": int(
            package.route_addressable_section_count
        ),
    }

    return CommittedProportionedSystemExportPayloadV1(
        ready=True,
        status=(
            "Ready — committed Proportioned-system export/report "
            "payload available"
        ),
        source_package_schema=_text_v1(package.schema),
        accepted_return_arrangement_basis=(
            _text_v1(package.accepted_return_arrangement_basis) or "—"
        ),
        summary=summary,
        committed_route_results=route_rows,
        committed_balancing_point_results=point_rows,
        committed_route_point_reconciliation=route_point_rows,
        committed_section_results=section_rows,
    )


def committed_proportioned_system_export_payload_to_dict_v1(
    payload: CommittedProportionedSystemExportPayloadV1 | None,
) -> dict[str, Any] | None:
    """Return the complete JSON-safe handoff mapping."""
    if payload is None:
        return None
    return {
        "schema": payload.schema,
        "ready": payload.ready,
        "status": payload.status,
        "blockers": tuple(payload.blockers),
        "source_package_schema": payload.source_package_schema,
        "accepted_return_arrangement_basis": (
            payload.accepted_return_arrangement_basis
        ),
        "summary": _jsonable_v1(payload.summary),
        "committed_route_results": tuple(
            payload.committed_route_results
        ),
        "committed_balancing_point_results": tuple(
            payload.committed_balancing_point_results
        ),
        "committed_route_point_reconciliation": tuple(
            payload.committed_route_point_reconciliation
        ),
        "committed_section_results": tuple(
            payload.committed_section_results
        ),
        "exclusions": tuple(payload.exclusions),
        "note": payload.note,
    }


def _normalise_rows_v1(rows: object) -> tuple[dict[str, Any], ...]:
    return tuple(_normalise_row_v1(row) for row in tuple(rows or ()))


def _normalise_row_v1(row: object) -> dict[str, Any]:
    if isinstance(row, dict):
        raw = dict(row)
    elif is_dataclass(row):
        raw = asdict(row)
    elif hasattr(row, "__dict__"):
        raw = dict(vars(row))
    else:
        raw = {"value": str(row)}
    return {
        str(key): _jsonable_v1(value)
        for key, value in raw.items()
    }


def _jsonable_v1(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {
            str(key): _jsonable_v1(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return tuple(_jsonable_v1(item) for item in value)
    return str(value)


def _blocked_v1(
    *blockers: str,
    source_package_schema: str = "",
) -> CommittedProportionedSystemExportPayloadV1:
    clean = _unique_v1(blockers)
    return CommittedProportionedSystemExportPayloadV1(
        ready=False,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
        source_package_schema=source_package_schema,
    )


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in output:
            output.append(text)
    return tuple(output)
