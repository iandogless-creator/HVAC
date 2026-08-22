from __future__ import annotations

import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from HVAC.gui_v3.panels.local_k_panel import LocalKPanel


def main() -> None:
    app = QApplication.instance() or QApplication([])
    panel = LocalKPanel()

    assert panel._section_combo.minimumWidth() == 420
    assert panel._section_combo.maximumWidth() == 720
    assert "\n" in panel._section_combo.toolTip()

    count_spins = (
        panel._bend_90,
        panel._bend_45,
        panel._tee_through,
        panel._tee_branch,
        panel._isolation_valve,
        panel._trv,
        panel._lockshield,
    )
    assert all(spin.maximumWidth() == 90 for spin in count_spins)
    assert all("\n" in spin.toolTip() for spin in count_spins)
    assert panel._misc_k.maximumWidth() == 120
    assert panel._length_m.maximumWidth() == 130
    assert "\n" in panel._misc_k.toolTip()
    assert "\n" in panel._length_m.toolTip()

    panel.set_sections([
        {
            "section_id": "SECTION-1",
            "scope": "Route section",
            "order": 1,
            "from": "Common main / leg entry",
            "to": "ROOM-1",
            "pipe": "22 mm",
            "flow": "0.1699 kg/s",
            "velocity": "0.531 m/s",
            "velocity_raw_m_s": 0.531,
            "dp_per_m": "211.8 Δp/m",
            "dp_per_m_raw": 211.8,
        }
    ])

    emitted: list[dict] = []
    panel.local_k_changed.connect(emitted.append)
    panel._bend_90.setValue(2)
    panel._length_m.setValue(5.0)

    assert emitted
    payload = emitted[-1]
    assert payload["section_id"] == "SECTION-1"
    assert payload["bend_90_count"] == 2
    assert math.isclose(payload["length_m"], 5.0)
    assert math.isclose(payload["k_total"], 1.4)
    assert "local_pressure_drop_Pa" in payload
    assert "straight_pressure_drop_Pa" in payload
    assert "section_total_pressure_drop_Pa" in payload

    print(
        "OK — H-S69-B2 keeps Local K section identity readable, compacts "
        "fitting and length inputs, adds concise hover help and preserves "
        "the live per-section intent payload."
    )


if __name__ == "__main__":
    main()
