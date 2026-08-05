from __future__ import annotations

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    panel = (
        root / "HVAC/gui_v3/panels/hydronics_schematic_panel.py"
    ).read_text(encoding="utf-8")
    adapter = (
        root / "HVAC/gui_v3/adapters/hydronics_schematic_panel_adapter.py"
    ).read_text(encoding="utf-8")

    assert "Pending local override:" in panel
    assert "Currently effective:" in panel
    assert "not persisted until the complete basis" in panel
    assert "Pending change: remove the local override" in panel
    assert "_on_committed_pipe_emissivity_draft_changed_v1" in panel
    assert "emissivity and h conv remain explicit" not in adapter
    assert "Emissivity inherits the " in adapter
    assert "Environment default unless locally overridden" in adapter
    assert "external " in adapter and "h conv remains explicit" in adapter

    print(
        "OK — H-S66-K2 pending versus effective emissivity wording passed."
    )


if __name__ == "__main__":
    main()
