"""Settings dialog: theme, default path, connections, speed limit."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from rdm.ui.themes import THEME_DARK, THEME_LIGHT, THEME_SYSTEM, apply_theme


class SettingsDialog(QDialog):
    """Application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._default_dir_edit = QLineEdit()
        self._default_dir_edit.setPlaceholderText("Default download folder")
        form.addRow("Default folder:", self._default_dir_edit)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["System", "Light", "Dark"])
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form.addRow("Theme:", self._theme_combo)
        self._speed_limit_spin = QSpinBox()
        self._speed_limit_spin.setRange(0, 1024 * 1024)
        self._speed_limit_spin.setSuffix(" KiB/s (0 = unlimited)")
        self._speed_limit_spin.setValue(0)
        form.addRow("Speed limit:", self._speed_limit_spin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_theme_changed(self, text: str) -> None:
        name = THEME_SYSTEM if text == "System" else (THEME_DARK if text == "Dark" else THEME_LIGHT)
        apply_theme(name)

    def _on_accept(self) -> None:
        main = self.parent()
        if main and hasattr(main, "get_speed_limiter"):
            kbps = self._speed_limit_spin.value()
            main.get_speed_limiter().set_global_limit_kbps(kbps)
            if hasattr(main, "_speed_widget"):
                main._speed_widget.set_limit(kbps)
        self.accept()
