"""Application setup: QApplication, single-instance lock, and run loop."""

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

# Single-instance lock file (in user data dir)
LOCK_DIR = Path.home() / ".rdm"
LOCK_FILE = LOCK_DIR / "rdm.lock"


def run_app() -> int:
    """Create QApplication, enforce single instance, then run main window. Returns exit code."""
    app = QApplication(sys.argv)
    app.setApplicationName("RDM")
    app.setApplicationDisplayName("RDM - Rohan's Download Manager")
    app.setOrganizationName("RDM")

    from rdm.ui.themes import apply_theme, THEME_SYSTEM
    apply_theme(THEME_SYSTEM)

    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = QLockFile(str(LOCK_FILE))
    if not lock_file.tryLock():
        QMessageBox.warning(
            None,
            "RDM",
            "Another instance of RDM is already running.",
            QMessageBox.StandardButton.Ok,
        )
        return 1

    from rdm.ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()
