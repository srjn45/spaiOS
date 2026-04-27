import math
import random
from dataclasses import dataclass

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget

from spaiOS.ui.tokens import (
    SPHERE_IDLE_COLOR,
    SPHERE_THINKING_COLOR,
    SPHERE_RESPONDING_COLOR,
    SPHERE_QUESTIONING_COLOR,
    SPHERE_LISTENING_COLOR,
)

# ── Sphere geometry (built once at import) ─────────────────────────────────────
_N = 60  # node count — clear mesh, light enough for 50ms paint loop


def _build_sphere(n: int) -> list[tuple[float, float, float]]:
    phi = (1 + 5**0.5) / 2
    pts = []
    for i in range(n):
        theta = math.acos(1 - 2 * (i + 0.5) / n)
        psi = 2 * math.pi * i / phi
        pts.append(
            (
                math.sin(theta) * math.cos(psi),
                math.sin(theta) * math.sin(psi),
                math.cos(theta),
            )
        )
    return pts


_NODES_BASE = _build_sphere(_N)

_EDGE_THRESH = 0.55
_EDGES: list[tuple[int, int]] = [
    (i, j)
    for i in range(_N)
    for j in range(i + 1, _N)
    if math.sqrt(sum((a - b) ** 2 for a, b in zip(_NODES_BASE[i], _NODES_BASE[j]))) < _EDGE_THRESH
]

# ── State labels ───────────────────────────────────────────────────────────────
_IDLE = "idle"
_THINKING = "thinking"
_RESPONDING = "responding"
_QUESTIONING = "questioning"
_LISTENING = "listening"

_TICK_MS = 50
_X_TILT = 0.12  # fixed X-axis tilt (radians) — matches logo orientation


@dataclass
class _Spark:
    """One signal streak fired from a node."""

    px_rel: float  # node 2D x, in sphere-radius units (relative to center)
    py_rel: float  # node 2D y, in sphere-radius units
    dx: float  # travel direction x (unit vector)
    dy: float  # travel direction y
    length: float  # maximum travel distance, in sphere-radius units
    age: int = 0
    max_age: int = 10


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _rotate(pts: list, ay: float, ax: float) -> list[tuple[float, float, float]]:
    """Apply Y-rotation then X-rotation to a list of (x,y,z) unit-sphere points."""
    cy, sy = math.cos(ay), math.sin(ay)
    cx, sx = math.cos(ax), math.sin(ax)
    out = []
    for x0, y0, z0 in pts:
        x1 = x0 * cy + z0 * sy
        z1 = -x0 * sy + z0 * cy
        y2 = y0 * cx - z1 * sx
        z2 = y0 * sx + z1 * cx
        out.append((x1, y2, z2))
    return out


