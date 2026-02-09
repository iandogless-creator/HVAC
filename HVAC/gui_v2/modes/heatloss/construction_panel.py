# ======================================================================
# HVAC/gui_v2/modes/heatloss/construction_panel.py
# ======================================================================

"""
HVACgooee — Construction Panel v3 (ROOM-SCOPED INTENT)

Purpose
-------
GUI selector for declared construction intent (preset pick),
applied explicitly to the ACTIVE ROOM.

RULES (LOCKED)
--------------
• GUI edits intent only
• No physics
• No U-value calculation inside GUI
• Registry resolves preset → ConstructionUValueResultDTO
• Commit targets ProjectState.rooms[active_room_id]
• GUI does NOT mutate ProjectState validity
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QMessageBox,
)

from HVAC_legacy.constructions.construction_preset import SurfaceClass
from HVAC_legacy.constructions.registry_v2 import CONSTRUCTION_REGISTRY_V2
from HVAC_legacy.constructions.dto.construction_uvalue_result_dto import (
    ConstructionUValueResultDTO,
)
from HVAC_legacy.project.project_state import ProjectState


class ConstructionPanel(QWidget):
    """
    GUI panel for selecting construction presets and committing
    resolved U-values as immutable DTOs to the ACTIVE ROOM.

    Emits:
        construction_committed(
            room_id: str,
            surface_class: SurfaceClass,
            dto: ConstructionUValueResultDTO
        )
    """

    construction_committed = Signal(str, object, ConstructionUValueResultDTO)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.project_state: Optional[ProjectState] = None
        self._current_surface: Optional[SurfaceClass] = None

        # Widgets
        self._element_combo = QComboBox()
        self._preset_combo = QComboBox()
        self._commit_btn = QPushButton("Commit Construction")
        self._commit_btn.setEnabled(False)

        # Layout
        root = QVBoxLayout(self)

        group = QGroupBox("Construction")
        g = QVBoxLayout(group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Element"))
        row1.addWidget(self._element_combo)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Preset"))
        row2.addWidget(self._preset_combo)

        g.addLayout(row1)
        g.addLayout(row2)
        g.addWidget(self._commit_btn)

        root.addWidget(group)
        root.addStretch(1)

        # Populate + wire
        self._populate_elements()

        self._element_combo.currentIndexChanged.connect(self._on_element_changed)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._commit_btn.clicked.connect(self._commit_construction)

        if self._element_combo.count() > 0:
            self._element_combo.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Binding
    # ------------------------------------------------------------------

    def bind_project_state(self, project_state: ProjectState) -> None:
        """
        Bind authoritative ProjectState.

        Required so commits can target the ACTIVE ROOM.
        """
        self.project_state = project_state

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def _populate_elements(self) -> None:
        self._element_combo.blockSignals(True)
        self._element_combo.clear()

        for surface in SurfaceClass:
            self._element_combo.addItem(
                self._surface_label(surface),
                surface.name,  # Qt-safe
            )

        self._element_combo.blockSignals(False)

    def _populate_presets_for_surface(self) -> None:
        self._preset_combo.blockSignals(True)
        self._preset_combo.clear()

        if self._current_surface is None:
            self._preset_combo.blockSignals(False)
            self._commit_btn.setEnabled(False)
            return

        presets = CONSTRUCTION_REGISTRY_V2.list_presets_for_surface(
            self._current_surface
        )

        for p in presets:
            self._preset_combo.addItem(p.name, p.ref)

        self._preset_combo.blockSignals(False)

        has_any = self._preset_combo.count() > 0
        self._commit_btn.setEnabled(has_any)
        if has_any:
            self._preset_combo.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_element_changed(self, _: int) -> None:
        surface_name = self._element_combo.currentData()

        try:
            self._current_surface = SurfaceClass[surface_name]
        except Exception:
            self._current_surface = None
            QMessageBox.critical(
                self,
                "Internal Error",
                f"Invalid surface selection: {surface_name!r}",
            )
            return

        self._commit_btn.setEnabled(False)
        self._populate_presets_for_surface()

    def _on_preset_changed(self, _: int) -> None:
        self._commit_btn.setEnabled(self._preset_combo.currentIndex() >= 0)

    # ------------------------------------------------------------------
    # Commit (ROOM-SCOPED)
    # ------------------------------------------------------------------

    def _commit_construction(self) -> None:
        if self.project_state is None:
            QMessageBox.warning(self, "No Project", "Project not bound.")
            return

        room_id = self.project_state.active_room_id
        if not room_id:
            QMessageBox.information(
                self,
                "No Active Room",
                "Select a room before committing construction.",
            )
            return

        if self._current_surface is None:
            return

        preset_ref = self._preset_combo.currentData()
        if not preset_ref:
            return

        try:
            dto = CONSTRUCTION_REGISTRY_V2.build_uvalue_result(
                surface_class=self._current_surface,
                preset_ref=str(preset_ref),
            )
        except Exception as e:
            QMessageBox.critical(self, "Construction Commit Failed", str(e))
            return

        print(
            "[Construction] COMMIT:",
            room_id,
            dto.surface_class,
            dto.construction_ref,
        )

        # Emit explicit, room-scoped intent (LOCKED)
        self.construction_committed.emit(
            room_id,
            dto.surface_class,
            dto,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _surface_label(surface: SurfaceClass) -> str:
        return {
            SurfaceClass.EXTERNAL_WALL: "External wall",
            SurfaceClass.INTERNAL_WALL: "Internal wall",
            SurfaceClass.ROOF: "Roof",
            SurfaceClass.CEILING: "Ceiling",
            SurfaceClass.FLOOR: "Floor",
            SurfaceClass.WINDOW: "Window / door",
            SurfaceClass.DOOR: "Door",
        }.get(surface, surface.value)
