"""Download scheduling: start downloads at a specific time, auto-shutdown when done."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal


@dataclass
class ScheduleEntry:
    """A scheduled action."""
    run_at: datetime
    action: str  # "start_downloads" | "shutdown"
    payload: Optional[dict] = None


class DownloadScheduler(QObject):
    """Runs scheduled actions (start time, shutdown). Uses QTimer for next run."""

    schedule_triggered = Signal(str, object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._entries: List[ScheduleEntry] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._timer.start(30 * 1000)

    def schedule_start_at(self, when: datetime) -> None:
        """Schedule 'start_downloads' at given time (others can be added later)."""
        self._entries.append(ScheduleEntry(run_at=when, action="start_downloads"))
        self._entries.sort(key=lambda e: e.run_at)
        self._reschedule()

    def schedule_shutdown_when_idle(self, callback: Callable[[], None]) -> None:
        """When there are no active downloads, call callback (e.g. shutdown). One-shot."""
        self._shutdown_when_idle_callback = callback

    def set_is_idle_check(self, check: Callable[[], bool]) -> None:
        """Set callable that returns True when there are no active downloads."""
        self._is_idle = check

    def _check(self) -> None:
        now = datetime.now()
        to_remove = []
        for e in self._entries:
            if e.run_at <= now:
                self.schedule_triggered.emit(e.action, e.payload)
                to_remove.append(e)
        for e in to_remove:
            self._entries.remove(e)
        self._reschedule()
        if getattr(self, "_shutdown_when_idle_callback", None) and getattr(self, "_is_idle", lambda: False)():
            cb = self._shutdown_when_idle_callback
            self._shutdown_when_idle_callback = None
            cb()

    def _reschedule(self) -> None:
        self._timer.stop()
        if not self._entries:
            self._timer.start(60 * 1000)
            return
        next_run = self._entries[0].run_at
        now = datetime.now()
        delta_ms = max(1000, int((next_run - now).total_seconds() * 1000))
        self._timer.start(min(delta_ms, 60 * 1000))

    def get_scheduled_times(self) -> List[datetime]:
        return [e.run_at for e in self._entries]
