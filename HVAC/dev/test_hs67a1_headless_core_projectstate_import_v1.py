from __future__ import annotations

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    core_initializer = root / "HVAC" / "core" / "__init__.py"
    source = core_initializer.read_text(encoding="utf-8")

    assert "PyQt" not in source
    assert "PySide" not in source
    assert "HVACSystemBuilder" not in source

    import HVAC.core
    from HVAC.core.environment_state import EnvironmentStateV1
    from HVAC.hydronics.topology.hydronic_topology_v1 import HydronicTopologyV1
    from HVAC.project.project_state import ProjectState

    assert HVAC.core.__all__ == ()
    assert EnvironmentStateV1 is not None
    assert HydronicTopologyV1 is not None
    assert ProjectState is not None

    print(
        "OK — H-S67-A1 HVAC.core is data-only and ProjectState imports "
        "without a GUI toolkit."
    )


if __name__ == "__main__":
    main()
