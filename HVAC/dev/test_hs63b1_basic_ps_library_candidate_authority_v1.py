from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from HVAC.core.materials.pipe_materials_library import get_material
from HVAC.hydronics.sizing.basic_ps_pipe_sizing_v1 import (
    DEFAULT_BASIC_PS_COPPER_SIZE_KEYS_V1,
    DEFAULT_PIPE_CANDIDATES,
    build_default_basic_ps_copper_candidates_v1,
    size_basic_ps_section_v1,
)


def main() -> None:
    material = get_material("copper")
    assert material is not None
    assert DEFAULT_BASIC_PS_COPPER_SIZE_KEYS_V1 == (10, 15, 22, 28, 35)

    rebuilt = build_default_basic_ps_copper_candidates_v1()
    assert rebuilt == DEFAULT_PIPE_CANDIDATES
    assert [row.pipe_size_label for row in rebuilt] == [
        "10 mm",
        "15 mm",
        "22 mm",
        "28 mm",
        "35 mm",
    ]

    expected_roughness_m = float(material.roughness_mm) / 1000.0
    for size_key, candidate in zip(
        DEFAULT_BASIC_PS_COPPER_SIZE_KEYS_V1,
        rebuilt,
        strict=True,
    ):
        library_size = material.sizes[size_key]
        assert abs(
            candidate.internal_diameter_m
            - float(library_size.id_mm) / 1000.0
        ) < 1.0e-12
        assert abs(candidate.roughness_m - expected_roughness_m) < 1.0e-12

    # A low-flow section proves the default selection now consumes the
    # authoritative 10 mm OD / 8.8 mm bore rather than the former 10 mm bore.
    section = SimpleNamespace(
        section_id="section-low-flow",
        order=1,
        from_label="Boiler / Heat Source",
        to_room_label="Room 1",
        carried_heat_W=840.0,
        carried_flow_kg_s=0.01,
        is_index_room=False,
        is_terminal=True,
    )
    selected = size_basic_ps_section_v1(section)
    assert selected.pipe_size_label == "10 mm"
    assert abs(selected.internal_diameter_m - 0.0088) < 1.0e-12
    assert selected.velocity_m_s <= selected.applied_max_velocity_m_s
    assert selected.pressure_gradient_Pa_per_m > 0.0

    source = Path(
        "HVAC/hydronics/sizing/basic_ps_pipe_sizing_v1.py"
    ).read_text(encoding="utf-8")
    assert 'BasicPSPipeCandidateV1("10 mm", 0.0100)' not in source
    assert 'get_material("copper")' in source

    print(
        "OK — H-S63-B1 Basic PS copper candidates use shared bore and "
        "roughness authority."
    )


if __name__ == "__main__":
    main()
