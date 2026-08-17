from pathlib import Path


def main() -> None:
    source = Path("HVAC/gui_v3/panels/uvp_panel.py").read_text(encoding="utf-8")
    assert '"Reset to selected preset"' in source
    assert "Reset candidate to selected teaching model" not in source
    print("OK — U-S5F1F candidate reset action uses concise preset wording.")


if __name__ == "__main__":
    main()
