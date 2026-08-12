from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.legacy_compatible_u_value_calculation_v1 import (
    resolve_legacy_compatible_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
    validate_shared_construction_layer_path_evidence_v1,
)
from HVAC.constructions.physics.u_value_teaching_models_v1 import (
    ONE_PATH_MODEL_ID,
    teaching_model_by_id_v1,
)


def main() -> None:
    original = teaching_model_by_id_v1(ONE_PATH_MODEL_ID).evidence
    plaster = original.layer_by_id()["plaster"]
    assert plaster.included
    assert plaster.thickness_m == 0.013

    legacy_with_plaster = resolve_legacy_compatible_u_value_v1(original)
    iso_with_plaster = resolve_iso_6946_combined_u_value_v1(original)
    assert legacy_with_plaster.ready, legacy_with_plaster.blockers
    assert iso_with_plaster.ready, iso_with_plaster.blockers

    excluded_plaster = replace(plaster, included=False)
    without_plaster = replace(
        original,
        layers=tuple(
            excluded_plaster if layer.layer_id == "plaster" else layer
            for layer in original.layers
        ),
    )
    assert without_plaster.active_path_layer_ids("solid-path") == ("masonry",)
    validation = validate_shared_construction_layer_path_evidence_v1(
        without_plaster
    )
    assert validation.ready, validation.blockers
    assert "Excluded candidate layer(s)" in " ".join(validation.warnings)
    legacy_without_plaster = resolve_legacy_compatible_u_value_v1(without_plaster)
    iso_without_plaster = resolve_iso_6946_combined_u_value_v1(without_plaster)
    assert legacy_without_plaster.ready, legacy_without_plaster.blockers
    assert iso_without_plaster.ready, iso_without_plaster.blockers
    assert legacy_without_plaster.u_value_W_m2K > legacy_with_plaster.u_value_W_m2K
    assert (
        iso_without_plaster.uncorrected_u_value_W_m2K
        > iso_with_plaster.uncorrected_u_value_W_m2K
    )
    assert excluded_plaster.thickness_m == 0.013

    roundtrip = SharedConstructionLayerPathEvidenceV1.from_dict(
        without_plaster.to_dict()
    )
    assert roundtrip == without_plaster
    old_payload = original.to_dict()
    for layer in old_payload["layers"]:
        layer.pop("included", None)
    assert all(
        layer.included
        for layer in SharedConstructionLayerPathEvidenceV1.from_dict(
            old_payload
        ).layers
    )

    invalid_included = replace(
        original,
        layers=tuple(
            replace(plaster, thickness_m=0.0)
            if layer.layer_id == "plaster"
            else layer
            for layer in original.layers
        ),
    )
    assert not validate_shared_construction_layer_path_evidence_v1(
        invalid_included
    ).ready

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        panel_source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        widget_source = Path(
            "HVAC/gui_v3/widgets/"
            "construction_layer_path_schematic_widget_v1.py"
        ).read_text(encoding="utf-8")
        assert "self._layer_included_check = QCheckBox(" in panel_source
        assert "included=self._layer_included_check.isChecked()" in panel_source
        assert 'label if included else f"{label}\\nNot included"' in widget_source
        assert "omitted from calculation" in widget_source
        print(
            "OK — U-S5D1A explicit layer inclusion and retained dimensions "
            "passed (physics boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(ONE_PATH_MODEL_ID)
    panel._teaching_schematic.focus_item("layer", "plaster")
    assert panel._layer_included_check.isChecked()
    assert panel._layer_thickness_edit.text() == "13"

    panel._layer_included_check.setChecked(False)
    panel._on_apply_focused_layer_properties()
    live = panel.teaching_candidate_evidence().layer_by_id()["plaster"]
    assert not live.included
    assert live.thickness_m == 0.013

    panel._layer_included_check.setChecked(True)
    panel._on_apply_focused_layer_properties()
    restored = panel.teaching_candidate_evidence().layer_by_id()["plaster"]
    assert restored.included
    assert restored.thickness_m == 0.013

    print(
        "OK — U-S5D1A explicit layer inclusion, user-entered dimensions and "
        "calculation omission passed."
    )


if __name__ == "__main__":
    main()
