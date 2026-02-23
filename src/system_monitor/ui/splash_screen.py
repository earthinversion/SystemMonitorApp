from __future__ import annotations

from typing import Callable

from PyQt5 import QtCore, uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QMainWindow

from system_monitor.constants import SPLASH_UI_FILE


class SplashScreen(QMainWindow):
    def __init__(self, window_factory: Callable[[], QMainWindow]) -> None:
        super().__init__()
        self.ui = uic.loadUi(str(SPLASH_UI_FILE), self)
        self.window_factory = window_factory

        self._counter = 0.0
        self._next_label_step = 10
        self.main_window: QMainWindow | None = None

        self.progress_bar_value(0.0)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.ui.circularBg.setGraphicsEffect(shadow)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.progress)
        self.timer.start(15)

    def progress(self) -> None:
        value = self._counter
        html_text = (
            '<p><span style=" font-size:68pt;">{VALUE}</span>'
            '<span style=" font-size:58pt; vertical-align:super;">%</span></p>'
        )

        if value > self._next_label_step:
            self.ui.labelPercentage.setText(html_text.replace("{VALUE}", str(self._next_label_step)))
            self._next_label_step += 10

        self.progress_bar_value(1.0 if value >= 100 else value)

        if self.main_window is None and self._counter >= 10:
            self.main_window = self.window_factory()

        if self._counter > 100:
            self.timer.stop()
            if self.main_window is None:
                self.main_window = self.window_factory()
            if getattr(self.main_window, "start_maximized", False):
                self.main_window.showMaximized()
            else:
                self.main_window.show()
            self.close()

        self._counter += 0.5

    def progress_bar_value(self, value: float) -> None:
        style_sheet = (
            "QFrame{"
            "border-radius: 150px;"
            "background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, "
            "stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} rgba(85, 170, 255, 255));"
            "}"
        )

        progress = (100 - value) / 100.0
        stop_1 = str(max(progress - 0.001, 0.0))
        stop_2 = str(progress)
        new_style = style_sheet.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2)
        self.ui.circularProgress.setStyleSheet(new_style)
