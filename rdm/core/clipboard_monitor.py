"""Monitor clipboard for URLs and offer to add as download."""

from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication

from rdm.utils.url_utils import is_downloadable_url


class ClipboardMonitor(QObject):
    """Polls clipboard for downloadable URLs and calls on_url_detected(url)."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._last_url: Optional[str] = None
        self._interval_ms = 1000
        self.on_url_detected: Optional[Callable[[str], None]] = None

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def _check(self) -> None:
        app = QApplication.instance()
        if not app:
            return
        clipboard = app.clipboard()
        if clipboard is None:
            return
        text = clipboard.text(QClipboard.Mode.Clipboard).strip()
        if not text or text == self._last_url:
            return
        if is_downloadable_url(text):
            self._last_url = text
            if self.on_url_detected:
                self.on_url_detected(text)

    def set_last_url(self, url: str) -> None:
        """Call after user adds a URL so we don't re-prompt for the same one."""
        self._last_url = url
