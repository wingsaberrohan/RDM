"""Download list: QTableView with model and progress bar delegate."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QMenu,
    QMessageBox,
    QStyle,
    QStyleOptionProgressBar,
    QStyledItemDelegate,
    QTableView,
)

from rdm.utils.file_utils import format_size


class ProgressBarDelegate(QStyledItemDelegate):
    """Draw a progress bar in the Progress column."""

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.UserRole)
        if value is None:
            super().paint(painter, option, index)
            return
        try:
            pct = float(value)
        except (TypeError, ValueError):
            super().paint(painter, option, index)
            return
        pct = min(100, max(0, pct))
        style = QApplication.style() if QApplication.instance() else None
        if style:
            opt = QStyleOptionProgressBar()
            opt.rect = option.rect
            opt.minimum = 0
            opt.maximum = 100
            opt.progress = int(pct)
            opt.textVisible = True
            opt.text = f"{pct:.0f}%"
            style.drawControl(QStyle.ControlElement.CE_ProgressBar, opt, painter)
        else:
            painter.save()
            painter.fillRect(option.rect, option.palette.base())
            w = option.rect.width() * pct / 100
            painter.fillRect(option.rect.x(), option.rect.y(), int(w), option.rect.height(), option.palette.highlight())
            painter.restore()

    def createEditor(self, parent, option, index):
        return None


class DownloadTableModel(QAbstractTableModel):
    """Table model: list of download dicts (gid -> data)."""

    COLUMNS = ("Name", "Size", "Progress", "Speed", "Status", "ETA")
    COL_NAME, COL_SIZE, COL_PROGRESS, COL_SPEED, COL_STATUS, COL_ETA = range(6)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: List[Dict[str, Any]] = []
        self._gid_to_row: Dict[str, int] = {}

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_NAME:
                return row.get("name", "—")
            if col == self.COL_SIZE:
                return format_size(row.get("total_length"))
            if col == self.COL_PROGRESS:
                total = row.get("total_length") or 0
                completed = row.get("completed_length") or 0
                if total and total > 0:
                    return f"{100 * completed / total:.1f}%"
                return "—"
            if col == self.COL_SPEED:
                speed = row.get("download_speed") or 0
                return f"{format_size(int(speed))}/s" if speed else "—"
            if col == self.COL_STATUS:
                return row.get("status", "—")
            if col == self.COL_ETA:
                eta = row.get("eta_seconds")
                if eta is not None and eta > 0:
                    m = int(eta // 60)
                    s = int(eta % 60)
                    return f"{m}:{s:02d}"
                return "—"
        if role == Qt.ItemDataRole.UserRole:
            if col == self.COL_PROGRESS:
                total = row.get("total_length") or 0
                completed = row.get("completed_length") or 0
                if total and total > 0:
                    return 100 * completed / total
            if col == 0:
                return row.get("gid")
        return None

    def add_download(self, data: Dict[str, Any]) -> None:
        gid = data.get("gid")
        if not gid or gid in self._gid_to_row:
            return
        row_idx = len(self._rows)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx)
        self._rows.append(data)
        self._gid_to_row[gid] = row_idx
        self.endInsertRows()

    def update_download(self, gid: str, data: Dict[str, Any]) -> None:
        row_idx = self._gid_to_row.get(gid)
        if row_idx is None:
            return
        if row_idx >= len(self._rows):
            self._gid_to_row.pop(gid, None)
            return
        self._rows[row_idx] = data
        top = self.index(row_idx, 0)
        bottom = self.index(row_idx, self.columnCount() - 1)
        self.dataChanged.emit(top, bottom)

    def remove_download(self, gid: str) -> None:
        row_idx = self._gid_to_row.get(gid)
        if row_idx is None:
            return
        self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
        self._rows.pop(row_idx)
        self._gid_to_row.pop(gid)
        for g, r in list(self._gid_to_row.items()):
            if r > row_idx:
                self._gid_to_row[g] = r - 1
        self.endRemoveRows()

    def get_gid_at(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._rows):
            return self._rows[row].get("gid")
        return None

    def get_data_at(self, row: int) -> Optional[Dict[str, Any]]:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


class DownloadTableView(QTableView):
    """Table view with progress delegate and context menu."""

    def __init__(self, download_manager, parent=None):
        super().__init__(parent)
        self._download_manager = download_manager
        self._model = DownloadTableModel(self)
        self.setModel(self._model)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(DownloadTableModel.COL_NAME, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        delegate = ProgressBarDelegate(self)
        self.setItemDelegateForColumn(DownloadTableModel.COL_PROGRESS, delegate)

    def set_download_manager(self, dm) -> None:
        self._download_manager = dm

    def model(self) -> DownloadTableModel:
        return self._model

    def _show_context_menu(self, pos):
        if not self._download_manager:
            return
        idx = self.indexAt(pos)
        if not idx.isValid():
            return
        gid = self._model.get_gid_at(idx.row())
        if not gid:
            return
        data = self._model.get_data_at(idx.row())
        status = (data or {}).get("status", "")

        menu = QMenu(self)
        if status == "active":
            menu.addAction("Pause", lambda: self._download_manager.pause(gid))
        elif status in ("paused", "waiting"):
            menu.addAction("Resume", lambda: self._download_manager.resume(gid))
        menu.addAction("Remove", lambda: self._confirm_remove(gid))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _confirm_remove(self, gid: str) -> None:
        reply = QMessageBox.question(
            self,
            "Remove download",
            "Remove this download from the list? (File on disk will not be deleted.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self._download_manager:
            self._download_manager.remove(gid)
