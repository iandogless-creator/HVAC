# ---------------------------------------------------------------
# HVACSystemBuilder.py
# GUI with unit system selector + test calculation button
# ---------------------------------------------------------------

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QMessageBox,
    QPushButton,  # ✅ added
)
import sys

try:
    from flowrate import pipe_data
except ImportError:
    pipe_data = {}
    print("⚠️ flowrate module not found — using placeholder data.")


class HVACSystemBuilder(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HVAC System Builder")
        self.resize(1200, 700)

        # === Main layout ===
        layout = QHBoxLayout(self)

        # === Sidebar (Wizard panel) ===
        self.sidebar = QVBoxLayout()
        self.status_label = QLabel("Step 1: Enter number of legs")
        self.sidebar.addWidget(self.status_label)

        # === Unit selector ===
        self.add_unit_selector()

        # === Add test calculation button ===
        self.test_button = QPushButton("Run Test Calculation")
        self.test_button.clicked.connect(
            lambda: self.calculate_pipe_size(material="Steel")
        )
        self.sidebar.addWidget(self.test_button)

        # Add sidebar to main layout
        layout.addLayout(self.sidebar)
        self.setLayout(layout)

    # ---------------------------------------------------------------
    # Unit selector setup
    # ---------------------------------------------------------------
    def add_unit_selector(self):
        unit_label = QLabel("Unit System:")
        self.unit_selector = QComboBox()
        self.unit_selector.addItems(["Metric (mm)", "Imperial (inch)"])
        self.unit_selector.setCurrentIndex(0)
        self.unit_selector.currentIndexChanged.connect(self.on_unit_change)

        self.unit_indicator = QLabel("Metric (mm)")
        self.unit_indicator.setStyleSheet("color: #3CB371; font-weight: bold;")

        self.sidebar.addWidget(unit_label)
        self.sidebar.addWidget(self.unit_selector)
        self.sidebar.addWidget(self.unit_indicator)
        self.use_metric = True

    def on_unit_change(self, index):
        if index == 0:
            self.unit_indicator.setText("Metric (mm)")
            self.unit_indicator.setStyleSheet("color: #3CB371; font-weight: bold;")
            self.use_metric = True
        else:
            self.unit_indicator.setText("Imperial (inch)")
            self.unit_indicator.setStyleSheet("color: #1E90FF; font-weight: bold;")
            self.use_metric = False

    # ---------------------------------------------------------------
    # Test calculation button logic
    # ---------------------------------------------------------------
    def calculate_pipe_size(self, material="Steel"):
        print(f"🧮 Running test calculation for {material}...")
        QMessageBox.information(
            self, "Calculation", f"Test calculation for {material} complete!"
        )


# ---------------------------------------------------------------
# Run GUI
# ---------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HVACSystemBuilder()
    window.show()
    sys.exit(app.exec_())
