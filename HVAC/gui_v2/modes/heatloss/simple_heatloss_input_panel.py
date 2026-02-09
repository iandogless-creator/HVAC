# ======================================================================
# BEGIN FILE: HVAC/gui_v2/modes/heatloss/simple_heatloss_input_panel.py
# ======================================================================
"""
HVACgooee — Simple Heat-Loss Input Panel (GUI v2)

TEMP wiring panel to drive HeatLossEngineV3.

Rules:
- GUI only
- No persistence
- No legacy engines
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox,
)

from HVAC_legacy.gui_v2.modes.heatloss.heatloss_panel import HeatLossPanel

from HVAC_legacy.constructions.construction_preset import (
    ConstructionPreset,
    SurfaceClass,
)
from HVAC_legacy.constructions.construction_preset_registry import (
    ConstructionPresetRegistry,
)
from HVAC_legacy.constructions.default_construction_presets_v2 import (
    DEFAULT_CONSTRUCTION_PRESETS_V2,
)

from HVAC_legacy.heatloss.engines.heatloss_engine_v3 import (
    HeatLossEngineV3,
    RoomHeatLossInput,
    BoundaryHeatLossInput,
)
from HVAC_legacy.heatloss.adapters.engine_to_dto import build_heatloss_dto


class SimpleHeatLossInputPanel(QWidget):
    """
    Minimal manual-input panel driving HeatLossEngineV3.
    """

    def __init__(
        self,
        *,
        heatloss_panel: HeatLossPanel,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self._heatloss_panel = heatloss_panel
        self._engine = HeatLossEngineV3()

        self._construction_registry = ConstructionPresetRegistry(
            DEFAULT_CONSTRUCTION_PRESETS_V2
        )

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(12)

        # ==============================================================
        # Room inputs
        # ==============================================================
        room_box = QGroupBox("Room inputs")
        root.addWidget(room_box)

        room_layout = QVBoxLayout(room_box)
        room_layout.setSpacing(8)

        self.ed_room = QLineEdit("Bedsit")
        self.ed_temp = QLineEdit("21.0")
        self.ed_volume = QLineEdit("50.0")
        self.ed_vent = QLineEdit("0.5")  # ACH

        room_layout.addLayout(self._row("Room name:", self.ed_room))
        room_layout.addLayout(self._row("Internal air temp (°C):", self.ed_temp))
        room_layout.addLayout(self._row("Room volume (m³):", self.ed_volume))
        room_layout.addLayout(
            self._row("Ventilation (air changes / hr):", self.ed_vent)
        )

        # ==============================================================
        # Boundary inputs (TEMP)
        # ==============================================================
        boundary_box = QGroupBox("Boundary inputs (TEMP)")
        root.addWidget(boundary_box)

        boundary_layout = QVBoxLayout(boundary_box)
        boundary_layout.setSpacing(8)

        self.cb_wall_construction = QComboBox()
        for preset in self._construction_registry.list_for_surface(
            SurfaceClass.EXTERNAL_WALL
        ):
            self.cb_wall_construction.addItem(preset.name, preset)

        self.cb_wall_construction.currentIndexChanged.connect(
            self._recalculate
        )

        boundary_layout.addLayout(
            self._row("External wall construction:", self.cb_wall_construction)
        )

        # ==============================================================
        # Actions
        # ==============================================================
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._heatloss_panel.clear)

        btn_calc = QPushButton("Calculate")
        btn_calc.clicked.connect(self._recalculate)

        btn_row.addWidget(btn_clear)
        btn_row.addWidget(btn_calc)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(label))
        row.addWidget(widget, 1)
        return row

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _recalculate(self) -> None:
        self._on_generate_clicked()

    def _on_generate_clicked(self) -> None:
        try:
            room = self.ed_room.text().strip() or "—"
            ti = float(self.ed_temp.text())
            vol = float(self.ed_volume.text())
            ach = float(self.ed_vent.text())

            preset: ConstructionPreset | None = (
                self.cb_wall_construction.currentData()
            )
            if preset is None:
                raise ValueError("No external wall construction selected")

            boundary = BoundaryHeatLossInput(
                element_type="external_wall",
                area_m2=12.0,  # TEMP until geometry v3
                construction=preset,
            )

            room_input = RoomHeatLossInput(
                room_name=room,
                internal_temp_c=ti,
                external_temp_c=self._heatloss_panel.boundary_reference_temp_c,
                boundaries=[boundary],
                room_volume_m3=vol,
                ventilation_ach=ach,
                ventilation_method="ACH (v3)",
            )

            engine_result = self._engine.compute_room(room_input)
            dto = build_heatloss_dto(engine_result)

            self._heatloss_panel.load_results(dto)

        except Exception as e:
            QMessageBox.warning(self, "Invalid input", str(e))


# ======================================================================
# END FILE
# ======================================================================
