# ======================================================================
# H-S56-A — Committed balancing-point allocation authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.balancing_point_resistance_allocation_v1 import (
    BalancingPointResistanceAllocationProjectionV1,
    BalancingPointResistanceAllocationRowV1,
    BalancingPointRouteConservationRowV1,
)


DEFAULT_POINT_ALLOCATION_TOLERANCE_PA = 0.05


@dataclass(frozen=True, slots=True)
class CommittedBalancingPointAllocationRowV1:
    """Frozen H-S44-B point allocation; never a valve setting or product."""

    balancing_point_id: str
    point_scope: str
    point_role: str
    label: str
    parent_balancing_point_id: str
    anchor_section_id: str
    downstream_route_ids: tuple[str, ...]
    is_shared: bool
    is_route_exclusive: bool
    point_flow_kg_s: float
    allocated_added_pressure_drop_Pa: float
    allocated_resistance_Pa_per_kg_s2: float
    status: str


@dataclass(frozen=True, slots=True)
class CommittedBalancingPointRouteConservationRowV1:
    """Frozen no-double-counting proof for one committed route burden."""

    route_id: str
    required_added_pressure_drop_Pa: float
    allocated_path_pressure_drop_Pa: float
    difference_Pa: float
    contributing_balancing_point_ids: tuple[str, ...]
    conserved: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedBalancingPointAllocationAuthorityV1:
    """
    Typed copy of ready H-S44-B point-allocation evidence.

    H-S56-B may place this authority in the committed basis snapshot. This
    module itself does not read or mutate ProjectState.
    """

    schema: str = "committed_balancing_point_allocation_authority_v1"
    ready: bool = False
    tolerance_Pa: float = DEFAULT_POINT_ALLOCATION_TOLERANCE_PA
    rows: tuple[CommittedBalancingPointAllocationRowV1, ...] = ()
    route_conservation: tuple[
        CommittedBalancingPointRouteConservationRowV1, ...
    ] = ()
    status: str = "Committed balancing-point allocation authority not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live point evidence after commit",
        "No ProjectState mutation",
        "No valve product selected",
        "No valve setting selected",
        "No automatic Kvs choice or revision",
        "No pump selection",
        "No pipe resizing",
        "No commissioning or final balancing",
    )
    note: str = (
        "Frozen point allocation and route-conservation evidence only; "
        "H-S56-C reconciliation remains deferred."
    )


