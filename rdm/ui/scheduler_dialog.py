"""Schedule downloads: start at time, shutdown when idle."""

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QTimeEdit,
    QVBoxLayout,
)

from rdm.core.scheduler import DownloadScheduler


class SchedulerDialog(QDialog):
    """Dialog to set schedule: start downloads at time, optional shutdown when idle."""

    def __init__(self, scheduler: Optional[DownloadScheduler] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule")
        self._scheduler = scheduler
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._time_edit = QTimeEdit()
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setTime(datetime.now().time())
        form.addRow("Start downloads at:", self._time_edit)
        self._shutdown_check = QCheckBox("Shutdown when all downloads complete")
        self._shutdown_check.setChecked(False)
        form.addRow("", self._shutdown_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        from datetime import date, time, timedelta
        t = self._time_edit.time()
        when = datetime.combine(date.today(), time(t.hour(), t.minute(), t.second()))
        if when < datetime.now():
            when += timedelta(days=1)
        if self._scheduler:
            self._scheduler.schedule_start_at(when)
            if self._shutdown_check.isChecked():
                def shutdown():
                    import os
                    os._exit(0)
                self._scheduler.schedule_shutdown_when_idle(shutdown)
                main = self.parent()
                if main and hasattr(main, "get_download_manager"):
                    self._scheduler.set_is_idle_check(lambda: main.get_download_manager().is_idle())
        QMessageBox.information(self, "Scheduled", f"Downloads will start at {when.strftime('%H:%M')}.")
        self.accept()
