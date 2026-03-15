"""Main window: toolbar, download table, category sidebar, status bar."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
)

from rdm.core.aria2_manager import Aria2Manager
from rdm.core.download_manager import DownloadManager
from rdm.core.rpc_client import RpcClient
from rdm.core.category import get_category_for_filename, get_download_dir_for_category
from rdm.core.clipboard_monitor import ClipboardMonitor
from rdm.core.scheduler import DownloadScheduler
from rdm.core.browser_server import BrowserExtServer
from rdm.utils.file_utils import format_size
from rdm.utils.url_utils import filename_from_url, is_downloadable_url
from rdm.ui.download_table import DownloadTableView
from rdm.ui.category_panel import CategoryPanel
from rdm.ui.speed_widget import SpeedWidget
from rdm.ui.system_tray import SystemTray
from rdm.core.speed_limiter import SpeedLimiter


class MainWindow(QMainWindow):
    """Main application window with toolbar, download table, and status bar."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RDM - Rohan's Download Manager")
        self.setMinimumSize(800, 500)
        self.resize(1000, 600)

        self._aria2 = Aria2Manager()
        self._rpc = RpcClient(self._aria2)
        self._download_manager = DownloadManager(self._aria2)
        self._download_manager.error_message.connect(self._on_error)

        # Toolbar
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_act = toolbar.addAction("Add", self._on_add)
        add_act.setShortcut("Ctrl+N")
        toolbar.addSeparator()
        pause_act = toolbar.addAction("Pause", self._on_pause_selection)
        resume_act = toolbar.addAction("Resume", self._on_resume_selection)
        remove_act = toolbar.addAction("Remove", self._on_remove_selection)
        toolbar.addSeparator()
        toolbar.addAction("Schedule...", self._on_schedule)
        toolbar.addAction("Batch...", self._on_batch)
        toolbar.addSeparator()
        settings_act = toolbar.addAction("Settings", self._on_settings)
        self.addToolBar(toolbar)

        # Central: category panel + table
        self._category_panel = CategoryPanel(self)
        self._table = DownloadTableView(self._download_manager, self)
        self._table.set_download_manager(self._download_manager)

        self._download_manager.download_added.connect(self._table.model().add_download)
        self._download_manager.download_updated.connect(self._table.model().update_download)
        self._download_manager.download_removed.connect(self._table.model().remove_download)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._category_panel)
        splitter.addWidget(self._table)
        splitter.setSizes([180, 820])
        self.setCentralWidget(splitter)

        # Status bar
        self._status_label = QLabel("Ready")
        status = QStatusBar()
        status.addWidget(self._status_label)
        self._speed_widget = SpeedWidget(self)
        status.addPermanentWidget(self._speed_widget)
        self.setStatusBar(status)
        self._speed_limiter = SpeedLimiter(self._rpc)
        self._scheduler = DownloadScheduler(self)
        self._tray = SystemTray(self)
        self._tray.set_show_window_callback(self._show_from_tray)
        self._tray.set_quit_callback(self._quit_app)
        self._really_quit = False
        self._tray.show()
        self._download_manager.download_completed.connect(self._on_download_completed)
        self._browser_server = BrowserExtServer()
        self._browser_server.set_on_url(self._on_browser_url)
        self._browser_server.start()
        self._speed_timer = QTimer(self)
        self._speed_timer.timeout.connect(self._update_speed_display)
        self._speed_timer.start(1000)

        # Clipboard monitor: prompt to add download when URL is copied
        self._clipboard_monitor = ClipboardMonitor(self)
        self._clipboard_monitor.on_url_detected = self._on_clipboard_url
        self._clipboard_monitor.start()

        # Start aria2 and polling
        if self._aria2.get_api():
            self._download_manager.start_polling()
            self._status_label.setText("aria2 connected")
        else:
            self._status_label.setText("aria2 not found. Install aria2 and add to PATH or ~/.rdm/aria2/")

    def _on_error(self, msg: str) -> None:
        QMessageBox.warning(self, "RDM", msg, QMessageBox.StandardButton.Ok)

    def _on_clipboard_url(self, url: str) -> None:
        reply = QMessageBox.question(
            self,
            "Add download",
            f"Add this download?\n\n{url[:200]}{'...' if len(url) > 200 else ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            name = filename_from_url(url)
            category = get_category_for_filename(name or "") if name else "General"
            base = Path.home() / "Downloads"
            save_dir = get_download_dir_for_category(category, base)
            self._download_manager.add_download(url, save_dir=save_dir, filename=name, connections=8)
            self._clipboard_monitor.set_last_url(url)

    def _on_add(self) -> None:
        from rdm.ui.add_download_dialog import AddDownloadDialog

        dialog = AddDownloadDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            save_dir = dialog.get_save_dir()
            filename = dialog.get_filename()
            connections = dialog.get_connections()
            if url:
                name = filename or ""
                if not save_dir and name:
                    category = get_category_for_filename(name)
                    base = Path.home() / "Downloads"
                    save_dir = get_download_dir_for_category(category, base)
                self._download_manager.add_download(url, save_dir=save_dir, filename=filename or None, connections=connections)

    def _on_pause_selection(self) -> None:
        gid = self._get_selected_gid()
        if gid:
            self._download_manager.pause(gid)

    def _on_resume_selection(self) -> None:
        gid = self._get_selected_gid()
        if gid:
            self._download_manager.resume(gid)

    def _on_remove_selection(self) -> None:
        gid = self._get_selected_gid()
        if gid:
            self._download_manager.remove(gid)

    def _get_selected_gid(self):
        sel = self._table.selectionModel()
        if not sel or not sel.hasSelection():
            return None
        rows = sel.selectedRows()
        if not rows:
            return None
        return self._table.model().get_gid_at(rows[0].row())

    def _on_schedule(self) -> None:
        from rdm.ui.scheduler_dialog import SchedulerDialog
        SchedulerDialog(self._scheduler, self).exec()

    def _on_batch(self) -> None:
        from rdm.ui.batch_download_dialog import BatchDownloadDialog
        dialog = BatchDownloadDialog(self)
        if dialog.exec():
            for url in dialog.get_urls():
                if url and is_downloadable_url(url):
                    name = filename_from_url(url)
                    category = get_category_for_filename(name or "") if name else "General"
                    base = Path.home() / "Downloads"
                    save_dir = get_download_dir_for_category(category, base)
                    self._download_manager.add_download(url, save_dir=save_dir, filename=name, connections=8)

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_download_completed(self, gid: str, data: dict) -> None:
        name = data.get("name", "Download")
        self._tray.show_message("RDM", f"Completed: {name}")

    def _on_browser_url(self, url: str) -> None:
        self._show_from_tray()
        name = filename_from_url(url)
        category = get_category_for_filename(name or "") if name else "General"
        base = Path.home() / "Downloads"
        save_dir = get_download_dir_for_category(category, base)
        self._download_manager.add_download(url, save_dir=save_dir, filename=name, connections=8)

    def _on_settings(self) -> None:
        from rdm.ui.settings_dialog import SettingsDialog
        SettingsDialog(self).exec()

    def get_download_manager(self) -> DownloadManager:
        return self._download_manager

    def get_speed_limiter(self) -> SpeedLimiter:
        return self._speed_limiter

    def get_aria2_manager(self) -> Aria2Manager:
        return self._aria2

    def _update_speed_display(self) -> None:
        total = 0
        for row in range(self._table.model().rowCount()):
            data = self._table.model().get_data_at(row)
            if data:
                total += data.get("download_speed") or 0
        self._speed_widget.set_speed(total)
        self._browser_server.drain_queue()

    def _quit_app(self) -> None:
        self._really_quit = True
        self.close()

    def closeEvent(self, event) -> None:
        if not getattr(self, "_really_quit", False):
            event.ignore()
            self.hide()
            return
        self._clipboard_monitor.stop()
        self._speed_timer.stop()
        self._browser_server.stop()
        self._tray.hide()
        self._download_manager.stop_polling()
        self._aria2.stop()
        event.accept()
