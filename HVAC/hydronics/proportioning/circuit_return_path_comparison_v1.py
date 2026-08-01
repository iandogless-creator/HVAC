# HVAC/hydronics/proportioning/circuit_return_path_comparison_v1.py
#
# H-S19-A — Direct return vs reverse return circuit comparison
#
# Preview-only:
# - no balancing valve settings
# - no pump selection
# - no pipe resizing
# - no final system commit

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any
from HVAC.hydronics.sizing.basic_ps_topology_sections_v1 import (
    build_basic_ps_topology_sections_v1,
)
from HVAC.hydronics.local_losses.local_k_pressure_preview_v1 import (
    build_local_k_pressure_preview_v1,
)
from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    build_basic_ps_readonly_projection_v1,
)
from HVAC.hydronics.proportioning.route_pressure_accumulator_v1 import (
    _local_k_section_length_m_v1,
    build_route_pressure_accumulator_v1,
)
from HVAC.hydronics.pipes.dp.mass_flow_pressure_drop_v1 import (
    calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1,
)
from HVAC.hydronics.proportioning.effective_rr_length_basis_resolver_v1 import (
    EffectiveRRAddedLengthBasisV1,
    resolve_subleg_rr_added_length_basis_v1,
)
from HVAC.hydronics.topology.primary_subleg_helpers_v1 import (
    find_primary_subleg_for_leg,
)

@dataclass(frozen=True, slots=True)
class CircuitReturnPathComparisonRowV1:
    room_id: str
    emitter_id: str
    route_id: str
    route_label: str

    flow_section_ids: tuple[str, ...]
    direct_return_section_ids: tuple[str, ...]
    reverse_return_section_ids: tuple[str, ...]

    rr_suitability_code: str
    rr_suitability_status: str

    flow_dp_Pa: float | None
    direct_return_dp_Pa: float | None
    reverse_return_dp_Pa: float | None

    rr_added_length_m: float
    rr_added_pressure_drop_Pa: float

    direct_total_dp_Pa: float | None
    reverse_return_total_dp_Pa: float | None

    direct_rank: int | None
    reverse_return_rank: int | None

    controlling_direct: bool
    controlling_reverse_return: bool

    status: str

    # H-S38-A3 route-specific RR length authority evidence.
    # Defaults retain compatibility with older direct DTO construction.
    rr_added_length_basis_mode: str = "physical_loop_zero_extra"
    rr_added_length_source: str = "system"
    rr_added_length_inherited_from: str = ""

    # H-S42-D physical upstream contribution, applied once to both bases.
    common_main_dp_Pa: float | None = 0.0
    leg_entry_dp_Pa: float | None = 0.0
    physical_main_entry_dp_Pa: float | None = 0.0

    # H-S51-D — explicit fail-closed upstream-length evidence.
    missing_upstream_length_section_ids: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ReverseReturnSuitabilityV1:
    suitable: bool
    code: str
    status: str

@dataclass(frozen=True, slots=True)
class CircuitReturnPathComparisonProjectionV1:
    rows: tuple[CircuitReturnPathComparisonRowV1, ...]
    status: str = "Circuit return path comparison preview only"


@dataclass(frozen=True, slots=True)
class _RRSectionPressureBasisV1:
    mass_flow_kg_s: float
    pipe_size_label: str
    # H-S63-B2B1 — exact RR added-length pipe identity. Display wording is
    # evidence only and is never parsed back into hydraulic authority.
    material_key: str
    pipe_size_key: int