def build_committed_balancing_point_allocation_authority_v1(
    projection: BalancingPointResistanceAllocationProjectionV1 | None,
    *,
    tolerance_Pa: float = DEFAULT_POINT_ALLOCATION_TOLERANCE_PA,
) -> CommittedBalancingPointAllocationAuthorityV1:
    """Validate and freeze ready H-S44-B point-allocation evidence."""

    tolerance = _finite_number_v1(tolerance_Pa)
    if tolerance is None or tolerance < 0.0:
        return _blocked_authority_v1(
            "tolerance_Pa must be finite and zero or greater"
        )
    if not isinstance(
        projection,
        BalancingPointResistanceAllocationProjectionV1,
    ):
        return _blocked_authority_v1(
            "H-S44-B balancing-point allocation projection required",
            tolerance_Pa=tolerance,
        )
    if not projection.ready:
        upstream = tuple(
            f"H-S44-B: {value}"
            for value in tuple(projection.blockers or ())
            if _text_v1(value)
        )
        return _blocked_authority_v1(
            *(upstream or ("H-S44-B point allocation is not ready",)),
            tolerance_Pa=tolerance,
        )

    source_rows = tuple(projection.rows or ())
    source_conservation = tuple(projection.route_conservation or ())
    blockers: list[str] = []
    if not source_rows:
        blockers.append("H-S44-B balancing-point allocation rows required")
    if not source_conservation:
        blockers.append("H-S44-B route-conservation rows required")

    rows: list[CommittedBalancingPointAllocationRowV1] = []
    row_by_id: dict[str, CommittedBalancingPointAllocationRowV1] = {}
    for source in source_rows:
        point_id = _text_v1(source.balancing_point_id)
        if not point_id:
            blockers.append("Every committed point allocation requires stable ID")
            continue
        if point_id in row_by_id:
            blockers.append(f"Duplicate committed balancing_point_id: {point_id}")
            continue

        point_scope = _text_v1(source.point_scope)
        point_role = _text_v1(source.point_role)
        label = _text_v1(source.label)
        route_ids = tuple(_text_v1(value) for value in source.downstream_route_ids)
        if not point_scope:
            blockers.append(f"{point_id}: point_scope required")
        if not point_role:
            blockers.append(f"{point_id}: point_role required")
        if not label:
            blockers.append(f"{point_id}: label required")
        if not route_ids or any(not value for value in route_ids):
            blockers.append(f"{point_id}: governed route identities required")
        elif len(set(route_ids)) != len(route_ids):
            blockers.append(f"{point_id}: duplicate governed route identity")

        flow = _finite_number_v1(source.point_flow_kg_s)
        allocated = _finite_number_v1(source.allocated_added_dp_pa)
        resistance = _finite_number_v1(
            source.allocated_resistance_pa_per_kg_s2
        )
        if flow is None or flow <= 0.0:
            blockers.append(f"{point_id}: positive point flow required")
        if allocated is None or allocated < 0.0:
            blockers.append(
                f"{point_id}: non-negative allocated added pressure drop required"
            )
        if resistance is None or resistance < 0.0:
            blockers.append(
                f"{point_id}: non-negative allocated resistance required"
            )
        if bool(source.is_shared) and bool(source.is_route_exclusive):
            blockers.append(
                f"{point_id}: point cannot be both shared and route-exclusive"
            )

        if (
            flow is None
            or flow <= 0.0
            or allocated is None
            or allocated < 0.0
            or resistance is None
            or resistance < 0.0
            or not point_scope
            or not point_role
            or not label
            or not route_ids
            or any(not value for value in route_ids)
            or len(set(route_ids)) != len(route_ids)
        ):
            continue

        expected_resistance = allocated / (flow ** 2)
        if not math.isclose(
            resistance,
            expected_resistance,
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        ):
            blockers.append(
                f"{point_id}: allocated resistance does not match Δp / flow²"
            )

        frozen = CommittedBalancingPointAllocationRowV1(
            balancing_point_id=point_id,
            point_scope=point_scope,
            point_role=point_role,
            label=label,
            parent_balancing_point_id=_text_v1(
                source.parent_balancing_point_id
            ),
            anchor_section_id=_text_v1(source.anchor_section_id),
            downstream_route_ids=route_ids,
            is_shared=bool(source.is_shared),
            is_route_exclusive=bool(source.is_route_exclusive),
            point_flow_kg_s=flow,
            allocated_added_pressure_drop_Pa=allocated,
            allocated_resistance_Pa_per_kg_s2=resistance,
            status=_text_v1(source.status),
        )
        rows.append(frozen)
        row_by_id[point_id] = frozen

    for row in rows:
        parent_id = row.parent_balancing_point_id
        if parent_id and parent_id not in row_by_id:
            blockers.append(
                f"{row.balancing_point_id}: committed parent point unresolved"
            )

    conservation: list[CommittedBalancingPointRouteConservationRowV1] = []
    seen_routes: set[str] = set()
    for source in source_conservation:
        route_id = _text_v1(source.route_id)
        if not route_id:
            blockers.append("Every route-conservation row requires stable route_id")
            continue
        if route_id in seen_routes:
            blockers.append(f"Duplicate committed conservation route_id: {route_id}")
            continue
        seen_routes.add(route_id)

        required = _finite_number_v1(source.required_added_dp_pa)
        allocated = _finite_number_v1(source.allocated_path_dp_pa)
        difference = _finite_number_v1(source.difference_pa)
        contributors = tuple(
            _text_v1(value)
            for value in source.contributing_balancing_point_ids
        )
        if required is None or required < 0.0:
            blockers.append(
                f"{route_id}: non-negative required added pressure drop required"
            )
        if allocated is None or allocated < 0.0:
            blockers.append(
                f"{route_id}: non-negative allocated path pressure drop required"
            )
        if difference is None:
            blockers.append(f"{route_id}: finite conservation difference required")
        if any(not value for value in contributors):
            blockers.append(f"{route_id}: stable contributor identities required")
        elif len(set(contributors)) != len(contributors):
            blockers.append(f"{route_id}: duplicate contributing point identity")

        expected_contributors = tuple(
            row.balancing_point_id
            for row in rows
            if route_id in row.downstream_route_ids
            and row.allocated_added_pressure_drop_Pa > 0.0
        )
        if contributors != expected_contributors:
            blockers.append(
                f"{route_id}: contributing point identities do not match "
                "committed governed-path allocations"
            )

        expected_allocated = sum(
            row_by_id[point_id].allocated_added_pressure_drop_Pa
            for point_id in contributors
            if point_id in row_by_id
        )
        if allocated is not None and abs(allocated - expected_allocated) > tolerance:
            blockers.append(
                f"{route_id}: allocated path pressure drop is not conserved"
            )
        expected_difference = (
            required - allocated
            if required is not None and allocated is not None
            else None
        )
        if (
            difference is not None
            and expected_difference is not None
            and abs(difference - expected_difference) > tolerance
        ):
            blockers.append(
                f"{route_id}: conservation difference is inconsistent"
            )
        if not bool(source.conserved):
            blockers.append(f"{route_id}: source route burden is not conserved")
        if difference is not None and abs(difference) > tolerance:
            blockers.append(
                f"{route_id}: route allocation residual exceeds "
                f"{tolerance:.3f} Pa"
            )

        if (
            required is None
            or required < 0.0
            or allocated is None
            or allocated < 0.0
            or difference is None
            or any(not value for value in contributors)
            or len(set(contributors)) != len(contributors)
        ):
            continue

        conservation.append(
            CommittedBalancingPointRouteConservationRowV1(
                route_id=route_id,
                required_added_pressure_drop_Pa=required,
                allocated_path_pressure_drop_Pa=allocated,
                difference_Pa=(
                    0.0 if abs(difference) <= tolerance else difference
                ),
                contributing_balancing_point_ids=contributors,
                conserved=bool(source.conserved) and abs(difference) <= tolerance,
                status=_text_v1(source.status),
            )
        )

    clean = _unique_v1(tuple(blockers))
    if clean:
        return _blocked_authority_v1(*clean, tolerance_Pa=tolerance)
    return CommittedBalancingPointAllocationAuthorityV1(
        ready=True,
        tolerance_Pa=tolerance,
        rows=tuple(rows),
        route_conservation=tuple(conservation),
        status=(
            "Ready — committed balancing-point allocation authority frozen"
        ),
        blockers=(),
    )


