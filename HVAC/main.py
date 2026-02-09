"""
HVACgooee — Main Entry Point (v1 Stabilisation)

GUI intentionally disabled.

Purpose of this entry point:
    • Allow python -m HVAC.main to run cleanly
    • Enable -X importtime tracing
    • Stabilise hydronics and heat-loss v1 cores
    • Prevent legacy GUI imports from polluting v1

GUI will be reintroduced after v1 core lock-down.
"""

from __future__ import annotations


def main() -> None:
    print("HVACgooee v1 core entry — GUI disabled (stabilisation mode)")


if __name__ == "__main__":
    main()
