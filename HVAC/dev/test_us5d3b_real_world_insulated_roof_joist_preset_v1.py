from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.constructions.physics.construction_path_heat_flow_temperature_evidence_v1 import (
    build_construction_path_heat_flow_temperature_evidence_v1,
)
from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.two_path_member_spacing_fraction_v1 import (
    resolve_two_path_member_spacing_fraction_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    ROOF_TWO_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)
from HVAC.gui_v3.panels.uvp_panel import UVPPanel


def main() -> None:
    model = teaching_model_by_id_v1(ROOF_TWO_PATH_MODEL_ID)
    evidence = model.evidence
    intent = model.member_spacing_intent
    assert intent is not None
    assert intent.member_width_m == 0.044
    assert intent.member_centres_m == 0.450
    fraction = resolve_two_path_member_spacing_fraction_v1(intent)
    assert fraction.ready, fraction.blockers
    assert abs(fraction.controlling_member_fraction - 0.044 / 0.450) < 1.0e-12

    layers = evidence.layer_by_id()
    assert layers["roof-timber-joist-layer"].thickness_m == 0.144
    assert layers["roof-timber-joist-layer"].thickness_m != intent.member_width_m
    for path in evidence.paths:
        assert "roof-over-joist-insulation" in path.layer_ids
        assert "roof-lining" in path.layer_ids
        assert "roof-deck" in path.layer_ids
    assert "roof-over-joist-insulation" in evidence.shared_layer_ids

    iso = resolve_iso_6946_combined_u_value_v1(evidence)
    assert iso.ready, iso.blockers
    profile = build_construction_path_heat_flow_temperature_evidence_v1(
        evidence,
        internal_temperature_C=21.0,
        external_temperature_C=-3.0,
    )
    assert profile.ready, profile.blockers
    assert len(profile.paths) == 2

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(ROOF_TWO_PATH_MODEL_ID)
    panel.set_heat_flow_temperature_contexts(
        [("room-001", "Roof room", 21.0, -3.0, "room override")],
        "room-001",
    )
    panel.resize(1250, 950)
    panel.show()
    app.processEvents()
    assert panel._member_width_mm.value() == 44.0
    assert panel._member_centres_mm.value() == 450.0
    assert panel._member_calculated_fraction.text() == "9.78 %"
    graph = panel._teaching_schematic._profile_graph.result()
    assert graph is not None and graph.ready
    displayed = panel.teaching_candidate_evidence()
    assert len(displayed.paths) == 2
    print(
        "OK — U-S5D3B insulated-between-joist and timber-joist paths "
        "share continuous over-joist insulation."
    )


if __name__ == "__main__":
    main()
