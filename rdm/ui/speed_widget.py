"""Speed display and limit control for status bar."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from rdm.utils.file_utils import format_size


class SpeedWidget(QWidget):
    """Shows current total download speed and optional limit. Updates from download manager."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = QLabel("↓ 0 B/s")
        self._label.setStyleSheet("padding: 0 8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self._current_speed = 0
        self._limit_kbps = 0

    def set_speed(self, bytes_per_sec: float) -> None:
        """Update displayed speed (bytes per second)."""
        self._current_speed = bytes_per_sec
        text = f"↓ {format_size(int(bytes_per_sec))}/s"
        if self._limit_kbps > 0:
            text += f" (limit: {self._limit_kbps} KiB/s)"
        self._label.setText(text)

    def set_limit(self, kbps: int) -> None:
        """Show limit in label."""
        self._limit_kbps = kbps
        self.set_speed(self._current_speed)
