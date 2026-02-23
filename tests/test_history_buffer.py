from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from system_monitor.services.history_buffer import HistoryBuffer


class HistoryBufferTest(unittest.TestCase):
    def test_history_keeps_recent_points(self) -> None:
        history = HistoryBuffer(max_points=3)
        history.append(1.0, 10.0, 20.0)
        history.append(2.0, 11.0, 21.0)
        history.append(3.0, 12.0, 22.0)
        history.append(4.0, 13.0, 23.0)

        self.assertEqual(history.time_points, [2.0, 3.0, 4.0])
        self.assertEqual(history.cpu_points, [11.0, 12.0, 13.0])
        self.assertEqual(history.ram_points, [21.0, 22.0, 23.0])


if __name__ == "__main__":
    unittest.main()
