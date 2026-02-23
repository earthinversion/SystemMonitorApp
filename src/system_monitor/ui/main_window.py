from __future__ import annotations

import platform
from typing import Literal

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QLabel, QMainWindow
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from system_monitor.constants import APP_NAME, MAIN_UI_FILE
from system_monitor.models import SystemSnapshot
from system_monitor.services.csv_exporter import CsvMetricsExporter
from system_monitor.services.history_buffer import HistoryBuffer
from system_monitor.services.system_stats import SystemStatsService

GraphName = Literal["cpu", "ram"]


class MainWindow(QMainWindow):
    def __init__(
        self,
        stats_service: SystemStatsService,
        history_seconds: int = 30,
        poll_interval_ms: int = 1000,
        exporter: CsvMetricsExporter | None = None,
    ) -> None:
        super().__init__()
        self.ui = uic.loadUi(str(MAIN_UI_FILE), self)
        self.setWindowTitle(APP_NAME)

        self.stats_service = stats_service
        self.history_seconds = max(10, history_seconds)
        self.poll_interval_ms = max(250, poll_interval_ms)
        self.exporter = exporter

        max_points = max(int((self.history_seconds * 1000) / self.poll_interval_ms) + 20, 40)
        self.history = HistoryBuffer(max_points=max_points)
        self.current_snapshot: SystemSnapshot | None = None

        self.graph_traces: dict[GraphName, pg.PlotDataItem] = {}
        self.graph_window_seconds = self.history_seconds
        self.graph_window_points = max(int((self.graph_window_seconds * 1000) / self.poll_interval_ms), 1)
        self.current_graph: GraphName = "cpu"

        self.cpu_graph = PlotWidget(title="CPU percent")
        self.ram_graph = PlotWidget(title="RAM percent")
        self._configure_graph(self.cpu_graph)
        self._configure_graph(self.ram_graph)

        self.ui.gridLayout.addWidget(self.cpu_graph, 0, 0, 1, 3)
        self.ui.gridLayout.addWidget(self.ram_graph, 0, 0, 1, 3)

        self.pushButton.clicked.connect(self.show_cpu_graph)
        self.pushButton_2.clicked.connect(self.show_ram_graph)

        self._build_extra_info_labels()
        self._set_static_labels()

        self.system_timer = QtCore.QTimer(self)
        self.system_timer.timeout.connect(self.refresh_snapshot)
        self.system_timer.start(self.poll_interval_ms)

        self.graph_timer = QtCore.QTimer(self)
        self.graph_timer.timeout.connect(self.refresh_graph)
        self.graph_timer.start(self.poll_interval_ms)

        self.show_cpu_graph()
        self.refresh_snapshot()

    def _configure_graph(self, graph_widget: PlotWidget) -> None:
        graph_widget.getAxis("bottom").setLabel(text="Time since launch (s)")
        graph_widget.getAxis("left").setLabel(text="Percent")
        graph_widget.showGrid(x=True, y=True, alpha=0.25)

    def _build_extra_info_labels(self) -> None:
        self.quick_stats_label = QLabel(self.ui.centralwidget)
        self.quick_stats_label.setGeometry(210, 118, 340, 28)
        self.quick_stats_label.setAlignment(QtCore.Qt.AlignCenter)
        self.quick_stats_label.setStyleSheet(
            "color: rgb(207, 224, 255); font-size: 12px; background-color: rgba(58, 58, 102, 135); border-radius: 8px;"
        )

        self.runtime_label = QLabel(self.ui.centralwidget)
        self.runtime_label.setGeometry(210, 146, 340, 16)
        self.runtime_label.setAlignment(QtCore.Qt.AlignCenter)
        self.runtime_label.setStyleSheet(
            "color: rgb(148, 148, 216); font-size: 11px; background-color: none;"
        )

    def _set_static_labels(self) -> None:
        self.ui.label_title.setText(APP_NAME)
        self.ui.label.setText(f"{platform.system()} {platform.machine()} | Python {platform.python_version()}")
        processor_name = platform.processor().strip() or "Unavailable"
        self.ui.label_2.setText(f"Processor: {processor_name}")

    def refresh_snapshot(self) -> None:
        snapshot = self.stats_service.sample()
        self.current_snapshot = snapshot
        self.history.append(snapshot.elapsed_seconds, snapshot.cpu_percent, snapshot.ram_percent)

        if self.exporter:
            self.exporter.write(snapshot)

        self._set_ring_value(snapshot.cpu_percent, self.ui.labelPercentageCPU, self.ui.circularProgressCPU, "rgba(85, 170, 255, 255)")
        self._set_ring_value(snapshot.ram_percent, self.ui.labelPercentageRAM, self.ui.circularProgressRAM, "rgba(255, 0, 127, 255)")
        self.quick_stats_label.setText(
            f"Disk {snapshot.disk_percent:.1f}% | Processes {snapshot.process_count:,} | Net {self._format_rate(snapshot.net_recv_bps)} down"
        )
        self.runtime_label.setText(
            f"Uptime {self._format_duration(snapshot.uptime_seconds)} | Capture {snapshot.captured_at.strftime('%H:%M:%S')}"
        )
        self.statusBar().showMessage(
            f"Upload {self._format_rate(snapshot.net_sent_bps)} | Download {self._format_rate(snapshot.net_recv_bps)}"
        )

    def refresh_graph(self) -> None:
        if len(self.history) == 0:
            return

        data_x = self.history.time_points
        if self.current_graph == "cpu":
            data_y = self.history.cpu_points
            self._set_plot_data("cpu", data_x, data_y, (85, 170, 255))
        else:
            data_y = self.history.ram_points
            self._set_plot_data("ram", data_x, data_y, (255, 0, 127))

        if data_x:
            x_end = data_x[-1]
            x_start = max(0.0, x_end - self.graph_window_seconds)
            window = data_y[-min(len(data_y), self.graph_window_points):]
            y_min, y_max = self._tight_range(window)
            target_graph = self.cpu_graph if self.current_graph == "cpu" else self.ram_graph
            target_graph.setRange(xRange=[x_start, x_end + 0.5], yRange=[y_min, y_max], padding=0.02)

    def show_cpu_graph(self) -> None:
        self.current_graph = "cpu"
        self.ram_graph.hide()
        self.cpu_graph.show()
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)
        self.pushButton.setStyleSheet("QPushButton { background-color: lightblue; }")
        self.pushButton_2.setStyleSheet(
            "QPushButton { background-color: rgb(255, 44, 174); color: white; }"
        )

    def show_ram_graph(self) -> None:
        self.current_graph = "ram"
        self.cpu_graph.hide()
        self.ram_graph.show()
        self.pushButton_2.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.pushButton_2.setStyleSheet("QPushButton { background-color: lightblue; }")
        self.pushButton.setStyleSheet(
            "QPushButton { background-color: rgba(85, 170, 255, 255); color: white; }"
        )

    def _set_plot_data(
        self,
        name: GraphName,
        data_x: list[float],
        data_y: list[float],
        color: tuple[int, int, int],
    ) -> None:
        if name not in self.graph_traces:
            target = self.cpu_graph if name == "cpu" else self.ram_graph
            self.graph_traces[name] = target.getPlotItem().plot(pen=pg.mkPen(color, width=3))
        self.graph_traces[name].setData(data_x, data_y)

    def _set_ring_value(self, value: float, label: QLabel, progress_bar, color: str) -> None:
        html_text = (
            '<p align="center"><span style=" font-size:50pt;">{VALUE}</span>'
            '<span style=" font-size:40pt; vertical-align:super;">%</span></p>'
        )
        label.setText(html_text.replace("{VALUE}", f"{value:.1f}"))
        self._apply_progress_bar(value, progress_bar, color)

    def _apply_progress_bar(self, value: float, widget, color: str) -> None:
        style = (
            "QFrame{"
            "border-radius: 110px;"
            "background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, "
            "stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} {COLOR});"
            "}"
        )

        progress = (100 - value) / 100.0
        stop_1 = "1.000" if value >= 100 else str(max(progress - 0.001, 0.0))
        stop_2 = "1.000" if value >= 100 else str(progress)
        widget.setStyleSheet(
            style.replace("{STOP_1}", stop_1).replace("{STOP_2}", stop_2).replace("{COLOR}", color)
        )

    @staticmethod
    def _format_rate(bytes_per_second: float) -> str:
        kib = 1024.0
        mib = kib * 1024.0
        if bytes_per_second >= mib:
            return f"{bytes_per_second / mib:.2f} MB/s"
        if bytes_per_second >= kib:
            return f"{bytes_per_second / kib:.1f} KB/s"
        return f"{bytes_per_second:.0f} B/s"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total = int(seconds)
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        if days > 0:
            return f"{days}d {hours:02d}h {minutes:02d}m"
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def _tight_range(values: list[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 100.0
        low = min(values)
        high = max(values)
        if low == high:
            pad = 2.5 if low < 95 else 1.0
            return max(0.0, low - pad), min(100.0, high + pad)
        return max(0.0, low - 2.0), min(100.0, high + 2.0)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self.exporter:
            self.exporter.close()
        super().closeEvent(event)
