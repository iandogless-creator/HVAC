# ======================================================================
# H-S54-A — Committed proportioning hydraulic-input authority
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Iterable

from HVAC.core.materials.pipe_materials_library import get_material


@dataclass(frozen=True, slots=True)
class CommittedProportioningHydraulicSectionV1:
    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    order: int
    from_label: str
    to_label: str
    carried_flow_kg_s: float
    pipe_size_label: str
    dn: int
    length_m: float
    k_total: float
    velocity_m_s: float
    reynolds_number: float
    friction_factor: float
    friction_method: str
    colebrook_iteration_count: int
    colebrook_converged: bool
    pressure_gradient_Pa_per_m: float
    straight_pressure_drop_Pa: float
    local_pressure_drop_Pa: float
    section_total_pressure_drop_Pa: float
    # H-S61-H1A — exact committed pipe identity. Defaults preserve legacy
    # copper snapshots created before material-family authority existed.
    material_key: str = "copper"
    material_label: str = "Copper EN1057"
    internal_diameter_m: float | None = None
    material_roughness_m: float | None = None


@dataclass(frozen=True, slots=True)
class CommittedProportioningHydraulicRouteV1:
    route_id: str
    route_label: str
    basis: str
    chosen_pressure_drop_Pa: float
    controlling: bool
    required_added_pressure_drop_Pa: float
    preliminary_resistance_Pa_per_kg_s2: float
    common_main_pressure_drop_Pa: float | None
    leg_entry_pressure_drop_Pa: float | None
    physical_main_entry_pressure_drop_Pa: float | None


@dataclass(frozen=True, slots=True)
class CommittedProportioningHydraulicInputAuthorityV1:
    """
    Frozen numeric input evidence for later proportioned hydraulics.

    It copies already-calculated evidence. It does not recalculate friction,
    resize pipework, select a pump or valve product, choose a valve setting,
    or perform final balancing.
    """

    schema: str = "committed_proportioning_hydraulic_input_authority_v1"
    ready: bool = False
    sections: tuple[CommittedProportioningHydraulicSectionV1, ...] = ()
    routes: tuple[CommittedProportioningHydraulicRouteV1, ...] = ()
    status: str = "Committed hydraulic-input authority not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Frozen current material, pipe size, actual bore, roughness, flow, "
        "physical-length, Local-K, Colebrook and chosen-route evidence only — "
        "no recalculation or final design."
    )


def build_committed_proportioning_hydraulic_input_authority_v1(
    *,
    route_pressure_projection: Any,
    chosen_controlling_rows: Iterable[Any],
    resistance_basis: Any,
) -> CommittedProportioningHydraulicInputAuthorityV1:
    route_rows = tuple(
        getattr(route_pressure_projection, "rows", ()) or ()
    )
    chosen_rows = tuple(chosen_controlling_rows or ())
    blockers: list[str] = []

    if not route_rows:
        blockers.append("Route pressure evidence required")
    if not chosen_rows:
        blockers.append("Chosen-basis controlling-route evidence required")

    section_sources: dict[str, Any] = {}
    section_route_ids: dict[str, list[str]] = {}
    for route in route_rows:
        route_id = _text(getattr(route, "route_id", ""))
        if not route_id:
            blockers.append("Every route pressure row requires stable route_id")
            continue
        if not bool(getattr(route, "complete", False)):
            blockers.append(f"{route_id}: complete route pressure evidence required")
        for source in tuple(getattr(route, "sections", ()) or ()):
            section_id = _text(getattr(source, "section_id", ""))
            if not section_id:
                blockers.append(f"{route_id}: stable section_id required")
                continue
            existing = section_sources.get(section_id)
            if existing is not None and _section_signature(existing) != _section_signature(source):
                blockers.append(
                    f"{section_id}: conflicting duplicated section evidence"
                )
                continue
            section_sources.setdefault(section_id, source)
            members = section_route_ids.setdefault(section_id, [])
            if route_id not in members:
                members.append(route_id)

    sections: list[CommittedProportioningHydraulicSectionV1] = []
    for section_id, source in section_sources.items():
        try:
            sections.append(
                _freeze_section(
                    source,
                    route_ids=tuple(section_route_ids[section_id]),
                )
            )
        except ValueError as exc:
            blockers.append(f"{section_id}: {exc}")

    resistance_by_id = {
        _text(getattr(row, "route_id", "")): row
        for row in tuple(getattr(resistance_basis, "rows", ()) or ())
        if _text(getattr(row, "route_id", ""))
    }
    routes: list[CommittedProportioningHydraulicRouteV1] = []
    seen_routes: set[str] = set()
    for row in chosen_rows:
        route_id = _text(getattr(row, "route_id", ""))
        if not route_id:
            blockers.append("Chosen-basis row requires stable route_id")
            continue
        if route_id in seen_routes:
            blockers.append(f"Duplicate chosen-basis route: {route_id}")
            continue
        seen_routes.add(route_id)
        resistance = resistance_by_id.get(route_id)
        try:
            routes.append(_freeze_route(row, resistance))
        except ValueError as exc:
            blockers.append(f"{route_id}: {exc}")

    clean = _unique(blockers)
    ready = bool(sections) and bool(routes) and not clean
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=ready,
        sections=tuple(sections),
        routes=tuple(routes),
        status=(
            "Ready — committed numeric proportioning hydraulic-input "
            "authority frozen"
            if ready
            else "Blocked — " + "; ".join(clean)
        ),
        blockers=clean,
    )


