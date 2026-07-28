# ======================================================================
# H-S55-A — Committed-basis route proportioning result
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math

from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


DEFAULT_PROPORTIONING_TOLERANCE_PA = 0.05


@dataclass(frozen=True, slots=True)
class CommittedBasisRouteProportioningResultRowV1:
    route_id: str = ""
    route_label: str = ""
    basis: str = ""
    controlling: bool = False
    chosen_pressure_drop_Pa: float | None = None
    required_added_pressure_drop_Pa: float | None = None
    proportioned_pressure_drop_Pa: float | None = None
    controlling_target_pressure_drop_Pa: float | None = None
    residual_to_target_Pa: float | None = None
    within_tolerance: bool = False
    ready: bool = False
    status: str = ""
    blockers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CommittedBasisRouteProportioningResultV1:
    """
    Deterministic route result derived only from frozen H-S54 authority.

    No live ProjectState evidence is read and no design state is mutated.
    """

    schema: str = "committed_basis_route_proportioning_result_v1"
    ready: bool = False
    controlling_target_pressure_drop_Pa: float | None = None
    tolerance_Pa: float = DEFAULT_PROPORTIONING_TOLERANCE_PA
    rows: tuple[CommittedBasisRouteProportioningResultRowV1, ...] = ()
    status: str = "Committed-basis route proportioning result not ready"
    blockers: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = (
        "No live hydraulic preview used",
        "No ProjectState mutation",
        "No pump selection",
        "No valve product or valve setting selected",
        "No pipe resizing",
        "No automatic design correction",
        "No commissioning or final balancing",
    )
    note: str = (
        "Route totals apply the committed required added pressure drop to "
        "the committed chosen route pressure drop only."
    )


def build_committed_basis_route_proportioning_result_v1(
    authority: CommittedProportioningHydraulicInputAuthorityV1 | None,
    *,
    tolerance_Pa: float = DEFAULT_PROPORTIONING_TOLERANCE_PA,
) -> CommittedBasisRouteProportioningResultV1:
    """Apply committed route additions and verify convergence."""

    tolerance = _finite_number_v1(tolerance_Pa)
    if tolerance is None or tolerance < 0.0:
        return _blocked_result_v1(
            "tolerance_Pa must be finite and zero or greater"
        )
    if not isinstance(
        authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked_result_v1(
            "H-S54-A committed hydraulic-input authority required",
            tolerance_Pa=tolerance,
        )

    upstream = tuple(
        f"H-S54-A: {value}"
        for value in tuple(authority.blockers or ())
        if str(value or "").strip()
    )
    if not authority.ready:
        return _blocked_result_v1(
            *(upstream or ("H-S54-A committed authority is not ready",)),
            tolerance_Pa=tolerance,
        )

    source_rows = tuple(authority.routes or ())
    if not source_rows:
        return _blocked_result_v1(
            "Committed route authority rows required",
            tolerance_Pa=tolerance,
        )

    source_by_id: dict[str, object] = {}
    validation_blockers: list[str] = []
    numeric_by_id: dict[str, tuple[float, float]] = {}
    controlling_ids: list[str] = []

    for source in source_rows:
        route_id = _text_v1(source.route_id)
        if not route_id:
            validation_blockers.append(
                "Every committed route requires stable route_id"
            )
            continue
        if route_id in source_by_id:
            validation_blockers.append(
                f"Duplicate committed route_id: {route_id}"
            )
            continue
        source_by_id[route_id] = source

        chosen = _finite_number_v1(source.chosen_pressure_drop_Pa)
        added = _finite_number_v1(
            source.required_added_pressure_drop_Pa
        )
        if chosen is None or chosen < 0.0:
            validation_blockers.append(
                f"{route_id}: non-negative chosen pressure drop required"
            )
        if added is None or added < 0.0:
            validation_blockers.append(
                f"{route_id}: non-negative required added pressure drop "
                "required"
            )
        if chosen is not None and chosen >= 0.0 and added is not None and added >= 0.0:
            numeric_by_id[route_id] = (chosen, added)
        if bool(source.controlling):
            controlling_ids.append(route_id)

    if not controlling_ids:
        validation_blockers.append(
            "At least one committed controlling route required"
        )

    clean_validation = _unique_v1(tuple(validation_blockers))
    if clean_validation:
        return _blocked_result_v1(
            *clean_validation,
            tolerance_Pa=tolerance,
        )

    target = max(numeric_by_id[route_id][0] for route_id in controlling_ids)
    rows: list[CommittedBasisRouteProportioningResultRowV1] = []
    blockers: list[str] = []

    for source in source_rows:
        route_id = _text_v1(source.route_id)
        chosen, added = numeric_by_id[route_id]
        proportioned = chosen + added
        residual = target - proportioned
        within_tolerance = abs(residual) <= tolerance
        row_blockers = (
            ()
            if within_tolerance
            else (
                "Committed chosen pressure drop plus required added "
                "pressure drop does not reach the controlling target "
                f"within {tolerance:.3f} Pa",
            )
        )
        if row_blockers:
            blockers.extend(
                f"{route_id}: {value}" for value in row_blockers
            )
        rows.append(
            CommittedBasisRouteProportioningResultRowV1(
                route_id=route_id,
                route_label=_text_v1(source.route_label) or route_id,
                basis=_text_v1(source.basis),
                controlling=bool(source.controlling),
                chosen_pressure_drop_Pa=chosen,
                required_added_pressure_drop_Pa=added,
                proportioned_pressure_drop_Pa=proportioned,
                controlling_target_pressure_drop_Pa=target,
                residual_to_target_Pa=residual,
                within_tolerance=within_tolerance,
                ready=within_tolerance,
                status=(
                    "Ready — committed route reaches controlling target"
                    if within_tolerance
                    else "Blocked — committed route does not reach "
                    "controlling target"
                ),
                blockers=row_blockers,
            )
        )

    clean = _unique_v1(tuple(blockers))
    ready = not clean and all(row.ready for row in rows)
    return CommittedBasisRouteProportioningResultV1(
        ready=ready,
        controlling_target_pressure_drop_Pa=target,
        tolerance_Pa=tolerance,
        rows=tuple(rows),
        status=(
            "Ready — committed-basis route proportioning result calculated"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


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


def _unique_v1(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _text_v1(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _blocked_result_v1(
    *blockers: str,
    tolerance_Pa: float = DEFAULT_PROPORTIONING_TOLERANCE_PA,
) -> CommittedBasisRouteProportioningResultV1:
    clean = _unique_v1(tuple(blockers))
    return CommittedBasisRouteProportioningResultV1(
        ready=False,
        tolerance_Pa=tolerance_Pa,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )
