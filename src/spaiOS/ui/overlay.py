from PyQt6.QtCore import Qt, QEvent, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel


class Overlay(QMainWindow):
    WIDTH = 480
    HEIGHT = 420

    def __init__(self) -> None:
        super().__init__()
        self._build_window()
        self._center_on_screen()

    def _build_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(
            "#container { background: rgba(10, 10, 20, 210); border-radius: 20px; }"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)

        # Placeholder — replaced in Session 4 with NeuralSphere widget
        placeholder = QLabel("Neural Sphere — Session 4")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: rgba(160, 160, 200, 180); font-size: 14px;")
        layout.addWidget(placeholder)

        self.setCentralWidget(container)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = (geom.width() - self.WIDTH) // 2 + geom.x()
        y = (geom.height() - self.HEIGHT) // 2 + geom.y()
        self.move(x, y)

    @pyqtSlot()
    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def keyPressEvent(self, event: QEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
