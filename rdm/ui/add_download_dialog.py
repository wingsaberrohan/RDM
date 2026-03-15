"""Add new download dialog: URL, save path, filename, connection count."""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from rdm.utils.url_utils import filename_from_url, is_downloadable_url


class AddDownloadDialog(QDialog):
    """Dialog to add a single download."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add Download")
        layout = QFormLayout(self)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://...")
        self._url_edit.textChanged.connect(self._on_url_changed)
        layout.addRow("URL:", self._url_edit)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Save directory (optional)")
        default_dir = Path.home() / "Downloads"
        self._path_edit.setText(str(default_dir))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self._path_edit)
        path_layout.addWidget(browse_btn)
        layout.addRow("Save to:", path_row)

        self._filename_edit = QLineEdit()
        self._filename_edit.setPlaceholderText("Leave empty to use server filename")
        layout.addRow("Filename:", self._filename_edit)

        self._connections_spin = QSpinBox()
        self._connections_spin.setRange(1, 16)
        self._connections_spin.setValue(8)
        layout.addRow("Connections:", self._connections_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_url_changed(self, text: str) -> None:
        text = text.strip()
        if not self._filename_edit.text().strip() and is_downloadable_url(text):
            name = filename_from_url(text)
            if name:
                self._filename_edit.setText(name)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose save directory", self._path_edit.text())
        if path:
            self._path_edit.setText(path)

    def get_url(self) -> str:
        return self._url_edit.text().strip()

    def get_save_dir(self) -> Optional[Path]:
        p = self._path_edit.text().strip()
        if not p:
            return None
        path = Path(p)
        return path if path.is_dir() else path.parent

    def get_filename(self) -> Optional[str]:
        s = self._filename_edit.text().strip()
        return s or None

    def get_connections(self) -> int:
        return self._connections_spin.value()