def committed_balancing_point_allocation_authority_to_dict_v1(
    authority: CommittedBalancingPointAllocationAuthorityV1 | None,
) -> dict | None:
    if authority is None:
        return None
    return {
        "schema": authority.schema,
        "ready": bool(authority.ready),
        "tolerance_Pa": float(authority.tolerance_Pa),
        "rows": [
            {
                "balancing_point_id": row.balancing_point_id,
                "point_scope": row.point_scope,
                "point_role": row.point_role,
                "label": row.label,
                "parent_balancing_point_id": row.parent_balancing_point_id,
                "anchor_section_id": row.anchor_section_id,
                "downstream_route_ids": list(row.downstream_route_ids),
                "is_shared": bool(row.is_shared),
                "is_route_exclusive": bool(row.is_route_exclusive),
                "point_flow_kg_s": row.point_flow_kg_s,
                "allocated_added_pressure_drop_Pa": (
                    row.allocated_added_pressure_drop_Pa
                ),
                "allocated_resistance_Pa_per_kg_s2": (
                    row.allocated_resistance_Pa_per_kg_s2
                ),
                "status": row.status,
            }
            for row in authority.rows
        ],
        "route_conservation": [
            {
                "route_id": row.route_id,
                "required_added_pressure_drop_Pa": (
                    row.required_added_pressure_drop_Pa
                ),
                "allocated_path_pressure_drop_Pa": (
                    row.allocated_path_pressure_drop_Pa
                ),
                "difference_Pa": row.difference_Pa,
                "contributing_balancing_point_ids": list(
                    row.contributing_balancing_point_ids
                ),
                "conserved": bool(row.conserved),
                "status": row.status,
            }
            for row in authority.route_conservation
        ],
        "status": authority.status,
        "blockers": list(authority.blockers),
        "note": authority.note,
    }


