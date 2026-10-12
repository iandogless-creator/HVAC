"""New job uses the existing folder chooser and checksummed project saver."""
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox
from HVAC.gui_v3.context import project_workspace_v1
from HVAC.gui_v3.context.startup_projects_v1 import create_new_project_v1
from HVAC.project_v3.persistence.saver import save as save_project


def choose_new_project_v1(parent=None):
    """Return a saved new job, or None without replacing the current project."""
    try:
        root = project_workspace_v1.default_project_root_v1()
        root.mkdir(parents=True, exist_ok=True)
        directory = QFileDialog.getExistingDirectory(
            parent, "New job — create and select an empty folder", str(root)
        )
        if not directory:
            return None
        project_dir = Path(directory).resolve()
        if project_dir == root.resolve():
            raise ValueError("Create a folder for this job inside HVACprojects, then select it.")
        if not project_dir.is_dir():
            raise ValueError("Create and select the new job folder first.")
        if any(project_dir.iterdir()):
            raise ValueError("This folder is not empty. Select a new empty job folder; use Open for an existing job.")
        project = create_new_project_v1()
        project.name = project_dir.name
        project.project_dir = project_dir
        save_project(project, project_dir)
        return project
    except (OSError, ValueError, RuntimeError) as exc:
        QMessageBox.warning(parent, "New project", str(exc))
        return None
