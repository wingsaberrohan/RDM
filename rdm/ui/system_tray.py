"""System tray icon with menu and download complete notifications."""

from typing import Callable, Optional

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class SystemTray(QObject):
    """System tray icon: show/hide window, quick actions, notifications."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(parent and parent.parent() or None)
        self._tray.setToolTip("RDM - Rohan's Download Manager")
        self._on_show_window: Optional[Callable[[], None]] = None
        self._on_quit: Optional[Callable[[], None]] = None
        self._menu = QMenu()
        show_act = QAction("Show RDM", self)
        show_act.triggered.connect(self._show_window)
        self._menu.addAction(show_act)
        self._menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self._quit)
        self._menu.addAction(quit_act)
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        try:
            app = QApplication.instance()
            if app and app.style():
                self._tray.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        except Exception:
            pass

    def set_show_window_callback(self, cb: Callable[[], None]) -> None:
        self._on_show_window = cb

    def set_quit_callback(self, cb: Callable[[], None]) -> None:
        self._on_quit = cb

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def show_message(self, title: str, message: str, timeout_ms: int = 3000) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, timeout_ms)

    def _show_window(self) -> None:
        if self._on_show_window:
            self._on_show_window()

    def _quit(self) -> None:
        if self._on_quit:
            self._on_quit()
        else:
            QApplication.quit()

    def _on_activated(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick and self._on_show_window:
            self._on_show_window()
