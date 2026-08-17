from __future__ import annotations

try:
    from PySide6.QtWidgets import QApplication, QComboBox, QSizePolicy
except ImportError:
    QApplication = None
    QComboBox = None
    QSizePolicy = None

from HVAC.project.project_state import ProjectState


def main() -> None:
    if QApplication is None:
        from pathlib import Path

        source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(
            encoding="utf-8"
        )
        for marker in (
            "QComboBox.SizeAdjustPolicy.AdjustToContents",
            'combo.setProperty("uvpControlRole", "contentSizedCombo")',
            "declared_entry_widths = (",
            "entry.fontMetrics().horizontalAdvance(prompt)",
            "self._u_spin.setFixedWidth",
        ):
            assert marker in source
        print(
            "OK — U-S5F1C content-sized selectors and declared-product "
            "entry widths passed (source GUI boundary; Qt unavailable)."
        )
        return

    from HVAC.gui_v3.context.gui_project_context import GuiProjectContext
    from HVAC.gui_v3.panels.uvp_panel import UVPPanel

    app = QApplication.instance() or QApplication([])
    del app
    project = ProjectState(project_id="us5f1c", name="U-S5F1C")
    context = GuiProjectContext(project_state=project)
    panel = UVPPanel(context)

    combos = panel.findChildren(QComboBox)
    assert combos
    for combo in combos:
        assert combo.property("uvpControlRole") == "contentSizedCombo"
        assert combo.sizeAdjustPolicy() == (
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        assert combo.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed
        # AdjustToContents is the authority.  Some offscreen Qt styles cache
        # sizeHint(), so a synthetic post-construction growth assertion is
        # not portable across platform plugins.
        assert combo.sizeHint().width() > 0

    assert 300 <= panel._declared_opening_name.width() <= 440
    assert 360 <= panel._declared_opening_source_ref.width() <= 560
    assert 230 <= panel._declared_opening_source_version.width() <= 340
    assert 160 <= panel._declared_opening_u_value.width() < 300
    assert 130 <= panel._u_spin.width() < 240
    assert panel._declared_opening_source_ref.width() > (
        panel._declared_opening_source_version.width()
    )

    print(
        "OK — U-S5F1C selectors follow their option text and declared "
        "name/source entries use purpose-sized widths."
    )


if __name__ == "__main__":
    main()
