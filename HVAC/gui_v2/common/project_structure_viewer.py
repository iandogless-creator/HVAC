"""
project_structure_viewer.py
---------------------------

HVACgooee — Project Structure Viewer (Read-Only)

Purpose
-------
Display a read-only tree view of the currently loaded ProjectV3.

Design Rules (LOCKED)
---------------------
✔ GUI-only
✔ Read-only
✔ No physics
✔ No calculations
✔ No mutation
✔ No signals emitted
✔ No implicit behaviour

This widget exists purely to make project intent visible.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
)


class ProjectStructureViewer(QWidget):
    """
    Read-only tree view of ProjectV3 structure.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(
            ["Element", "Type", "Details"]
        )
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setSelectionMode(
            QTreeWidget.NoSelection
        )

        layout.addWidget(self._tree)

    # ------------------------------------------------------------------
    # Public API (LOCKED)
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear the tree."""
        self._tree.clear()

    def set_project(self, project) -> None:
        """
        Populate the tree from a ProjectV3 instance.

        Parameters
        ----------
        project : ProjectV3 | None
        """
        self.clear()

        if project is None:
            return

        root = QTreeWidgetItem(
            ["Project", "ProjectV3", ""]
        )
        self._tree.addTopLevelItem(root)

        # Project info
        info_item = QTreeWidgetItem(
            ["Project Info", "dict", ""]
        )
        root.addChild(info_item)

        for key, value in project.project_info.items():
            QTreeWidgetItem(
                info_item,
                [str(key), type(value).__name__, str(value)],
            )

        # Spaces
        spaces_item = QTreeWidgetItem(
            ["Spaces", "list", str(len(project.spaces))]
        )
        root.addChild(spaces_item)

        for space in project.spaces:
            self._add_space(spaces_item, space)

        self._tree.expandAll()

    # ------------------------------------------------------------------
    # Internal helpers (GUI-only)
    # ------------------------------------------------------------------

    def _add_space(self, parent: QTreeWidgetItem, space) -> None:
        space_item = QTreeWidgetItem(
            [
                space.name,
                "SpaceV3",
                f"id={space.space_id}, T={space.design_temp_C}°C",
            ]
        )
        parent.addChild(space_item)

        surfaces_item = QTreeWidgetItem(
            ["Surfaces", "list", str(len(space.surfaces))]
        )
        space_item.addChild(surfaces_item)

        for surface in space.surfaces:
            QTreeWidgetItem(
                surfaces_item,
                [
                    surface.surface_id,
                    surface.surface_class,

                    (
                        f"A={surface.area_m2} m², "
                        f"ref={surface.construction_ref}"
                    ),
                ],
            )
