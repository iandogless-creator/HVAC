from __future__ import annotations

from pathlib import Path


def main() -> None:
    source = Path("HVAC/gui_v3/main_window.py").read_text(
        encoding="utf-8"
    )
    menu_start = source.index("    def _build_menu(self) -> None:")
    menu_end = source.index("    # ------------------------------------------------------------------", menu_start)
    menu_source = source[menu_start:menu_end]

    assert 'menubar.addMenu("Project")' not in menu_source
    assert 'QAction("Run Heat-Loss", self)' not in menu_source
    assert 'menubar.addMenu("File")' in menu_source
    assert 'menubar.addMenu("View")' in menu_source
    assert 'menubar.addMenu("Help")' in menu_source

    # Removing the duplicate menu must not remove the existing run route.
    assert "def _run_heatloss_project_action" in source

    print(
        "OK — H-S69-B3H removes the redundant top-level Project menu "
        "while retaining File, View, Help and the existing Heat-Loss run route."
    )


if __name__ == "__main__":
    main()
