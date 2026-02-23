from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

try:
    import psutil
except ModuleNotFoundError:  # pragma: no cover - handled at runtime on launch
    psutil = None

from system_monitor.models import SystemSnapshot


class SystemStatsService:
    def __init__(self) -> None:
        if psutil is None:
            raise RuntimeError(
                "psutil is not installed. I install dependencies with: pip install -r requirements.txt"
            )
        self._started_monotonic = time.monotonic()
        self._boot_time = psutil.boot_time()
        self._last_net_time = self._started_monotonic
        self._last_net_counters = psutil.net_io_counters()

    def sample(self) -> SystemSnapshot:
        now_monotonic = time.monotonic()
        elapsed_seconds = now_monotonic - self._started_monotonic
        uptime_seconds = max(0.0, time.time() - self._boot_time)

        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage(str(Path.home().anchor)).percent
        process_count = len(psutil.pids())

        net_counters = psutil.net_io_counters()
        window_seconds = max(now_monotonic - self._last_net_time, 1e-6)
        net_sent_bps = (net_counters.bytes_sent - self._last_net_counters.bytes_sent) / window_seconds
        net_recv_bps = (net_counters.bytes_recv - self._last_net_counters.bytes_recv) / window_seconds
        self._last_net_time = now_monotonic
        self._last_net_counters = net_counters

        return SystemSnapshot(
            captured_at=datetime.now(),
            elapsed_seconds=elapsed_seconds,
            uptime_seconds=uptime_seconds,
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            disk_percent=disk_percent,
            process_count=process_count,
            net_sent_bps=max(0.0, net_sent_bps),
            net_recv_bps=max(0.0, net_recv_bps),
        )
