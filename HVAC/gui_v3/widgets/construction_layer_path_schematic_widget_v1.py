from __future__ import annotations

from dataclasses import dataclass
import json

from PySide6.QtCore import QByteArray, QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from HVAC.constructions.physics.construction_layer_path_candidate_edit_v1 import (
    ConstructionLayerCandidateEditV1,
    StagedConstructionLayerV1,
    move_construction_layer_candidate_v1,
    restore_staged_construction_layer_candidate_v1,
    stage_construction_layer_candidate_v1,
    update_construction_layer_properties_candidate_v1,
    update_construction_path_properties_candidate_v1,
)
from HVAC.constructions.physics.iso_6946_combined_u_value_calculation_v1 import (
    resolve_iso_6946_combined_u_value_v1,
)
from HVAC.constructions.physics.shared_construction_layer_path_evidence_v1 import (
    SharedConstructionLayerPathEvidenceV1,
)
from HVAC.constructions.physics.u_value_method_comparison_acceptance_v1 import (
    build_u_value_method_comparison_v1,
)


CONSTRUCTION_LAYER_MIME_V1 = (
    "application/x-hvacgooee-construction-layer-candidate-v1"
)
PATH_DRAG_SOURCE = "path"
STAGING_DRAG_SOURCE = "staging"
BASE_SCHEMATIC_MINIMUM_WIDTH = 680


def _natural_text_width(widget: QWidget, text: str, padding: int) -> int:
    lines = str(text).splitlines() or [""]
    return max(
        widget.fontMetrics().horizontalAdvance(line) for line in lines
    ) + int(padding)


def _natural_text_height(widget: QWidget, text: str, padding: int) -> int:
    line_count = max(1, len(str(text).splitlines()))
    return widget.fontMetrics().lineSpacing() * line_count + int(padding)


@dataclass(frozen=True, slots=True)
class ConstructionLayerDragEvidenceV1:
    layer_id: str
    source_kind: str
    source_path_id: str
    shared_layer: bool