def committed_proportioning_hydraulic_input_authority_to_dict_v1(
    authority: CommittedProportioningHydraulicInputAuthorityV1 | None,
) -> dict | None:
    if authority is None:
        return None
    return {
        "schema": authority.schema,
        "ready": bool(authority.ready),
        "sections": [
            {
                "section_id": row.section_id,
                "section_scope": row.section_scope,
                "route_ids": list(row.route_ids),
                "order": row.order,
                "from_label": row.from_label,
                "to_label": row.to_label,
                "carried_flow_kg_s": row.carried_flow_kg_s,
                "pipe_size_label": row.pipe_size_label,
                "dn": row.dn,
                "material_key": row.material_key,
                "material_label": row.material_label,
                "internal_diameter_m": row.internal_diameter_m,
                "material_roughness_m": row.material_roughness_m,
                "length_m": row.length_m,
                "k_total": row.k_total,
                "velocity_m_s": row.velocity_m_s,
                "reynolds_number": row.reynolds_number,
                "friction_factor": row.friction_factor,
                "friction_method": row.friction_method,
                "colebrook_iteration_count": row.colebrook_iteration_count,
                "colebrook_converged": row.colebrook_converged,
                "pressure_gradient_Pa_per_m": row.pressure_gradient_Pa_per_m,
                "straight_pressure_drop_Pa": row.straight_pressure_drop_Pa,
                "local_pressure_drop_Pa": row.local_pressure_drop_Pa,
                "section_total_pressure_drop_Pa": (
                    row.section_total_pressure_drop_Pa
                ),
            }
            for row in authority.sections
        ],
        "routes": [
            {
                "route_id": row.route_id,
                "route_label": row.route_label,
                "basis": row.basis,
                "chosen_pressure_drop_Pa": row.chosen_pressure_drop_Pa,
                "controlling": row.controlling,
                "required_added_pressure_drop_Pa": (
                    row.required_added_pressure_drop_Pa
                ),
                "preliminary_resistance_Pa_per_kg_s2": (
                    row.preliminary_resistance_Pa_per_kg_s2
                ),
                "common_main_pressure_drop_Pa": (
                    row.common_main_pressure_drop_Pa
                ),
                "leg_entry_pressure_drop_Pa": row.leg_entry_pressure_drop_Pa,
                "physical_main_entry_pressure_drop_Pa": (
                    row.physical_main_entry_pressure_drop_Pa
                ),
            }
            for row in authority.routes
        ],
        "status": authority.status,
        "blockers": list(authority.blockers),
        "note": authority.note,
    }


