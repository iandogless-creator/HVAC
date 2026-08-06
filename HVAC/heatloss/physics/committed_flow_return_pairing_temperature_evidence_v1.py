# ======================================================================
# H-S66-N2B — Committed flow/return pairing, order and temperature evidence
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.heatloss.physics.committed_pipe_external_arrangement_authority_v1 import (
    CommittedPipeExternalArrangementAuthorityV1,
    SEPARATE_PIPE_V1,
    STACKED_FLOW_RETURN_PAIR_V1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


FLOW_PIPE_V1 = "flow"
RETURN_PIPE_V1 = "return"
NOT_SET_UPPER_PIPE_ROLE_V1 = "not_set"
UPPER_POSITION_V1 = "upper"
LOWER_POSITION_V1 = "lower"
DORMANT_POSITION_V1 = "dormant"


@dataclass(frozen=True, slots=True)
class CommittedFlowReturnPairingTemperatureRowV1:
    """Pairing/order/temperature evidence for one exact committed section."""

    section_id: str
    section_scope: str
    order: int
    external_arrangement: str
    paired: bool
    material_key: str
    material_label: str
    catalogue_size_key: int
    actual_outside_diameter_mm: float
    upper_pipe_role: str | None
    lower_pipe_role: str | None
    flow_pipe_vertical_position: str
    return_pipe_vertical_position: str
    flow_pipe_surface_temperature_C: float
    return_pipe_surface_temperature_C: float
    vertical_order_source: str
    temperature_source: str
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedFlowReturnPairingTemperatureEvidenceV1:
    """Non-mutating evidence for later separate/stacked convection physics."""

    schema: str = "committed_flow_return_pairing_temperature_evidence_v1"
    ready: bool = False
    sections: tuple[CommittedFlowReturnPairingTemperatureRowV1, ...] = ()
    section_count: int = 0
    stacked_section_count: int = 0
    separate_section_count: int = 0
    status: str = "Committed flow/return pairing evidence not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Exact committed section and external-arrangement evidence only. "
        "Flow/return design temperatures are retained separately as v1 "
        "no-temperature-decay pipe-surface proxies. Stacked vertical order "
        "must be explicit; separate pipework has no pair order. No convection "
        "coefficient, plume interaction, spacing correction or heat loss is "
        "calculated."
    )


