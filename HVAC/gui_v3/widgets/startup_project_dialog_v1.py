"""Explicit project choice before building the workspace."""
from pathlib import Path
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QPushButton, QVBoxLayout
from HVAC.version import DISPLAY_VERSION
from HVAC.gui_v3.context import project_workspace_v1
from HVAC.gui_v3.widgets.new_project_folder_v1 import choose_new_project_v1


class StartupProjectDialogV1(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"HVACgooee — {DISPLAY_VERSION}")
        self.setMinimumWidth(440)
        self.action = None
        self.project_dir = None
        self.project_state = None
        layout = QVBoxLayout(self)
        title = QLabel(f"HVACgooee · {DISPLAY_VERSION}")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        text = QLabel("Create a project, open a saved project folder, or explore the sample.")
        text.setWordWrap(True); layout.addWidget(text)
        for label, action in (("New project", "new"), ("Open project…", "open"), ("Sample project — 20 rooms", "sample")):
            button = QPushButton(label)
            button.setObjectName(f"startup_{action}")
            button.setMinimumHeight(34)
            button.clicked.connect(lambda checked=False, key=action: self.choose(key))
            layout.addWidget(button)
        note = QLabel("20-room example: review its inputs; room adjacency is not defined.\nSave uses your own copy. Engineering acceptance stays explicit.")
        note.setWordWrap(True); layout.addWidget(note)
        close = QPushButton("Quit"); close.clicked.connect(self.reject); layout.addWidget(close)

    def choose(self, action):
        if action not in {"new", "open", "sample"}:
            raise ValueError("Unknown startup action")
        if action == "new":
            project = choose_new_project_v1(self)
            if project is None:
                return
            self.project_state = project
            self.project_dir = project.project_dir
        if action == "open":
            directory = QFileDialog.getExistingDirectory(
                self, "Open folder containing project.json",
                str(project_workspace_v1.default_project_root_v1()),
            )
            if not directory:
                return
            self.project_dir = Path(directory)
        self.action = action
        self.accept()
