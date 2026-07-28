# ======================================================================
# H-S55-A — Committed-basis route proportioning result
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.proportioning.committed_basis_route_proportioning_result_v1 import (
    build_committed_basis_route_proportioning_result_v1,
)
from HVAC.hydronics.proportioning.committed_proportioning_hydraulic_input_authority_v1 import (
    CommittedProportioningHydraulicInputAuthorityV1,
    CommittedProportioningHydraulicRouteV1,
    committed_proportioning_hydraulic_input_authority_to_dict_v1,
)


def _route(
    route_id: str,
    *,
    chosen: float,
    added: float,
    controlling: bool = False,
) -> CommittedProportioningHydraulicRouteV1:
    return CommittedProportioningHydraulicRouteV1(
        route_id=route_id,
        route_label=route_id.replace("-", " ").title(),
        basis="F&R",
        chosen_pressure_drop_Pa=chosen,
        controlling=controlling,
        required_added_pressure_drop_Pa=added,
        preliminary_resistance_Pa_per_kg_s2=1.0,
        common_main_pressure_drop_Pa=1_000.0,
        leg_entry_pressure_drop_Pa=500.0,
        physical_main_entry_pressure_drop_Pa=1_500.0,
    )


def _authority(*routes, ready=True, blockers=()):
    return CommittedProportioningHydraulicInputAuthorityV1(
        ready=ready,
        routes=tuple(routes),
        status="Ready" if ready else "Blocked",
        blockers=tuple(blockers),
    )


def main() -> None:
    authority = _authority(
        _route(
            "route-controlling",
            chosen=40_000.0,
            added=0.0,
            controlling=True,
        ),
        _route("route-two", chosen=32_500.0, added=7_500.0),
        _route(
            "route-tied",
            chosen=39_999.98,
            added=0.02,
            controlling=True,
        ),
    )
    before = committed_proportioning_hydraulic_input_authority_to_dict_v1(
        authority
    )
    result = build_committed_basis_route_proportioning_result_v1(authority)

    assert result.ready is True, result.status
    assert result.controlling_target_pressure_drop_Pa == 40_000.0
    assert result.tolerance_Pa == 0.05
    assert len(result.rows) == 3
    by_id = {row.route_id: row for row in result.rows}
    assert by_id["route-two"].proportioned_pressure_drop_Pa == 40_000.0
    assert by_id["route-two"].residual_to_target_Pa == 0.0
    assert by_id["route-two"].within_tolerance is True
    assert by_id["route-controlling"].required_added_pressure_drop_Pa == 0.0
    assert by_id["route-tied"].controlling is True
    assert "No pump selection" in result.exclusions
    assert "No ProjectState mutation" in result.exclusions

    repeated = build_committed_basis_route_proportioning_result_v1(authority)
    assert repeated == result
    assert (
        committed_proportioning_hydraulic_input_authority_to_dict_v1(
            authority
        )
        == before
    )

    mismatch = build_committed_basis_route_proportioning_result_v1(
        _authority(
            _route(
                "route-controlling",
                chosen=40_000.0,
                added=0.0,
                controlling=True,
            ),
            _route("route-short", chosen=32_500.0, added=7_000.0),
        )
    )
    assert mismatch.ready is False
    assert mismatch.rows[1].proportioned_pressure_drop_Pa == 39_500.0
    assert mismatch.rows[1].residual_to_target_Pa == 500.0
    assert "does not reach" in mismatch.blockers[0]

    upstream = build_committed_basis_route_proportioning_result_v1(
        _authority(
            ready=False,
            blockers=("committed evidence incomplete",),
        )
    )
    assert upstream.ready is False
    assert upstream.blockers == (
        "H-S54-A: committed evidence incomplete",
    )

    no_controller = build_committed_basis_route_proportioning_result_v1(
        _authority(_route("route-one", chosen=10.0, added=0.0))
    )
    assert no_controller.ready is False
    assert "controlling route" in no_controller.blockers[0]

    invalid = build_committed_basis_route_proportioning_result_v1(
        _authority(
            _route(
                "route-one",
                chosen=10.0,
                added=-1.0,
                controlling=True,
            )
        )
    )
    assert invalid.ready is False
    assert "non-negative required added" in invalid.blockers[0]

    duplicate = build_committed_basis_route_proportioning_result_v1(
        _authority(
            _route(
                "route-one",
                chosen=10.0,
                added=0.0,
                controlling=True,
            ),
            _route("route-one", chosen=8.0, added=2.0),
        )
    )
    assert duplicate.ready is False
    assert "Duplicate committed route_id" in duplicate.blockers[0]

    absent = build_committed_basis_route_proportioning_result_v1(None)
    assert absent.ready is False
    assert "H-S54-A" in absent.blockers[0]

    print(
        "OK — H-S55-A committed-basis route proportioning result passed."
    )


if __name__ == "__main__":
    main()
