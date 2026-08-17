from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.constructions.physics.u_value_teaching_models_v1 import TWO_PATH_MODEL_ID
from HVAC.gui_v3.panels.uvp_panel import UVPPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = UVPPanel(SimpleNamespace(project_state=None))
    panel.set_teaching_workspace_expanded(True)
    panel.set_teaching_model(TWO_PATH_MODEL_ID)

    spins = (
        panel._member_width_mm,
        panel._member_centres_mm,
        panel._member_declared_fraction,
    )
    widths = {spin.width() for spin in spins}
    assert len(widths) == 1
    width = widths.pop()
    assert 150 <= width <= 180
    for spin in spins:
        assert spin.minimumWidth() == spin.maximumWidth() == width

    assert panel._member_width_mm.value() == 38.0
    assert panel._member_centres_mm.value() == 600.0
    assert panel._member_declared_fraction.value() == 15.0
    basis_hint = panel._member_fraction_basis.sizeHint().width()
    assert basis_hint < 420
    assert basis_hint > width

    before = panel.teaching_candidate_evidence()
    panel._on_apply_member_spacing()
    after = panel.teaching_candidate_evidence()
    assert before.paths == after.paths
    app.processEvents()
    print(
        "OK — U-S5D3C3 member width, centres and declared-fraction "
        "spin boxes are compact without changing candidate authority."
    )


if __name__ == "__main__":
    main()
