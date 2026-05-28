# ======================================================================
# HVAC/dev/test_basic_ps_readonly_projection.py
# ======================================================================

from __future__ import annotations

from HVAC.hydronics.sizing.basic_ps_readonly_projection_v1 import (
    BasicPSReadonlyProjectionV1,
)


def main() -> None:
    # H-S8-J smoke test.
    # Full project-backed test should be added once section length authority
    # is available from a deterministic DEV project fixture.
    assert BasicPSReadonlyProjectionV1 is not None

    print()
    print("==============================")
    print("Basic PS Readonly Projection Test")
    print("==============================")
    print()
    print("PASS — DTO/import smoke test")


if __name__ == "__main__":
    main()