def committed_proportioning_hydraulic_input_authority_from_dict_v1(
    data: object,
) -> CommittedProportioningHydraulicInputAuthorityV1 | None:
    if not isinstance(data, dict):
        return None
    sections: list[CommittedProportioningHydraulicSectionV1] = []
    routes: list[CommittedProportioningHydraulicRouteV1] = []
    try:
        for raw in list(data.get("sections", ()) or ()):
            pipe_identity = _pipe_identity_v1(
                material_key=raw.get("material_key", "copper"),
                dn=raw.get("dn"),
                material_label=raw.get("material_label"),
                internal_diameter_m=raw.get("internal_diameter_m"),
                material_roughness_m=raw.get("material_roughness_m"),
            )
            sections.append(
                CommittedProportioningHydraulicSectionV1(
                    section_id=_required_text(raw, "section_id"),
                    section_scope=_required_text(raw, "section_scope"),
                    route_ids=tuple(
                        _text(value)
                        for value in list(raw.get("route_ids", ()) or ())
                        if _text(value)
                    ),
                    order=int(raw.get("order")),
                    from_label=_text(raw.get("from_label")),
                    to_label=_text(raw.get("to_label")),
                    carried_flow_kg_s=_positive(raw.get("carried_flow_kg_s")),
                    pipe_size_label=_required_text(raw, "pipe_size_label"),
                    dn=_positive_int(raw.get("dn")),
                    material_key=pipe_identity[0],
                    material_label=pipe_identity[1],
                    internal_diameter_m=pipe_identity[2],
                    material_roughness_m=pipe_identity[3],
                    length_m=_positive(raw.get("length_m")),
                    k_total=_non_negative(raw.get("k_total")),
                    velocity_m_s=_positive(raw.get("velocity_m_s")),
                    reynolds_number=_positive(raw.get("reynolds_number")),
                    friction_factor=_positive(raw.get("friction_factor")),
                    friction_method=_required_text(raw, "friction_method"),
                    colebrook_iteration_count=_non_negative_int(
                        raw.get("colebrook_iteration_count")
                    ),
                    colebrook_converged=bool(
                        raw.get("colebrook_converged")
                    ),
                    pressure_gradient_Pa_per_m=_positive(
                        raw.get("pressure_gradient_Pa_per_m")
                    ),
                    straight_pressure_drop_Pa=_positive(
                        raw.get("straight_pressure_drop_Pa")
                    ),
                    local_pressure_drop_Pa=_non_negative(
                        raw.get("local_pressure_drop_Pa")
                    ),
                    section_total_pressure_drop_Pa=_positive(
                        raw.get("section_total_pressure_drop_Pa")
                    ),
                )
            )
        for raw in list(data.get("routes", ()) or ()):
            routes.append(
                CommittedProportioningHydraulicRouteV1(
                    route_id=_required_text(raw, "route_id"),
                    route_label=_required_text(raw, "route_label"),
                    basis=_required_text(raw, "basis"),
                    chosen_pressure_drop_Pa=_positive(
                        raw.get("chosen_pressure_drop_Pa")
                    ),
                    controlling=bool(raw.get("controlling")),
                    required_added_pressure_drop_Pa=_non_negative(
                        raw.get("required_added_pressure_drop_Pa")
                    ),
                    preliminary_resistance_Pa_per_kg_s2=_non_negative(
                        raw.get("preliminary_resistance_Pa_per_kg_s2")
                    ),
                    common_main_pressure_drop_Pa=_optional_non_negative(
                        raw.get("common_main_pressure_drop_Pa")
                    ),
                    leg_entry_pressure_drop_Pa=_optional_non_negative(
                        raw.get("leg_entry_pressure_drop_Pa")
                    ),
                    physical_main_entry_pressure_drop_Pa=_optional_non_negative(
                        raw.get("physical_main_entry_pressure_drop_Pa")
                    ),
                )
            )
    except (TypeError, ValueError):
        return None
    return CommittedProportioningHydraulicInputAuthorityV1(
        schema=_text(
            data.get("schema")
            or "committed_proportioning_hydraulic_input_authority_v1"
        ),
        ready=bool(data.get("ready")),
        sections=tuple(sections),
        routes=tuple(routes),
        status=_text(data.get("status")),
        blockers=tuple(
            _text(value)
            for value in list(data.get("blockers", ()) or ())
            if _text(value)
        ),
        note=_text(data.get("note")),
    )


