from __future__ import annotations

import ast
from pathlib import Path


def _save_as_source() -> tuple[str, str]:
    source = Path("HVAC/gui_v3/main_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindowV3":
            for member in node.body:
                if (
                    isinstance(member, ast.FunctionDef)
                    and member.name == "_save_project_as"
                ):
                    method_source = ast.get_source_segment(source, member)
                    assert method_source is not None
                    return source, method_source

    raise AssertionError("MainWindowV3._save_project_as was not found")


def main() -> None:
    source, method = _save_as_source()

    assert "QInputDialog" not in source
    assert '"Choose or create project folder"' in method
    assert 'default_dir = hvac_root / "HVACprojects"' in method
    assert "str(default_dir)" in method
    assert "project_dir = Path(directory).resolve()" in method
    assert "project.project_dir = project_dir" in method
    assert "project.name = project_dir.name" in method
    assert "save_project(project, project_dir)" in method
    assert "project_dir.mkdir(" not in method
    assert "Choose parent folder for project" not in method
    assert "QInputDialog.getText(" not in method

    print(
        "OK — HL-S2C3A Save As selects one final project folder and writes "
        "project.json directly inside it."
    )


if __name__ == "__main__":
    main()
