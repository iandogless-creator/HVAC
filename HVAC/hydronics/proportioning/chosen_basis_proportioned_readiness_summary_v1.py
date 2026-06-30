from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChosenBasisProportionedReadinessRowV1:
    item: str
    status: str


def build_chosen_basis_proportioned_readiness_summary_v1(
    *,
    has_resolved_return_arrangement_basis: bool,
    has_chosen_route_pressure_evidence: bool,
    has_chosen_basis_controlling_route: bool,
    has_chosen_basis_shortfall_preview: bool,
) -> list[ChosenBasisProportionedReadinessRowV1]:
    """
    H-S27-F chosen-basis proportioned readiness summary.

    Read-only readiness/authority summary only.

    No pump sizing.
    No valve selection.
    No pipe resizing.
    No final hydraulic result.
    No ProjectState mutation.
    """

    return [
        ChosenBasisProportionedReadinessRowV1(
            item="Return arrangement basis",
            status=(
                "Ready — resolved from accepted overrides"
                if has_resolved_return_arrangement_basis
                else "Not ready — no resolved accepted basis"
            ),
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Chosen route pressure evidence",
            status=(
                "Ready — accepted F&R/F+RR basis selected"
                if has_chosen_route_pressure_evidence
                else "Not ready — no chosen route pressure evidence"
            ),
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Controlling route",
            status=(
                "Ready — route identified from chosen Δp"
                if has_chosen_basis_controlling_route
                else "Not ready — no chosen-basis controlling route"
            ),
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Shortfall / burden preview",
            status=(
                "Ready — preliminary added Δp only"
                if has_chosen_basis_shortfall_preview
                else "Not ready — no shortfall preview"
            ),
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Final hydraulics",
            status="Not committed — preview only",
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Pump sizing",
            status="Not included",
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Valve selection",
            status="Not included",
        ),
        ChosenBasisProportionedReadinessRowV1(
            item="Pipe resizing",
            status="Not included",
        ),
    ]