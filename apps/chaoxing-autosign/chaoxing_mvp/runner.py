from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .engine import AutoSignEngine, ScanStats


@dataclass(slots=True)
class RunnerConfig:
    poll_seconds: float = 30.0
    jitter_seconds: float = 10.0
    backoff_initial_seconds: float = 15.0
    backoff_max_seconds: float = 300.0


class MonitorRunner:
    """Long-running scan loop with jitter, exponential backoff and cooperative stop."""

    def __init__(
        self,
        engine: AutoSignEngine,
        config: RunnerConfig | None = None,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self.engine = engine
        self.config = config or RunnerConfig()
        self.sleeper = sleeper
        self.rng = rng or random.Random()
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run_forever(self, *, on_scan: Callable[[ScanStats], None] | None = None) -> None:
        backoff = self.config.backoff_initial_seconds
        while not self._stop.is_set():
            try:
                stats = self.engine.scan_once()
                if on_scan is not None:
                    on_scan(stats)
                backoff = self.config.backoff_initial_seconds
                delay = self.config.poll_seconds + self.rng.uniform(
                    0.0, max(0.0, self.config.jitter_seconds)
                )
            except Exception as exc:
                self.engine.ports.notifier.notify(
                    "Auto-sign monitor error",
                    f"{type(exc).__name__}: {exc}; retrying with backoff",
                )
                delay = backoff
                backoff = min(backoff * 2.0, self.config.backoff_max_seconds)

            self._sleep_interruptibly(delay)

    def _sleep_interruptibly(self, seconds: float) -> None:
        remaining = max(0.0, seconds)
        quantum = 1.0
        while remaining > 0 and not self._stop.is_set():
            part = min(quantum, remaining)
            self.sleeper(part)
            remaining -= part
