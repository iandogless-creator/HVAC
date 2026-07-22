# HVAC/gui_v3/widgets/common_main_leg_subleg_schematic_widget_v1.py
#
# H-S26-G2:
# Display-only common-main / leg / subleg schematic.
#
# Branch sublegs are shown from a parent/common subleg take-off marker,
# not as if they originate directly from the leg.
#
# Engineering boundary:
# • no ProjectState access
# • no pressure calculation
# • no pipe sizing
# • no balancing
# • no final take-off geometry
# • branch take-off location remains TBA

from __future__ import annotations

from dataclasses import dataclass
import textwrap

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QToolTip, QWidget


@dataclass(frozen=True)
class CommonMainLegSublegSectionEvidenceV1:
    """
    H-S36-A2:
    Read-only pipe-section evidence mapped to one room-entry trace segment.

    section_ordinal 1 maps to trace_index 0 entering the first room.
    Branch take-off geometry remains TBA and is not inferred here.
    """
    section_id: str = ""
    section_ordinal: int = 0
    trace_index: int = -1
    trace_room_id: str = ""
    route_id: str = ""
    leg_id: str = ""
    subleg_id: str = ""
    from_label: str = ""
    to_label: str = ""
    flow_kg_s: str = ""
    pipe_dn: str = ""
    dp_per_m: str = ""
    length: str = ""
    k: str = ""
    section_dp: str = ""
    iter: str = ""
    status: str = ""


@dataclass(frozen=True)
class CommonMainLegSublegRoomEvidenceV1:
    """
    H-S39-A:
    Read-only room, heat-loss, emitter and emitter-flow evidence.

    Values are prepared outside the widget. This DTO carries no sizing,
    pressure, balancing, pump, valve or persistence authority.
    """
    room_id: str = ""
    room_label: str = ""
    design_heat_loss_W: str = ""
    emitter_summary: str = ""
    emitter_output_W: str = ""
    emitter_flow_kg_s: str = ""
    flow_basis: str = ""
    status: str = ""


@dataclass(frozen=True)
class CommonMainLegSublegBalancingPointEvidenceV1:
    """H-S44-E prepared allocation, method and valve-duty evidence."""
    balancing_point_id: str = ""
    point_scope: str = ""
    point_role: str = ""
    target_id: str = ""
    label: str = ""
    topology: str = ""
    governed_routes: str = ""
    point_flow: str = ""
    allocated_dp: str = ""
    resistance: str = ""
    method: str = ""
    valve_duty: str = ""
    required_kv: str = ""
    controlled_dp: str = ""
    authority: str = ""
    ready: str = ""
    status: str = ""


@dataclass(frozen=True)
class CommonMainLegSublegRouteV1:
    leg_id: str = ""
    leg_label: str = ""
    subleg_id: str = ""
    subleg_label: str = ""
    role: str = ""
    room_labels: tuple[str, ...] = ()

    # H-S39-A — shared read-only room hover evidence.
    room_evidence: tuple[CommonMainLegSublegRoomEvidenceV1, ...] = ()

    # H-S36-A2 — clean Proportioned display evidence only. The shared
    # renderer ignores this until H-S36-B hover presentation is added.
    section_evidence: tuple[CommonMainLegSublegSectionEvidenceV1, ...] = ()

    # H-S26-G2 display-only branch parentage.
    parent_subleg_id: str = ""
    parent_subleg_label: str = ""
    parent_takeoff_label: str = ""
    is_branch_subleg: bool = False


@dataclass(frozen=True)
class CommonMainLegSublegSchematicV1:
    heat_source_label: str = "Boiler"
    common_main_label: str = "Common main"
    routes: tuple[CommonMainLegSublegRouteV1, ...] = ()
    balancing_point_evidence: tuple[
        CommonMainLegSublegBalancingPointEvidenceV1, ...
    ] = ()
    status: str = ""


