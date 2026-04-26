import math
import random

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget

_IDLE = "idle"
_THINKING = "thinking"
_RESPONDING = "responding"

_TICK_MS = 50
_SPHERE_RADIUS = 60
_NODE_COUNT = 8
_ORBIT_RADIUS = 90
_NODE_RADIUS = 6


class NeuralSphere(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 240)

        self._state = _IDLE
        self._tick = 0

        # idle pulse
        self._pulse_t = 0.0

        # thinking nodes: each has an angle and current opacity
        self._node_angles = [2 * math.pi * i / _NODE_COUNT for i in range(_NODE_COUNT)]
        self._node_opacities = [1.0] * _NODE_COUNT

        # responding: lerp factor 0→1 (nodes converging inward)
        self._converge_t = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def set_state(self, state: str) -> None:
        if state not in (_IDLE, _THINKING, _RESPONDING):
            return
        self._state = state
        if state == _RESPONDING:
            self._converge_t = 0.0

    def _advance(self) -> None:
        self._tick += 1
        self._pulse_t = (self._tick * _TICK_MS / 1000.0) % (2 * math.pi)

        if self._state == _THINKING:
            speed = 0.03
            for i in range(_NODE_COUNT):
                self._node_angles[i] = (
                    self._node_angles[i] + speed * (1 + i * 0.05)
                ) % (2 * math.pi)
                if random.random() < 0.3:
                    self._node_opacities[i] = random.uniform(0.3, 1.0)

        elif self._state == _RESPONDING:
            self._converge_t = min(1.0, self._converge_t + 0.04)

        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2

        self._draw_sphere(painter, cx, cy)

        if self._state in (_THINKING, _RESPONDING):
            self._draw_nodes(painter, cx, cy)

        painter.end()

    def _draw_sphere(self, painter: QPainter, cx: float, cy: float) -> None:
        scale = 1.0 + 0.05 * math.sin(self._pulse_t * 2)
        opacity = 0.6 + 0.1 * math.sin(self._pulse_t * 2)
        r = int(_SPHERE_RADIUS * scale)

        gradient = QRadialGradient(cx - r * 0.2, cy - r * 0.2, r * 1.4)
        gradient.setColorAt(0.0, QColor(120, 100, 255, int(255 * opacity)))
        gradient.setColorAt(0.5, QColor(60, 40, 180, int(200 * opacity)))
        gradient.setColorAt(1.0, QColor(10, 5, 60, int(80 * opacity)))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(int(cx - r), int(cy - r), r * 2, r * 2)

        glow_pen = QPen(QColor(140, 120, 255, int(60 * opacity)))
        glow_pen.setWidth(8)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(cx - r - 4), int(cy - r - 4), (r + 4) * 2, (r + 4) * 2)

    def _draw_nodes(self, painter: QPainter, cx: float, cy: float) -> None:
        ease = self._converge_t**2 if self._state == _RESPONDING else 0.0
        effective_orbit = _ORBIT_RADIUS * (1.0 - ease)

        for i in range(_NODE_COUNT):
            angle = self._node_angles[i]
            nx = cx + effective_orbit * math.cos(angle)
            ny = cy + effective_orbit * math.sin(angle)

            node_opacity = self._node_opacities[i] if self._state == _THINKING else 1.0

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(180, 160, 255, int(220 * node_opacity)))
            nr = _NODE_RADIUS
            painter.drawEllipse(int(nx - nr), int(ny - nr), nr * 2, nr * 2)

            # connector line from sphere edge to node
            line_pen = QPen(QColor(140, 120, 255, int(60 * node_opacity)))
            line_pen.setWidth(1)
            painter.setPen(line_pen)
            painter.drawLine(int(cx), int(cy), int(nx), int(ny))
