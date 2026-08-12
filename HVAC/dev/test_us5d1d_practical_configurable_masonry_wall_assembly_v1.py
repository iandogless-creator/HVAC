from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    DECLARED_RESISTANCE_LAYER_BASIS,
    HOMOGENEOUS_LAYER_BASIS,
    validate_shared_construction_layer_path_evidence_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    CAVITY_WALL_MODEL_ID,
    teaching_model_by_id_v1,
)


def _include(evidence, layer_id: str, included: bool):
    return replace(
        evidence,
        layers=tuple(
            replace(layer, included=included)
            if layer.layer_id == layer_id
            else layer
            for layer in evidence.layers
        ),
    )


def main() -> None:
    model = teaching_model_by_id_v1(CAVITY_WALL_MODEL_ID)
    evidence = model.evidence
    expected_ids = (
        "cavity-plaster",
        "inner-leaf",
        "cavity-insulation",
        "residual-air-cavity",
        "outer-leaf",
    )
    assert evidence.paths[0].layer_ids == expected_ids
    assert evidence.active_path_layer_ids("masonry-cavity-path") == expected_ids

    layers = evidence.layer_by_id()
    assert layers["cavity-plaster"].thickness_m == 0.013
    assert layers["inner-leaf"].thickness_m == 0.100
    assert layers["cavity-insulation"].thickness_m == 0.100
    assert layers["outer-leaf"].thickness_m == 0.1025
    assert all(
        layers[layer_id].basis == HOMOGENEOUS_LAYER_BASIS
        for layer_id in expected_ids
        if layer_id != "residual-air-cavity"
    )

    cavity = layers["residual-air-cavity"]
    assert cavity.basis == DECLARED_RESISTANCE_LAYER_BASIS
    assert cavity.thickness_m == 0.050
    assert cavity.declared_resistance_m2K_W == 0.18
    assert cavity.conductivity_W_mK is None
    assert "conductivity is not applicable" in cavity.property_notes

    default_validation = validate_shared_construction_layer_path_evidence_v1(
        evidence
    )
    assert default_validation.ready, default_validation.blockers
    default_result = resolve_iso_6946_combined_u_value_v1(evidence)
    assert default_result.ready, default_result.blockers

    full_fill_candidate = _include(
        evidence, "residual-air-cavity", False
    )
    full_fill_validation = validate_shared_construction_layer_path_evidence_v1(
        full_fill_candidate
    )
    assert full_fill_validation.ready, full_fill_validation.blockers
    assert full_fill_candidate.layer_by_id()[
        "residual-air-cavity"
    ].thickness_m == 0.050

    empty_cavity_candidate = _include(
        evidence, "cavity-insulation", False
    )
    empty_validation = validate_shared_construction_layer_path_evidence_v1(
        empty_cavity_candidate
    )
    assert empty_validation.ready, empty_validation.blockers
    assert empty_cavity_candidate.layer_by_id()[
        "cavity-insulation"
    ].thickness_m == 0.100

    no_plaster_candidate = _include(evidence, "cavity-plaster", False)
    assert validate_shared_construction_layer_path_evidence_v1(
        no_plaster_candidate
    ).ready

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        source = Path(
            "HVAC/constructions/physics/u_value_teaching_models_v1.py"
        ).read_text(encoding="utf-8")
        assert "partial-fill masonry cavity wall" in source
        assert "Residual unventilated air cavity" in source
        print(
            "OK — U-S5D1D configurable masonry wall assembly and declared "
            "air-cavity resistance passed (source boundary; Qt unavailable)."
        )
        return

    from types import SimpleNamespace

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(CAVITY_WALL_MODEL_ID)
    panel._teaching_schematic.focus_item("layer", "residual-air-cavity")
    assert panel._layer_basis_combo.currentData() == (
        DECLARED_RESISTANCE_LAYER_BASIS
    )
    assert panel._layer_thickness_edit.text() == "50"
    assert panel._layer_declared_r_edit.text() == "0.18"
    assert not panel._layer_conductivity_edit.isEnabled()
    assert panel._layer_included_check.isChecked()

    panel._layer_included_check.setChecked(False)
    panel._on_apply_focused_layer_properties()
    live = panel.teaching_candidate_evidence().layer_by_id()[
        "residual-air-cavity"
    ]
    assert not live.included
    assert live.thickness_m == 0.050
    assert live.declared_resistance_m2K_W == 0.18

    print(
        "OK — U-S5D1D practical partial-fill masonry assembly supports "
        "partial-fill, full-fill, empty-cavity and no-plaster candidates."
    )


if __name__ == "__main__":
    main()