def build_committed_flow_return_pairing_temperature_evidence_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        external_arrangement_authority: (
            CommittedPipeExternalArrangementAuthorityV1
        ),
        design_flow_temperature_C: object,
        design_return_temperature_C: object,
        project_upper_pipe_role: object,
        upper_pipe_role_override_by_section_id: Mapping[str, str],
) -> CommittedFlowReturnPairingTemperatureEvidenceV1:
    """Resolve exact pairing/order/temperature evidence without persistence."""

    blockers: list[str] = []
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked_v1(
            "Committed proportioning hydraulic-input authority is required"
        )
    if not isinstance(
        external_arrangement_authority,
        CommittedPipeExternalArrangementAuthorityV1,
    ):
        return _blocked_v1(
            "Committed pipe external-arrangement authority is required"
        )
    if not committed_authority.ready:
        blockers.append(
            "Committed proportioning hydraulic-input authority is not ready"
        )
    if not external_arrangement_authority.ready:
        blockers.append(
            "Committed pipe external-arrangement authority is not ready"
        )

    flow_temperature, flow_blocker = _temperature_v1(
        design_flow_temperature_C,
        "Hydronic design flow temperature",
    )
    return_temperature, return_blocker = _temperature_v1(
        design_return_temperature_C,
        "Hydronic design return temperature",
    )
    blockers.extend(value for value in (flow_blocker, return_blocker) if value)
    if (
        flow_temperature is not None
        and return_temperature is not None
        and flow_temperature <= return_temperature
    ):
        blockers.append("Hydronic design flow temperature must exceed return")

    try:
        project_role = _project_pipe_role_v1(project_upper_pipe_role)
    except ValueError as exc:
        blockers.append(str(exc))
        project_role = NOT_SET_UPPER_PIPE_ROLE_V1

    if not isinstance(upper_pipe_role_override_by_section_id, Mapping):
        blockers.append(
            "Stacked-section upper-pipe role override mapping is required"
        )
        upper_role_overrides: dict[str, object] = {}
    else:
        upper_role_overrides = {}
        for raw_section_id, role in (
            upper_pipe_role_override_by_section_id.items()
        ):
            section_id = _text_v1(raw_section_id)
            if not section_id:
                blockers.append(
                    "Every stacked-section upper-pipe role override requires "
                    "section_id"
                )
            elif section_id in upper_role_overrides:
                blockers.append(
                    "Duplicate stacked-section upper-pipe role override: "
                    f"{section_id}"
                )
            else:
                upper_role_overrides[section_id] = role

    committed_by_id = _unique_rows_by_section_id_v1(
        committed_authority.sections,
        "committed hydraulic section",
        blockers,
    )
    arrangement_by_id = _unique_rows_by_section_id_v1(
        external_arrangement_authority.sections,
        "external-arrangement section",
        blockers,
    )
    committed_ids = set(committed_by_id)
    arrangement_ids = set(arrangement_by_id)
    for section_id in sorted(committed_ids - arrangement_ids):
        blockers.append(
            f"{section_id}: committed external arrangement is required"
        )
    for section_id in sorted(arrangement_ids - committed_ids):
        blockers.append(
            f"{section_id}: external arrangement has no committed section"
        )

    stacked_ids = {
        section_id
        for section_id, row in arrangement_by_id.items()
        if _text_v1(getattr(row, "external_arrangement", ""))
        == STACKED_FLOW_RETURN_PAIR_V1
    }
    separate_ids = {
        section_id
        for section_id, row in arrangement_by_id.items()
        if _text_v1(getattr(row, "external_arrangement", ""))
        == SEPARATE_PIPE_V1
    }
    invalid_arrangement_ids = arrangement_ids - stacked_ids - separate_ids
    for section_id in sorted(invalid_arrangement_ids):
        blockers.append(
            f"{section_id}: committed external arrangement is unsupported"
        )

    supplied_override_ids = set(upper_role_overrides)
    for section_id in sorted(supplied_override_ids - stacked_ids):
        if section_id in separate_ids:
            blockers.append(
                f"{section_id}: upper-pipe role override is dormant for "
                "separate pipework"
            )
        else:
            blockers.append(
                f"{section_id}: upper-pipe role override has no committed "
                "stacked section"
            )

    normalised_overrides: dict[str, str] = {}
    for section_id in sorted(stacked_ids & supplied_override_ids):
        try:
            normalised_overrides[section_id] = _pipe_role_v1(
                upper_role_overrides[section_id]
            )
        except ValueError as exc:
            blockers.append(f"{section_id}: {exc}")

    effective_upper_roles: dict[str, str] = {}
    vertical_order_sources: dict[str, str] = {}
    for section_id in sorted(stacked_ids):
        if section_id in normalised_overrides:
            effective_upper_roles[section_id] = normalised_overrides[section_id]
            vertical_order_sources[section_id] = (
                "Exact committed-section upper-pipe role override"
            )
        elif project_role in {FLOW_PIPE_V1, RETURN_PIPE_V1}:
            effective_upper_roles[section_id] = project_role
            vertical_order_sources[section_id] = (
                "Project-wide explicit upper-pipe role"
            )
        else:
            blockers.append(
                f"{section_id}: project upper-pipe role is not set and no "
                "local override exists"
            )

    rows: list[CommittedFlowReturnPairingTemperatureRowV1] = []
    if not blockers and flow_temperature is not None and return_temperature is not None:
        for section_id, section in committed_by_id.items():
            arrangement_row = arrangement_by_id[section_id]
            arrangement = _text_v1(
                getattr(arrangement_row, "external_arrangement", "")
            )
            if not bool(getattr(arrangement_row, "ready", False)):
                blockers.append(
                    f"{section_id}: committed external arrangement is not ready"
                )
                continue
            if int(getattr(arrangement_row, "order", 0)) != int(
                getattr(section, "order", 0)
            ):
                blockers.append(
                    f"{section_id}: committed external-arrangement order is stale"
                )
                continue
            if _text_v1(
                getattr(arrangement_row, "section_scope", "")
            ) != _text_v1(getattr(section, "section_scope", "")):
                blockers.append(
                    f"{section_id}: committed external-arrangement scope is stale"
                )
                continue
            try:
                pipe_identity = _pipe_identity_v1(section)
            except ValueError as exc:
                blockers.append(f"{section_id}: {exc}")
                continue

            if arrangement == STACKED_FLOW_RETURN_PAIR_V1:
                upper_role = effective_upper_roles[section_id]
                lower_role = (
                    RETURN_PIPE_V1
                    if upper_role == FLOW_PIPE_V1
                    else FLOW_PIPE_V1
                )
                flow_position = (
                    UPPER_POSITION_V1
                    if upper_role == FLOW_PIPE_V1
                    else LOWER_POSITION_V1
                )
                return_position = (
                    UPPER_POSITION_V1
                    if upper_role == RETURN_PIPE_V1
                    else LOWER_POSITION_V1
                )
                paired = True
                order_source = vertical_order_sources[section_id]
                status = "Ready — stacked flow/return pairing and order resolved"
            else:
                upper_role = None
                lower_role = None
                flow_position = DORMANT_POSITION_V1
                return_position = DORMANT_POSITION_V1
                paired = False
                order_source = "Dormant — committed separate pipework"
                status = "Ready — separate flow/return pipes; pair order dormant"

            rows.append(
                CommittedFlowReturnPairingTemperatureRowV1(
                    section_id=section_id,
                    section_scope=_text_v1(
                        getattr(section, "section_scope", "")
                    ),
                    order=int(getattr(section, "order", 0)),
                    external_arrangement=arrangement,
                    paired=paired,
                    material_key=pipe_identity[0],
                    material_label=pipe_identity[1],
                    catalogue_size_key=pipe_identity[2],
                    actual_outside_diameter_mm=pipe_identity[3],
                    upper_pipe_role=upper_role,
                    lower_pipe_role=lower_role,
                    flow_pipe_vertical_position=flow_position,
                    return_pipe_vertical_position=return_position,
                    flow_pipe_surface_temperature_C=flow_temperature,
                    return_pipe_surface_temperature_C=return_temperature,
                    vertical_order_source=order_source,
                    temperature_source=(
                        "Environment hydronic design flow/return temperatures — "
                        "v1 no-temperature-decay surface proxies"
                    ),
                    ready=True,
                    status=status,
                )
            )

    clean = _unique_v1(blockers)
    if clean:
        return _blocked_v1(*clean)

    ordered_rows = tuple(sorted(rows, key=lambda row: (row.order, row.section_id)))
    return CommittedFlowReturnPairingTemperatureEvidenceV1(
        ready=True,
        sections=ordered_rows,
        section_count=len(ordered_rows),
        stacked_section_count=sum(row.paired for row in ordered_rows),
        separate_section_count=sum(not row.paired for row in ordered_rows),
        status="Ready — committed flow/return pairing, order and temperatures resolved",
        blockers=(),
    )