class ConstructionLayerDragDropInteractionV1:
    @staticmethod
    def mime_data(evidence: ConstructionLayerDragEvidenceV1) -> QMimeData:
        payload = {
            "schema": "construction_layer_drag_v1",
            "layer_id": evidence.layer_id,
            "source_kind": evidence.source_kind,
            "source_path_id": evidence.source_path_id,
            "shared_layer": evidence.shared_layer,
        }
        mime = QMimeData()
        mime.setData(
            CONSTRUCTION_LAYER_MIME_V1,
            QByteArray(json.dumps(payload, sort_keys=True).encode("utf-8")),
        )
        return mime

    @staticmethod
    def decode(mime: QMimeData | None) -> ConstructionLayerDragEvidenceV1 | None:
        if mime is None or not mime.hasFormat(CONSTRUCTION_LAYER_MIME_V1):
            return None
        try:
            payload = json.loads(
                bytes(mime.data(CONSTRUCTION_LAYER_MIME_V1)).decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return None
        if not isinstance(payload, dict) or payload.get("schema") != (
            "construction_layer_drag_v1"
        ):
            return None
        layer_id = str(payload.get("layer_id") or "")
        source_kind = str(payload.get("source_kind") or "")
        source_path_id = str(payload.get("source_path_id") or "")
        if not layer_id or source_kind not in {PATH_DRAG_SOURCE, STAGING_DRAG_SOURCE}:
            return None
        if source_kind == PATH_DRAG_SOURCE and not source_path_id:
            return None
        return ConstructionLayerDragEvidenceV1(
            layer_id=layer_id,
            source_kind=source_kind,
            source_path_id=source_path_id,
            shared_layer=bool(payload.get("shared_layer", False)),
        )


class ConstructionLayerDragTokenV1(QLabel):
    focus_requested = Signal(str, str)

    def __init__(
        self,
        *,
        label: str,
        drag_evidence: ConstructionLayerDragEvidenceV1,
        detail: str = "",
        included: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(label, parent)
        self.drag_evidence = drag_evidence
        self.included = bool(included)
        self._press_position = QPoint()
        self.setObjectName("constructionLayerDragToken")
        self.setToolTip(detail or "Drag to reorder this candidate layer")
        self._set_token_style(False)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumWidth(
            max(self.sizeHint().width(), _natural_text_width(self, label, 30))
        )
        self.setMinimumHeight(
            max(self.sizeHint().height(), _natural_text_height(self, label, 20))
        )

    def set_focused(self, focused: bool) -> None:
        self._set_token_style(bool(focused))

    def _set_token_style(self, focused: bool) -> None:
        if not self.included:
            shared_style = (
                "background: #eeeeee; border: 3px solid #8f4f08;"
                if focused
                else "background: #eeeeee; border: 1px dashed #888888;"
            )
        elif self.drag_evidence.shared_layer:
            shared_style = (
                "background: #ffe6bf; border: 3px solid #8f4f08;"
                if focused
                else "background: #ffe6bf; border: 2px solid #b56b18;"
            )
        else:
            shared_style = (
                "background: #eaf2fb; border: 3px solid #c66a13;"
                if focused
                else "background: #eaf2fb; border: 1px solid #4d698c;"
            )
        self.setStyleSheet(
            "QLabel { " + shared_style
            + " color: #202020; border-radius: 5px; padding: 7px; }"
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._press_position = event.position().toPoint()
            self.focus_requested.emit("layer", self.drag_evidence.layer_id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not (event.buttons() & Qt.LeftButton):
            return
        if (
            event.position().toPoint() - self._press_position
        ).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        drag.setMimeData(
            ConstructionLayerDragDropInteractionV1.mime_data(self.drag_evidence)
        )
        drag.setPixmap(self.grab())
        drag.exec(Qt.MoveAction)


class ConstructionPathDropRowV1(QFrame):
    layer_drop_requested = Signal(object, str, int)
    focus_requested = Signal(str, str)

    def __init__(self, path_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.path_id = path_id
        self._tokens: list[ConstructionLayerDragTokenV1] = []
        self.setAcceptDrops(True)
        self.setObjectName("constructionPathDropRow")
        self.setStyleSheet(
            "QFrame#constructionPathDropRow { background: #fafcff; "
            "border: 1px solid #a9b7c7; border-radius: 5px; }"
        )
        self.layout_row = QHBoxLayout(self)
        self.layout_row.setContentsMargins(7, 6, 7, 6)
        self.layout_row.setSpacing(8)

    def set_path(
        self,
        *,
        path_label: str,
        area_fraction: float,
        layers: list[tuple[str, str, str, bool, bool]],
        focused_layer_id: str = "",
        path_focused: bool = False,
    ) -> None:
        _clear_layout(self.layout_row)
        self._tokens = []
        heading_text = f"{path_label}\n{area_fraction * 100:.1f}%"
        heading = QPushButton(heading_text)
        heading.setObjectName("constructionPathFocusButton")
        heading.setFlat(True)
        heading.setStyleSheet(
            "QPushButton { font-weight: 600; color: #293d55; "
            "text-align: left; padding: 3px; "
            + (
                "background: #fff0df; border: 2px solid #c66a13; }"
                if path_focused
                else "background: transparent; border: 1px solid transparent; }"
            )
        )
        heading.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        heading.setMinimumWidth(
            max(
                105,
                heading.sizeHint().width(),
                _natural_text_width(heading, heading_text, 18),
            )
        )
        heading.setMinimumHeight(
            max(
                heading.sizeHint().height(),
                _natural_text_height(heading, heading_text, 12),
            )
        )
        heading.clicked.connect(
            lambda _checked=False: self.focus_requested.emit("path", self.path_id)
        )
        self.layout_row.addWidget(heading)
        inside_label = QLabel("Inside →")
        inside_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.layout_row.addWidget(inside_label)
        for layer_id, label, detail, shared, included in layers:
            token = ConstructionLayerDragTokenV1(
                label=label if included else f"{label}\nNot included",
                detail=detail,
                included=included,
                drag_evidence=ConstructionLayerDragEvidenceV1(
                    layer_id=layer_id,
                    source_kind=PATH_DRAG_SOURCE,
                    source_path_id=self.path_id,
                    shared_layer=shared,
                ),
            )
            token.set_focused(layer_id == focused_layer_id)
            token.focus_requested.connect(self.focus_requested.emit)
            self._tokens.append(token)
            self.layout_row.addWidget(token)
        outside_label = QLabel("→ Outside")
        outside_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.layout_row.addWidget(outside_label)
        self.layout_row.addStretch()
        self.layout_row.activate()
        self.setMinimumWidth(
            max(
                self.layout_row.minimumSize().width(),
                self.layout_row.sizeHint().width(),
            )
        )
        self.setFixedHeight(
            max(
                self.layout_row.minimumSize().height(),
                self.layout_row.sizeHint().height(),
            )
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if ConstructionLayerDragDropInteractionV1.decode(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        drag = ConstructionLayerDragDropInteractionV1.decode(event.mimeData())
        if drag is None:
            event.ignore()
            return
        target_index = sum(
            1 for token in self._tokens
            if event.position().x() > token.geometry().center().x()
        )
        self.layer_drop_requested.emit(drag, self.path_id, target_index)
        event.acceptProposedAction()


class ConstructionLayerStagingTrayV1(QFrame):
    layer_stage_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("constructionLayerStagingTray")
        self.setStyleSheet(
            "QFrame#constructionLayerStagingTray { background: #f7f7f3; "
            "border: 1px dashed #77776f; border-radius: 5px; }"
        )
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(7, 6, 7, 6)

    def set_layers(
        self,
        layers: list[tuple[StagedConstructionLayerV1, str, str]],
    ) -> None:
        _clear_layout(self._layout)
        self._layout.addWidget(QLabel("Candidate staging:"))
        for staged, label, detail in layers:
            token = ConstructionLayerDragTokenV1(
                label=label,
                detail=detail,
                drag_evidence=ConstructionLayerDragEvidenceV1(
                    layer_id=staged.layer_id,
                    source_kind=STAGING_DRAG_SOURCE,
                    source_path_id=staged.source_path_id,
                    shared_layer=staged.shared_layer,
                ),
            )
            self._layout.addWidget(token)
        if not layers:
            self._layout.addWidget(QLabel("No staged layers"))
        self._layout.addStretch()

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        drag = ConstructionLayerDragDropInteractionV1.decode(event.mimeData())
        if drag is not None and drag.source_kind == PATH_DRAG_SOURCE:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        self.dragEnterEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        drag = ConstructionLayerDragDropInteractionV1.decode(event.mimeData())
        if drag is None or drag.source_kind != PATH_DRAG_SOURCE:
            event.ignore()
            return
        self.layer_stage_requested.emit(drag)
        event.acceptProposedAction()


class ConstructionLayerPathSchematicWidgetV1(QWidget):
    """Candidate-only draggable layer/path schematic and network summary."""

    candidate_changed = Signal(object)
    focus_changed = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("constructionLayerPathSchematicWidget")
        self._evidence: SharedConstructionLayerPathEvidenceV1 | None = None
        self._staged: dict[str, StagedConstructionLayerV1] = {}
        self._focused_kind = ""
        self._focused_id = ""
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(6, 6, 6, 6)
        self._title = QLabel("No construction teaching model selected")
        self._title.setStyleSheet("font-weight: 650;")
        self._guidance = QLabel(
            "Orange layers are shared and move across every path together. "
            "Blue layers belong to one path."
        )
        self._guidance.setWordWrap(True)
        self._staging = ConstructionLayerStagingTrayV1()
        self._staging.layer_stage_requested.connect(self._on_stage_drop)
        self._rows = QVBoxLayout()
        self._network = QLabel("Thermal network: —")
        self._network.setWordWrap(True)
        self._status = QLabel("Candidate only — accepted U-value is unchanged")
        self._status.setWordWrap(True)
        self._root.addWidget(self._title)
        self._root.addWidget(self._guidance)
        self._root.addWidget(self._staging)
        self._root.addLayout(self._rows)
        self._root.addWidget(self._network)
        self._root.addWidget(self._status)
        self.setMinimumWidth(BASE_SCHEMATIC_MINIMUM_WIDTH)

    def set_evidence(
        self,
        evidence: SharedConstructionLayerPathEvidenceV1,
    ) -> None:
        self._evidence = evidence
        self._staged = {}
        self._focused_kind = ""
        self._focused_id = ""
        self._rebuild()

    def candidate_evidence(self) -> SharedConstructionLayerPathEvidenceV1 | None:
        return self._evidence

    def staged_layers(self) -> tuple[StagedConstructionLayerV1, ...]:
        return tuple(self._staged.values())

    def focused_item(self) -> tuple[str, str]:
        return self._focused_kind, self._focused_id

    def focus_item(self, kind: str, item_id: str) -> None:
        kind = str(kind or "")
        item_id = str(item_id or "")
        evidence = self._evidence
        valid = bool(
            evidence is not None
            and (
                (kind == "layer" and item_id in evidence.layer_by_id())
                or (
                    kind == "path"
                    and item_id in {path.path_id for path in evidence.paths}
                )
            )
        )
        if not valid:
            kind, item_id = "", ""
        self._focused_kind = kind
        self._focused_id = item_id
        self._rebuild()
        self.focus_changed.emit(kind, item_id)

    def update_focused_layer(self, **properties) -> ConstructionLayerCandidateEditV1:
        if self._evidence is None or self._focused_kind != "layer":
            return ConstructionLayerCandidateEditV1(
                operation_ready=False,
                blockers=("Exact focused construction layer is required",),
            )
        result = update_construction_layer_properties_candidate_v1(
            self._evidence,
            layer_id=self._focused_id,
            **properties,
        )
        return self._apply_edit(result)

    def update_focused_path(
        self,
        *,
        label: str,
        area_fraction: float,
    ) -> ConstructionLayerCandidateEditV1:
        if self._evidence is None or self._focused_kind != "path":
            return ConstructionLayerCandidateEditV1(
                operation_ready=False,
                blockers=("Exact focused construction path is required",),
            )
        result = update_construction_path_properties_candidate_v1(
            self._evidence,
            path_id=self._focused_id,
            label=label,
            area_fraction=area_fraction,
        )
        return self._apply_edit(result)

    def move_layer(
        self,
        layer_id: str,
        source_path_id: str,
        target_path_id: str,
        target_index: int,
    ) -> ConstructionLayerCandidateEditV1:
        if self._evidence is None:
            return ConstructionLayerCandidateEditV1(
                operation_ready=False,
                blockers=("Construction evidence is required",),
            )
        result = move_construction_layer_candidate_v1(
            self._evidence,
            layer_id=layer_id,
            source_path_id=source_path_id,
            target_path_id=target_path_id,
            target_index=target_index,
        )
        return self._apply_edit(result)

    def stage_layer(
        self,
        layer_id: str,
        source_path_id: str,
    ) -> ConstructionLayerCandidateEditV1:
        if self._evidence is None:
            return ConstructionLayerCandidateEditV1(
                operation_ready=False,
                blockers=("Construction evidence is required",),
            )
        result = stage_construction_layer_candidate_v1(
            self._evidence,
            layer_id=layer_id,
            source_path_id=source_path_id,
        )
        if result.operation_ready and result.staged_layer is not None:
            self._staged[result.staged_layer.layer_id] = result.staged_layer
        return self._apply_edit(result)

    def restore_layer(
        self,
        layer_id: str,
        target_path_id: str,
        target_index: int,
    ) -> ConstructionLayerCandidateEditV1:
        if self._evidence is None or layer_id not in self._staged:
            return ConstructionLayerCandidateEditV1(
                operation_ready=False,
                blockers=("Recognised staged construction layer is required",),
            )
        result = restore_staged_construction_layer_candidate_v1(
            self._evidence,
            self._staged[layer_id],
            target_path_id=target_path_id,
            target_index=target_index,
        )
        if result.operation_ready:
            self._staged.pop(layer_id, None)
        return self._apply_edit(result)

    def _on_stage_drop(self, drag: ConstructionLayerDragEvidenceV1) -> None:
        self.stage_layer(drag.layer_id, drag.source_path_id)

    def _on_row_drop(
        self,
        drag: ConstructionLayerDragEvidenceV1,
        target_path_id: str,
        target_index: int,
    ) -> None:
        if drag.source_kind == STAGING_DRAG_SOURCE:
            self.restore_layer(drag.layer_id, target_path_id, target_index)
        else:
            self.move_layer(
                drag.layer_id,
                drag.source_path_id,
                target_path_id,
                target_index,
            )

    def _apply_edit(
        self,
        result: ConstructionLayerCandidateEditV1,
    ) -> ConstructionLayerCandidateEditV1:
        if not result.operation_ready or result.evidence is None:
            self._status.setText(
                "Blocked — " + "; ".join(result.blockers)
            )
            return result
        self._evidence = result.evidence
        self._rebuild()
        self.candidate_changed.emit(self._evidence)
        return result

    def _rebuild(self) -> None:
        _clear_layout(self._rows)
        evidence = self._evidence
        if evidence is None:
            return
        self._title.setText(evidence.label)
        layers = evidence.layer_by_id()
        staged_rows = []
        for staged in self._staged.values():
            layer = layers[staged.layer_id]
            staged_rows.append((staged, layer.label, _layer_detail(layer)))
        self._staging.set_layers(staged_rows)

        path_rows: list[ConstructionPathDropRowV1] = []
        for path in evidence.paths:
            row = ConstructionPathDropRowV1(path.path_id)
            row.set_path(
                path_label=path.label,
                area_fraction=float(path.area_fraction),
                focused_layer_id=(
                    self._focused_id if self._focused_kind == "layer" else ""
                ),
                path_focused=(
                    self._focused_kind == "path"
                    and self._focused_id == path.path_id
                ),
                layers=[
                    (
                        layer_id,
                        layers[layer_id].label,
                        _layer_detail(layers[layer_id]),
                        layer_id in evidence.shared_layer_ids,
                        layers[layer_id].included,
                    )
                    for layer_id in path.layer_ids
                ],
            )
            row.layer_drop_requested.connect(self._on_row_drop)
            row.focus_requested.connect(self.focus_item)
            self._rows.addWidget(row)
            path_rows.append(row)

        root_margins = self._root.contentsMargins()
        required_width = max(
            [BASE_SCHEMATIC_MINIMUM_WIDTH]
            + [
                row.minimumWidth()
                + root_margins.left()
                + root_margins.right()
                for row in path_rows
            ]
        )
        self.setMinimumWidth(required_width)

        iso = resolve_iso_6946_combined_u_value_v1(evidence)
        comparison = build_u_value_method_comparison_v1(evidence)
        if iso.ready:
            self._network.setText(
                f"Knitted thermal network: {len(iso.network_nodes)} nodes, "
                f"{len(iso.network_edges)} edges. Shared layers rejoin at "
                "common interfaces."
            )
        else:
            self._network.setText(
                "Thermal network blocked: " + "; ".join(iso.blockers)
            )
        if comparison.ready:
            self._status.setText(
                "Candidate only — Legacy "
                f"{comparison.rows[0].u_value_W_m2K:.3f} / ISO base "
                f"{comparison.rows[1].u_value_W_m2K:.3f} W/m²K. "
                "Accepted U-value is unchanged."
            )
        else:
            self._status.setText(
                "Candidate incomplete — " + "; ".join(comparison.blockers)
            )
        self.updateGeometry()
        self.adjustSize()


def _layer_detail(layer) -> str:
    thickness = (
        "—" if layer.thickness_m is None else f"{layer.thickness_m * 1000:.1f} mm"
    )
    conductivity = (
        "—"
        if layer.conductivity_W_mK is None
        else f"λ {layer.conductivity_W_mK:.3f} W/mK"
    )
    state = "Included" if layer.included else "Not included — omitted from calculation"
    return f"{state}; {thickness}; {conductivity}"


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif child_layout is not None:
            _clear_layout(child_layout)
