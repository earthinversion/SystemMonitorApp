from __future__ import annotations

import csv
from pathlib import Path

from system_monitor.models import SystemSnapshot


class CsvMetricsExporter:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.output_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._handle)
        self._writer.writerow(
            [
                "captured_at",
                "elapsed_seconds",
                "uptime_seconds",
                "cpu_percent",
                "ram_percent",
                "disk_percent",
                "process_count",
                "net_sent_bps",
                "net_recv_bps",
            ]
        )

    def write(self, snapshot: SystemSnapshot) -> None:
        self._writer.writerow(snapshot.csv_row())
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()