def committed_balancing_point_allocation_authority_from_dict_v1(
    data: object,
) -> CommittedBalancingPointAllocationAuthorityV1 | None:
    if not isinstance(data, dict):
        return None
    try:
        projection = BalancingPointResistanceAllocationProjectionV1(
            ready=bool(data.get("ready", False)),
            rows=tuple(
                BalancingPointResistanceAllocationRowV1(
                    balancing_point_id=_required_mapping_text_v1(
                        raw, "balancing_point_id"
                    ),
                    point_scope=_required_mapping_text_v1(raw, "point_scope"),
                    point_role=_required_mapping_text_v1(raw, "point_role"),
                    label=_required_mapping_text_v1(raw, "label"),
                    parent_balancing_point_id=_text_v1(
                        raw.get("parent_balancing_point_id")
                    ),
                    anchor_section_id=_text_v1(raw.get("anchor_section_id")),
                    downstream_route_ids=tuple(
                        _text_v1(value)
                        for value in tuple(raw.get("downstream_route_ids", ()) or ())
                    ),
                    is_shared=bool(raw.get("is_shared", False)),
                    is_route_exclusive=bool(
                        raw.get("is_route_exclusive", False)
                    ),
                    point_flow_kg_s=_finite_number_v1(
                        raw.get("point_flow_kg_s")
                    ),
                    allocated_added_dp_pa=_finite_number_v1(
                        raw.get("allocated_added_pressure_drop_Pa")
                    ),
                    allocated_resistance_pa_per_kg_s2=_finite_number_v1(
                        raw.get("allocated_resistance_Pa_per_kg_s2")
                    ),
                    status=_text_v1(raw.get("status")),
                )
                for raw in tuple(data.get("rows", ()) or ())
                if isinstance(raw, dict)
            ),
            route_conservation=tuple(
                BalancingPointRouteConservationRowV1(
                    route_id=_required_mapping_text_v1(raw, "route_id"),
                    required_added_dp_pa=_finite_number_v1(
                        raw.get("required_added_pressure_drop_Pa")
                    ),
                    allocated_path_dp_pa=_finite_number_v1(
                        raw.get("allocated_path_pressure_drop_Pa")
                    ),
                    difference_pa=_finite_number_v1(raw.get("difference_Pa")),
                    contributing_balancing_point_ids=tuple(
                        _text_v1(value)
                        for value in tuple(
                            raw.get(
                                "contributing_balancing_point_ids",
                                (),
                            )
                            or ()
                        )
                    ),
                    conserved=bool(raw.get("conserved", False)),
                    status=_text_v1(raw.get("status")),
                )
                for raw in tuple(data.get("route_conservation", ()) or ())
                if isinstance(raw, dict)
            ),
            blockers=tuple(
                _text_v1(value)
                for value in tuple(data.get("blockers", ()) or ())
                if _text_v1(value)
            ),
            status=_text_v1(data.get("status")),
        )
        return build_committed_balancing_point_allocation_authority_v1(
            projection,
            tolerance_Pa=data.get(
                "tolerance_Pa",
                DEFAULT_POINT_ALLOCATION_TOLERANCE_PA,
            ),
        )
    except (TypeError, ValueError):
        return None


def _finite_number_v1(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _required_mapping_text_v1(mapping: dict, name: str) -> str:
    value = _text_v1(mapping.get(name))
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_authority_v1(
    *blockers: str,
    tolerance_Pa: float = DEFAULT_POINT_ALLOCATION_TOLERANCE_PA,
) -> CommittedBalancingPointAllocationAuthorityV1:
    clean = _unique_v1(tuple(blockers))
    return CommittedBalancingPointAllocationAuthorityV1(
        ready=False,
        tolerance_Pa=tolerance_Pa,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
