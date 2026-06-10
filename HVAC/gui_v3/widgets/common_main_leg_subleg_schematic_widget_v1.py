# ======================================================================
# HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True, slots=True)
class CommonMainLegSublegRouteV1:
    leg_id: str
    leg_label: str
    subleg_id: str
    subleg_label: str
    role: str
    room_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CommonMainLegSublegSchematicV1:
    heat_source_label: str
    common_main_label: str
    routes: tuple[CommonMainLegSublegRouteV1, ...]
    status: str = "DEV common-main / leg / subleg schematic preview only"


class CommonMainLegSublegSchematicWidgetV1(QWidget):
    """
    DEV topology/proportioning aid.

    Visual grammar:
    - common main = elongated blue distribution spine
    - leg = take-off from common main
    - subleg = room-carrying route from a leg
    - rooms = ordered chain carried by the subleg

    Preview only:
    - no final pipe routing
    - no pump
    - no committed return arrangement
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._schematic: CommonMainLegSublegSchematicV1 | None = None
        self.setMinimumSize(1100, 360)
        self._focus: dict[str, str] = {}

        self._focus_callback = None
        self._room_hit_rects: list[tuple[QRectF, dict[str, str]]] = []

    def set_focus_callback(self, callback) -> None:
        """
        H-S19-M:
        Register a panel callback for schematic click focus.

        Display/focus only.
        No ProjectState access.
        No engineering mutation.
        """
        self._focus_callback = callback

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """
        H-S19-M:
        Schematic click focus.

        Clicking a drawn room sends a focus payload back to the panel.
        Display/focus only; no engineering authority.
        """
        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        pos = event.position()

        for rect, focus in reversed(self._room_hit_rects):
            if rect.contains(pos):
                self.set_focus(focus)

                if self._focus_callback is not None:
                    self._focus_callback(dict(focus))

                event.accept()
                return

        event.ignore()

    def set_schematic(
        self,
        schematic: CommonMainLegSublegSchematicV1 | None,
    ) -> None:
        self._schematic = schematic
        self._update_size()
        self.update()

    def sizeHint(self) -> QSize:
        if self._schematic is None:
            return QSize(1100, 360)

        route_count = max(1, len(self._schematic.routes))
        return QSize(1250, 160 + route_count * 82)

    def _update_size(self) -> None:
        size = self.sizeHint()
        self.setMinimumSize(size)
        self.resize(size)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._room_hit_rects = []
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.fillRect(self.rect(), QColor(250, 250, 250))

        if self._schematic is None:
            self._draw_empty(painter)
            return

        self._draw_schematic(painter, self._schematic)

    def _draw_empty(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(110, 110, 110), 1))
        painter.drawText(
            QRectF(20, 20, self.width() - 40, 40),
            Qt.AlignLeft | Qt.AlignVCenter,
            "No hydronic topology available",
        )

    def set_focus(self, focus: dict | None) -> None:
        """
        DEV visual focus only.

        Does not mutate ProjectState.
        Does not commit a return arrangement.
        """
        self._focus = dict(focus or {})
        self.update()

    def _draw_schematic(
            self,
            painter: QPainter,
            schematic: CommonMainLegSublegSchematicV1,
    ) -> None:
        routes = tuple(schematic.routes)
        self._room_hit_rects = []
        grouped_routes: list[tuple[str, str, list[CommonMainLegSublegRouteV1]]] = []
        by_leg: dict[str, tuple[str, list[CommonMainLegSublegRouteV1]]] = {}

        focused_subleg_id = str(self._focus.get("subleg_id", "") or "")
        focused_room_id = str(self._focus.get("room_id", "") or "")

        for route in routes:
            leg_id = str(route.leg_id or "")
            leg_label = str(route.leg_label or leg_id or "Leg")

            if leg_id not in by_leg:
                by_leg[leg_id] = (leg_label, [])

            by_leg[leg_id][1].append(route)

        for leg_id, value in by_leg.items():
            leg_label, leg_routes = value
            grouped_routes.append((leg_id, leg_label, leg_routes))

        x_heat = 25
        x_common = 230
        x_leg = 340
        x_subleg = 515
        x_rooms = 700

        y_top = 70
        leg_gap = 170
        subleg_gap = 62

        common_w = 48
        leg_w = 130
        leg_h = 44
        subleg_w = 180
        subleg_h = 44

        leg_count = max(1, len(grouped_routes))
        first_leg_y = y_top
        last_leg_y = y_top + (leg_count - 1) * leg_gap

        common_rect = QRectF(
            x_common,
            first_leg_y - 35,
            common_w,
            (last_leg_y - first_leg_y) + 70,
        )

        heat_rect = QRectF(
            x_heat,
            common_rect.top() + 20,
            160,
            46,
        )

        # --------------------------------------------------
        # Status / title
        # --------------------------------------------------
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.setFont(QFont("Sans Serif", 9))
        painter.drawText(
            QRectF(25, 18, self.width() - 50, 24),
            Qt.AlignLeft | Qt.AlignVCenter,
            schematic.status,
        )

        # --------------------------------------------------
        # Heat source
        # --------------------------------------------------
        self._draw_box(
            painter,
            heat_rect,
            schematic.heat_source_label,
            border=QColor(170, 70, 70),
            fill=QColor(255, 245, 245),
            text_colour=QColor(70, 40, 40),
            bold=True,
        )

        # --------------------------------------------------
        # Common main — narrow vertical blue spine
        # --------------------------------------------------
        self._draw_box(
            painter,
            common_rect,
            schematic.common_main_label,
            border=QColor(45, 100, 180),
            fill=QColor(230, 240, 255),
            text_colour=QColor(25, 65, 130),
            bold=True,
            vertical=True,
        )

        # Heat source to common main connector.
        self._draw_line(
            painter,
            heat_rect.right(),
            heat_rect.center().y(),
            common_rect.left(),
            heat_rect.center().y(),
            QColor(90, 90, 90),
            2,
        )

        for leg_index, (_leg_id, leg_label, leg_routes) in enumerate(
                grouped_routes
        ):
            leg_y = y_top + leg_index * leg_gap
            leg_rect = QRectF(x_leg, leg_y - leg_h / 2, leg_w, leg_h)

            # Common main take-off to leg.
            self._draw_line(
                painter,
                common_rect.right(),
                leg_y,
                leg_rect.left(),
                leg_y,
                QColor(65, 100, 150),
                2,
            )

            self._draw_box(
                painter,
                leg_rect,
                leg_label,
                border=QColor(70, 105, 150),
                fill=QColor(242, 247, 255),
                text_colour=QColor(40, 70, 110),
                bold=True,
            )

            count = len(leg_routes)
            offset = (count - 1) / 2.0

            for subleg_index, route in enumerate(leg_routes):
                subleg_y = leg_y + (subleg_index - offset) * subleg_gap

                subleg_rect = QRectF(
                    x_subleg,
                    subleg_y - subleg_h / 2,
                    subleg_w,
                    subleg_h,
                )

                route_leg_id = str(getattr(route, "leg_id", "") or leg_id or "")
                route_subleg_id = str(getattr(route, "subleg_id", "") or "")

                room_labels = list(
                    getattr(route, "room_labels", None)
                    or getattr(route, "rooms", None)
                    or []
                )

                is_focused_subleg = (
                        bool(focused_subleg_id)
                        and route_subleg_id == focused_subleg_id
                )

                subleg_border = (
                    QColor(190, 115, 35)  # orange focus border
                    if is_focused_subleg
                    else QColor(90, 135, 90)
                )

                subleg_fill = QColor(242, 252, 242)  # no focus infill

                # Leg to subleg connector.
                self._draw_line(
                    painter,
                    leg_rect.right(),
                    leg_y,
                    subleg_rect.left(),
                    subleg_y,
                    QColor(190, 115, 35) if is_focused_subleg else QColor(95, 120, 95),
                    3 if is_focused_subleg else 2,
                )

                role = str(route.role or "")
                status_note = "\nTBD" if "branch" in role.lower() else ""

                self._draw_box(
                    painter,
                    subleg_rect,
                    f"{route.subleg_label}\n{role}{status_note}",
                    border=subleg_border,
                    fill=subleg_fill,
                    text_colour=QColor(45, 90, 45),
                    bold=True,
                )

                # Subleg to first room connector.
                self._draw_line(
                    painter,
                    subleg_rect.right(),
                    subleg_y,
                    x_rooms,
                    subleg_y,
                    QColor(190, 115, 35) if is_focused_subleg else QColor(120, 120, 120),
                    3 if is_focused_subleg else 1,
                )

                self._draw_room_chain(
                    painter,
                    room_labels,
                    x_rooms,
                    subleg_y,
                    leg_id=route_leg_id,
                    subleg_id=route_subleg_id,
                    focused_room_id=focused_room_id,
                )

    def _draw_room_chain(
            self,
            painter: QPainter,
            rooms: list,
            start_x: int,
            start_y: int,
            *,
            leg_id: str = "",
            subleg_id: str = "",
            focused_room_id: str = "",
    ) -> None:
        x = start_x
        room_w = 74
        room_h = 34
        gap = 16

        labels = tuple(rooms or [])

        if not labels:
            self._draw_box(
                painter,
                QRectF(x, start_y - room_h / 2, room_w, room_h),
                "No rooms",
                border=QColor(120, 120, 120),
                fill=QColor(248, 255, 248),
                text_colour=QColor(20, 20, 20),
                bold=False,
            )
            return

        for label in labels:
            room_id = str(label or "").strip()

            room_rect = QRectF(
                x,
                start_y - room_h / 2,
                room_w,
                room_h,
            )

            is_focused_room = bool(
                focused_room_id
                and room_id
                and room_id == focused_room_id
            )

            room_border = (
                QColor(190, 115, 35)  # orange focus border
                if is_focused_room
                else QColor(110, 135, 110)
            )

            room_fill = QColor(248, 255, 248)  # no focus infill
            room_text_colour = QColor(20, 20, 20)  # dark text

            self._draw_box(
                painter,
                room_rect,
                room_id,
                border=room_border,
                fill=room_fill,
                text_colour=room_text_colour,
                bold=False,
            )

            if is_focused_room:
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QColor(190, 115, 35), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(room_rect, 8, 8)
                painter.restore()

            if room_id:
                self._room_hit_rects.append(
                    (
                        QRectF(room_rect),
                        {
                            "leg_id": str(leg_id or ""),
                            "subleg_id": str(subleg_id or ""),
                            "room_id": room_id,
                        },
                    )
                )

            x += room_w + gap


    @staticmethod
    def _draw_box(
            painter: QPainter,
            rect: QRectF,
            label: str,
            *,
            border: QColor,
            fill: QColor,
            text_colour: QColor,
            bold: bool = False,
            vertical: bool = False,
    ) -> None:
        painter.setPen(QPen(border, 2))
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(rect, 8, 8)

        font = QFont("Sans Serif", 9)
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(QPen(text_colour, 1))

        if vertical:
            painter.save()
            painter.translate(rect.center())
            painter.rotate(-90)
            rotated = QRectF(
                -rect.height() / 2,
                -rect.width() / 2,
                rect.height(),
                rect.width(),
            )
            painter.drawText(
                rotated,
                Qt.AlignCenter | Qt.TextWordWrap,
                label,
            )
            painter.restore()
        else:
            painter.drawText(
                rect.adjusted(4, 2, -4, -2),
                Qt.AlignCenter | Qt.TextWordWrap,
                label,
            )

    @staticmethod
    def _draw_line(
        painter: QPainter,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        colour: QColor,
        width: int,
    ) -> None:
        painter.setPen(QPen(colour, width))
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))