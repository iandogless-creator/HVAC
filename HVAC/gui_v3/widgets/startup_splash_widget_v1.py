from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QElapsedTimer, QLineF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget


_SPLASH_CYCLE_MS_V1 = 1800


@dataclass(frozen=True)
class SplashAnimationStateV1:
    phase: str
    drop_progress: float = 0.0
    splash_progress: float = 0.0


def splash_animation_state_v1(elapsed_ms: int) -> SplashAnimationStateV1:
    """Return the deterministic state for one repeated drop-and-splash cycle."""
    elapsed = max(0, int(elapsed_ms)) % _SPLASH_CYCLE_MS_V1
    if elapsed < 220:
        return SplashAnimationStateV1(
            "forming",
            drop_progress=elapsed / 220.0,
        )
    if elapsed < 980:
        return SplashAnimationStateV1(
            "falling",
            drop_progress=(elapsed - 220) / 760.0,
        )
    if elapsed < 1380:
        return SplashAnimationStateV1(
            "splash",
            splash_progress=(elapsed - 980) / 400.0,
        )
    return SplashAnimationStateV1("settled")


class StartupSplashWidgetV1(QWidget):
    """Small code-painted startup splash with one drop and one impact ripple."""

    def __init__(self) -> None:
        flags = (
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        super().__init__(None, flags)
        self.setObjectName("hvacgooeeStartupSplashV1")
        self.setFixedSize(360, 210)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._visible_clock_v1 = QElapsedTimer()
        self._animation_timer_v1 = QTimer(self)
        self._animation_timer_v1.setInterval(33)
        self._animation_timer_v1.timeout.connect(self.update)

    @staticmethod
    def minimum_visible_ms_v1() -> int:
        return _SPLASH_CYCLE_MS_V1

    def remaining_minimum_ms_v1(self) -> int:
        elapsed = (
            self._visible_clock_v1.elapsed()
            if self._visible_clock_v1.isValid()
            else 0
        )
        return max(0, self.minimum_visible_ms_v1() - elapsed)

    def finish_v1(self, main_window: QWidget) -> None:
        """Reveal the ready main window and retire the transient splash."""
        main_window.show()
        main_window.raise_()
        self._animation_timer_v1.stop()
        self.close()
        main_window.activateWindow()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._visible_clock_v1.start()
        self._animation_timer_v1.start()
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            self.move(available.center() - self.rect().center())

    def hideEvent(self, event) -> None:
        self._animation_timer_v1.stop()
        super().hideEvent(event)

    @staticmethod
    def _drop_path_v1(x: float, y: float, size: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(x, y - size)
        path.cubicTo(
            x - size * 0.35,
            y - size * 0.35,
            x - size * 0.72,
            y,
            x - size * 0.72,
            y + size * 0.28,
        )
        path.cubicTo(
            x - size * 0.72,
            y + size * 0.92,
            x - size * 0.30,
            y + size * 1.22,
            x,
            y + size * 1.22,
        )
        path.cubicTo(
            x + size * 0.30,
            y + size * 1.22,
            x + size * 0.72,
            y + size * 0.92,
            x + size * 0.72,
            y + size * 0.28,
        )
        path.cubicTo(
            x + size * 0.72,
            y,
            x + size * 0.35,
            y - size * 0.35,
            x,
            y - size,
        )
        path.closeSubpath()
        return path

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        card = QRectF(2.0, 2.0, self.width() - 4.0, self.height() - 4.0)
        painter.setPen(QPen(QColor("#7894a3"), 2.0))
        painter.setBrush(QColor("#263b47"))
        painter.drawRoundedRect(card, 15.0, 15.0)

        pipe = QPainterPath()
        pipe.moveTo(55.0, 50.0)
        pipe.lineTo(153.0, 50.0)
        pipe.cubicTo(174.0, 50.0, 184.0, 61.0, 184.0, 78.0)
        pipe.lineTo(184.0, 84.0)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(
                QColor("#aab5bb"),
                14.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawPath(pipe)
        painter.setPen(QPen(QColor("#d6dde0"), 3.0))
        painter.drawPath(pipe)
        painter.setPen(
            QPen(
                QColor("#8d999f"),
                8.0,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(QLineF(174.0, 84.0, 194.0, 84.0))

        elapsed = (
            self._visible_clock_v1.elapsed()
            if self._visible_clock_v1.isValid()
            else 0
        )
        state = splash_animation_state_v1(elapsed)
        if state.phase in ("forming", "falling"):
            if state.phase == "forming":
                x = 184.0
                y = 91.0
                size = 3.0 + 4.0 * state.drop_progress
            else:
                progress = state.drop_progress * state.drop_progress
                x = 184.0
                y = 92.0 + 49.0 * progress
                size = 7.0
            water = QLinearGradient(x - size, y - size, x + size, y + size)
            water.setColorAt(0.0, QColor("#9cdef5"))
            water.setColorAt(1.0, QColor("#3188b5"))
            painter.setPen(QPen(QColor("#b9e8f7"), 1.0))
            painter.setBrush(water)
            painter.drawPath(self._drop_path_v1(x, y, size))

        surface_y = 151.0
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#9db4bf"), 2.0))
        painter.drawLine(QLineF(104.0, surface_y, 264.0, surface_y))

        if state.phase == "splash":
            progress = state.splash_progress
            opacity = max(0.0, 1.0 - progress * 0.72)
            splash_colour = QColor("#74c6e8")
            splash_colour.setAlphaF(opacity)
            painter.setPen(
                QPen(
                    splash_colour,
                    2.5,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            reach = 8.0 + 20.0 * progress
            rise = 5.0 + 10.0 * (1.0 - progress)
            left = QPainterPath()
            left.moveTo(181.0, surface_y)
            left.cubicTo(
                176.0,
                surface_y - rise,
                168.0 - reach * 0.25,
                surface_y - rise,
                184.0 - reach,
                surface_y - 2.0,
            )
            right = QPainterPath()
            right.moveTo(187.0, surface_y)
            right.cubicTo(
                192.0,
                surface_y - rise,
                200.0 + reach * 0.25,
                surface_y - rise,
                184.0 + reach,
                surface_y - 2.0,
            )
            painter.drawPath(left)
            painter.drawPath(right)
            ripple_width = 18.0 + 54.0 * progress
            painter.drawEllipse(
                QRectF(
                    184.0 - ripple_width / 2.0,
                    surface_y - 3.0,
                    ripple_width,
                    6.0,
                )
            )

        painter.setPen(QColor("#f1f5f6"))
        font = QFont(painter.font())
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(20.0, 165.0, self.width() - 40.0, 30.0),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
            "HVACgooee",
        )