class NeuralSphere(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 260)

        self._state = _IDLE
        self._tick = 0
        self._angle_y = 0.0
        self._nodes: list[tuple[float, float, float]] = _rotate(_NODES_BASE, 0.0, _X_TILT)

        self._sparks: list[_Spark] = []
        self._cooldown = [0] * _N  # per-node firing cooldown in ticks

        self._pulse_t = 0.0
        self._converge_t = 0.0

        r, g, b = SPHERE_IDLE_COLOR
        self._glow_r, self._glow_g, self._glow_b = float(r), float(g), float(b)

        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_state(self, state: str) -> None:
        if state not in (_IDLE, _THINKING, _RESPONDING, _QUESTIONING, _LISTENING):
            return
        self._state = state
        if state == _RESPONDING:
            self._converge_t = 0.0

    # ── Tick ───────────────────────────────────────────────────────────────────

    def _advance(self) -> None:
        self._tick += 1
        self._pulse_t = (self._tick * _TICK_MS / 1000.0) % (2 * math.pi)

        rot_speed = {
            _IDLE: 0.005,
            _THINKING: 0.022,
            _RESPONDING: 0.010,
            _QUESTIONING: 0.007,
            _LISTENING: 0.016,
        }[self._state]
        self._angle_y = (self._angle_y + rot_speed) % (2 * math.pi)
        self._nodes = _rotate(_NODES_BASE, self._angle_y, _X_TILT)

        if self._state == _RESPONDING:
            self._converge_t = min(1.0, self._converge_t + 0.04)

        # Color lerp toward state target
        tr, tg, tb = {
            _IDLE: SPHERE_IDLE_COLOR,
            _THINKING: SPHERE_THINKING_COLOR,
            _RESPONDING: SPHERE_RESPONDING_COLOR,
            _QUESTIONING: SPHERE_QUESTIONING_COLOR,
            _LISTENING: SPHERE_LISTENING_COLOR,
        }[self._state]
        s = 0.06
        self._glow_r = _lerp(self._glow_r, float(tr), s)
        self._glow_g = _lerp(self._glow_g, float(tg), s)
        self._glow_b = _lerp(self._glow_b, float(tb), s)

        # Random node firing
        fire_p = {
            _IDLE: 0.012,
            _THINKING: 0.050,
            _RESPONDING: 0.0,
            _QUESTIONING: 0.018,
            _LISTENING: 0.035,
        }[self._state]
        for i, (x3, y3, z3) in enumerate(self._nodes):
            if self._cooldown[i] > 0:
                self._cooldown[i] -= 1
            elif z3 > 0.15 and random.random() < fire_p:
                self._spawn_sparks(i, x3, y3)
                self._cooldown[i] = random.randint(12, 28)

        # Age sparks
        for sp in self._sparks:
            sp.age += 1
        self._sparks = [sp for sp in self._sparks if sp.age < sp.max_age]

        self.update()

    def _spawn_sparks(self, _idx: int, x3: float, y3: float) -> None:
        # Outward direction from sphere center to this node (2D projection)
        ol = math.sqrt(x3 * x3 + y3 * y3) or 1e-9
        ox, oy = x3 / ol, y3 / ol
        for _ in range(random.randint(2, 3)):
            ang = random.uniform(-0.4, 0.4)
            ca, sa = math.cos(ang), math.sin(ang)
            self._sparks.append(
                _Spark(
                    px_rel=x3,
                    py_rel=y3,
                    dx=ox * ca - oy * sa,
                    dy=ox * sa + oy * ca,
                    length=random.uniform(0.18, 0.52),
                    max_age=random.randint(7, 14),
                )
            )

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        R = min(w, h) * 0.37

        self._draw_glow(painter, cx, cy, R)
        self._draw_mesh(painter, cx, cy, R)
        self._draw_sparks(painter, cx, cy, R)

        painter.end()

    # ── Glow ───────────────────────────────────────────────────────────────────

    def _draw_glow(self, painter: QPainter, cx: float, cy: float, R: float) -> None:
        pulse = 1.0 + 0.06 * math.sin(self._pulse_t * 2)
        gr, gg, gb = int(self._glow_r), int(self._glow_g), int(self._glow_b)

        painter.setPen(Qt.PenStyle.NoPen)

        # Layered halos
        for scale, alpha in [(2.6, 10), (1.9, 24), (1.35, 46)]:
            r = R * scale * pulse
            grad = QRadialGradient(cx, cy, r)
            grad.setColorAt(0.0, QColor(gr, gg, gb, alpha))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(grad)
            painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # Bright inner core glow
        core_r = R * 0.7 * pulse
        grad = QRadialGradient(cx, cy, core_r)
        grad.setColorAt(0.0, QColor(gr, gg, gb, 80))
        grad.setColorAt(0.55, QColor(gr, gg, gb, 35))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(grad)
        painter.drawEllipse(int(cx - core_r), int(cy - core_r), int(core_r * 2), int(core_r * 2))

    # ── Mesh ───────────────────────────────────────────────────────────────────

    def _draw_mesh(self, painter: QPainter, cx: float, cy: float, R: float) -> None:
        nodes = self._nodes
        gr, gg, gb = int(self._glow_r), int(self._glow_g), int(self._glow_b)

        # ── Edges ──────────────────────────────────────────────────────────────
        for i, j in _EDGES:
            x1, y1, z1 = nodes[i]
            x2, y2, z2 = nodes[j]
            avg_z = (z1 + z2) / 2
            depth = (avg_z + 1) / 2  # 0 = back, 1 = front
            # Limb darkening: edges near silhouette are dimmer
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            limb = max(0.0, 1.0 - (mx * mx + my * my) ** 1.3)
            alpha = int((12 + 175 * depth) * (0.15 + 0.85 * limb))
            if alpha < 5:
                continue
            # Front edges blend toward white-cyan; back edges stay glow color
            t = depth**0.6
            er = min(255, int(gr + (210 - gr) * t))
            eg = min(255, int(gg + (235 - gg) * t))
            eb = min(255, int(gb + (255 - gb) * t * 0.5))
            pen = QPen(QColor(er, eg, eb, alpha))
            pen.setWidth(max(1, int(depth * 2)))
            painter.setPen(pen)
            painter.drawLine(
                int(cx + x1 * R),
                int(cy + y1 * R),
                int(cx + x2 * R),
                int(cy + y2 * R),
            )

        # ── Nodes back → front ─────────────────────────────────────────────────
        painter.setPen(Qt.PenStyle.NoPen)
        for idx in sorted(range(_N), key=lambda i: nodes[i][2]):
            x3, y3, z3 = nodes[idx]
            px, py = cx + x3 * R, cy + y3 * R
            depth = (z3 + 1) / 2
            firing = self._cooldown[idx] > 0
            if firing:
                nr = max(2, int(3 + 4 * depth))
                er = min(255, int(gr + (210 - gr) * depth))
                eg = min(255, int(gg + (235 - gg) * depth))
                eb = min(255, int(gb + (255 - gb) * depth * 0.5))
                na = min(255, int(185 + 70 * depth))
            else:
                nr = max(1, int(1 + 3 * depth))
                er, eg, eb = gr, gg, gb
                na = int(45 + 155 * depth)
            painter.setBrush(QColor(er, eg, eb, na))
            painter.drawEllipse(int(px - nr), int(py - nr), nr * 2, nr * 2)

    # ── Sparks ─────────────────────────────────────────────────────────────────

    def _draw_sparks(self, painter: QPainter, cx: float, cy: float, R: float) -> None:
        if not self._sparks:
            return
        gr, gg, gb = int(self._glow_r), int(self._glow_g), int(self._glow_b)

        for sp in self._sparks:
            progress = sp.age / max(sp.max_age, 1)
            fade = 1.0 - progress**1.4
            alpha = int(190 * fade)
            if alpha < 8:
                continue

            # Start at the actual node position on sphere surface
            sx = cx + sp.px_rel * R
            sy = cy + sp.py_rel * R
            ex = sx + sp.dx * sp.length * R * progress
            ey = sy + sp.dy * sp.length * R * progress

            er = min(255, gr + 70)
            eg = min(255, gg + 35)
            pen = QPen(QColor(er, eg, gb, alpha))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(int(sx), int(sy), int(ex), int(ey))

            # Glowing tip
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(215, 238, 255, alpha))
            tr = 2
            painter.drawEllipse(int(ex - tr), int(ey - tr), tr * 2, tr * 2)
