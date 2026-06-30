from __future__ import annotations

from HVAC.hydronics.proportioning.chosen_basis_proportioned_readiness_summary_v1 import (
    build_chosen_basis_proportioned_readiness_summary_v1,
)


def test_ready_summary_rows() -> None:
    rows = build_chosen_basis_proportioned_readiness_summary_v1(
        has_resolved_return_arrangement_basis=True,
        has_chosen_route_pressure_evidence=True,
        has_chosen_basis_controlling_route=True,
        has_chosen_basis_shortfall_preview=True,
    )

    assert len(rows) == 8

    by_item = {row.item: row.status for row in rows}

    assert by_item["Return arrangement basis"] == "Ready — resolved from accepted overrides"
    assert by_item["Chosen route pressure evidence"] == "Ready — accepted F&R/F+RR basis selected"
    assert by_item["Controlling route"] == "Ready — route identified from chosen Δp"
    assert by_item["Shortfall / burden preview"] == "Ready — preliminary added Δp only"

    assert by_item["Final hydraulics"] == "Not committed — preview only"
    assert by_item["Pump sizing"] == "Not included"
    assert by_item["Valve selection"] == "Not included"
    assert by_item["Pipe resizing"] == "Not included"


def test_not_ready_summary_rows() -> None:
    rows = build_chosen_basis_proportioned_readiness_summary_v1(
        has_resolved_return_arrangement_basis=False,
        has_chosen_route_pressure_evidence=False,
        has_chosen_basis_controlling_route=False,
        has_chosen_basis_shortfall_preview=False,
    )

    by_item = {row.item: row.status for row in rows}

    assert by_item["Return arrangement basis"] == "Not ready — no resolved accepted basis"
    assert by_item["Chosen route pressure evidence"] == "Not ready — no chosen route pressure evidence"
    assert by_item["Controlling route"] == "Not ready — no chosen-basis controlling route"
    assert by_item["Shortfall / burden preview"] == "Not ready — no shortfall preview"

    assert by_item["Final hydraulics"] == "Not committed — preview only"
    assert by_item["Pump sizing"] == "Not included"
    assert by_item["Valve selection"] == "Not included"
    assert by_item["Pipe resizing"] == "Not included"


if __name__ == "__main__":
    test_ready_summary_rows()
    test_not_ready_summary_rows()
    print("OK — H-S27-F chosen-basis proportioned readiness summary passed.")