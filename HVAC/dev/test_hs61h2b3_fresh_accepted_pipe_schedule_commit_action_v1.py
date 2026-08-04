# ======================================================================
# H-S61-H2B3 — Fresh accepted schedule enables confirmed commit action
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace

from HVAC.hydronics.proportioning.proportioned_pipe_schedule_commit_rebuild_v1 import (
    _bridge_committed_routes_to_projected_v1,
)


def _routes(*route_ids: str) -> dict[str, object]:
    return {
        route_id: SimpleNamespace(route_id=route_id)
        for route_id in route_ids
    }


def _must_block(old_ids: tuple[str, ...], projected_ids: tuple[str, ...]) -> None:
    try:
        _bridge_committed_routes_to_projected_v1(
            old_routes=_routes(*old_ids),
            projected_routes=_routes(*projected_ids),
        )
    except ValueError as exc:
        assert "do not match committed routes" in str(exc)
    else:
        raise AssertionError("Expected incompatible route identities to block")


def main() -> None:
    exact_old = _routes("leg-001:subleg-a", "leg-002:subleg-b")
    exact = _bridge_committed_routes_to_projected_v1(
        old_routes=exact_old,
        projected_routes=_routes(
            "leg-002:subleg-b",
            "leg-001:subleg-a",
        ),
    )
    assert set(exact) == set(exact_old)
    assert exact["leg-001:subleg-a"] is exact_old["leg-001:subleg-a"]

    physical_old = _routes("subleg-a", "subleg-b")
    bridged = _bridge_committed_routes_to_projected_v1(
        old_routes=physical_old,
        projected_routes=_routes(
            "leg-001:subleg-a",
            "leg-002:subleg-b",
        ),
    )
    assert tuple(bridged) == (
        "leg-001:subleg-a",
        "leg-002:subleg-b",
    )
    assert bridged["leg-001:subleg-a"] is physical_old["subleg-a"]
    assert bridged["leg-002:subleg-b"] is physical_old["subleg-b"]

    _must_block(
        ("subleg-a",),
        ("leg-001:subleg-a", "leg-002:subleg-b"),
    )
    _must_block(
        ("subleg-a", "subleg-extra"),
        ("leg-001:subleg-a",),
    )
    _must_block(
        ("subleg-a", "subleg-b"),
        ("leg-001:subleg-a", "leg-002:subleg-renamed"),
    )
    _must_block(
        ("subleg-a",),
        ("leg-001:subleg-a", "leg-002:subleg-a"),
    )

    print(
        "OK — H-S61-H2B3 fresh accepted pipe schedule canonical route "
        "identity commit readiness passed."
    )


if __name__ == "__main__":
    main()
