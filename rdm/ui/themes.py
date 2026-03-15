"""Light and dark QSS themes and system theme detection."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

# Theme names
THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_SYSTEM = "system"

# Directory for style sheets
STYLES_DIR = Path(__file__).resolve().parent.parent / "resources" / "styles"

LIGHT_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f5f5;
}
QToolBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #ccc;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    padding: 6px 12px;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
}
QToolButton:hover {
    background-color: #d0d0d0;
}
QTableView {
    background-color: white;
    alternate-background-color: #f9f9f9;
    gridline-color: #e0e0e0;
}
QTableView::item:selected {
    background-color: #cce0ff;
}
QHeaderView::section {
    background-color: #e8e8e8;
    padding: 6px;
    border: none;
    border-right: 1px solid #ccc;
    border-bottom: 1px solid #ccc;
}
QTreeWidget {
    background-color: white;
}
QStatusBar {
    background-color: #e8e8e8;
    border-top: 1px solid #ccc;
}
QLineEdit, QSpinBox {
    padding: 4px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
}
QPushButton {
    padding: 6px 14px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
QPushButton:pressed {
    background-color: #d0d0d0;
}
"""

DARK_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #2d2d2d;
}
QToolBar {
    background-color: #383838;
    border-bottom: 1px solid #505050;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    padding: 6px 12px;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #e0e0e0;
}
QToolButton:hover {
    background-color: #505050;
}
QTableView {
    background-color: #353535;
    alternate-background-color: #3a3a3a;
    gridline-color: #505050;
    color: #e0e0e0;
}
QTableView::item:selected {
    background-color: #2060a0;
}
QHeaderView::section {
    background-color: #383838;
    color: #e0e0e0;
    padding: 6px;
    border: none;
    border-right: 1px solid #505050;
    border-bottom: 1px solid #505050;
}
QTreeWidget {
    background-color: #353535;
    color: #e0e0e0;
}
QStatusBar {
    background-color: #383838;
    border-top: 1px solid #505050;
    color: #e0e0e0;
}
QLineEdit, QSpinBox {
    padding: 4px;
    border: 1px solid #505050;
    border-radius: 4px;
    background-color: #404040;
    color: #e0e0e0;
}
QPushButton {
    padding: 6px 14px;
    background-color: #404040;
    border: 1px solid #505050;
    border-radius: 4px;
    color: #e0e0e0;
}
QPushButton:hover {
    background-color: #505050;
}
QPushButton:pressed {
    background-color: #606060;
}
QLabel {
    color: #e0e0e0;
}
"""


def _is_system_dark() -> bool:
    """Heuristic: check if system palette suggests dark mode."""
    app = QApplication.instance()
    if not app:
        return False
    try:
        from PySide6.QtGui import QPalette
        bg = app.palette().color(QPalette.ColorGroup.Current, QPalette.ColorRole.Window)
        return bg.lightness() < 128
    except Exception:
        return False


def get_effective_theme(theme_name: str) -> str:
    """Return THEME_LIGHT or THEME_DARK from theme name (THEME_SYSTEM -> system detection)."""
    if theme_name == THEME_SYSTEM:
        return THEME_DARK if _is_system_dark() else THEME_LIGHT
    return THEME_DARK if theme_name == THEME_DARK else THEME_LIGHT


def apply_theme(theme_name: str) -> None:
    """Apply theme by name. theme_name: 'light' | 'dark' | 'system'."""
    effective = get_effective_theme(theme_name)
    qss = DARK_QSS if effective == THEME_DARK else LIGHT_QSS
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)


def load_stylesheet(filename: str) -> Optional[str]:
    """Load QSS from resources/styles/filename if it exists."""
    path = STYLES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None
