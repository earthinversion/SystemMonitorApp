from __future__ import annotations

from collections import deque
from typing import Deque, Iterable


class HistoryBuffer:
    def __init__(self, max_points: int) -> None:
        self._time: Deque[float] = deque(maxlen=max_points)
        self._cpu: Deque[float] = deque(maxlen=max_points)
        self._ram: Deque[float] = deque(maxlen=max_points)

    def append(self, elapsed_seconds: float, cpu_percent: float, ram_percent: float) -> None:
        self._time.append(elapsed_seconds)
        self._cpu.append(cpu_percent)
        self._ram.append(ram_percent)

    @property
    def time_points(self) -> list[float]:
        return list(self._time)

    @property
    def cpu_points(self) -> list[float]:
        return list(self._cpu)

    @property
    def ram_points(self) -> list[float]:
        return list(self._ram)

    def __len__(self) -> int:
        return len(self._time)

    def cpu_window(self, size: int) -> Iterable[float]:
        return list(self._cpu)[-size:]

    def ram_window(self, size: int) -> Iterable[float]:
        return list(self._ram)[-size:]