def _freeze_section(
    row: Any,
    *,
    route_ids: tuple[str, ...],
) -> CommittedProportioningHydraulicSectionV1:
    if not route_ids:
        raise ValueError("route membership required")
    if not bool(getattr(row, "colebrook_converged", False)):
        raise ValueError("converged Colebrook evidence required")
    dn = _positive_int(getattr(row, "dn", None))
    pipe_identity = _pipe_identity_v1(
        material_key=(
            getattr(row, "material_key", None)
            or getattr(row, "current_material_key", None)
            or "copper"
        ),
        dn=dn,
        material_label=(
            getattr(row, "material_label", None)
            or getattr(row, "current_material_label", None)
        ),
        internal_diameter_m=(
            getattr(row, "internal_diameter_m", None)
            or getattr(row, "current_internal_diameter_m", None)
        ),
        material_roughness_m=(
            getattr(row, "material_roughness_m", None)
            or getattr(row, "roughness_m", None)
        ),
    )
    return CommittedProportioningHydraulicSectionV1(
        section_id=_required_attr_text(row, "section_id"),
        section_scope=_required_attr_text(row, "section_scope"),
        route_ids=route_ids,
        order=int(getattr(row, "order")),
        from_label=_text(getattr(row, "from_label", "")),
        to_label=_text(getattr(row, "to_label", "")),
        carried_flow_kg_s=_positive(getattr(row, "carried_flow_kg_s", None)),
        pipe_size_label=_required_attr_text(row, "pipe_size_label"),
        dn=dn,
        material_key=pipe_identity[0],
        material_label=pipe_identity[1],
        internal_diameter_m=pipe_identity[2],
        material_roughness_m=pipe_identity[3],
        length_m=_positive(getattr(row, "length_m", None)),
        k_total=_non_negative(getattr(row, "k_total", None)),
        velocity_m_s=_positive(getattr(row, "velocity_m_s", None)),
        reynolds_number=_positive(getattr(row, "reynolds_number", None)),
        friction_factor=_positive(getattr(row, "friction_factor", None)),
        friction_method=_required_attr_text(row, "friction_method"),
        colebrook_iteration_count=_non_negative_int(
            getattr(row, "colebrook_iteration_count", None)
        ),
        colebrook_converged=True,
        pressure_gradient_Pa_per_m=_positive(
            getattr(row, "pressure_gradient_Pa_per_m", None)
        ),
        straight_pressure_drop_Pa=_positive(
            getattr(row, "straight_pressure_drop_Pa", None)
        ),
        local_pressure_drop_Pa=_non_negative(
            getattr(row, "local_pressure_drop_Pa", None)
        ),
        section_total_pressure_drop_Pa=_positive(
            getattr(row, "section_total_pressure_drop_Pa", None)
        ),
    )


def _freeze_route(
    row: Any,
    resistance: Any,
) -> CommittedProportioningHydraulicRouteV1:
    if resistance is None:
        raise ValueError("chosen-basis resistance evidence required")
    return CommittedProportioningHydraulicRouteV1(
        route_id=_required_attr_text(row, "route_id"),
        route_label=_required_attr_text(row, "route"),
        basis=_required_attr_text(row, "basis"),
        chosen_pressure_drop_Pa=_positive(
            getattr(row, "chosen_dp_pa", None)
        ),
        controlling=bool(getattr(row, "is_controlling", False)),
        required_added_pressure_drop_Pa=_named_non_negative(
            getattr(resistance, "required_added_dp", None),
            "required_added_pressure_drop_Pa",
        ),
        preliminary_resistance_Pa_per_kg_s2=_named_non_negative(
            getattr(resistance, "resistance_pa_per_kg_s2", None),
            "preliminary_resistance_Pa_per_kg_s2",
        ),
        common_main_pressure_drop_Pa=_optional_non_negative(
            getattr(row, "common_main_dp_pa", None)
        ),
        leg_entry_pressure_drop_Pa=_optional_non_negative(
            getattr(row, "leg_entry_dp_pa", None)
        ),
        physical_main_entry_pressure_drop_Pa=_optional_non_negative(
            getattr(row, "physical_main_entry_dp_pa", None)
        ),
    )


