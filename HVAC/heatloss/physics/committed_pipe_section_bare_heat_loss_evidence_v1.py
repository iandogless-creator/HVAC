# ======================================================================
# H-S66-E — Committed pipe-section bare heat-loss evidence
# ======================================================================

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from HVAC.heatloss.physics.bare_pipe_section_heat_loss_evidence_v1 import (
    BarePipeSectionHeatLossEvidenceV1,
    build_bare_pipe_section_heat_loss_evidence_v1,
)
from HVAC.heatloss.physics.bare_pipe_thermal_condition_basis_v1 import (
    BarePipeThermalConditionBasisV1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionBareHeatLossEvidenceRowV1:
    """Read-only bare-pipe loss evidence for one committed section."""

    section_id: str
    section_scope: str
    route_ids: tuple[str, ...]
    order: int
    from_label: str
    to_label: str
    pipe_size_label: str
    material_key: str
    material_label: str
    catalogue_size_key: int
    actual_outside_diameter_mm: float
    length_m: float
    surface_temperature_C: float
    ambient_air_temperature_C: float
    mean_radiant_temperature_C: float
    emissivity: float
    external_convection_coefficient_W_m2K: float
    exposed_area_m2: float
    convection_heat_loss_W_per_m: float
    radiation_heat_loss_W_per_m: float
    total_heat_loss_W_per_m: float
    convection_heat_loss_W: float
    radiation_heat_loss_W: float
    total_heat_loss_W: float
    ready: bool
    status: str


@dataclass(frozen=True, slots=True)
class CommittedPipeSectionBareHeatLossEvidenceV1:
    """Deterministic evidence across the unique committed pipe sections."""

    schema: str = "committed_pipe_section_bare_heat_loss_evidence_v1"
    ready: bool = False
    sections: tuple[CommittedPipeSectionBareHeatLossEvidenceRowV1, ...] = ()
    section_count: int = 0
    status: str = "Committed pipe-section bare heat-loss evidence not ready"
    blockers: tuple[str, ...] = ()
    note: str = (
        "Unique committed sections and explicit external thermal conditions "
        "only — no route aggregation, insulation, water-temperature decay, "
        "hydraulic mutation or persistence."
    )


def build_committed_pipe_section_bare_heat_loss_evidence_v1(
        *,
        committed_authority: CommittedProportioningHydraulicInputAuthorityV1,
        thermal_basis_by_section_id: Mapping[
            str, BarePipeThermalConditionBasisV1
        ],
) -> CommittedPipeSectionBareHeatLossEvidenceV1:
    """Calculate each unique committed section against its explicit basis."""

    blockers: list[str] = []
    if not isinstance(
        committed_authority,
        CommittedProportioningHydraulicInputAuthorityV1,
    ):
        return _blocked_v1(
            "Committed proportioning hydraulic-input authority is required"
        )
    if not committed_authority.ready:
        blockers.append(
            "Committed proportioning hydraulic-input authority is not ready"
        )

    committed_sections = tuple(committed_authority.sections or ())
    if not committed_sections:
        blockers.append("Committed pipe sections are required")

    source_by_id: dict[str, Any] = {}
    for source in committed_sections:
        section_id = str(getattr(source, "section_id", "") or "").strip()
        if not section_id:
            blockers.append("Every committed pipe section requires section_id")
            continue
        if section_id in source_by_id:
            blockers.append(f"Duplicate committed section identity: {section_id}")
            continue
        source_by_id[section_id] = source

    basis_by_id: dict[str, BarePipeThermalConditionBasisV1] = {}
    if not isinstance(thermal_basis_by_section_id, Mapping):
        blockers.append("Section thermal-condition basis mapping is required")
    else:
        for raw_section_id, basis in thermal_basis_by_section_id.items():
            if not isinstance(raw_section_id, str) or not raw_section_id.strip():
                blockers.append(
                    "Every thermal-condition basis requires section_id"
                )
                continue
            section_id = raw_section_id.strip()
            if section_id != raw_section_id:
                blockers.append(
                    f"Thermal-condition section identity is not canonical: "
                    f"{raw_section_id!r}"
                )
                continue
            if not isinstance(basis, BarePipeThermalConditionBasisV1):
                blockers.append(
                    f"{section_id}: explicit bare-pipe thermal-condition "
                    "basis is required"
                )
                continue
            basis_by_id[section_id] = basis

    committed_ids = set(source_by_id)
    basis_ids = set(basis_by_id)
    for section_id in sorted(committed_ids - basis_ids):
        blockers.append(
            f"{section_id}: explicit bare-pipe thermal-condition basis missing"
        )
    for section_id in sorted(basis_ids - committed_ids):
        blockers.append(
            f"{section_id}: thermal-condition basis has no committed section"
        )

    clean_blockers = _unique_v1(blockers)
    if clean_blockers:
        return _blocked_v1(*clean_blockers)

    rows: list[CommittedPipeSectionBareHeatLossEvidenceRowV1] = []
    for section_id, source in source_by_id.items():
        try:
            section_evidence = (
                build_bare_pipe_section_heat_loss_evidence_v1(
                    section_id=section_id,
                    material_key=getattr(source, "material_key", ""),
                    catalogue_size_key=int(getattr(source, "dn")),
                    length_m=float(getattr(source, "length_m")),
                    thermal_basis=basis_by_id[section_id],
                )
            )
            rows.append(_row_v1(source, section_evidence))
        except (TypeError, ValueError) as exc:
            blockers.append(f"{section_id}: {exc}")

    clean_blockers = _unique_v1(blockers)
    if clean_blockers:
        return _blocked_v1(*clean_blockers)

    ordered_rows = tuple(
        sorted(rows, key=lambda row: (row.order, row.section_id))
    )
    return CommittedPipeSectionBareHeatLossEvidenceV1(
        ready=True,
        sections=ordered_rows,
        section_count=len(ordered_rows),
        status=(
            "Ready — committed pipe-section bare heat-loss evidence "
            "calculated"
        ),
        blockers=(),
    )


def _row_v1(
        source: Any,
        evidence: BarePipeSectionHeatLossEvidenceV1,
) -> CommittedPipeSectionBareHeatLossEvidenceRowV1:
    return CommittedPipeSectionBareHeatLossEvidenceRowV1(
        section_id=evidence.section_id,
        section_scope=str(getattr(source, "section_scope", "") or ""),
        route_ids=tuple(getattr(source, "route_ids", ()) or ()),
        order=int(getattr(source, "order")),
        from_label=str(getattr(source, "from_label", "") or ""),
        to_label=str(getattr(source, "to_label", "") or ""),
        pipe_size_label=str(
            getattr(source, "pipe_size_label", "") or ""
        ),
        material_key=evidence.material_key,
        material_label=evidence.material_label,
        catalogue_size_key=evidence.catalogue_size_key,
        actual_outside_diameter_mm=evidence.actual_outside_diameter_mm,
        length_m=evidence.length_m,
        surface_temperature_C=evidence.surface_temperature_C,
        ambient_air_temperature_C=evidence.ambient_air_temperature_C,
        mean_radiant_temperature_C=evidence.mean_radiant_temperature_C,
        emissivity=evidence.emissivity,
        external_convection_coefficient_W_m2K=(
            evidence.external_convection_coefficient_W_m2K
        ),
        exposed_area_m2=evidence.exposed_area_m2,
        convection_heat_loss_W_per_m=(
            evidence.convection_heat_loss_W_per_m
        ),
        radiation_heat_loss_W_per_m=(
            evidence.radiation_heat_loss_W_per_m
        ),
        total_heat_loss_W_per_m=evidence.total_heat_loss_W_per_m,
        convection_heat_loss_W=evidence.convection_heat_loss_W,
        radiation_heat_loss_W=evidence.radiation_heat_loss_W,
        total_heat_loss_W=evidence.total_heat_loss_W,
        ready=evidence.ready,
        status=evidence.status,
    )


def _blocked_v1(
        *blockers: str,
) -> CommittedPipeSectionBareHeatLossEvidenceV1:
    clean = _unique_v1(blockers)
    return CommittedPipeSectionBareHeatLossEvidenceV1(
        ready=False,
        sections=(),
        section_count=0,
        status="Blocked — " + "; ".join(clean),
        blockers=clean,
    )


def _unique_v1(values: Any) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)
