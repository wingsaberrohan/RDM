"""Batch add downloads: multiple URLs, URL patterns, import from file."""

import re
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from rdm.utils.url_utils import is_downloadable_url


def expand_pattern(pattern: str) -> List[str]:
    """Expand pattern like file_[001-100].jpg to list of URLs (if base URL given) or filenames."""
    urls = []
    # Match [001-100] or [1-10] style
    match = re.search(r"\[(\d+)-(\d+)\]", pattern)
    if not match:
        return [pattern.strip()] if pattern.strip() else []
    start = int(match.group(1))
    end = int(match.group(2))
    width = len(match.group(1))
    fmt = f"{{:0{width}d}}"
    for i in range(start, end + 1):
        repl = re.sub(r"\[\d+-\d+\]", fmt.format(i), pattern, count=1)
        urls.append(repl)
    return urls


class BatchDownloadDialog(QDialog):
    """Dialog to add multiple URLs; supports pasted list and import from file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Download")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter one URL per line, or use pattern e.g. http://example.com/file_[001-010].zip"))
        self._text = QTextEdit()
        self._text.setPlaceholderText("https://...\nhttps://...\n or file_[001-005].jpg")
        self._text.setMinimumHeight(120)
        layout.addWidget(self._text)
        import_btn = QPushButton("Import from file...")
        import_btn.clicked.connect(self._import_file)
        layout.addWidget(import_btn)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select text file with URLs", "", "Text (*.txt);;All (*)")
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8", errors="replace")
                self._text.setPlainText(content)
            except Exception:
                pass

    def get_urls(self) -> List[str]:
        """Return list of URLs (expanded from patterns, filtered to valid URLs)."""
        lines = self._text.toPlainText().strip().splitlines()
        urls = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            expanded = expand_pattern(line)
            for u in expanded:
                if u and is_downloadable_url(u):
                    urls.append(u)
        return urls