def build_circuit_return_path_comparison_v1(
    project_state: Any,
) -> CircuitReturnPathComparisonProjectionV1:
    """
    H-S19-A shell.

    Future purpose:
    Compare each circuit/emitter under:
        F + R   direct return
        F + RR  reverse return

    Current shell deliberately does not invent return paths yet.
    It only confirms that topology/emitter traversal can produce
    comparison rows for future pressure calculations.
    """

    topology = getattr(project_state, "hydronic_topology", None)
    emitters = getattr(project_state, "emitters", {}) or {}

    if topology is None:
        return CircuitReturnPathComparisonProjectionV1(
            rows=(),
            status="No hydronic topology — cannot compare return paths",
        )

    rows: list[CircuitReturnPathComparisonRowV1] = []

    for leg in getattr(topology, "legs", []) or []:
        leg_id = str(getattr(leg, "leg_id", "") or "")
        leg_sublegs = list(getattr(leg, "sublegs", []) or [])
        primary_subleg = find_primary_subleg_for_leg(leg)
        primary_subleg_id = str(
            getattr(primary_subleg, "subleg_id", "") or ""
        )

        for subleg in leg_sublegs:
            subleg_id = str(getattr(subleg, "subleg_id", "") or "")
            subleg_label = str(
                getattr(subleg, "label", None)
                or getattr(subleg, "name", None)
                or subleg_id
            )

            room_ids = _subleg_room_ids(subleg)

            flow_sections_by_room = _flow_section_ids_by_room(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            reverse_return_sections_by_room = _reverse_return_section_ids_by_room(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            section_dp_by_id = _section_total_dp_by_id(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            section_pressure_basis_by_id = _section_pressure_basis_by_id(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            section_length_by_id = _section_length_by_id(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )

            # H-S42-D: one route-specific physical upstream contribution.
            (
                common_main_dp_Pa,
                leg_entry_dp_Pa,
                missing_upstream_length_section_ids,
            ) = _main_entry_pressure_evidence_v1(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
            )
            physical_main_entry_dp_Pa = _add_complete_dp_v1(
                common_main_dp_Pa,
                leg_entry_dp_Pa,
            )

            # H-S38-A3: resolve one most-specific RR length authority
            # for this route. Current v1 branch siblings inherit from
            # the leg primary/common subleg, matching arrangement scope.
            parent_subleg_id = (
                primary_subleg_id
                if primary_subleg_id and subleg_id != primary_subleg_id
                else ""
            )
            rr_length_resolution = _resolve_route_rr_added_length_basis_v1(
                project_state,
                leg_id=leg_id,
                subleg_id=subleg_id,
                parent_subleg_id=parent_subleg_id,
            )
            rr_added_length_basis_mode = (
                rr_length_resolution.effective_basis_mode
            )

            rr_suitability = _appraise_reverse_return_suitability_v1(
                subleg,
                room_ids=room_ids,
            )

            for room_id in room_ids:
                flow_section_ids = flow_sections_by_room.get(
                    str(room_id),
                    (),
                )

                direct_return_section_ids = tuple(
                    reversed(flow_section_ids)
                )

                reverse_return_section_ids = (
                    reverse_return_sections_by_room.get(str(room_id), ())
                    if rr_suitability.code == "ordered-subleg"
                    else ()
                )

                rr_added_length_m = _rr_added_length_for_row_v1(
                    project_state=project_state,
                    basis_mode=rr_added_length_basis_mode,
                    section_length_by_id=section_length_by_id,
                    reverse_return_section_ids=reverse_return_section_ids,
                    manual_added_length_m=(
                        rr_length_resolution.effective_added_length_m
                    ),
                )

                flow_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    flow_section_ids,
                )

                direct_return_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    direct_return_section_ids,
                )

                reverse_return_dp_Pa = _sum_section_dp(
                    section_dp_by_id,
                    reverse_return_section_ids,
                )

                rr_added_pressure_drop_Pa = _rr_added_length_pressure_drop_Pa(
                    project_state=project_state,
                    section_pressure_basis_by_id=section_pressure_basis_by_id,
                    candidate_section_ids=(
                        reverse_return_section_ids or flow_section_ids
                    ),
                    length_m=(
                        rr_added_length_m
                        if reverse_return_section_ids
                        else 0.0
                    ),
                )

                direct_total_dp_Pa = _add_complete_dp_v1(
                    _add_optional_dp(flow_dp_Pa, direct_return_dp_Pa),
                    physical_main_entry_dp_Pa,
                )

                reverse_return_total_dp_Pa = _add_complete_dp_v1(
                    _reverse_return_total_with_rr_added_dp_v1(
                        flow_dp_Pa=flow_dp_Pa,
                        reverse_return_dp_Pa=reverse_return_dp_Pa,
                        rr_added_pressure_drop_Pa=rr_added_pressure_drop_Pa,
                    ),
                    physical_main_entry_dp_Pa,
                )

                emitter_id = _find_emitter_id_for_room(
                    emitters,
                    room_id=str(room_id),
                )

                rows.append(
                    CircuitReturnPathComparisonRowV1(
                        room_id=str(room_id),
                        emitter_id=emitter_id,
                        route_id=f"{leg_id}:{subleg_id}",
                        route_label=subleg_label,
                        flow_section_ids=flow_section_ids,
                        direct_return_section_ids=direct_return_section_ids,
                        reverse_return_section_ids=reverse_return_section_ids,
                        flow_dp_Pa=flow_dp_Pa,
                        direct_return_dp_Pa=direct_return_dp_Pa,
                        reverse_return_dp_Pa=reverse_return_dp_Pa,
                        rr_added_length_m=rr_added_length_m,
                        rr_added_pressure_drop_Pa=rr_added_pressure_drop_Pa,
                        direct_total_dp_Pa=direct_total_dp_Pa,
                        reverse_return_total_dp_Pa=reverse_return_total_dp_Pa,
                        direct_rank=None,
                        reverse_return_rank=None,
                        rr_suitability_code=rr_suitability.code,
                        rr_suitability_status=rr_suitability.status,
                        controlling_direct=False,
                        controlling_reverse_return=False,
                        status=_return_comparison_status_v1(
                            flow_section_ids=flow_section_ids,
                            reverse_return_section_ids=reverse_return_section_ids,
                            rr_added_length_basis_mode=rr_added_length_basis_mode,
                            rr_added_length_m=rr_added_length_m,
                            rr_added_pressure_drop_Pa=rr_added_pressure_drop_Pa,
                            rr_added_length_source=rr_length_resolution.source,
                            rr_added_length_inherited_from=(
                                rr_length_resolution.inherited_from
                            ),
                            missing_upstream_length_section_ids=(
                                missing_upstream_length_section_ids
                            ),
                        ),
                        rr_added_length_basis_mode=(
                            rr_length_resolution.effective_basis_mode
                        ),
                        rr_added_length_source=rr_length_resolution.source,
                        rr_added_length_inherited_from=(
                            rr_length_resolution.inherited_from
                        ),
                        common_main_dp_Pa=common_main_dp_Pa,
                        leg_entry_dp_Pa=leg_entry_dp_Pa,
                        physical_main_entry_dp_Pa=physical_main_entry_dp_Pa,
                        missing_upstream_length_section_ids=(
                            missing_upstream_length_section_ids
                        ),
                    )
                )

    ranked_rows = _rank_circuit_pressure_totals_v1(tuple(rows))

    return CircuitReturnPathComparisonProjectionV1(
        rows=ranked_rows,
        status=(
            "Circuit return path comparison ready"
            if ranked_rows
            else "No room-carrying hydronic circuits found"
        ),
    )


def _main_entry_pressure_evidence_v1(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> tuple[float | None, float | None, tuple[str, ...]]:
    """Read route-specific H-S42-C scope totals and blockers.

    H-S51-D exposes the stable upstream section identities whenever their
    physical length / Local-K pressure evidence is incomplete.  It never
    supplies a default length, recalculates pressure or persists intent.
    """
    projection = build_route_pressure_accumulator_v1(
        project_state,
        leg_id=leg_id,
        subleg_id=subleg_id,
    )
    rows = tuple(getattr(projection, "rows", ()) or ())
    if len(rows) != 1:
        return None, None, ()
    row = rows[0]
    missing_ids = tuple(dict.fromkeys(
        str(getattr(section, "section_id", "") or "").strip()
        for section in tuple(getattr(row, "sections", ()) or ())
        if (
            str(getattr(section, "section_scope", "") or "")
            in {"common_main", "leg_entry"}
            and getattr(
                section,
                "section_total_pressure_drop_Pa",
                None,
            ) is None
            and str(getattr(section, "section_id", "") or "").strip()
        )
    ))
    return (
        row.common_main_pressure_drop_total_Pa,
        row.leg_entry_pressure_drop_total_Pa,
        missing_ids,
    )


def _add_complete_dp_v1(
    first: float | None,
    second: float | None,
) -> float | None:
    if first is None or second is None:
        return None
    return float(first) + float(second)


def _find_emitter_id_for_room(
    emitters: dict,
    *,
    room_id: str,
) -> str:
    for emitter_key, emitter in emitters.items():
        candidate_room_id = str(getattr(emitter, "room_id", "") or "")

        if candidate_room_id == room_id:
            return str(getattr(emitter, "emitter_id", "") or emitter_key)

    return ""

def _flow_section_ids_by_room(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, tuple[str, ...]]:
    """
    Build flow-side section paths for each room in a subleg.

    For a subleg route:
        room-001 -> section-001
        room-002 -> section-001, section-002
        room-003 -> section-001, section-002, section-003

    This is the F path only.
    Direct return and reverse return paths are deliberately deferred.
    """
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    sections = sorted(
        tuple(getattr(projection, "sections", ()) or ()),
        key=lambda section: int(getattr(section, "order", 0) or 0),
    )

    result: dict[str, tuple[str, ...]] = {}
    accumulated: list[str] = []

    for section in sections:
        section_id = str(getattr(section, "section_id", "") or "")
        to_room_id = str(getattr(section, "to_room_id", "") or "")

        if not section_id or not to_room_id:
            continue

        accumulated.append(section_id)
        result[to_room_id] = tuple(accumulated)

    return result

def _subleg_room_ids(subleg: Any) -> tuple[str, ...]:
    """
    Return room ids carried by a hydronic subleg.

    Current HydronicSublegV1 uses route_room_ids.
    Other names are tolerated to keep the projection resilient
    while topology DTOs settle.
    """
    for field_name in (
        "route_room_ids",
        "room_ids",
        "rooms",
        "room_sequence",
        "terminal_room_ids",
    ):
        value = getattr(subleg, field_name, None)

        if not value:
            continue

        result: list[str] = []

        for item in value:
            if isinstance(item, str):
                result.append(item)
            else:
                room_id = (
                    getattr(item, "room_id", None)
                    or getattr(item, "id", None)
                )
                if room_id:
                    result.append(str(room_id))

        if result:
            return tuple(result)

    return ()

def _appraise_reverse_return_suitability_v1(
    subleg: Any,
    *,
    room_ids: tuple[str, ...],
) -> ReverseReturnSuitabilityV1:
    """
    H-S19-D:
    Appraise whether reverse return is suitable for this ordered group.

    This does not generate reverse-return paths.
    It only classifies whether RR comparison is meaningful.

    v1 principle:
    - reverse return is valid for an appraised ordered group;
    - nested sublegs/branches are not automatically rejected;
    - nested/grouped routes require separate appraisal unless explicitly handled.
    """
    if len(room_ids) < 2:
        return ReverseReturnSuitabilityV1(
            suitable=False,
            code="single-emitter-not-useful",
            status="RR unavailable — single emitter group",
        )

    nested_sublegs = tuple(getattr(subleg, "sublegs", ()) or ())

    if nested_sublegs:
        return ReverseReturnSuitabilityV1(
            suitable=False,
            code="nested-subleg-requires-separate-appraisal",
            status="RR requires appraisal — nested subleg/grouped route",
        )

    return ReverseReturnSuitabilityV1(
        suitable=True,
        code="ordered-subleg",
        status="RR comparable — ordered subleg",
    )

def _reverse_return_section_ids_by_room(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, tuple[str, ...]]:
    """
    Build provisional reverse-return section paths for each room.

    For an ordered subleg route:
        room-001 -> section-001, section-002, section-003
        room-002 -> section-002, section-003
        room-003 -> section-003

    This is only a path-ID comparison scaffold.
    It does not yet create separate physical return pipe DTOs.
    It must only be used after RR suitability appraisal says the group is comparable.
    """
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    sections = sorted(
        tuple(getattr(projection, "sections", ()) or ()),
        key=lambda section: int(getattr(section, "order", 0) or 0),
    )

    result: dict[str, tuple[str, ...]] = {}

    for index, section in enumerate(sections):
        to_room_id = str(getattr(section, "to_room_id", "") or "")

        if not to_room_id:
            continue

        result[to_room_id] = tuple(
            str(getattr(item, "section_id", "") or "")
            for item in sections[index:]
            if str(getattr(item, "section_id", "") or "")
        )

    return result

def _section_total_dp_by_id(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, float | None]:
    """
    Build section_id -> section total Δp lookup.

    Uses the existing H-S17 route pressure accumulator because it already
    composes Basic PS + Local K pressure preview into per-section totals.

    Preview-only.
    """
    try:
        projection = build_route_pressure_accumulator_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    result: dict[str, float | None] = {}

    for route_row in getattr(projection, "rows", ()) or ():
        for section in getattr(route_row, "sections", ()) or ():
            section_id = str(getattr(section, "section_id", "") or "")

            if not section_id:
                continue

            value = getattr(section, "section_total_pressure_drop_Pa", None)

            if value is None:
                result[section_id] = None
                continue

            try:
                result[section_id] = float(value)
            except (TypeError, ValueError):
                result[section_id] = None

    return result

def _section_length_by_id(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, float | None]:
    """
    H-S29-K:
    Build section_id -> length lookup for RR added-length basis modes.

    Uses the same Local K / section-length authority as route pressure.
    Preview only.
    """
    try:
        projection = build_basic_ps_topology_sections_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    result: dict[str, float | None] = {}

    for section in getattr(projection, "sections", ()) or ():
        section_id = str(getattr(section, "section_id", "") or "")

        if not section_id:
            continue

        value = _local_k_section_length_m_v1(
            project_state,
            section_id=section_id,
        )

        if value is None:
            result[section_id] = None
            continue

        try:
            result[section_id] = max(float(value), 0.0)
        except (TypeError, ValueError):
            result[section_id] = None

    return result


def _resolve_route_rr_added_length_basis_v1(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
    parent_subleg_id: str = "",
) -> EffectiveRRAddedLengthBasisV1:
    """Resolve the single effective RR length basis for one route.

    H-S38-A3 consumes the H-S38-A1 hierarchy without combining values
    from System, Leg, Common and Branch scopes.
    """
    intent = getattr(
        project_state,
        "hydronic_return_arrangement_intent",
        None,
    )
    return resolve_subleg_rr_added_length_basis_v1(
        intent,
        leg_id=leg_id,
        subleg_id=subleg_id,
        parent_subleg_id=parent_subleg_id,
    )


def _rr_added_length_basis_mode(project_state: Any) -> str:
    """
    H-S29-K / H-S29-M1:
    Choose how RR extra/additional length is interpreted.

    Authority order:
    1) return-arrangement intent field
    2) temporary legacy ProjectState attributes, for dev tolerance
    3) safe default: physical_loop_zero_extra

    Default is physical_loop_zero_extra so a good/perfect perimeter
    reverse-return loop is not penalised with invented extra pipe.
    """

    def normalise(raw_value: Any) -> str | None:
        if raw_value is None:
            return None

        value = (
            str(raw_value)
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if value in {
            "physical_loop",
            "physical_loop_zero_extra",
            "perfect_rr",
            "perfect_rr_loop",
            "loop_zero_extra",
            "zero_extra",
            "none",
            "no_extra",
        }:
            return "physical_loop_zero_extra"

        if value in {
            "downstream",
            "downstream_proxy",
            "derived_downstream",
            "downstream_allowance",
        }:
            return "downstream_proxy"

        if value in {
            "manual",
            "manual_allowance",
            "manual_length",
            "manual_extra",
        }:
            return "manual_allowance"

        return None

    intent = getattr(
        project_state,
        "hydronic_return_arrangement_intent",
        None,
    )

    intent_mode = normalise(
        getattr(intent, "rr_added_length_basis_mode", None)
    )

    if intent_mode is not None:
        return intent_mode

    for attr_name in (
        "hydronic_rr_added_length_basis_mode",
        "hydronic_reverse_return_added_length_basis_mode",
        "rr_added_length_basis_mode",
    ):
        project_mode = normalise(getattr(project_state, attr_name, None))

        if project_mode is not None:
            return project_mode

    return "physical_loop_zero_extra"


def _rr_added_length_for_row_v1(
    *,
    project_state: Any,
    basis_mode: str,
    section_length_by_id: dict[str, float | None],
    reverse_return_section_ids: tuple[str, ...],
    manual_added_length_m: float | None = None,
) -> float:
    """
    H-S29-K / H-S38-A3:
    Calculate the RR extra/additional length for one comparison row.

    physical_loop_zero_extra:
        Perfect/represented RR loop. No extra allowance.

    downstream_proxy:
        Provisional retrofit/proxy allowance. Uses downstream section
        lengths after the current room.

    manual_allowance:
        Existing hidden H-S29-I hook. UI/manual entry comes later.
    """
    mode = str(basis_mode or "").strip().lower()

    if mode == "downstream_proxy":
        return _downstream_proxy_rr_added_length_m_v1(
            reverse_return_section_ids=reverse_return_section_ids,
            section_length_by_id=section_length_by_id,
        )

    if mode == "manual_allowance":
        if manual_added_length_m is not None:
            try:
                return max(float(manual_added_length_m), 0.0)
            except (TypeError, ValueError):
                return 0.0
        # Backward-compatible H-S29 helper behaviour for direct calls.
        return _rr_added_length_m(project_state)

    return 0.0


def _downstream_proxy_rr_added_length_m_v1(
    *,
    reverse_return_section_ids: tuple[str, ...],
    section_length_by_id: dict[str, float | None],
) -> float:
    """
    Sum downstream section lengths after the current room.

    Current reverse-return path scaffold is:
        current section + downstream sections

    Therefore the added downstream proxy excludes the first/current
    section and sums the remainder.
    """
    if len(reverse_return_section_ids) <= 1:
        return 0.0

    total = 0.0

    for section_id in reverse_return_section_ids[1:]:
        value = section_length_by_id.get(str(section_id))

        if value is None:
            continue

        try:
            total += max(float(value), 0.0)
        except (TypeError, ValueError):
            continue

    return total


def _rr_added_length_basis_label_v1(basis_mode: str) -> str:
    mode = str(basis_mode or "").strip().lower()

    if mode == "downstream_proxy":
        return "Downstream proxy allowance"

    if mode == "manual_allowance":
        return "Manual allowance"

    return "Physical loop — no extra allowance"


def _section_pressure_basis_by_id(
    project_state: Any,
    *,
    leg_id: str,
    subleg_id: str,
) -> dict[str, _RRSectionPressureBasisV1]:
    """
    Build section_id -> pressure basis for RR added-length preview.

    Uses received Basic PS pipe/flow basis only as the section authority.
    The added-length pressure is then calculated through the hydronic
    mass-flow/Colebrook wrapper.
    """
    try:
        projection = build_basic_ps_readonly_projection_v1(
            project_state,
            leg_id=leg_id,
            subleg_id=subleg_id,
        )
    except Exception:
        return {}

    result: dict[str, _RRSectionPressureBasisV1] = {}

    for row in getattr(projection.pipe_sizing_projection, "results", ()) or ():
        section_id = str(getattr(row, "section_id", "") or "")
        pipe_size_label = str(getattr(row, "pipe_size_label", "") or "")
        mass_flow = _optional_float(getattr(row, "carried_flow_kg_s", None))
        material_key = str(
            getattr(row, "material_key", "") or ""
        ).strip().lower()
        raw_size_key = getattr(row, "pipe_size_key", None)
        try:
            pipe_size_key = int(raw_size_key)
        except (TypeError, ValueError):
            pipe_size_key = 0

        if (
            not section_id
            or mass_flow is None
            or not pipe_size_label
            or not material_key
            or pipe_size_key <= 0
        ):
            continue

        result[section_id] = _RRSectionPressureBasisV1(
            mass_flow_kg_s=float(mass_flow),
            pipe_size_label=pipe_size_label,
            material_key=material_key,
            pipe_size_key=pipe_size_key,
        )

    return result


def _rr_added_length_m(project_state: Any) -> float:
    """
    H-S29-N:
    Manual RR added-length basis.

    Read the manual value from return-arrangement intent first.
    Legacy loose ProjectState attributes remain fallback only.
    """
    intent = getattr(
        project_state,
        "hydronic_return_arrangement_intent",
        None,
    )

    if isinstance(intent, dict):
        value = intent.get("rr_added_length_m")
    else:
        value = getattr(intent, "rr_added_length_m", None)

    if value is not None:
        parsed = _optional_float(value)

        if parsed is not None:
            return max(float(parsed), 0.0)

    for attr_name in (
        "hydronic_rr_added_length_m",
        "hydronic_reverse_return_added_length_m",
        "rr_added_length_m",
    ):
        value = getattr(project_state, attr_name, None)

        if value is None:
            continue

        parsed = _optional_float(value)

        if parsed is not None:
            return max(float(parsed), 0.0)

    return 0.0

def _rr_added_length_pressure_drop_Pa(
    *,
    project_state: Any,
    section_pressure_basis_by_id: dict[str, _RRSectionPressureBasisV1],
    candidate_section_ids: tuple[str, ...],
    length_m: float,
) -> float:
    """
    Calculate RR added-length pressure using H-S29-C mass-flow wrapper.

    The candidate section path supplies a flow/pipe basis. This is still
    preview evidence, not final return-pipe modelling.
    """
    if length_m <= 0.0:
        return 0.0

    basis = _first_pressure_basis_for_path_v1(
        section_pressure_basis_by_id,
        candidate_section_ids,
    )

    if basis is None or basis.mass_flow_kg_s <= 0.0:
        return 0.0

    try:
        result = calculate_hydronic_pipe_pressure_drop_from_mass_flow_v1(
            mass_flow_kg_s=float(basis.mass_flow_kg_s),
            material=basis.material_key,
            dn=basis.pipe_size_key,
            length_m=float(length_m),
            friction_method="colebrook",
        )
    except Exception:
        return 0.0

    return float(result.pressure_drop_pa or 0.0)


def _first_pressure_basis_for_path_v1(
    section_pressure_basis_by_id: dict[str, _RRSectionPressureBasisV1],
    section_ids: tuple[str, ...],
) -> _RRSectionPressureBasisV1 | None:
    for section_id in section_ids:
        basis = section_pressure_basis_by_id.get(str(section_id))

        if basis is not None:
            return basis

    return None


def _reverse_return_total_with_rr_added_dp_v1(
    *,
    flow_dp_Pa: float | None,
    reverse_return_dp_Pa: float | None,
    rr_added_pressure_drop_Pa: float,
) -> float | None:
    base = _add_optional_dp(flow_dp_Pa, reverse_return_dp_Pa)

    if base is None:
        return None

    return float(base) + max(float(rr_added_pressure_drop_Pa or 0.0), 0.0)


def _return_comparison_status_v1(
    *,
    flow_section_ids: tuple[str, ...],
    reverse_return_section_ids: tuple[str, ...],
    rr_added_length_basis_mode: str,
    rr_added_length_m: float,
    rr_added_pressure_drop_Pa: float,
    rr_added_length_source: str = "",
    rr_added_length_inherited_from: str = "",
    missing_upstream_length_section_ids: tuple[str, ...] = (),
) -> str:
    missing_ids = tuple(dict.fromkeys(
        str(section_id or "").strip()
        for section_id in tuple(missing_upstream_length_section_ids or ())
        if str(section_id or "").strip()
    ))
    upstream_blocker_prefix = (
        "Blocked — upstream physical length missing: "
        + ", ".join(missing_ids)
        + " | "
        if missing_ids
        else ""
    )
    if reverse_return_section_ids:
        base = "Flow + direct + reverse return paths ready"
        basis = _rr_added_length_basis_label_v1(rr_added_length_basis_mode)
        source = str(rr_added_length_source or "system")
        inherited = (
            f" from {rr_added_length_inherited_from}"
            if rr_added_length_inherited_from
            else ""
        )

        return (
            f"{upstream_blocker_prefix}{base} | "
            f"RR length basis: {basis}; "
            f"extra {rr_added_length_m:.2f} m adds "
            f"{rr_added_pressure_drop_Pa:.1f} Pa; "
            f"authority {source}{inherited}; "
            "one effective allowance only — no scope summing"
        )

    if flow_section_ids:
        return (
            f"{upstream_blocker_prefix}Flow + direct return path ready — "
            "reverse return not generated"
        )

    return (
        f"{upstream_blocker_prefix}Missing flow path — "
        "return paths not modelled yet"
    )


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_section_dp(
        section_dp_by_id: dict[str, float | None],
        section_ids: tuple[str, ...],
) -> float | None:
    """
    Sum section Δp values for a path.

    Returns None if any required section Δp is missing.
    """
    total = 0.0

    for section_id in section_ids:
        value = section_dp_by_id.get(section_id)

        if value is None:
            return None

        total += float(value)

    return total

def _add_optional_dp(
        first: float | None,
        second: float | None,
) -> float | None:
    if first is None or second is None:
        return None

    return float(first) + float(second)

def _rank_circuit_pressure_totals_v1(
    rows: tuple[CircuitReturnPathComparisonRowV1, ...],
) -> tuple[CircuitReturnPathComparisonRowV1, ...]:
    """
    Rank direct-return and reverse-return circuit totals separately.

    Controlling circuit = highest total pressure drop.

    Preview-only:
    - no balancing
    - no valve authority
    - no pump selection
    - no committed return arrangement
    """
    direct_rank_by_key = _rank_rows_by_total_dp(
        rows,
        total_attr="direct_total_dp_Pa",
    )

    reverse_rank_by_key = _rank_rows_by_total_dp(
        rows,
        total_attr="reverse_return_total_dp_Pa",
    )

    ranked: list[CircuitReturnPathComparisonRowV1] = []

    for row in rows:
        row_key = _circuit_row_key(row)

        direct_rank = direct_rank_by_key.get(row_key)
        reverse_rank = reverse_rank_by_key.get(row_key)

        ranked.append(
            replace(
                row,
                direct_rank=direct_rank,
                reverse_return_rank=reverse_rank,
                controlling_direct=(direct_rank == 1),
                controlling_reverse_return=(reverse_rank == 1),
            )
        )

    return tuple(ranked)


def _rank_rows_by_total_dp(
    rows: tuple[CircuitReturnPathComparisonRowV1, ...],
    *,
    total_attr: str,
) -> dict[str, int]:
    complete_rows = [
        row
        for row in rows
        if getattr(row, total_attr, None) is not None
    ]

    sorted_rows = sorted(
        complete_rows,
        key=lambda row: float(getattr(row, total_attr) or 0.0),
        reverse=True,
    )

    return {
        _circuit_row_key(row): rank
        for rank, row in enumerate(sorted_rows, start=1)
    }


def _circuit_row_key(row: CircuitReturnPathComparisonRowV1) -> str:
    return "|".join(
        (
            str(row.route_id),
            str(row.room_id),
            str(row.emitter_id),
        )
    )