def _unique_rows_by_section_id_v1(
        rows: object,
        label: str,
        blockers: list[str],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for row in tuple(rows or ()):
        section_id = _text_v1(getattr(row, "section_id", ""))
        if not section_id:
            blockers.append(f"Every {label} requires section_id")
        elif section_id in result:
            blockers.append(f"Duplicate {label} identity: {section_id}")
        else:
            result[section_id] = row
    if not result:
        blockers.append(f"At least one {label} is required")
    return result


def _pipe_identity_v1(section: object) -> tuple[str, str, int, float]:
    material_key = _text_v1(getattr(section, "material_key", "")).lower()
    material = get_material(material_key)
    if material is None:
        raise ValueError("committed pipe material is unavailable")
    try:
        size_key = int(getattr(section, "dn"))
    except (TypeError, ValueError):
        raise ValueError("committed catalogue pipe size is required") from None
    size = material.sizes.get(size_key)
    if size is None:
        raise ValueError("committed catalogue pipe identity is unavailable")
    outside_diameter_mm = float(size.od_mm)
    if not math.isfinite(outside_diameter_mm) or outside_diameter_mm <= 0.0:
        raise ValueError("committed catalogue pipe outside diameter is invalid")
    return material_key, str(material.name), size_key, outside_diameter_mm


def _temperature_v1(value: object, label: str) -> tuple[float | None, str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label} is required"
    if not math.isfinite(number) or number <= -273.15:
        return None, f"{label} is invalid"
    return number, ""


def _pipe_role_v1(value: object) -> str:
    role = _text_v1(value).lower()
    if role in {FLOW_PIPE_V1, RETURN_PIPE_V1}:
        return role
    raise ValueError("upper-pipe role must be flow or return")


def _project_pipe_role_v1(value: object) -> str:
    role = _text_v1(value).lower()
    if role in {
        NOT_SET_UPPER_PIPE_ROLE_V1,
        FLOW_PIPE_V1,
        RETURN_PIPE_V1,
    }:
        return role
    raise ValueError("Project upper-pipe role must be not_set, flow or return")


def _blocked_v1(
        *blockers: str,
) -> CommittedFlowReturnPairingTemperatureEvidenceV1:
    clean = _unique_v1(blockers)
    return CommittedFlowReturnPairingTemperatureEvidenceV1(
        ready=False,
        sections=(),
        section_count=0,
        stacked_section_count=0,
        separate_section_count=0,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _text_v1(value: object) -> str:
    return str(value or "").strip()


def _unique_v1(values: object) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_text_v1(value) for value in values if _text_v1(value)))
