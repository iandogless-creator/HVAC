from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class EducationPanel(QWidget):
    def __init__(self, view_state):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Education Panel (v2 stub)"))
