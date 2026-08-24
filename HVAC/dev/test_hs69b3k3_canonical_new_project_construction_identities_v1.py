from __future__ import annotations

from pathlib import Path

from HVAC.project_v3.project_factory_v3 import ProjectFactoryV3
from HVAC.topology.dev_topology_fabric_bridge import (
    DEFAULT_EXTERNAL_CONSTRUCTION_ID,
    DEFAULT_FLOOR_CONSTRUCTION_ID,
    DEFAULT_INTERNAL_CONSTRUCTION_ID,
    DEFAULT_ROOF_CONSTRUCTION_ID,
    _resolve_u_value,
)


def main() -> None:
    project = ProjectFactoryV3.create_default()

    expected = {
        "DEV-EXT-WALL": ("External Wall", 0.26),
        "DEV-INT-WALL": ("Internal Wall", 1.50),
        "DEV-FLOOR": ("Floor", 0.18),
        "DEV-ROOF": ("Roof / Ceiling", 0.16),
        "DEV-WINDOW": ("Window / Door", 1.60),
    }
    assert set(project.constructions) == set(expected)
    for construction_id, (name, u_value) in expected.items():
        construction = project.constructions[construction_id]
        assert construction.construction_id == construction_id
        assert construction.name == name
        assert construction.u_value_W_m2K == u_value

    topology_ids = {
        DEFAULT_EXTERNAL_CONSTRUCTION_ID,
        DEFAULT_INTERNAL_CONSTRUCTION_ID,
        DEFAULT_FLOOR_CONSTRUCTION_ID,
        DEFAULT_ROOF_CONSTRUCTION_ID,
    }
    assert topology_ids <= set(project.constructions)
    for construction_id in topology_ids:
        assert _resolve_u_value(project, construction_id) is not None

    assert not {
        "DEFAULT-WALL",
        "DEFAULT-WINDOW",
        "DEFAULT-ROOF",
    } & set(project.constructions)

    factory_source = Path(
        "HVAC/project_v3/project_factory_v3.py"
    ).read_text(encoding="utf-8")
    assert '"DEFAULT-WALL"' not in factory_source
    assert '"DEFAULT-WINDOW"' not in factory_source
    assert '"DEFAULT-ROOF"' not in factory_source

    print(
        "OK — H-S69-B3K3 creates new projects with the five established "
        "canonical construction identities and values required by topology "
        "and fabric projection, without new physics or schema change."
    )


if __name__ == "__main__":
    main()