def _pipe_identity_v1(
    *,
    material_key: object,
    dn: object,
    material_label: object = None,
    internal_diameter_m: object = None,
    material_roughness_m: object = None,
) -> tuple[str, str, float, float]:
    """Resolve and validate one exact material/DN/bore/roughness identity."""
    key = _text(material_key).lower()
    material = get_material(key)
    if material is None:
        raise ValueError(f"known pipe material required: {key or '—'}")
    nominal = _positive_int(dn)
    size = material.sizes.get(nominal)
    if size is None:
        raise ValueError(
            f"material/size identity absent from library: {key} DN{nominal}"
        )

    expected_label = _text(material.name)
    supplied_label = _text(material_label)
    if supplied_label and supplied_label != expected_label:
        raise ValueError(
            f"material label does not match library: {supplied_label}"
        )

    expected_bore = float(size.id_mm) / 1000.0
    bore = (
        expected_bore
        if internal_diameter_m is None
        else _positive(internal_diameter_m)
    )
    if not math.isclose(bore, expected_bore, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError(
            f"{key} DN{nominal} internal diameter does not match library"
        )

    expected_roughness = float(material.roughness_mm) / 1000.0
    roughness = (
        expected_roughness
        if material_roughness_m is None
        else _positive(material_roughness_m)
    )
    if not math.isclose(
        roughness,
        expected_roughness,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise ValueError(
            f"{key} material roughness does not match library"
        )
    return key, expected_label, bore, roughness


def _section_signature(row: Any) -> tuple:
    names = (
        "section_scope", "order", "from_label", "to_label",
        "carried_flow_kg_s", "pipe_size_label", "dn",
        "material_key", "current_material_key",
        "internal_diameter_m", "current_internal_diameter_m",
        "material_roughness_m", "roughness_m",
        "length_m", "k_total",
        "velocity_m_s", "reynolds_number", "friction_factor",
        "friction_method", "colebrook_iteration_count",
        "colebrook_converged", "pressure_gradient_Pa_per_m",
        "straight_pressure_drop_Pa", "local_pressure_drop_Pa",
        "section_total_pressure_drop_Pa",
    )
    return tuple(getattr(row, name, None) for name in names)


def _number(value: object) -> float:
    if value is None or isinstance(value, bool):
        raise ValueError("numeric evidence required")
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        match = re.search(
            r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
            str(value).replace(",", ""),
        )
        if not match:
            raise ValueError("numeric evidence required")
        number = float(match.group(0))
    if not math.isfinite(number):
        raise ValueError("finite numeric evidence required")
    return number


def _positive(value: object) -> float:
    number = _number(value)
    if number <= 0.0:
        raise ValueError("positive numeric evidence required")
    return number


def _non_negative(value: object) -> float:
    number = _number(value)
    if number < 0.0:
        raise ValueError("non-negative numeric evidence required")
    return number


def _positive_int(value: object) -> int:
    number = int(_number(value))
    if number <= 0:
        raise ValueError("positive integer evidence required")
    return number


def _non_negative_int(value: object) -> int:
    number = int(_number(value))
    if number < 0:
        raise ValueError("non-negative integer evidence required")
    return number


def _optional_non_negative(value: object) -> float | None:
    if value is None:
        return None
    return _non_negative(value)


def _named_non_negative(value: object, name: str) -> float:
    try:
        return _non_negative(value)
    except ValueError as exc:
        raise ValueError(f"{name}: {exc}") from exc


def _text(value: object) -> str:
    return str(value or "").strip()


def _required_text(mapping: dict, name: str) -> str:
    value = _text(mapping.get(name))
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _required_attr_text(row: Any, name: str) -> str:
    value = _text(getattr(row, name, ""))
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in result:
            result.append(text)
    return tuple(result)
