"""Explicit project choice before building the workspace."""
from pathlib import Path
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QPushButton, QVBoxLayout
from HVAC.version import DISPLAY_VERSION


class StartupProjectDialogV1(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"HVACgooee — {DISPLAY_VERSION}")
        self.setMinimumWidth(440)
        self.action = None
        self.project_dir = None
        layout = QVBoxLayout(self)
        title = QLabel(f"HVACgooee · {DISPLAY_VERSION}")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        text = QLabel("Create a project, open a saved project folder, or explore the sample.")
        text.setWordWrap(True); layout.addWidget(text)
        for label, action in (("New project", "new"), ("Open project…", "open"), ("Sample project", "sample")):
            button = QPushButton(label)
            button.setObjectName(f"startup_{action}")
            button.setMinimumHeight(34)
            button.clicked.connect(lambda checked=False, key=action: self.choose(key))
            layout.addWidget(button)
        note = QLabel("Sample dimensions and construction values are examples to review.\nEngineering acceptance remains an explicit design action.")
        note.setWordWrap(True); layout.addWidget(note)
        close = QPushButton("Quit"); close.clicked.connect(self.reject); layout.addWidget(close)

    def choose(self, action):
        if action not in {"new", "open", "sample"}:
            raise ValueError("Unknown startup action")
        if action == "open":
            directory = QFileDialog.getExistingDirectory(
                self, "Open folder containing project.json",
                str(Path.home() / "Documents" / "HVACgooee"),
            )
            if not directory:
                return
            self.project_dir = Path(directory)
        self.action = action
        self.accept()
