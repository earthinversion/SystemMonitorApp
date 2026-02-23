from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from system_monitor.services.system_stats import SystemStatsService


class _Counters:
    def __init__(self, sent: int, recv: int) -> None:
        self.bytes_sent = sent
        self.bytes_recv = recv


class _Memory:
    def __init__(self, percent: float) -> None:
        self.percent = percent


class SystemStatsServiceTest(unittest.TestCase):
    @patch("system_monitor.services.system_stats.psutil")
    @patch("system_monitor.services.system_stats.time")
    def test_sample_includes_network_rate(self, time_module, psutil_module) -> None:
        time_module.monotonic.side_effect = [10.0, 12.0]
        time_module.time.return_value = 100.0

        psutil_module.boot_time.return_value = 20.0
        psutil_module.cpu_percent.return_value = 40.0
        psutil_module.virtual_memory.return_value = _Memory(percent=55.0)
        psutil_module.disk_usage.return_value = _Memory(percent=70.0)
        psutil_module.pids.return_value = [1, 2, 3]
        psutil_module.net_io_counters.side_effect = [_Counters(1000, 3000), _Counters(1600, 3800)]

        service = SystemStatsService()
        snapshot = service.sample()

        self.assertEqual(snapshot.cpu_percent, 40.0)
        self.assertEqual(snapshot.ram_percent, 55.0)
        self.assertEqual(snapshot.disk_percent, 70.0)
        self.assertEqual(snapshot.process_count, 3)
        self.assertAlmostEqual(snapshot.net_sent_bps, 300.0)
        self.assertAlmostEqual(snapshot.net_recv_bps, 400.0)


if __name__ == "__main__":
    unittest.main()
