"""Category sidebar: tree of categories with download counts, filter by category."""

from pathlib import Path
from typing import Callable, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rdm.core.category import (
    DEFAULT_CATEGORIES,
    get_all_categories,
    get_save_path_for_category,
    set_save_path_for_category,
)


class CategoryPanel(QWidget):
    """Left sidebar showing categories and counts. Emits category_selected when user selects one."""

    category_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(("Category", "Count"))
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._tree.setColumnWidth(1, 50)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(QLabel("Categories"))
        layout.addWidget(self._tree)

        self._counts: Dict[str, int] = {}
        self._items: Dict[str, QTreeWidgetItem] = {}
        for cat in get_all_categories():
            item = QTreeWidgetItem([cat, "0"])
            self._tree.addTopLevelItem(item)
            self._items[cat] = item
            self._counts[cat] = 0
        # All
        self._all_item = QTreeWidgetItem(["All", "0"])
        self._tree.insertTopLevelItem(0, self._all_item)
        self._items[""] = self._all_item
        self._counts[""] = 0

    def set_category_count(self, category: str, count: int) -> None:
        """Update the count displayed for a category."""
        self._counts[category] = count
        if category in self._items:
            self._items[category].setText(1, str(count))
        if category == "":
            self._all_item.setText(1, str(count))

    def set_all_counts(self, counts: Dict[str, int]) -> None:
        """Update counts for all categories. counts can be {category: count}."""
        total = 0
        for cat in get_all_categories():
            c = counts.get(cat, 0)
            self._counts[cat] = c
            total += c
            if cat in self._items:
                self._items[cat].setText(1, str(c))
        self._counts[""] = total
        self._all_item.setText(1, str(total))

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            return
        item = items[0]
        name = item.text(0)
        if name == "All":
            self.category_selected.emit("")
        elif name in self._items:
            self.category_selected.emit(name)

    def _show_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if not item:
            return
        name = item.text(0)
        if name == "All":
            return
        menu = QMenu(self)
        menu.addAction("Set save path...", lambda: self._set_save_path(name))
        path = get_save_path_for_category(name)
        if path:
            menu.addAction("Clear save path", lambda: self._clear_save_path(name))
        menu.exec(self._tree.mapToGlobal(pos))

    def _set_save_path(self, category: str) -> None:
        current = get_save_path_for_category(category)
        path = QFileDialog.getExistingDirectory(self, f"Save path for {category}", str(current or Path.home()))
        if path:
            set_save_path_for_category(category, Path(path))

    def _clear_save_path(self, category: str) -> None:
        set_save_path_for_category(category, None)

    def get_selected_category(self) -> str:
        """Return currently selected category name or '' for All."""
        items = self._tree.selectedItems()
        if not items:
            return ""
        name = items[0].text(0)
        return "" if name == "All" else name
