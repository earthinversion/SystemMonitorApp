from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SystemSnapshot:
    captured_at: datetime
    elapsed_seconds: float
    uptime_seconds: float
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    process_count: int
    net_sent_bps: float
    net_recv_bps: float

    def csv_row(self) -> tuple[str, float, float, float, float, float, int, float, float]:
        return (
            self.captured_at.isoformat(),
            self.elapsed_seconds,
            self.uptime_seconds,
            self.cpu_percent,
            self.ram_percent,
            self.disk_percent,
            self.process_count,
            self.net_sent_bps,
            self.net_recv_bps,
        )
