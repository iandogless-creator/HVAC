from __future__ import annotations

from pathlib import Path

from HVAC.gui_v3.adapters.hydronics_schematic_panel_adapter import (
    HydronicsSchematicPanelAdapter,
)
from HVAC.gui_v3.panels.hydronics_schematic_panel import (
    HydronicsSchematicPanel,
)


# H-S36-A1 — explicit section-evidence delivery.


class _FakePanel:
    def __init__(self) -> None:
        self.rows = None

    def set_clean_proportioned_focused_section_source_rows_v1(
            self,
            rows,
    ) -> None:
        self.rows = rows


def _source_row() -> dict:
    return {
        "section_id": "leg-002-subleg-b-section-0003",
        "order": 3,
        "from": "L2B-R02",
        "to": "L2B-R03",
        "flow_kg_s": "0.0395 kg/s",
        "pipe_dn": "10 mm",
        "dp_per_m": "474.6",
        "length_m": "5.00 m",
        "k_total": "2.40",
        "section_dp": "2914.3 Pa",
        "status": "First-pass Haaland estimate",
    }


def main() -> None:
    adapter_source = Path(
        "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text()
    panel_source = Path(
        "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text()

    assert "H-S36-A1 — explicit section-evidence delivery" in adapter_source
    # H-S36-A1T — raw source-text literals.
    assert r'link_labels.append(f"{flow_text}\n{size_text}")' in adapter_source
    assert (
        r'link_labels.append(f"{flow_text}\n        self._push_clean_'
        not in adapter_source
    )
    assert (
        "        self._push_clean_proportioned_focused_section_source_rows_v1()\n\n"
        "        # --------------------------------------------------\n"
        "        # Legacy drawn topology schematic"
    ) in adapter_source
    assert "H-S36-A1: preserve stable section/route identity" in panel_source

    adapter = HydronicsSchematicPanelAdapter.__new__(
        HydronicsSchematicPanelAdapter
    )
    normalised = adapter._normalise_clean_proportioned_adapter_section_row_v1(
        _source_row()
    )

    assert normalised["section"] == "3"
    assert normalised["section_id"] == (
        "leg-002-subleg-b-section-0003"
    )
    assert normalised["route_code"] == "L2B"
    assert normalised["leg_id"] == "leg-002"
    assert normalised["subleg_id"] == "leg-002-subleg-b"
    assert normalised["route_id"] == "leg-002-subleg-b"

    panel = HydronicsSchematicPanel.__new__(HydronicsSchematicPanel)
    panel_normalised = (
        panel._normalise_clean_proportioned_section_source_row_v1(
            normalised
        )
    )

    for key in (
        "section_id",
        "route_code",
        "leg_id",
        "subleg_id",
        "route_id",
    ):
        assert panel_normalised[key] == normalised[key]

    fake_panel = _FakePanel()
    adapter._panel = fake_panel
    adapter._build_clean_proportioned_focused_section_source_rows_v1 = (
        lambda: [normalised]
    )
    adapter._push_clean_proportioned_focused_section_source_rows_v1()

    assert fake_panel.rows == [normalised]

    # H-S36-A3 — runtime section-evidence fallback.
    # A real panel already holds the enriched Basic PS snapshot even when
    # the adapter's defensive object scan has no discoverable rows.
    fallback_row = dict(normalised)
    fake_panel.rows = None
    fake_panel._proportioning_snapshot_section_rows = [fallback_row]
    adapter._build_clean_proportioned_focused_section_source_rows_v1 = (
        lambda: []
    )
    adapter._push_clean_proportioned_focused_section_source_rows_v1()

    assert fake_panel.rows == [fallback_row]

    # No explicit evidence must preserve the existing panel fallback.
    fake_panel.rows = None
    fake_panel._proportioning_snapshot_section_rows = []
    adapter._push_clean_proportioned_focused_section_source_rows_v1()

    assert fake_panel.rows is None

    print("OK — H-S36-A1 explicit section-evidence delivery passed.")


if __name__ == "__main__":
    main()