class CommonMainLegSublegSchematicWidgetV1(QWidget):
    """
    Display-only DEV topology schematic.

    H-S26-G2:
    Branch sublegs are visually attached to the parent/common subleg
    via a "Branch take-off — TBA" marker.

    This is topology meaning only, not final engineering geometry.
    """

    # --------------------------------------------------------------
    # H-S34-C — shared schematic geometry
    # --------------------------------------------------------------
    # Shared by the Proportioning and clean Proportioned instances.
    # Layout/display only; no engineering or ProjectState mutation.
    _MIN_CANVAS_WIDTH = 1500
    _BASE_CANVAS_HEIGHT = 260

    _FIRST_LEG_Y = 92.0
    _ROUTE_ROW_PITCH = 70.0
    _BRANCH_ROW_PITCH = 72.0
    _AFTER_PRIMARY_GAP = 12.0
    _AFTER_LEG_GAP = 14.0
    _FOOTER_RESERVE = 64.0

    _BOILER_X = 18.0
    _BOILER_Y = 14.0
    _BOILER_WIDTH = 120.0
    _BOILER_HEIGHT = 28.0

    _COMMON_MAIN_X = 60.0
    _COMMON_MAIN_TOP = 58.0
    _COMMON_MAIN_WIDTH = 36.0
    _COMMON_MAIN_MIN_HEIGHT = 96.0
    _COMMON_MAIN_BOTTOM_PAD = 20.0

    _LEG_X = 118.0
    _LEG_WIDTH = 92.0
    _LEG_HEIGHT = 24.0

    _SUBLEG_X = 252.0
    _SUBLEG_WIDTH = 104.0
    _SUBLEG_HEIGHT = 24.0

    # H-S34-E: leave usable trace lengths for later hover evidence while
    # keeping the schematic nodes compact.
    _SUBLEG_TO_ROOM_GAP = 42.0
    _ROOM_WIDTH = 58.0
    _ROOM_HEIGHT = 22.0
    _ROOM_GAP = 42.0

    _RIGHT_MARGIN = 80.0
    _NODE_CENTER_OFFSET = 5.0

    _BRANCH_MIN_X = 390.0
    _BRANCH_TAKEOFF_TO_WIDGET_GAP = 42.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._schematic: CommonMainLegSublegSchematicV1 | None = None
        self._focus: dict[str, str] = {}
        self._focus_callback = None

        self._room_hit_rects: list[tuple[QRectF, dict[str, str]]] = []
        self._subleg_hit_rects: list[tuple[QRectF, dict[str, str]]] = []

        # H-S39-A — room authority-evidence hover hit regions.
        self._room_hover_hit_rects: list[
            tuple[
                QRectF,
                CommonMainLegSublegRouteV1,
                CommonMainLegSublegRoomEvidenceV1,
                int,
            ]
        ] = []
        # H-S39-B — blue room-node hover presentation only.
        self._hovered_room_key: tuple[str, str] | None = None

        # H-S36-B — schematic section-evidence hover.
        # Hit rectangles exist only for mapped room-entry trace segments.
        self._section_trace_hit_rects: list[
            tuple[
                QRectF,
                CommonMainLegSublegRouteV1,
                CommonMainLegSublegSectionEvidenceV1,
            ]
        ] = []
        self._hovered_section_trace_key: tuple[str, int, str] | None = None

        # H-S41-A — display-only common-main / leg / subleg hover.
        self._hierarchy_hover_hit_rects: list[
            tuple[QRectF, str, str]
        ] = []
        self._hovered_hierarchy_key: tuple[str, str] | None = None

        self.setMinimumSize(
            self._MIN_CANVAS_WIDTH,
            self._BASE_CANVAS_HEIGHT,
        )
        self.setMouseTracking(True)

    def set_schematic(
            self,
            schematic: CommonMainLegSublegSchematicV1 | None,
    ) -> None:
        self._schematic = schematic
        self._hovered_section_trace_key = None
        self._hovered_room_key = None
        self._hovered_hierarchy_key = None
        self._section_trace_hit_rects = []
        self._room_hover_hit_rects = []
        self._hierarchy_hover_hit_rects = []
        QToolTip.hideText()

        routes = list(getattr(schematic, "routes", ()) or ())
        route_count = len(routes)

        compact_base_width = self._MIN_CANVAS_WIDTH
        compact_base_height = self._BASE_CANVAS_HEIGHT

        route_start_x = self._SUBLEG_X
        subleg_width = self._SUBLEG_WIDTH
        room_start_gap = self._SUBLEG_TO_ROOM_GAP
        room_width = self._ROOM_WIDTH
        room_gap = self._ROOM_GAP
        right_margin = self._RIGHT_MARGIN

        def route_width_from_start(
                *,
                x_start: float,
                room_count: int,
        ) -> float:
            if room_count <= 0:
                return x_start + subleg_width + right_margin

            return (
                x_start
                + subleg_width
                + room_start_gap
                + (room_count * room_width)
                + (max(0, room_count - 1) * room_gap)
                + right_margin
            )

        max_required_width = float(compact_base_width)
        max_parent_room_count = 0

        for route in routes:
            room_count = len(
                tuple(getattr(route, "room_labels", ()) or ())
            )

            max_required_width = max(
                max_required_width,
                route_width_from_start(
                    x_start=route_start_x,
                    room_count=room_count,
                ),
            )

            if not bool(getattr(route, "is_branch_subleg", False)):
                max_parent_room_count = max(
                    max_parent_room_count,
                    room_count,
                )

        if max_parent_room_count > 1:
            takeoff_gap_index = max(
                0,
                min(max_parent_room_count - 2, max_parent_room_count // 2),
            )
            approximate_takeoff_x = (
                route_start_x
                + subleg_width
                + room_start_gap
                + (takeoff_gap_index * (room_width + room_gap))
                + room_width
                + (room_gap / 2.0)
            )
        elif max_parent_room_count == 1:
            approximate_takeoff_x = (
                route_start_x
                + subleg_width
                + room_start_gap
                - 10.0
            )
        else:
            approximate_takeoff_x = route_start_x + subleg_width + 40.0

        branch_x_start = max(
            self._BRANCH_MIN_X,
            approximate_takeoff_x
            + self._BRANCH_TAKEOFF_TO_WIDGET_GAP,
        )

        for route in routes:
            if not bool(getattr(route, "is_branch_subleg", False)):
                continue

            room_count = len(
                tuple(getattr(route, "room_labels", ()) or ())
            )

            max_required_width = max(
                max_required_width,
                route_width_from_start(
                    x_start=branch_x_start,
                    room_count=room_count,
                ),
            )

        required_width = int(max_required_width)
        required_height = max(
            compact_base_height,
            int(
                self._FIRST_LEG_Y
                + (max(1, route_count) * self._BRANCH_ROW_PITCH)
                + self._FOOTER_RESERVE
            ),
        )

        self.setMinimumSize(
            required_width,
            required_height,
        )

        self.update()

    def set_focus_callback(self, callback) -> None:
        self._focus_callback = callback

    def set_focus(self, focus: dict | None) -> None:
        focus = focus or {}

        self._focus = {
            "leg_id": str(focus.get("leg_id", "") or ""),
            "subleg_id": str(focus.get("subleg_id", "") or ""),
            "room_id": str(focus.get("room_id", "") or ""),
        }

        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QBrush(Qt.white))

        self._room_hit_rects = []
        self._subleg_hit_rects = []
        self._section_trace_hit_rects = []
        self._room_hover_hit_rects = []
        self._hierarchy_hover_hit_rects = []

        schematic = self._schematic

        if schematic is None or not getattr(schematic, "routes", ()):
            painter.setPen(QPen(Qt.gray))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "No common-main / leg / subleg topology available",
            )
            return

        routes = list(getattr(schematic, "routes", ()) or [])

        route_by_id = {
            str(route.subleg_id): route
            for route in routes
            if str(route.subleg_id or "")
        }

        children_by_parent: dict[str, list[CommonMainLegSublegRouteV1]] = {}
        routes_by_leg: dict[str, list[CommonMainLegSublegRouteV1]] = {}
        leg_order: list[str] = []

        for route in routes:
            leg_id = str(route.leg_id or "")

            if leg_id not in routes_by_leg:
                routes_by_leg[leg_id] = []
                leg_order.append(leg_id)

            routes_by_leg[leg_id].append(route)

            parent_id = str(route.parent_subleg_id or "")
            if parent_id:
                children_by_parent.setdefault(parent_id, []).append(route)

        # H-S34-F: carry existing route focus back to the heat source.
        schematic_focused = any(
            self._is_route_focused(route)
            for leg_routes in routes_by_leg.values()
            for route in leg_routes
        )
        self._paint_header(
            painter,
            schematic,
            focused=schematic_focused,
        )

        y = self._FIRST_LEG_Y

        leg_center_ys: list[float] = []

        for leg_id in leg_order:
            leg_routes = routes_by_leg.get(leg_id, [])

            if not leg_routes:
                continue

            top_routes = [
                route for route in leg_routes
                if not str(route.parent_subleg_id or "")
            ]

            if not top_routes:
                top_routes = [
                    route for route in leg_routes
                    if not bool(getattr(route, "is_branch_subleg", False))
                ]

            if not top_routes and leg_routes:
                top_routes = [leg_routes[0]]

            leg_label = str(top_routes[0].leg_label or leg_id or "Leg")
            leg_focused = any(
                self._is_route_focused(route)
                for route in leg_routes
            )
            y = self._paint_leg_heading(
                painter,
                leg_id,
                leg_label,
                y,
                focused=leg_focused,
            )

            # H-S26-G2j:
            # Leg heading centre. The common-main vertical tracer stops at
            # the last leg, not below it.
            leg_center_ys.append(
                y + self._NODE_CENTER_OFFSET
            )

            for route in top_routes:
                parent_y = y

                route_geometry = self._paint_route(
                    painter,
                    route=route,
                    x_start=self._SUBLEG_X,
                    y=parent_y,
                    branch=False,
                )

                y = parent_y + self._ROUTE_ROW_PITCH

                for child in children_by_parent.get(route.subleg_id, []):
                    takeoff_x = route_geometry.get("takeoff_x", 360.0)

                    # H-S26-G2h:
                    # Branch subleg sits to the right of the take-off
                    # trace, so the branch clearly joins the parent/common
                    # route.
                    branch_x_start = max(
                        self._BRANCH_MIN_X,
                        takeoff_x
                        + self._BRANCH_TAKEOFF_TO_WIDGET_GAP,
                    )

                    if self._is_route_focused(child):
                        self._paint_route_trace_to_x(
                            painter,
                            route=route,
                            x_start=self._SUBLEG_X,
                            y=parent_y,
                            stop_x=takeoff_x,
                        )

                    self._paint_branch_takeoff(
                        painter,
                        parent_route=route,
                        branch_route=child,
                        takeoff_x=takeoff_x,
                        branch_x_start=branch_x_start,
                        parent_y=parent_y,
                        branch_y=y,
                    )

                    self._paint_route(
                        painter,
                        route=child,
                        x_start=branch_x_start,
                        y=y,
                        branch=True,
                    )

                    y += self._BRANCH_ROW_PITCH

                y += self._AFTER_PRIMARY_GAP

            y += self._AFTER_LEG_GAP

        # H-S26-G2j final common-main tracer.
        # Drawn after route layout is known so the spine stops exactly at
        # the final leg connection.
        if leg_center_ys:
            self._paint_common_main_tracer(
                painter,
                y_top=self._COMMON_MAIN_TOP,
                y_bottom=leg_center_ys[-1],
                focused=schematic_focused,
            )

        self._paint_footer(painter, schematic)

    def _paint_header(
            self,
            painter: QPainter,
            schematic: CommonMainLegSublegSchematicV1,
            *,
            focused: bool = False,
    ) -> None:
        # H-S34-C: boiler above the shared left-hand common-main spine.
        painter.setFont(QFont("", 8))

        heat_rect = QRectF(
            self._BOILER_X,
            self._BOILER_Y,
            self._BOILER_WIDTH,
            self._BOILER_HEIGHT,
        )

        heat_border_width = 2.2 if focused else 1.4
        painter.setPen(QPen(QColor(170, 70, 70), heat_border_width))
        painter.setBrush(QBrush(QColor(255, 245, 245)))
        painter.drawRoundedRect(heat_rect, 6.0, 6.0)

        painter.setPen(QPen(QColor(70, 40, 40)))
        painter.drawText(
            heat_rect,
            Qt.AlignCenter,
            str(
                schematic.heat_source_label
                or "Boiler / Heat Source"
            ),
        )

        painter.setPen(self._trace_pen(focused=focused))
        painter.drawLine(
            QPointF(
                heat_rect.center().x(),
                heat_rect.bottom(),
            ),
            QPointF(
                self._COMMON_MAIN_X
                + (self._COMMON_MAIN_WIDTH / 2.0),
                self._COMMON_MAIN_TOP,
            ),
        )

    def _paint_common_main_tracer(
            self,
            painter: QPainter,
            *,
            y_top: float,
            y_bottom: float,
            focused: bool = False,
    ) -> None:
        # H-S34-C: far-left vertical rounded common-main spine.
        common_height = max(
            self._COMMON_MAIN_MIN_HEIGHT,
            (
                y_bottom
                - y_top
                + self._COMMON_MAIN_BOTTOM_PAD
            ),
        )

        common_rect = QRectF(
            self._COMMON_MAIN_X,
            y_top,
            self._COMMON_MAIN_WIDTH,
            common_height,
        )

        # H-S41-A: hover is display-only and takes visual priority over
        # the existing focus outline without changing focus itself.
        common_hovered = self._hovered_hierarchy_key == (
            "common_main",
            "common_main",
        )
        if common_hovered:
            common_border = QColor(35, 125, 185)
            common_border_width = 3.0
        elif focused:
            common_border = QColor(170, 35, 35)
            common_border_width = 1.8
        else:
            common_border = QColor(45, 100, 180)
            common_border_width = 1.6

        self._hierarchy_hover_hit_rects.append(
            (common_rect, "common_main", "common_main")
        )
        painter.setPen(QPen(common_border, common_border_width))
        painter.setBrush(QBrush(QColor(230, 240, 255)))
        painter.drawRoundedRect(
            common_rect,
            self._COMMON_MAIN_WIDTH / 2.0,
            self._COMMON_MAIN_WIDTH / 2.0,
        )

        painter.save()
        painter.translate(common_rect.center())
        painter.rotate(-90.0)

        rotated_text_rect = QRectF(
            -common_rect.height() / 2.0,
            -common_rect.width() / 2.0,
            common_rect.height(),
            common_rect.width(),
        )

        schematic = self._schematic
        common_main_label = str(
            getattr(
                schematic,
                "common_main_label",
                "",
            )
            or "Common main"
        )

        painter.setPen(QPen(QColor(25, 65, 130)))
        painter.setFont(QFont("", 8))
        painter.drawText(
            rotated_text_rect.adjusted(
                8.0,
                0.0,
                -8.0,
                0.0,
            ),
            Qt.AlignCenter,
            common_main_label,
        )
        painter.restore()

    def _paint_leg_heading(
            self,
            painter: QPainter,
            leg_id: str,
            leg_label: str,
            y: float,
            *,
            focused: bool = False,
    ) -> float:
        painter.setFont(QFont("", 8))

        leg_rect = QRectF(
            self._LEG_X,
            y - 7.0,
            self._LEG_WIDTH,
            self._LEG_HEIGHT,
        )

        # H-S41-A: blue hierarchy hover does not alter route focus.
        leg_key = str(leg_id or "")
        leg_hovered = self._hovered_hierarchy_key == ("leg", leg_key)
        if leg_hovered:
            leg_border = QColor(35, 125, 185)
            leg_border_width = 3.0
        elif focused:
            leg_border = QColor(170, 35, 35)
            leg_border_width = 1.4
        else:
            leg_border = QColor(70, 105, 150)
            leg_border_width = 1.3

        self._hierarchy_hover_hit_rects.append(
            (leg_rect, "leg", leg_key)
        )
        painter.setPen(QPen(leg_border, leg_border_width))
        painter.setBrush(QBrush(QColor(242, 247, 255)))
        painter.drawRoundedRect(leg_rect, 5.0, 5.0)

        painter.setPen(QPen(QColor(35, 75, 130)))
        painter.drawText(
            leg_rect.adjusted(3.0, 0.0, -3.0, 0.0),
            Qt.AlignCenter,
            leg_label or "Leg",
        )

        painter.setPen(self._trace_pen(focused=focused))

        centre_y = y + self._NODE_CENTER_OFFSET

        painter.drawLine(
            QPointF(
                self._COMMON_MAIN_X + self._COMMON_MAIN_WIDTH,
                centre_y,
            ),
            QPointF(leg_rect.left(), centre_y),
        )

        painter.drawLine(
            QPointF(leg_rect.right(), centre_y),
            QPointF(self._SUBLEG_X, centre_y),
        )

        return y

    @staticmethod
    def _display_room_label(room_label: object) -> str:
        """
        H-S26-G2d:
        Compact schematic room label.

        Display only:
        • underlying room_id remains unchanged for focus/click linkage
        • only the visible text is shortened
        """
        text = str(room_label or "").strip()

        if text.lower().startswith("room-"):
            text = text[5:]

        if len(text) > 10:
            text = text[:9] + "…"

        return text or "—"

    def _is_route_focused(
            self,
            route: CommonMainLegSublegRouteV1,
    ) -> bool:
        focus_subleg_id = str(self._focus.get("subleg_id", "") or "")
        route_subleg_id = str(getattr(route, "subleg_id", "") or "")

        return bool(focus_subleg_id) and focus_subleg_id == route_subleg_id

    @staticmethod
    def _trace_pen(*, focused: bool) -> QPen:
        """
        H-S26-G2h:
        Tracer lines are neutral unless the route/subleg is selected.
        """
        if focused:
            return QPen(QColor(170, 35, 35), 2.2)

        return QPen(QColor(120, 120, 120), 1.8)


    @staticmethod
    def _shown_hierarchy_value_v1(value: object) -> str:
        text = str(value or "").strip()
        return text if text and text not in {"-", "—"} else "—"

    @staticmethod
    def _unique_route_values_v1(
            routes: tuple[CommonMainLegSublegRouteV1, ...],
            attribute: str,
    ) -> tuple[str, ...]:
        values: list[str] = []
        for route in routes:
            value = str(getattr(route, attribute, "") or "").strip()
            if value and value not in values:
                values.append(value)
        return tuple(values)

    @staticmethod
    def _first_section_evidence_v1(
            route: CommonMainLegSublegRouteV1 | None,
    ) -> CommonMainLegSublegSectionEvidenceV1 | None:
        evidence_rows = tuple(
            getattr(route, "section_evidence", ()) or ()
        )
        if not evidence_rows:
            return None
        return min(
            evidence_rows,
            key=lambda row: (
                int(getattr(row, "section_ordinal", 0) or 0),
                int(getattr(row, "trace_index", -1)),
            ),
        )

    def _balancing_point_tooltip_lines_v1(
            self,
            scope: str,
            stable_id: str,
    ) -> list[str]:
        schematic = self._schematic
        wanted_scope = "main" if scope == "common_main" else scope
        evidence_rows = tuple(
            row
            for row in tuple(
                getattr(schematic, "balancing_point_evidence", ()) or ()
            )
            if str(getattr(row, "point_scope", "") or "").lower()
            == wanted_scope
            and (
                scope == "common_main"
                or str(getattr(row, "target_id", "") or "") == stable_id
            )
        )
        if not evidence_rows:
            return []
        shown = self._shown_hierarchy_value_v1
        lines = ["Balancing-point evidence:"]
        for index, row in enumerate(evidence_rows):
            if index:
                lines.append("—")
            lines.extend(
                [
                    f"Point: {shown(getattr(row, 'label', ''))}",
                    f"Topology: {shown(getattr(row, 'topology', ''))}",
                    f"Governed routes: {shown(getattr(row, 'governed_routes', ''))}",
                    f"Point flow: {shown(getattr(row, 'point_flow', ''))}",
                    f"Allocated Δp: {shown(getattr(row, 'allocated_dp', ''))}",
                    f"Resistance: {shown(getattr(row, 'resistance', ''))}",
                    f"Method: {shown(getattr(row, 'method', ''))}",
                    f"Valve duty: {shown(getattr(row, 'valve_duty', ''))}",
                    f"Required Kv: {shown(getattr(row, 'required_kv', ''))}",
                    f"Controlled circuit Δp: {shown(getattr(row, 'controlled_dp', ''))}",
                    f"Authority: {shown(getattr(row, 'authority', ''))}",
                ]
            )
        return lines

    def _hierarchy_tooltip_text_v1(
            self,
            scope: str,
            stable_id: str,
    ) -> str:
        # Summarise prepared topology/evidence; derive no hydraulics.
        shown = self._shown_hierarchy_value_v1
        schematic = self._schematic
        routes = tuple(getattr(schematic, "routes", ()) or ())

        if scope == "common_main":
            leg_ids = self._unique_route_values_v1(routes, "leg_id")
            leg_labels = self._unique_route_values_v1(routes, "leg_label")
            subleg_ids = self._unique_route_values_v1(routes, "subleg_id")
            # room_labels is tuple-valued, so count stable room identities
            # separately while preserving their displayed order.
            rooms: list[str] = []
            for route in routes:
                for room_id in tuple(getattr(route, "room_labels", ()) or ()):
                    room_key = str(room_id or "")
                    if room_key and room_key not in rooms:
                        rooms.append(room_key)
            label = shown(
                getattr(schematic, "common_main_label", "") or "Common main"
            )
            status = shown(getattr(schematic, "status", ""))
            status_lines = textwrap.wrap(status, width=72) or ["—"]
            leg_text = ", ".join(leg_labels) if leg_labels else "—"
            lines = [
                label,
                "Scope: Common main",
                f"Legs supplied: {len(leg_ids)} ({leg_text})",
                f"Sublegs supplied: {len(subleg_ids)}",
                f"Unique rooms supplied: {len(rooms)}",
                *self._balancing_point_tooltip_lines_v1(scope, stable_id),
                f"Status: {status_lines[0]}",
            ]
            lines.extend(f"        {line}" for line in status_lines[1:])
            return "\n".join(lines)

        if scope == "leg":
            leg_routes = tuple(
                route for route in routes
                if str(getattr(route, "leg_id", "") or "") == stable_id
            )
            if not leg_routes:
                return f"Leg\nLeg ID: {shown(stable_id)}"
            primary = next(
                (
                    route for route in leg_routes
                    if not str(getattr(route, "parent_subleg_id", "") or "")
                ),
                leg_routes[0],
            )
            rooms: list[str] = []
            for route in leg_routes:
                for room_id in tuple(getattr(route, "room_labels", ()) or ()):
                    room_key = str(room_id or "")
                    if room_key and room_key not in rooms:
                        rooms.append(room_key)
            subleg_labels = self._unique_route_values_v1(
                leg_routes,
                "subleg_label",
            )
            entry = self._first_section_evidence_v1(primary)
            return "\n".join(
                [
                    shown(getattr(primary, "leg_label", "") or stable_id),
                    "Scope: Leg",
                    f"Leg ID: {shown(stable_id)}",
                    f"Sublegs: {len(leg_routes)} ({', '.join(subleg_labels) or '—'})",
                    f"Unique rooms: {len(rooms)}",
                    f"Entry carried flow: {shown(getattr(entry, 'flow_kg_s', ''))}",
                    f"Entry pipe: {shown(getattr(entry, 'pipe_dn', ''))}",
                    *self._balancing_point_tooltip_lines_v1(scope, stable_id),
                ]
            )

        route = next(
            (
                candidate for candidate in routes
                if str(getattr(candidate, "subleg_id", "") or "") == stable_id
            ),
            None,
        )
        if route is None:
            return f"Subleg\nSubleg ID: {shown(stable_id)}"
        entry = self._first_section_evidence_v1(route)
        parent = (
            shown(
                getattr(route, "parent_subleg_label", "")
                or getattr(route, "parent_subleg_id", "")
            )
            if str(getattr(route, "parent_subleg_id", "") or "")
            else "Common main / leg entry"
        )
        role = shown(getattr(route, "role", "") or "Subleg")
        room_labels = tuple(getattr(route, "room_labels", ()) or ())
        return "\n".join(
            [
                shown(
                    getattr(route, "subleg_label", "")
                    or getattr(route, "subleg_id", "")
                ),
                f"Scope: {role}",
                f"Subleg ID: {shown(stable_id)}",
                f"Leg: {shown(getattr(route, 'leg_label', ''))} ({shown(getattr(route, 'leg_id', ''))})",
                f"Parent: {parent}",
                f"Rooms: {len(room_labels)}",
                f"Entry carried flow: {shown(getattr(entry, 'flow_kg_s', ''))}",
                f"Entry pipe: {shown(getattr(entry, 'pipe_dn', ''))}",
                f"Entry Δp/m: {shown(getattr(entry, 'dp_per_m', ''))}",
                *self._balancing_point_tooltip_lines_v1(scope, stable_id),
            ]
        )

    @staticmethod
    def _room_evidence_for_room_id_v1(
            route: CommonMainLegSublegRouteV1,
            room_id: str,
    ) -> CommonMainLegSublegRoomEvidenceV1 | None:
        """Return prepared evidence for one stable room identity."""
        wanted = str(room_id or "")

        for evidence in tuple(getattr(route, "room_evidence", ()) or ()):
            if str(getattr(evidence, "room_id", "") or "") == wanted:
                return evidence

        return None

    @staticmethod
    def _room_evidence_key_v1(
            route: CommonMainLegSublegRouteV1,
            evidence: CommonMainLegSublegRoomEvidenceV1,
    ) -> tuple[str, str]:
        return (
            str(getattr(route, "subleg_id", "") or ""),
            str(getattr(evidence, "room_id", "") or ""),
        )

    @staticmethod
    def _room_evidence_tooltip_text_v1(
            route: CommonMainLegSublegRouteV1,
            evidence: CommonMainLegSublegRoomEvidenceV1,
            incoming_section: CommonMainLegSublegSectionEvidenceV1 | None = None,
    ) -> str:
        """Format prepared evidence only; no engineering derivation."""
        def shown(value: object) -> str:
            text = str(value or "").strip()
            return text if text and text not in {"-", "—"} else "—"

        route_label = shown(
            getattr(route, "subleg_label", "")
            or getattr(route, "subleg_id", "")
        )
        room_label = shown(
            getattr(evidence, "room_label", "")
            or getattr(evidence, "room_id", "")
        )
        status = shown(getattr(evidence, "status", ""))
        status_lines = textwrap.wrap(status, width=72) or ["—"]

        lines = [
            room_label,
            f"Room ID: {shown(getattr(evidence, 'room_id', ''))}",
            f"Route: {route_label}",
            f"Design heat loss: {shown(getattr(evidence, 'design_heat_loss_W', ''))}",
            f"Emitter(s): {shown(getattr(evidence, 'emitter_summary', ''))}",
            f"Emitter design output: {shown(getattr(evidence, 'emitter_output_W', ''))}",
            f"Emitter design flow: {shown(getattr(evidence, 'emitter_flow_kg_s', ''))}",
            f"Flow basis: {shown(getattr(evidence, 'flow_basis', ''))}",
        ]

        if incoming_section is not None:
            lines.extend(
                [
                    f"Incoming Basic PS carried flow: {shown(getattr(incoming_section, 'flow_kg_s', ''))}",
                    f"Incoming Basic PS pipe: {shown(getattr(incoming_section, 'pipe_dn', ''))}",
                ]
            )

        lines.append(f"Status: {status_lines[0]}")
        lines.extend(f"        {line}" for line in status_lines[1:])
        return "\n".join(lines)

    @staticmethod
    def _section_evidence_for_trace_index_v1(
            route: CommonMainLegSublegRouteV1,
            trace_index: int,
    ) -> CommonMainLegSublegSectionEvidenceV1 | None:
        """Return existing evidence for one mapped room-entry trace."""
        for evidence in tuple(
                getattr(route, "section_evidence", ()) or ()
        ):
            if int(getattr(evidence, "trace_index", -1)) == int(trace_index):
                return evidence

        return None

    @staticmethod
    def _section_evidence_key_v1(
            route: CommonMainLegSublegRouteV1,
            evidence: CommonMainLegSublegSectionEvidenceV1,
    ) -> tuple[str, int, str]:
        return (
            str(getattr(route, "subleg_id", "") or ""),
            int(getattr(evidence, "trace_index", -1)),
            str(getattr(evidence, "section_id", "") or ""),
        )

    @staticmethod
    def _section_evidence_tooltip_text_v1(
            route: CommonMainLegSublegRouteV1,
            evidence: CommonMainLegSublegSectionEvidenceV1,
    ) -> str:
        """Format existing evidence only; no engineering derivation."""
        def shown(value: object) -> str:
            text = str(value or "").strip()
            return text if text and text not in {"-", "—"} else "—"

        status = shown(getattr(evidence, "status", ""))
        status_lines = textwrap.wrap(status, width=72) or ["—"]
        ordinal = int(getattr(evidence, "section_ordinal", 0) or 0)
        route_label = shown(
            getattr(route, "subleg_label", "")
            or getattr(route, "subleg_id", "")
        )

        lines = [
            f"{route_label} — Section {ordinal or '—'}",
            f"From: {shown(getattr(evidence, 'from_label', ''))}",
            f"To: {shown(getattr(evidence, 'to_label', ''))}",
            f"Flow: {shown(getattr(evidence, 'flow_kg_s', ''))}",
            f"Pipe DN: {shown(getattr(evidence, 'pipe_dn', ''))}",
            f"Δp/m: {shown(getattr(evidence, 'dp_per_m', ''))}",
            f"Length: {shown(getattr(evidence, 'length', ''))}",
            f"K: {shown(getattr(evidence, 'k', ''))}",
            f"Section Δp: {shown(getattr(evidence, 'section_dp', ''))}",
            f"Iter: {shown(getattr(evidence, 'iter', ''))}",
            f"Status: {status_lines[0]}",
        ]
        lines.extend(f"        {line}" for line in status_lines[1:])
        return "\n".join(lines)

    def _register_section_trace_hit_rect_v1(
            self,
            *,
            rect: QRectF,
            route: CommonMainLegSublegRouteV1,
            trace_index: int,
    ) -> CommonMainLegSublegSectionEvidenceV1 | None:
        evidence = self._section_evidence_for_trace_index_v1(
            route,
            trace_index,
        )

        if evidence is not None:
            self._section_trace_hit_rects.append((rect, route, evidence))

        return evidence

    def _section_trace_pen_v1(
            self,
            *,
            default_pen: QPen,
            route: CommonMainLegSublegRouteV1,
            evidence: CommonMainLegSublegSectionEvidenceV1 | None,
    ) -> QPen:
        if evidence is None:
            return default_pen

        evidence_key = self._section_evidence_key_v1(route, evidence)

        if evidence_key == self._hovered_section_trace_key:
            return QPen(QColor(35, 125, 185), 3.2)

        return default_pen

    def _paint_route(
            self,
            painter: QPainter,
            *,
            route: CommonMainLegSublegRouteV1,
            x_start: float,
            y: float,
            branch: bool,
    ) -> dict[str, float]:
        route_focused = self._is_route_focused(route)
        trace_pen = self._trace_pen(focused=route_focused)

        subleg_w = self._SUBLEG_WIDTH
        subleg_h = self._SUBLEG_HEIGHT
        room_w = self._ROOM_WIDTH
        room_h = self._ROOM_HEIGHT
        room_gap = self._ROOM_GAP

        subleg_rect = QRectF(x_start, y - 6.5, subleg_w, subleg_h)

        # H-S34-F4: when a room is the exact selection, its containing
        # subleg is traversed path structure rather than the selected object.
        room_focus_active = bool(
            str(self._focus.get("room_id", "") or "")
        )
        subleg_exactly_focused = route_focused and not room_focus_active

        subleg_key = str(getattr(route, "subleg_id", "") or "")
        subleg_hovered = self._hovered_hierarchy_key == (
            "subleg",
            subleg_key,
        )
        if subleg_hovered:
            border = QColor(35, 125, 185)
            border_width = 3.0
        elif subleg_exactly_focused:
            border = QColor(190, 115, 35)
            border_width = 2.6
        elif route_focused:
            border = QColor(170, 35, 35)
            border_width = 1.4
        else:
            border = QColor(70, 105, 150)
            border_width = 1.2

        fill = QColor(242, 247, 255)

        painter.setPen(QPen(border, border_width))
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(subleg_rect, 5.0, 5.0)

        painter.setPen(QPen(QColor(35, 75, 130)))
        painter.setFont(QFont("", 7))
        painter.drawText(
            subleg_rect.adjusted(4.0, 1.0, -4.0, -1.0),
            Qt.AlignCenter | Qt.TextWordWrap,
            str(route.subleg_label or route.subleg_id or "Subleg"),
        )

        focus = {
            "leg_id": str(route.leg_id or ""),
            "subleg_id": str(route.subleg_id or ""),
            "room_id": "",
        }
        self._subleg_hit_rects.append((subleg_rect, focus))
        self._hierarchy_hover_hit_rects.append(
            (subleg_rect, "subleg", subleg_key)
        )

        role_text = str(route.role or "")
        if role_text:
            painter.setPen(QPen(QColor(90, 90, 90)))
            painter.setFont(QFont("", 7))
            painter.drawText(
                QRectF(
                    subleg_rect.left(),
                    subleg_rect.bottom() + 0.5,
                    subleg_rect.width(),
                    12.0,
                ),
                Qt.AlignCenter,
                role_text,
            )

        room_labels = tuple(route.room_labels or ())

        # H-S34-F1: stop exact room focus at the clicked room.
        focus_room_id = str(self._focus.get("room_id", "") or "")
        focused_room_index = next(
            (
                index
                for index, room_label in enumerate(room_labels)
                if focus_room_id and str(room_label) == focus_room_id
            ),
            None,
        )

        line_y = subleg_rect.center().y()
        previous_x = subleg_rect.right()

        if room_labels:
            first_room_x = (
                subleg_rect.right()
                + self._SUBLEG_TO_ROOM_GAP
            )

            first_trace_evidence = (
                self._register_section_trace_hit_rect_v1(
                    rect=QRectF(
                        previous_x,
                        line_y - 7.0,
                        first_room_x - previous_x,
                        14.0,
                    ),
                    route=route,
                    trace_index=0,
                )
            )
            painter.setPen(
                self._section_trace_pen_v1(
                    default_pen=trace_pen,
                    route=route,
                    evidence=first_trace_evidence,
                )
            )
            painter.drawLine(
                QPointF(previous_x, line_y),
                QPointF(first_room_x, line_y),
            )

            for index, room_label in enumerate(room_labels):
                x = first_room_x + (index * (room_w + room_gap))
                room_rect = QRectF(x, y - 4.5, room_w, room_h)
                room_evidence = self._room_evidence_for_room_id_v1(
                    route,
                    str(room_label),
                )
                room_hovered = (
                    room_evidence is not None
                    and self._room_evidence_key_v1(route, room_evidence)
                    == self._hovered_room_key
                )

                room_focused = (
                    str(self._focus.get("room_id", "") or "")
                    and str(self._focus.get("room_id", "") or "")
                    == str(room_label)
                )

                # H-S34-F2: distinguish traversed rooms from the clicked room.
                room_on_focused_path = (
                    route_focused
                    and (
                        focused_room_index is None
                        or index <= focused_room_index
                    )
                )

                if room_hovered:
                    room_border = QColor(35, 125, 185)
                    room_border_width = 3.0
                elif room_focused:
                    room_border = QColor(190, 115, 35)
                    room_border_width = 2.4
                elif room_on_focused_path:
                    room_border = QColor(170, 35, 35)
                    room_border_width = 1.4
                else:
                    room_border = QColor(110, 145, 110)
                    room_border_width = 1.1

                painter.setPen(QPen(room_border, room_border_width))
                painter.setBrush(QBrush(QColor(248, 255, 248)))
                painter.drawRoundedRect(room_rect, 4.0, 4.0)

                painter.setPen(QPen(Qt.black))
                painter.setFont(QFont("", 7))
                painter.drawText(
                    room_rect,
                    Qt.AlignCenter,
                    self._display_room_label(room_label),
                )

                self._room_hit_rects.append(
                    (
                        room_rect,
                        {
                            "leg_id": str(route.leg_id or ""),
                            "subleg_id": str(route.subleg_id or ""),
                            "room_id": str(room_label),
                        },
                    )
                )

                if room_evidence is not None:
                    self._room_hover_hit_rects.append(
                        (room_rect, route, room_evidence, index)
                    )

                if index > 0:
                    prev_right = x - room_gap
                    connector_focused = (
                        route_focused
                        and (
                            focused_room_index is None
                            or index <= focused_room_index
                        )
                    )
                    connector_evidence = (
                        self._register_section_trace_hit_rect_v1(
                            rect=QRectF(
                                prev_right,
                                line_y - 7.0,
                                x - prev_right,
                                14.0,
                            ),
                            route=route,
                            trace_index=index,
                        )
                    )
                    painter.setPen(
                        self._section_trace_pen_v1(
                            default_pen=self._trace_pen(
                                focused=connector_focused
                            ),
                            route=route,
                            evidence=connector_evidence,
                        )
                    )
                    painter.drawLine(
                        QPointF(prev_right, line_y),
                        QPointF(x, line_y),
                    )

            # Branch take-off is placed in a pipe/duct gap, not in the
            # middle of a room box.
            if len(room_labels) > 1:
                takeoff_gap_index = max(
                    0,
                    min(len(room_labels) - 2, len(room_labels) // 2),
                )
                takeoff_x = (
                    first_room_x
                    + (takeoff_gap_index * (room_w + room_gap))
                    + room_w
                    + (room_gap / 2.0)
                )
            else:
                takeoff_x = first_room_x - 10.0

        else:
            takeoff_x = subleg_rect.right() + 40.0

        return {
            "takeoff_x": takeoff_x,
            "line_y": line_y,
        }

    def _paint_route_trace_to_x(
            self,
            painter: QPainter,
            *,
            route: CommonMainLegSublegRouteV1,
            x_start: float,
            y: float,
            stop_x: float,
    ) -> None:
        # H-S34-F1: overlay focused connector gaps along a parent/common
        # route only as far as the selected child branch take-off. Room
        # boxes are not repainted.
        subleg_rect = QRectF(
            x_start,
            y - 6.5,
            self._SUBLEG_WIDTH,
            self._SUBLEG_HEIGHT,
        )
        line_y = subleg_rect.center().y()
        room_labels = tuple(route.room_labels or ())

        # H-S34-F3: the parent/common subleg is part of the traversed path,
        # but is not the exact selected subleg. Give it the same thin red
        # path outline used by included rooms, without changing its fill.
        painter.save()
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.setPen(QPen(QColor(170, 35, 35), 1.4))
        painter.drawRoundedRect(subleg_rect, 5.0, 5.0)
        painter.restore()

        segments: list[tuple[float, float]] = []

        if room_labels:
            first_room_x = (
                subleg_rect.right()
                + self._SUBLEG_TO_ROOM_GAP
            )
            segments.append((subleg_rect.right(), first_room_x))

            for index in range(1, len(room_labels)):
                room_x = (
                    first_room_x
                    + (index * (self._ROOM_WIDTH + self._ROOM_GAP))
                )
                segments.append(
                    (room_x - self._ROOM_GAP, room_x)
                )
        else:
            segments.append((subleg_rect.right(), stop_x))

        painter.setPen(self._trace_pen(focused=True))

        for segment_start, segment_end in segments:
            if stop_x <= segment_start:
                break

            focused_end = min(segment_end, stop_x)
            if focused_end > segment_start:
                painter.drawLine(
                    QPointF(segment_start, line_y),
                    QPointF(focused_end, line_y),
                )

            if stop_x <= segment_end:
                break

        # H-S34-F2: parent/common rooms already traversed before the selected
        # branch take-off share the thin focus-red path border. Their fill and
        # text remain unchanged.
        if room_labels:
            painter.save()
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.setPen(QPen(QColor(170, 35, 35), 1.4))

            for index in range(len(room_labels)):
                room_x = (
                    first_room_x
                    + (index * (self._ROOM_WIDTH + self._ROOM_GAP))
                )
                room_rect = QRectF(
                    room_x,
                    y - 4.5,
                    self._ROOM_WIDTH,
                    self._ROOM_HEIGHT,
                )

                if room_rect.right() > stop_x:
                    break

                painter.drawRoundedRect(room_rect, 4.0, 4.0)

            painter.restore()

    def _paint_branch_takeoff(
            self,
            painter: QPainter,
            *,
            parent_route: CommonMainLegSublegRouteV1,
            branch_route: CommonMainLegSublegRouteV1,
            takeoff_x: float,
            branch_x_start: float,
            parent_y: float,
            branch_y: float,
    ) -> None:
        """
        H-S26-G2K:
        Simplified branch take-off.

        Visual rule:
        • parent/common route continues through the tee via its normal route
          trace
        • branch drop/tee marks the approximate take-off
        • branch drop is vertical
        • only a short connector enters the branch subleg

        Display-only topology meaning.
        """
        parent_line_y = (
            parent_y + self._NODE_CENTER_OFFSET
        )
        branch_line_y = (
            branch_y + self._NODE_CENTER_OFFSET
        )

        branch_focused = self._is_route_focused(branch_route)
        branch_pen = self._trace_pen(focused=branch_focused)

        painter.setPen(branch_pen)

        # Vertical drop from parent/common route.
        painter.drawLine(
            QPointF(takeoff_x, parent_line_y),
            QPointF(takeoff_x, branch_line_y),
        )

        # Short connector into branch subleg.
        painter.drawLine(
            QPointF(takeoff_x, branch_line_y),
            QPointF(branch_x_start, branch_line_y),
        )

        # H-S34-D: the branch drop/tee is the take-off marker. Keep the
        # provisional-location label neutral so it is not mistaken for an
        # engineering warning or result state.
        painter.setPen(QPen(QColor(105, 105, 105)))
        painter.setFont(QFont("", 7))
        painter.drawText(
            QRectF(
                takeoff_x + 5.0,
                parent_line_y + 1.0,
                42.0,
                14.0,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            "TBA",
        )

    def _paint_footer(
            self,
            painter: QPainter,
            schematic: CommonMainLegSublegSchematicV1,
    ) -> None:
        status = str(schematic.status or "")

        if not status:
            return

        painter.setPen(QPen(QColor(95, 95, 95)))
        painter.setFont(QFont("", 8))
        painter.drawText(
            QRectF(
                12.0,
                float(self.height()) - 30.0,
                float(self.width()) - 24.0,
                22.0,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            status,
        )


    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position()

        # H-S39-A — room evidence has priority inside the room node.
        for rect, route, evidence, trace_index in reversed(
                self._room_hover_hit_rects
        ):
            if not rect.contains(pos):
                continue

            incoming_section = self._section_evidence_for_trace_index_v1(
                route,
                trace_index,
            )
            room_key = self._room_evidence_key_v1(route, evidence)
            needs_update = room_key != self._hovered_room_key
            self._hovered_room_key = room_key

            if self._hovered_section_trace_key is not None:
                self._hovered_section_trace_key = None
                needs_update = True
            if self._hovered_hierarchy_key is not None:
                self._hovered_hierarchy_key = None
                needs_update = True

            if needs_update:
                self.update()

            QToolTip.showText(
                event.globalPosition().toPoint(),
                self._room_evidence_tooltip_text_v1(
                    route,
                    evidence,
                    incoming_section,
                ),
                self,
            )
            event.accept()
            return

        for rect, route, evidence in reversed(
                self._section_trace_hit_rects
        ):
            if not rect.contains(pos):
                continue

            evidence_key = self._section_evidence_key_v1(route, evidence)
            needs_update = evidence_key != self._hovered_section_trace_key
            self._hovered_section_trace_key = evidence_key

            if self._hovered_room_key is not None:
                self._hovered_room_key = None
                needs_update = True
            if self._hovered_hierarchy_key is not None:
                self._hovered_hierarchy_key = None
                needs_update = True

            if needs_update:
                self.update()

            QToolTip.showText(
                event.globalPosition().toPoint(),
                self._section_evidence_tooltip_text_v1(route, evidence),
                self,
            )
            event.accept()
            return

        # H-S41-A — hierarchy nodes follow room and pipe-section priority.
        for rect, scope, stable_id in reversed(
                self._hierarchy_hover_hit_rects
        ):
            if not rect.contains(pos):
                continue

            hierarchy_key = (scope, stable_id)
            needs_update = hierarchy_key != self._hovered_hierarchy_key
            self._hovered_hierarchy_key = hierarchy_key

            if self._hovered_room_key is not None:
                self._hovered_room_key = None
                needs_update = True
            if self._hovered_section_trace_key is not None:
                self._hovered_section_trace_key = None
                needs_update = True

            if needs_update:
                self.update()

            QToolTip.showText(
                event.globalPosition().toPoint(),
                self._hierarchy_tooltip_text_v1(scope, stable_id),
                self,
            )
            event.accept()
            return

        needs_update = False
        if self._hovered_section_trace_key is not None:
            self._hovered_section_trace_key = None
            needs_update = True
        if self._hovered_room_key is not None:
            self._hovered_room_key = None
            needs_update = True
        if self._hovered_hierarchy_key is not None:
            self._hovered_hierarchy_key = None
            needs_update = True
        if needs_update:
            self.update()

        QToolTip.hideText()
        event.accept()

    def leaveEvent(self, event) -> None:  # noqa: N802
        needs_update = False
        if self._hovered_section_trace_key is not None:
            self._hovered_section_trace_key = None
            needs_update = True
        if self._hovered_room_key is not None:
            self._hovered_room_key = None
            needs_update = True
        if self._hovered_hierarchy_key is not None:
            self._hovered_hierarchy_key = None
            needs_update = True
        if needs_update:
            self.update()

        QToolTip.hideText()
        event.accept()

    def mousePressEvent(self, event) -> None:  # noqa: N802
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

        for rect, focus in reversed(self._subleg_hit_rects):
            if rect.contains(pos):
                self.set_focus(focus)

                if self._focus_callback is not None:
                    self._focus_callback(dict(focus))

                event.accept()
                return

        event.ignore()
